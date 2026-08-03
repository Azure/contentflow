"""
SQL Database Document Retriever Executor.

Queries a SQL database (e.g., Azure SQL / SQL Server) to discover documents
associated with a case, then downloads those files from a source blob storage
and uploads them to the customer's target blob storage for pipeline processing.

Designed for the SARSP pharmacy license validation workflow where document
file references are stored in a relational database.
"""

import asyncio
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import aiohttp

from agent_framework import WorkflowContext

from .base import BaseExecutor
from ..models import Content, ContentIdentifier, ExecutorLogEntry
from ..connectors import AzureBlobConnector
from ..utils.credential_provider import get_azure_credential

logger = logging.getLogger("contentflow.executors.sql_database_document_retriever_executor")


class SQLDatabaseDocumentRetrieverExecutor(BaseExecutor):
    """
    Query a SQL database for document references and retrieve files to blob storage.

    This executor connects to a SQL database (Azure SQL / SQL Server), executes a
    parameterised query to discover documents for a given case, downloads each file
    from its source URL, and uploads it to the customer's Azure Blob Storage container.

    Workflow:
        1. Read the case_number from the incoming Content item.
        2. Execute the configured SQL query against the database.
        3. For each row returned, download the file from the FileUrl column.
        4. Upload the file to the target blob container under input/{case_number}/.
        5. Emit one Content item per downloaded document for downstream processing.

    Configuration (settings dict):
        Database Connection:
            - sql_connection_string (str): ODBC/pyodbc connection string for the database.
              Supports ${ENV_VAR} syntax. Required.
              Example: "Driver={ODBC Driver 18 for SQL Server};Server=tcp:myserver.database.windows.net,1433;Database=mydb;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30"
            - sql_use_managed_identity (bool): Use DefaultAzureCredential for SQL auth
              instead of username/password in the connection string.
              Default: False
            - sql_query (str): Parameterised SQL query with {case_number} placeholder.
              Required.

        Source File Access:
            - source_auth_method (str): How to authenticate when downloading source files.
              Options: "sas_in_url" (URL already contains SAS token),
                       "managed_identity" (use DefaultAzureCredential for source blob),
                       "source_sas_token" (append a configured SAS token),
                       "source_account_key" (use AzureBlobConnector with account key).
              Default: "sas_in_url"
            - source_sas_token (str): SAS token to append to source URLs
              (when source_auth_method is "source_sas_token"). Supports ${ENV_VAR}.
              Default: None
            - source_storage_account (str): Source storage account name (required for
              "managed_identity" and "source_account_key" auth methods).
              Default: None
            - source_storage_account_key (str): Source storage account key
              (when source_auth_method is "source_account_key"). Supports ${ENV_VAR}.
              Default: None

        Target Blob Storage:
            - target_storage_account (str): Target Azure Storage account name. Required.
            - target_container_name (str): Target container name. Required.
            - target_credential_type (str): "default_azure_credential" or "azure_key_credential".
              Default: "default_azure_credential"
            - target_storage_account_key (str): Storage key (if using azure_key_credential).
              Default: None
            - target_path_template (str): Blob path template for uploaded files.
              Supports: {case_number}, {execution_id}, {file_id}, {filename}
              Default: "input/{case_number}_{execution_id}/"

        Query Result Mapping:
            - case_number_field (str): Field in content.data containing the case number.
              Default: "case_number"
            - file_url_column (str): Column name in SQL results containing the file URL.
              Default: "Fileurl"
            - file_id_column (str): Column name for the file identifier.
              Default: "FileId"
            - document_type_column (str): Column name for document/requirement type.
              Default: "RequirementName"
            - process_type_column (str): Column name for the process type.
              Default: "ProcessAlias"
            - status_column (str): Column name for the case status.
              Default: "StatusAlias"

        Behaviour:
            - max_concurrent_downloads (int): Max parallel file downloads.
              Default: 5
            - download_timeout_secs (int): Timeout per file download in seconds.
              Default: 120
            - continue_on_download_error (bool): Continue if a single file fails to download.
              Default: True
            - skip_existing (bool): Skip upload if blob already exists at target path.
              Default: False

    Example Pipeline YAML:
        ```yaml
        - id: sql_document_retriever
          type: sql_database_document_retriever
          settings:
            sql_connection_string: "${SQL_CONNECTION_STRING}"
            sql_use_managed_identity: true
            sql_query: |
              SELECT
                up.CaseNumber,
                s.StatusAlias,
                pt.ProcessAlias,
                r.RequirementAlias AS RequirementName,
                upr.FileId,
                'https://saluddigitalprodstorage.blob.core.windows.net/uploadedfilesr/' + upr.FileId AS Fileurl
              FROM process.UserProcess up
              LEFT JOIN process.ProcessType pt ON pt.Id = up.ProcessTypeId
              LEFT JOIN sct.Status s ON s.Id = up.CurrentStatusId
              LEFT JOIN process.UserProcessRequirement upr ON upr.ProcessId = up.Id
              LEFT JOIN process.Requirement r ON r.Id = upr.RequirementId
              WHERE up.CaseNumber = '{case_number}'
                AND r.RequirementTypeId = 2
                AND upr.IsComplete = 1
                AND upr.FileId IS NOT NULL
                AND up.CurrentStatusId <> -12
            target_storage_account: "${AZURE_STORAGE_ACCOUNT_NAME}"
            target_container_name: "content"
            target_path_template: "input/{case_number}_{execution_id}/"
            case_number_field: "case_number"
            file_url_column: "Fileurl"
            file_id_column: "FileId"
            document_type_column: "RequirementName"
            max_concurrent_downloads: 5
            continue_on_download_error: true
        ```

    Input:
        Content item with data[case_number_field] containing the case number to query.

    Output:
        List[Content] — one Content item per downloaded document, each containing:
        - data["temp_file_path"]: Local temp file path of the downloaded document
        - data["file_id"]: The FileId from the database
        - data["document_type"]: The RequirementName / document type
        - data["process_type"]: The ProcessAlias
        - data["status"]: The StatusAlias
        - data["source_url"]: The original source URL
        - data["blob_path"]: The target blob path where the file was uploaded
        - id.path: Target blob path
        - id.container: Target container name
    """

    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(id=id, settings=settings, **kwargs)

        # ---- Database connection ----
        self.sql_connection_string = self.get_setting("sql_connection_string", required=True)
        self.sql_use_managed_identity = self.get_setting("sql_use_managed_identity", default=False)
        self.sql_query = self.get_setting("sql_query", required=True)

        # ---- Source file access ----
        self.source_auth_method = self.get_setting("source_auth_method", default="sas_in_url")
        if self.source_auth_method not in ("sas_in_url", "managed_identity", "source_sas_token", "source_account_key"):
            raise ValueError(
                f"{self.id}: Invalid source_auth_method '{self.source_auth_method}'. "
                "Must be 'sas_in_url', 'managed_identity', 'source_sas_token', or 'source_account_key'."
            )
        self.source_sas_token = self.get_setting("source_sas_token", default=None)
        self.source_storage_account = self.get_setting("source_storage_account", default=None)
        self.source_storage_account_key = self.get_setting("source_storage_account_key", default=None)

        # ---- Target blob storage ----
        self.target_storage_account = self.get_setting("target_storage_account", required=True)
        self.target_container_name = self.get_setting("target_container_name", required=True)
        self.target_credential_type = self.get_setting(
            "target_credential_type", default="default_azure_credential"
        )
        self.target_storage_account_key = self.get_setting("target_storage_account_key", default=None)
        self.target_path_template = self.get_setting(
            "target_path_template", default="input/{case_number}_{execution_id}/"
        )

        # ---- Query result column mapping ----
        self.default_case_number = self.get_setting("default_case_number", default=None)
        self.case_number_field = self.get_setting("case_number_field", default="case_number")
        self.file_url_column = self.get_setting("file_url_column", default="Fileurl")
        self.file_id_column = self.get_setting("file_id_column", default="FileId")
        self.document_type_column = self.get_setting("document_type_column", default="RequirementName")
        self.process_type_column = self.get_setting("process_type_column", default="ProcessAlias")
        self.status_column = self.get_setting("status_column", default="StatusAlias")

        # ---- Behaviour ----
        self.max_concurrent_downloads = self.get_setting("max_concurrent_downloads", default=5)
        self.download_timeout_secs = self.get_setting("download_timeout_secs", default=120)
        self.continue_on_download_error = self.get_setting("continue_on_download_error", default=True)
        self.skip_existing = self.get_setting("skip_existing", default=False)

        # ---- Temp folder for downloads ----
        self.temp_folder = self.get_setting("temp_folder", default="./tmp/contentflow")
        os.makedirs(self.temp_folder, exist_ok=True)

        # Lazy-initialised connectors
        self._target_blob_connector: Optional[AzureBlobConnector] = None
        self._source_blob_connector: Optional[AzureBlobConnector] = None

        if self.debug_mode:
            logger.debug(
                f"SQLDatabaseDocumentRetrieverExecutor '{self.id}' initialized: "
                f"target={self.target_storage_account}/{self.target_container_name}"
            )

    # ------------------------------------------------------------------
    # Connector lifecycle
    # ------------------------------------------------------------------

    async def _get_target_blob_connector(self) -> AzureBlobConnector:
        """Lazily initialize the target blob storage connector."""
        if self._target_blob_connector is None:
            self._target_blob_connector = AzureBlobConnector(
                name=f"target_blob_{self.id}",
                settings={
                    "account_name": self.target_storage_account,
                    "credential_type": self.target_credential_type,
                    "credential_key": self.target_storage_account_key,
                },
            )
            await self._target_blob_connector.initialize()
        return self._target_blob_connector

    async def _get_source_blob_connector(self) -> AzureBlobConnector:
        """Lazily initialize the source blob storage connector (for managed_identity or account_key auth)."""
        if self._source_blob_connector is None:
            if not self.source_storage_account:
                raise ValueError(
                    f"{self.id}: source_storage_account is required when "
                    "source_auth_method is 'managed_identity' or 'source_account_key'."
                )
            connector_settings = {
                "account_name": self.source_storage_account,
            }
            if self.source_auth_method == "source_account_key":
                connector_settings["credential_type"] = "azure_key_credential"
                connector_settings["credential_key"] = self.source_storage_account_key
            else:
                connector_settings["credential_type"] = "default_azure_credential"

            self._source_blob_connector = AzureBlobConnector(
                name=f"source_blob_{self.id}",
                settings=connector_settings,
            )
            await self._source_blob_connector.initialize()
        return self._source_blob_connector

    # ------------------------------------------------------------------
    # SQL execution
    # ------------------------------------------------------------------

    async def _execute_sql_query(self, case_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """Execute the SQL query and return rows as a list of dictionaries.

        Uses pyodbc for database connectivity. If case_number is provided,
        the {case_number} placeholder is parameterised. If None, the query
        runs as-is (bulk mode).
        """
        import pyodbc

        if case_number and "{case_number}" in self.sql_query:
            # Parameterised query — replace placeholder with ?
            query = self.sql_query.replace("{case_number}", "?")
            params = (case_number,)
        else:
            # Bulk query — no parameter substitution needed
            query = self.sql_query
            params = None

        # Run the blocking pyodbc call in a thread pool
        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(
            None, self._sync_execute_query, query, params
        )
        return rows

    def _sync_execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Synchronous SQL query execution (runs in thread pool)."""
        import pyodbc

        connection_string = self.sql_connection_string

        # If using managed identity, add the token to the connection
        if self.sql_use_managed_identity:
            credential = get_azure_credential()
            token = credential.get_token("https://database.windows.net/.default")
            # For pyodbc with Azure AD token auth
            import struct
            token_bytes = token.token.encode("utf-16-le")
            token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
            conn = pyodbc.connect(
                connection_string,
                attrs_before={1256: token_struct}  # SQL_COPT_SS_ACCESS_TOKEN
            )
        else:
            conn = pyodbc.connect(connection_string)

        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = []
            for row in cursor.fetchall():
                rows.append(dict(zip(columns, row)))
            return rows
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # File download
    # ------------------------------------------------------------------

    async def _download_file(self, file_url: str, file_id: str) -> Optional[str]:
        """Download a file from the source URL to a local temp file.

        Returns the local temp file path, or None on failure.
        """
        # Determine the file extension from the URL or default to empty
        parsed = urlparse(file_url.split("?")[0])  # Strip SAS params
        path_part = parsed.path
        ext = os.path.splitext(path_part)[1] if path_part else ""
        if not ext:
            ext = ""  # Will be detected later or default to .bin

        local_path = os.path.join(self.temp_folder, f"{file_id}{ext}")

        if self.source_auth_method in ("managed_identity", "source_account_key"):
            # Use the source blob connector to download directly
            return await self._download_via_blob_connector(file_url, local_path)
        else:
            # Download via HTTP (SAS token in URL or appended)
            return await self._download_via_http(file_url, local_path)

    async def _download_via_http(self, file_url: str, local_path: str) -> Optional[str]:
        """Download a file via HTTP(S) with optional SAS token."""
        url = file_url
        if self.source_auth_method == "source_sas_token" and self.source_sas_token:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{self.source_sas_token}"

        timeout = aiohttp.ClientTimeout(total=self.download_timeout_secs)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise RuntimeError(
                        f"HTTP {response.status} downloading {file_url}"
                    )
                content = await response.read()
                with open(local_path, "wb") as f:
                    f.write(content)
        return local_path

    async def _download_via_blob_connector(self, file_url: str, local_path: str) -> Optional[str]:
        """Download a file using the source blob connector (managed identity).
        
        Tries multiple container/blob path interpretations to handle URL formats like:
        https://account.blob.core.windows.net/uploadedfilesr/filename.pdf
        where actual container is 'uploadedfiles' and blob is 'filename.pdf'
        """
        parsed = urlparse(file_url)
        path_parts = parsed.path.lstrip("/").split("/", 1)
        if len(path_parts) < 2:
            raise ValueError(f"Cannot parse container/blob from URL: {file_url}")

        url_container = path_parts[0]
        url_blob = path_parts[1]

        connector = await self._get_source_blob_connector()

        # Try multiple container/blob combinations
        attempts = [
            (url_container, url_blob),                    # as-is from URL
            ("uploadedfiles", url_blob),                  # common container name
            ("uploadedfiles", f"{url_container[-1]}{url_blob}" if len(url_container) > 0 else url_blob),  # last char of container + blob
        ]

        last_error = None
        for container, blob_path in attempts:
            try:
                content_bytes = await connector.download_blob(
                    container_name=container,
                    blob_path=blob_path,
                )
                with open(local_path, "wb") as f:
                    f.write(content_bytes)
                return local_path
            except Exception as e:
                last_error = e
                continue

        raise last_error or ValueError(f"All download attempts failed for {file_url}")

    # ------------------------------------------------------------------
    # File upload to target
    # ------------------------------------------------------------------

    async def _upload_to_target(
        self, local_path: str, target_blob_path: str
    ) -> str:
        """Upload a local file to the target blob storage. Returns the blob path."""
        connector = await self._get_target_blob_connector()

        if self.skip_existing:
            exists = await connector.blob_exists(
                container_name=self.target_container_name,
                blob_path=target_blob_path,
            )
            if exists:
                logger.info(f"{self.id}: Skipping existing blob: {target_blob_path}")
                return target_blob_path

        with open(local_path, "rb") as f:
            data = f.read()

        await connector.upload_blob(
            container_name=self.target_container_name,
            blob_path=target_blob_path,
            data=data,
            overwrite=True,
        )
        return target_blob_path

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]],
    ) -> Union[Content, List[Content]]:
        """
        Main entry point: query DB, download files, upload to target, emit content items.
        """
        start_time = datetime.now(timezone.utc)
        contents = input if isinstance(input, list) else [input]
        if not contents or (isinstance(contents, list) and len(contents) == 0):
            # First executor in pipeline — no upstream input. Create a default Content.
            content = Content(
                id=ContentIdentifier(
                    canonical_id=f"sql_retriever_{self.id}",
                    unique_id=f"sql_retriever_{self.id}",
                ),
                data={},
            )
        else:
            content = contents[0]
        content_id = content.id.canonical_id if content.id else "unknown"

        # Extract case_number from content or use default (optional for bulk queries)
        case_number = self.try_extract_nested_field_from_content(content, self.case_number_field)
        if not case_number:
            case_number = self.default_case_number
        # case_number can be None for bulk queries without WHERE clause
        case_number = str(case_number) if case_number else None

        # Extract execution_id if available
        execution_id = (
            self.try_extract_nested_field_from_content(content, "execution_id")
            or content_id
        )

        logger.info(f"{self.id}: Querying database for case_number={case_number}")

        # Step 1: Query the SQL database
        try:
            rows = await self._execute_sql_query(case_number)
        except Exception as e:
            logger.error(f"{self.id}: SQL query failed for case {case_number}: {e}", exc_info=True)
            raise ValueError(f"Database query failed for case '{case_number}': {e}")

        if not rows:
            logger.warning(f"{self.id}: No documents found for case {case_number}")
            content.data["sql_retriever_status"] = "no_documents"
            content.data["sql_retriever_document_count"] = 0
            return content

        logger.info(f"{self.id}: Found {len(rows)} document(s) for case {case_number}")

        # Store case metadata from first row
        first_row = rows[0]
        content.data["case_status"] = first_row.get(self.status_column)
        content.data["process_type"] = first_row.get(self.process_type_column)

        # Step 2: Download and upload files concurrently
        target_prefix = self.target_path_template.format(
            case_number=case_number or "all",
            execution_id=execution_id,
        )

        semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        output_contents: List[Content] = []

        async def process_row(row: Dict[str, Any]) -> Optional[Content]:
            async with semaphore:
                return await self._process_single_document(
                    row, case_number, execution_id, target_prefix
                )

        tasks = [process_row(row) for row in rows]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                if self.continue_on_download_error:
                    logger.warning(
                        f"{self.id}: Failed to process document {i+1}/{len(rows)}: {result}"
                    )
                else:
                    raise result
            elif result is not None:
                output_contents.append(result)

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"{self.id}: Retrieved {len(output_contents)}/{len(rows)} documents "
            f"for case {case_number} in {elapsed:.2f}s"
        )

        # Store summary in the original content
        content.data["sql_retriever_status"] = "success"
        content.data["sql_retriever_document_count"] = len(output_contents)
        content.summary_data["sql_retriever_documents"] = len(output_contents)

        # Log execution
        content.executor_logs.append(ExecutorLogEntry(
            executor_id=self.id,
            start_time=start_time,
            end_time=datetime.now(timezone.utc),
            status="completed",
            details={
                "case_number": case_number,
                "documents_found": len(rows),
                "documents_retrieved": len(output_contents),
            },
            errors=[],
        ))

        if not output_contents:
            return content

        return output_contents

    async def _process_single_document(
        self,
        row: Dict[str, Any],
        case_number: str,
        execution_id: str,
        target_prefix: str,
    ) -> Optional[Content]:
        """Download a single document and create a Content item for it."""
        file_url = row.get(self.file_url_column)
        file_id = row.get(self.file_id_column)
        document_type = row.get(self.document_type_column, "Unknown")
        process_type = row.get(self.process_type_column)
        status = row.get(self.status_column)
        # Use CaseNumber from the row if available (for per-case folder organization)
        row_case_number = str(row.get("CaseNumber", case_number or "unknown"))

        if not file_url:
            logger.warning(f"{self.id}: Row missing '{self.file_url_column}', skipping")
            return None

        file_id_str = str(file_id) if file_id else "unknown"

        # Determine filename from URL
        parsed = urlparse(file_url.split("?")[0])
        url_filename = os.path.basename(parsed.path) if parsed.path else file_id_str
        # If the URL path is just the file_id (no extension), try to preserve it
        if not os.path.splitext(url_filename)[1]:
            url_filename = f"{url_filename}.pdf"  # Default to PDF for document files

        if self.debug_mode:
            logger.debug(f"{self.id}: Processing file_id={file_id_str}, url={file_url}")

        # Download file
        local_path = await self._download_file(file_url, file_id_str)
        if not local_path:
            return None

        # Upload to target blob storage — use row's CaseNumber for folder
        row_target_prefix = self.target_path_template.format(
            case_number=row_case_number,
            execution_id=execution_id,
        )
        target_blob_path = f"{row_target_prefix}{url_filename}"
        await self._upload_to_target(local_path, target_blob_path)

        # Create Content item for downstream processing
        content_item = Content(
            id=ContentIdentifier(
                canonical_id=f"{row_case_number}/{file_id_str}",
                unique_id=file_id_str,
                source_name="sql_database",
                source_type="azure_blob",
                container=self.target_container_name,
                path=target_blob_path,
                filename=url_filename,
                metadata={
                    "case_number": row_case_number,
                    "file_id": file_id_str,
                    "document_type": document_type,
                },
            ),
            data={
                "temp_file_path": local_path,
                "file_id": file_id_str,
                "document_type": document_type,
                "process_type": process_type,
                "status": status,
                "source_url": file_url,
                "blob_path": target_blob_path,
                "case_number": row_case_number,
                "execution_id": execution_id,
            },
            summary_data={
                "source": "sql_database_retriever",
                "blob_path": target_blob_path,
            },
        )

        if self.debug_mode:
            logger.debug(
                f"{self.id}: Document ready: file_id={file_id_str}, "
                f"type={document_type}, blob={target_blob_path}"
            )

        return content_item
