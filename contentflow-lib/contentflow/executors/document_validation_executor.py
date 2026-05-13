"""
Document Validation Executor for comparing fetched document details 
against provided details using configurable validation rules.

This executor reads FetchedDetails_*.json, ProvidedDetails.json, and rules.json
from an Azure Blob Storage folder, performs field-by-field comparison per document type,
and writes a consolidated results.json back to the same blob location.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union

try:
    from agent_framework.openai import OpenAIChatClient
    from agent_framework import Agent, AgentResponse
except ImportError:
    raise ImportError(
        "agent-framework import error. Either the library is not installed or there is "
        "an issue with the version of the installed library."
    )

from agent_framework import WorkflowContext

from .base import BaseExecutor
from ..models import Content, ExecutorLogEntry
from ..connectors import AzureBlobConnector
from ..utils.credential_provider import get_azure_credential

logger = logging.getLogger("contentflow.executors.document_validation_executor")


class DocumentValidationExecutor(BaseExecutor):
    """
    Validate fetched document details against provided details using rules.

    This executor reads FetchedDetails_*.json, ProvidedDetails.json, and rules.json from
    Azure Blob Storage, performs field-by-field comparison per document type using
    configurable validation types (exact match, date match, expiry check, name match,
    address match with AI-powered fuzzy comparison), and writes a consolidated
    results.json back to the same blob location.

    Configuration (settings dict):
        - blob_storage_account (str): Azure Storage account name
          Required: True
        - blob_container_name (str): Container where input files reside
          Required: True
        - blob_storage_credential_type (str): Credential type for blob storage
          Default: "default_azure_credential"
          Options: "default_azure_credential", "azure_key_credential"
        - blob_storage_account_key (str): Storage account key (if using azure_key_credential)
          Default: None
        - provided_details_filename (str): Name of the provided details file
          Default: "ProvidedDetails.json"
        - rules_filename (str): Name of the rules file
          Default: "rules.json"
        - fetched_details_prefix (str): Prefix for fetched details files
          Default: "FetchedDetails_"
        - output_filename (str): Name of the output results file
          Default: "results.json"
        - case_sensitive_comparison (bool): Whether string comparisons are case-sensitive
          Default: False
        - input_prefix_field (str): Field in content.data containing the blob prefix/folder path
          Default: "blob_path"
        - endpoint (str): Azure OpenAI endpoint URL for AI-powered address matching
          Default: None
        - deployment_name (str): Azure OpenAI model deployment name
          Default: None
        - credential_type (str): Azure credential type for OpenAI
          Default: "default_azure_credential"
          Options: "default_azure_credential", "azure_key_credential"
        - api_key (str): API key for Azure OpenAI (if using azure_key_credential)
          Default: None
        - temperature (float): Sampling temperature for AI address matching
          Default: 0.1

    Example:
        ```yaml
        - id: document_validator
          type: document_validation
          settings:
            blob_storage_account: "${AZURE_STORAGE_ACCOUNT_NAME}"
            blob_container_name: "inputs"
            provided_details_filename: "ProvidedDetails.json"
            rules_filename: "rules.json"
            output_filename: "results.json"
            endpoint: "${AZURE_OPENAI_ENDPOINT}"
            deployment_name: "gpt-4.1"
        ```

    Input:
        Content item representing a case folder (with blob_path in data from
        upstream blob discovery using virtual_folders mode)

    Output:
        Content with data["validation_results"] containing the consolidated results,
        and results.json written to the same blob folder.
    """

    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(id=id, settings=settings, **kwargs)

        # Blob storage config
        self.blob_storage_account = self.get_setting("blob_storage_account", required=True)
        self.blob_container_name = self.get_setting("blob_container_name", required=True)
        self.blob_storage_credential_type = self.get_setting(
            "blob_storage_credential_type", default="default_azure_credential"
        )
        self.blob_storage_account_key = self.get_setting("blob_storage_account_key", default=None)

        # File names
        self.provided_details_filename = self.get_setting("provided_details_filename", default="ProvidedDetails.json")
        self.rules_filename = self.get_setting("rules_filename", default="rules.json")
        self.fetched_details_prefix = self.get_setting("fetched_details_prefix", default="FetchedDetails_")
        self.output_filename = self.get_setting("output_filename", default="results.json")

        # Path settings
        self.base_path = self.get_setting("base_path", default=None)
        self.fetched_details_path = self.get_setting("fetched_details_path", default=None)
        self.fetched_details_path_field = self.get_setting("fetched_details_path_field", default="blob_output.blob_path")
        # Read rules_base_path directly from settings dict because get_setting
        # converts empty string to None, but empty string is a valid value
        # meaning "container root".
        self.rules_base_path = self.settings.get("rules_base_path", None)
        if isinstance(self.rules_base_path, str):
            self.rules_base_path = self.rules_base_path.strip()

        # Cleanup settings
        self.cleanup_input_after_results = self.get_setting("cleanup_input_after_results", default=False)
        self.cleanup_preserve_files = self.get_setting("cleanup_preserve_files", default="results.json")

        # Comparison settings
        self.case_sensitive = self.get_setting("case_sensitive_comparison", default=False)
        self.input_prefix_field = self.get_setting("input_prefix_field", default="blob_path")

        # Azure OpenAI config for AI-powered address matching
        self.openai_endpoint = self.get_setting("endpoint", default=None)
        self.openai_deployment_name = self.get_setting("deployment_name", default=None)
        self.openai_credential_type = self.get_setting("credential_type", default="default_azure_credential")
        self.openai_api_key = self.get_setting("api_key", default=None)
        self.temperature = self.get_setting("temperature", default=0.1)

        # Validate OpenAI credential config
        if self.openai_credential_type not in ["default_azure_credential", "azure_key_credential"]:
            raise ValueError(f"{self.id}: Invalid credential_type '{self.openai_credential_type}'")
        if self.openai_credential_type == "azure_key_credential" and not self.openai_api_key:
            raise ValueError(f"{self.id}: api_key must be provided for azure_key_credential")

        # Initialize blob connector
        self.blob_connector = AzureBlobConnector(
            name="validation_blob_connector",
            settings={
                "account_name": self.blob_storage_account,
                "credential_type": self.blob_storage_credential_type,
                "credential_key": self.blob_storage_account_key,
            }
        )

        # AI agent (lazily initialized)
        self.agent: Optional[Agent] = None

        if self.debug_mode:
            logger.debug(f"DocumentValidationExecutor {self.id} initialized")

    def _init_agent(self) -> None:
        """Initialize the AI agent for address matching."""
        client_kwargs = {
            "model": self.openai_deployment_name,
            "azure_endpoint": self.openai_endpoint,
            "credential": get_azure_credential() if self.openai_credential_type == "default_azure_credential" else None,
            "api_key": self.openai_api_key if self.openai_credential_type == "azure_key_credential" else None,
        }

        client = OpenAIChatClient(**client_kwargs)

        instructions = (
            "You are an address comparison expert. You will be given two addresses and must determine "
            "if they refer to the same physical location. Consider abbreviations, formatting differences, "
            "partial matches, and regional address conventions (especially Puerto Rico/US formats). "
            "Respond ONLY with a JSON object: {\"match\": true/false, \"confidence\": 0.0-1.0, \"reason\": \"brief explanation\"}"
        )

        self.agent = client.as_agent(
            id=f"{self.id}_address_agent",
            name=f"{self.id}_address_agent",
            instructions=instructions,
            default_options={
                "temperature": self.temperature,
                "max_tokens": 150
            },
        )

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """Main processing: load files, compare, produce results.
        
        Collects the exact blob paths written by upstream executors in the current run
        to ensure only current-execution FetchedDetails files are validated.
        """
        contents = input if isinstance(input, list) else [input]

        # Collect all specific FetchedDetails blob paths from current execution's content items.
        # Each content item processed by the upstream blob output executor carries its own
        # blob_output.blob_path in summary_data — these are the ONLY files from this run.
        current_run_blob_paths = self._collect_current_run_fetched_paths(contents)

        if isinstance(input, list):
            results = []
            for content in contents:
                results.append(await self._process_single(content, current_run_blob_paths))
            # Run cleanup ONCE after all content items are processed
            if self.cleanup_input_after_results and results:
                base_prefix = self._get_base_prefix(contents[0])
                await self.blob_connector.initialize()
                await self._cleanup_case_folder(base_prefix)
            return results

        result = await self._process_single(contents[0], current_run_blob_paths)
        # Run cleanup after the single item is processed
        if self.cleanup_input_after_results:
            base_prefix = self._get_base_prefix(contents[0])
            await self.blob_connector.initialize()
            await self._cleanup_case_folder(base_prefix)
        return result

    def _collect_current_run_fetched_paths(self, contents: List[Content]) -> List[str]:
        """Collect all FetchedDetails blob paths written by upstream executors in the current run.
        
        Iterates all content items and extracts their blob_output.blob_path values,
        filtering only those that match the fetched details prefix pattern.
        This ensures we ONLY process files from the current pipeline execution.
        """
        paths = []
        for content in contents:
            blob_path = self._resolve_nested_field(content.summary_data, self.fetched_details_path_field)
            if blob_path and isinstance(blob_path, str):
                filename = blob_path.split("/")[-1] if "/" in blob_path else blob_path
                if filename.startswith(self.fetched_details_prefix) and filename.endswith(".json"):
                    paths.append(blob_path)
        
        # Also check executor_logs from earlier executors in the same pipeline run
        # that may have written multiple files (e.g., content items processed in parallel)
        for content in contents:
            for log in content.executor_logs:
                if log.details and "blob_path" in log.details:
                    bp = log.details["blob_path"]
                    if isinstance(bp, str):
                        filename = bp.split("/")[-1] if "/" in bp else bp
                        if filename.startswith(self.fetched_details_prefix) and filename.endswith(".json"):
                            if bp not in paths:
                                paths.append(bp)

        return paths

    async def _process_single(self, content: Content, current_run_blob_paths: List[str]) -> Content:
        """Process a single case (folder)."""
        start_time = datetime.now(timezone.utc)
        content_id = content.id.canonical_id if content.id else "unknown"
        logger.info(f"{self.id}: Starting validation for content: {content_id}")

        try:
            # Initialize blob connector
            init_start = datetime.now(timezone.utc)
            await self.blob_connector.initialize()
            if self.debug_mode:
                init_elapsed = (datetime.now(timezone.utc) - init_start).total_seconds()
                logger.debug(f"{self.id}: Blob connector initialized in {init_elapsed:.2f}s")

            # Determine the blob prefix for ProvidedDetails, rules, and output
            base_prefix = self._get_base_prefix(content)
            # Determine where FetchedDetails files are stored (may differ from base)
            fetched_prefix = self._get_fetched_details_prefix(content)

            logger.info(f"{self.id}: Base path: {base_prefix}, Fetched details path: {fetched_prefix}")

            # Step 1: Load ProvidedDetails.json
            provided_details = await self._load_json_from_blob(base_prefix, self.provided_details_filename)
            if self.debug_mode:
                logger.debug(f"{self.id}: Loaded ProvidedDetails with {len(provided_details.get('documents', []))} documents")

            # Step 2: Load rules.json (from rules_base_path if set, else from base_prefix)
            rules_prefix = self._get_rules_prefix()
            if rules_prefix is None:
                rules_prefix = base_prefix
            rules = await self._load_json_from_blob(rules_prefix, self.rules_filename)
            if self.debug_mode:
                logger.debug(f"{self.id}: Loaded rules with {len(rules.get('rules', []))} document type rules")

            # Step 3: Load FetchedDetails - prefer exact paths from current run over folder listing
            fetched_details_list = await self._load_fetched_details_for_current_run(
                current_run_blob_paths, fetched_prefix
            )
            if self.debug_mode:
                logger.debug(f"{self.id}: Loaded {len(fetched_details_list)} fetched detail entries")

            # Step 4: Run validation
            results = await self._run_validation(provided_details, fetched_details_list, rules)

            # Step 5: Write results.json to base path
            await self._write_results_to_blob(base_prefix, results)

            # Step 6: Store results in content for downstream use
            # Note: cleanup is handled in process_input() after ALL items are done
            content.data["validation_results"] = results
            content.summary_data["validation_status"] = results.get("summary", {}).get("overallStatus", "unknown")
            content.summary_data["executor_status"] = "success"

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                f"{self.id}: Validation complete for {content_id} in {elapsed:.2f}s - "
                f"Status: {results['summary']['overallStatus']}, "
                f"Passed: {results['summary']['passed']}, Failed: {results['summary']['failed']}"
            )

            # Append executor log entry for pipeline status tracking
            content.executor_logs.append(ExecutorLogEntry(
                executor_id=self.id,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                status="completed",
                details={
                    "total_documents": results["summary"]["totalDocuments"],
                    "passed": results["summary"]["passed"],
                    "failed": results["summary"]["failed"],
                },
                errors=[]
            ))

        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(
                f"{self.id}: Validation failed for {content_id} after {elapsed:.2f}s: {e}",
                exc_info=True
            )
            content.summary_data["executor_status"] = "failed"
            content.executor_logs.append(ExecutorLogEntry(
                executor_id=self.id,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                status="failed",
                details={},
                errors=[str(e)]
            ))
            raise

        return content

    def _get_base_prefix(self, content: Content) -> str:
        """Get the base path for ProvidedDetails, rules, and results output.
        
        Priority: static base_path setting > content field > content.id.path
        """
        # If static base_path is set, use it directly
        if self.base_path:
            path = self.base_path.strip("/")
            return f"{path}/" if path else ""

        # Fall back to dynamic resolution from content
        prefix = self.try_extract_nested_field_from_content(content, self.input_prefix_field)
        if prefix:
            return prefix if prefix.endswith("/") else prefix + "/"
        if content.id and content.id.path:
            path = content.id.path
            # content.id.path is typically a file path (e.g., input/case_001/doc.pdf)
            # Extract the parent directory to get the case folder prefix
            if "/" in path:
                path = path.rsplit("/", 1)[0]
            return f"{path}/" if path else ""
        raise ValueError(f"{self.id}: Cannot determine base path. Set 'base_path' in settings.")

    def _get_fetched_details_prefix(self, content: Content) -> str:
        """Get the path where FetchedDetails files are stored.
        
        Priority:
          1. Static fetched_details_path setting (manual override)
          2. Derived from upstream blob output (content.summary_data nested field)
          3. Fall back to base_path
        """
        # 1. Static override
        if self.fetched_details_path:
            path = self.fetched_details_path.strip("/")
            return f"{path}/" if path else ""

        # 2. Derive from upstream blob output path
        #    The blob output executor stores: content.summary_data['blob_output']['blob_path']
        #    e.g., "azure_blob_output-xxx_2026_05_01/FetchedDetails_abc.json"
        upstream_path = self._resolve_nested_field(content.summary_data, self.fetched_details_path_field)
        
        if upstream_path:
            # Extract directory from full blob path
            if "/" in upstream_path:
                folder = upstream_path.rsplit("/", 1)[0]
                return f"{folder}/"
            # If no slash, it's a file at root level
            return ""

        # 3. Fall back to base path
        return self._get_base_prefix(content)

    def _get_rules_prefix(self) -> str:
        """Get the path prefix for loading rules.json.
        
        If rules_base_path is set (even to empty string), use it.
        Returns None if not configured, so caller can fall back to base_prefix.
        """
        if self.rules_base_path is not None:
            path = self.rules_base_path.strip("/")
            return f"{path}/" if path else ""
        return None

    async def _cleanup_case_folder(self, base_prefix: str) -> None:
        """Delete all blobs under the case folder prefix except preserved files.
        
        Preserves files listed in cleanup_preserve_files (comma-separated).
        """
        preserve_set = set()
        if self.cleanup_preserve_files:
            preserve_set = {f.strip() for f in self.cleanup_preserve_files.split(",") if f.strip()}

        deleted_count = 0
        async for blobs in self.blob_connector.list_blobs(
            container_name=self.blob_container_name,
            prefix=base_prefix,
            max_results=1000,
            batch_size=100
        ):
            if not blobs:
                continue
            for blob in blobs:
                blob_name = blob.get("name", "")
                filename = blob_name.split("/")[-1] if "/" in blob_name else blob_name
                if filename in preserve_set:
                    if self.debug_mode:
                        logger.debug(f"{self.id}: Preserving {blob_name}")
                    continue
                try:
                    await self.blob_connector.delete_blob(
                        container_name=self.blob_container_name,
                        blob_path=blob_name
                    )
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"{self.id}: Failed to delete {blob_name}: {e}")

        logger.info(f"{self.id}: Cleanup complete — deleted {deleted_count} blob(s) from {base_prefix}")

    def _resolve_nested_field(self, data: dict, field_path: str):
        """Resolve a dot-notation field path from a dictionary.
        
        E.g., 'blob_output.blob_path' resolves data['blob_output']['blob_path']
        """
        if not data or not field_path:
            return None
        parts = field_path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value if value is not data else None

    async def _load_json_from_blob(self, prefix: str, filename: str) -> dict:
        """Download and parse a JSON file from blob storage."""
        blob_path = f"{prefix}{filename}"
        try:
            content_bytes = await self.blob_connector.download_blob(
                container_name=self.blob_container_name,
                blob_path=blob_path
            )
            return json.loads(content_bytes.decode("utf-8"))
        except Exception as e:
            logger.error(f"{self.id}: Failed to load {blob_path}: {e}", exc_info=True)
            raise ValueError(f"Failed to load required file '{filename}' from {blob_path}: {e}")

    async def _load_fetched_details_for_current_run(
        self, current_run_blob_paths: List[str], fetched_prefix: str
    ) -> List[dict]:
        """Load FetchedDetails files scoped to the current pipeline execution only.
        
        Strategy:
          1. If exact blob paths from the current run are available (collected from
             upstream blob output executor's summary_data), load ONLY those specific files.
             This guarantees no cross-run contamination.
          2. Fallback: If no specific paths are available (e.g., manual/static config),
             list the folder but log a warning about potential cross-run inclusion.
        """
        if current_run_blob_paths:
            # PREFERRED: Load only the exact files written in this execution
            logger.info(
                f"{self.id}: Loading {len(current_run_blob_paths)} FetchedDetails file(s) "
                f"from current run (exact path resolution)"
            )
            return await self._load_fetched_details_by_paths(current_run_blob_paths)
        
        # FALLBACK: No exact paths available — use folder listing with warning
        logger.warning(
            f"{self.id}: No exact FetchedDetails paths from current run available. "
            f"Falling back to folder listing at '{fetched_prefix}'. "
            f"This may include files from previous executions if the folder is shared."
        )
        return await self._load_all_fetched_details_from_folder(fetched_prefix)

    async def _load_fetched_details_by_paths(self, blob_paths: List[str]) -> List[dict]:
        """Load FetchedDetails from specific blob paths (current run only)."""
        all_fetched = []
        for blob_path in blob_paths:
            try:
                content_bytes = await self.blob_connector.download_blob(
                    container_name=self.blob_container_name,
                    blob_path=blob_path
                )
                fetched = json.loads(content_bytes.decode("utf-8"))
                if isinstance(fetched, list):
                    all_fetched.extend(fetched)
                else:
                    all_fetched.append(fetched)
                if self.debug_mode:
                    logger.debug(f"{self.id}: Loaded FetchedDetails from exact path: {blob_path}")
            except Exception as e:
                logger.warning(f"{self.id}: Failed to load fetched details from {blob_path}: {e}")
        return all_fetched

    async def _load_all_fetched_details_from_folder(self, fetched_prefix: str) -> List[dict]:
        """Fallback: Find and load all FetchedDetails_*.json files in the fetched details path.
        
        WARNING: This may include files from previous pipeline executions if the folder
        is shared across runs (e.g., date-based folder naming).
        """
        all_fetched = []
        async for blobs in self.blob_connector.list_blobs(
            container_name=self.blob_container_name,
            prefix=fetched_prefix,
            max_results=100,
            batch_size=100
        ):
            if not blobs:
                continue
            for blob in blobs:
                blob_name = blob.get("name", "")
                filename = blob_name.split("/")[-1] if "/" in blob_name else blob_name
                if filename.startswith(self.fetched_details_prefix) and filename.endswith(".json"):
                    try:
                        content_bytes = await self.blob_connector.download_blob(
                            container_name=self.blob_container_name,
                            blob_path=blob_name
                        )
                        fetched = json.loads(content_bytes.decode("utf-8"))
                        if isinstance(fetched, list):
                            all_fetched.extend(fetched)
                        else:
                            all_fetched.append(fetched)
                    except Exception as e:
                        logger.warning(f"{self.id}: Failed to load fetched details from {blob_name}: {e}")
        return all_fetched

    async def _run_validation(
        self,
        provided_details: dict,
        fetched_details_list: List[dict],
        rules: dict
    ) -> dict:
        """
        Core validation logic:
        - Match fetched documents to provided documents by documentType
        - Apply rules for each document type
        - Produce consolidated results
        """
        results = {
            "validationTimestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "totalDocuments": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "notFound": 0,
                "overallStatus": "passed"
            },
            "documentResults": []
        }

        # Support two ProvidedDetails formats:
        # 1. Per-document: {"documents": [{"documentType": "Passport", "details": {...}}, ...]}
        # 2. Flat/shared: {"caseId": "...", "details": {"firstName": "...", ...}}
        #    In flat format, the same details apply to ALL document types.
        if "documents" in provided_details and provided_details["documents"]:
            provided_docs = {
                doc["documentType"]: doc["details"]
                for doc in provided_details["documents"]
            }
            shared_details = None
        else:
            provided_docs = {}
            shared_details = provided_details.get("details", {})

        rules_by_type = {
            rule["documentType"]: rule["validations"]
            for rule in rules.get("rules", [])
        }

        for fetched in fetched_details_list:
            fetched_doc_type = fetched.get("document_type", "")
            doc_result = {
                "documentType": fetched_doc_type,
                "status": "passed",
                "errors": [],
                "fieldResults": []
            }
            results["summary"]["totalDocuments"] += 1

            # Find matching provided document details
            # If flat format (shared_details), use the same details for all doc types
            if shared_details is not None:
                provided = shared_details
            else:
                provided = self._find_matching_provided(fetched_doc_type, provided_docs)
            if provided is None:
                doc_result["status"] = "not_found"
                doc_result["errors"].append({
                    "errorCode": "DOC_NOT_IN_PROVIDED",
                    "message_en": f"Document type '{fetched_doc_type}' not found in ProvidedDetails.",
                    "message_es": f"Tipo de documento '{fetched_doc_type}' no encontrado en los detalles proporcionados."
                })
                results["summary"]["notFound"] += 1
                results["documentResults"].append(doc_result)
                continue

            # Find matching rules
            validations = self._find_matching_rules(fetched_doc_type, rules_by_type)
            if not validations:
                # No rules means no validation needed - pass through
                doc_result["status"] = "passed"
                doc_result["fieldResults"].append({
                    "field": "_meta",
                    "result": "skipped",
                    "message_en": f"No validation rules defined for document type '{fetched_doc_type}'."
                })
                results["summary"]["passed"] += 1
                results["documentResults"].append(doc_result)
                continue

            # Extract fetched field values from Azure CU output
            fetched_fields = self._extract_fetched_fields(fetched)

            # Apply each validation rule
            for validation in validations:
                field_result = await self._validate_field(validation, fetched_fields, provided, fetched_doc_type)
                doc_result["fieldResults"].append(field_result)
                if field_result["result"] == "fail":
                    doc_result["status"] = "failed"

            # Update summary
            if doc_result["status"] == "failed":
                results["summary"]["failed"] += 1
            else:
                results["summary"]["passed"] += 1

            if self.debug_mode:
                passed_fields = sum(1 for fr in doc_result["fieldResults"] if fr["result"] == "pass")
                failed_fields = sum(1 for fr in doc_result["fieldResults"] if fr["result"] == "fail")
                logger.debug(
                    f"{self.id}: Document '{fetched_doc_type}' - "
                    f"{len(doc_result['fieldResults'])} fields validated: "
                    f"{passed_fields} passed, {failed_fields} failed"
                )

            results["documentResults"].append(doc_result)

        # Set overall status
        if results["summary"]["failed"] > 0 or results["summary"]["notFound"] > 0:
            results["summary"]["overallStatus"] = "failed"

        return results

    def _find_matching_provided(self, fetched_type: str, provided_docs: dict) -> Optional[dict]:
        """Match fetched document_type to ProvidedDetails documentType."""
        # Exact match first
        if fetched_type in provided_docs:
            return provided_docs[fetched_type]
        # Case-insensitive match
        for key, val in provided_docs.items():
            if key.lower() == fetched_type.lower():
                return val
        # Partial/contains match (e.g., "Telecom Utility bill" matches "Telecom utility bill_claro")
        for key, val in provided_docs.items():
            if fetched_type.lower() in key.lower() or key.lower() in fetched_type.lower():
                return val
        return None

    def _find_matching_rules(self, fetched_type: str, rules_by_type: dict) -> Optional[List[dict]]:
        """Match fetched document type to rules."""
        # Exact match
        if fetched_type in rules_by_type:
            return rules_by_type[fetched_type]
        # Case-insensitive match
        for key, val in rules_by_type.items():
            if key.lower() == fetched_type.lower():
                return val
        # Partial match for variants (e.g., "Telecom Utility bill" partial matches "Telecom utility bill_claro")
        for key, val in rules_by_type.items():
            if fetched_type.lower() in key.lower() or key.lower() in fetched_type.lower():
                return val
        return None

    def _extract_fetched_fields(self, fetched: dict) -> Dict[str, Any]:
        """
        Extract field values from the Azure Content Understanding response.
        Returns dict like {"FirstName": "LIZANDRA", "LastName": "MARTES SIERRA", ...}
        """
        fields = {}
        try:
            contents = fetched.get("details", {}).get("result", {}).get("contents", [])
            if contents:
                raw_fields = contents[0].get("fields", {})
                for field_name, field_data in raw_fields.items():
                    if field_data.get("type") == "date":
                        value = field_data.get("valueDate")
                    else:
                        value = field_data.get("valueString")
                    if value:
                        fields[field_name] = value
        except (KeyError, IndexError, TypeError) as e:
            logger.warning(f"{self.id}: Error extracting fetched fields: {e}")
        return fields

    async def _validate_field(
        self,
        validation: dict,
        fetched_fields: Dict[str, Any],
        provided: dict,
        doc_type: str
    ) -> dict:
        """Apply a single validation rule and return the field result."""
        field = validation.get("field", "")
        validation_type = validation.get("validationType", "exact_match")
        error_code = validation.get("errorCode", "")

        result = {
            "field": field,
            "validationType": validation_type,
            "errorCode": error_code,
            "result": "pass",
            "fetchedValue": None,
            "providedValue": None,
            "message_en": None,
            "message_es": None
        }

        # Dispatch based on validation type
        if validation_type == "expiry_check":
            await self._check_expiry(result, field, fetched_fields, provided, validation)
        elif validation_type == "exact_match":
            self._check_exact_match(result, field, fetched_fields, provided, validation)
        elif validation_type == "date_match":
            self._check_date_match(result, field, fetched_fields, provided, validation)
        elif validation_type == "name_match":
            self._check_name_match(result, field, fetched_fields, provided, validation)
        elif validation_type == "address_match":
            await self._check_address_match(result, field, fetched_fields, provided, validation)
        else:
            # Default to exact match
            self._check_exact_match(result, field, fetched_fields, provided, validation)

        return result

    async def _check_expiry(
        self, result: dict, field: str,
        fetched_fields: dict, provided: dict, validation: dict
    ) -> None:
        """Check if a document has expired."""
        fetched_value = fetched_fields.get(field)
        provided_value = provided.get(field)
        result["fetchedValue"] = fetched_value
        result["providedValue"] = provided_value

        # If provided says "Permanent", it never expires
        if provided_value and str(provided_value).lower() == "permanent":
            result["result"] = "pass"
            return

        # Use fetched expiry date for the check
        date_to_check = fetched_value or provided_value
        if date_to_check:
            try:
                exp_date = datetime.strptime(str(date_to_check), "%Y-%m-%d")
                if exp_date < datetime.now():
                    result["result"] = "fail"
                    result["message_en"] = validation.get("message_en")
                    result["message_es"] = validation.get("message_es")
            except ValueError:
                result["result"] = "warning"
                result["message_en"] = f"Could not parse expiry date: {date_to_check}"
        else:
            result["result"] = "warning"
            result["message_en"] = "Expiry date not found in fetched or provided details"

    def _check_exact_match(
        self, result: dict, field: str,
        fetched_fields: dict, provided: dict, validation: dict
    ) -> None:
        """Exact string comparison (case-insensitive by default)."""
        fetched_value = fetched_fields.get(field)
        provided_value = provided.get(field)
        result["fetchedValue"] = fetched_value
        result["providedValue"] = provided_value

        if fetched_value is None:
            result["result"] = "warning"
            result["message_en"] = f"Field '{field}' not found in fetched document details"
            return
        if provided_value is None:
            result["result"] = "warning"
            result["message_en"] = f"Field '{field}' not found in provided details"
            return

        if not self._values_match(str(fetched_value), str(provided_value)):
            result["result"] = "fail"
            result["message_en"] = validation.get("message_en")
            result["message_es"] = validation.get("message_es")

    def _check_date_match(
        self, result: dict, field: str,
        fetched_fields: dict, provided: dict, validation: dict
    ) -> None:
        """Date comparison (normalizes to YYYY-MM-DD)."""
        fetched_value = fetched_fields.get(field)
        provided_value = provided.get(field)
        result["fetchedValue"] = fetched_value
        result["providedValue"] = provided_value

        if fetched_value is None:
            result["result"] = "warning"
            result["message_en"] = f"Field '{field}' not found in fetched document details"
            return
        if provided_value is None:
            result["result"] = "warning"
            result["message_en"] = f"Field '{field}' not found in provided details"
            return

        # Normalize dates for comparison
        fetched_normalized = self._normalize_date(str(fetched_value))
        provided_normalized = self._normalize_date(str(provided_value))

        if fetched_normalized and provided_normalized:
            if fetched_normalized != provided_normalized:
                result["result"] = "fail"
                result["message_en"] = validation.get("message_en")
                result["message_es"] = validation.get("message_es")
        else:
            # Fallback to string comparison
            if not self._values_match(str(fetched_value), str(provided_value)):
                result["result"] = "fail"
                result["message_en"] = validation.get("message_en")
                result["message_es"] = validation.get("message_es")

    def _check_name_match(
        self, result: dict, field: str,
        fetched_fields: dict, provided: dict, validation: dict
    ) -> None:
        """
        Name comparison for full name fields.
        For utility bills: concatenates FirstName + LastName from fetched, compares to FullName in provided.
        """
        provided_value = provided.get(field)

        # Build fetched full name from FirstName + LastName if field is FullName
        if field == "FullName":
            first = fetched_fields.get("FirstName", "")
            last = fetched_fields.get("LastName", "")
            fetched_value = f"{first} {last}".strip()
        else:
            fetched_value = fetched_fields.get(field)

        result["fetchedValue"] = fetched_value
        result["providedValue"] = provided_value

        if not fetched_value:
            result["result"] = "warning"
            result["message_en"] = f"Field '{field}' not found in fetched document details"
            return
        if not provided_value:
            result["result"] = "warning"
            result["message_en"] = f"Field '{field}' not found in provided details"
            return

        if not self._names_match(str(fetched_value), str(provided_value)):
            result["result"] = "fail"
            result["message_en"] = validation.get("message_en")
            result["message_es"] = validation.get("message_es")

    async def _check_address_match(
        self, result: dict, field: str,
        fetched_fields: dict, provided: dict, validation: dict
    ) -> None:
        """AI-powered address comparison using Azure OpenAI."""
        fetched_value = fetched_fields.get(field)
        provided_value = provided.get(field)
        result["fetchedValue"] = fetched_value
        result["providedValue"] = provided_value

        if not fetched_value:
            result["result"] = "warning"
            result["message_en"] = f"Field '{field}' not found in fetched document details"
            return
        if not provided_value:
            result["result"] = "warning"
            result["message_en"] = f"Field '{field}' not found in provided details"
            return

        # Also append Region if available for more complete address
        region = fetched_fields.get("Region")
        full_fetched_address = fetched_value
        if region and region not in fetched_value:
            full_fetched_address = f"{fetched_value}, {region}"

        # Use AI-powered comparison if endpoint is configured
        if self.openai_endpoint and self.openai_deployment_name:
            is_match = await self._ai_address_match(full_fetched_address, str(provided_value))
            if not is_match:
                result["result"] = "fail"
                result["message_en"] = validation.get("message_en")
                result["message_es"] = validation.get("message_es")
        else:
            # Fallback to basic string comparison
            if not self._values_match(str(full_fetched_address), str(provided_value)):
                result["result"] = "fail"
                result["message_en"] = validation.get("message_en")
                result["message_es"] = validation.get("message_es")

    async def _ai_address_match(self, address1: str, address2: str) -> bool:
        """Use Azure OpenAI to determine if two addresses match."""
        if not self.agent:
            self._init_agent()

        query = (
            f"Address 1: {address1}\n"
            f"Address 2: {address2}\n\n"
            f"Do these two addresses refer to the same physical location?"
        )

        try:
            response: AgentResponse = await self.agent.run(query)
            response_text = response.content if hasattr(response, "content") else str(response)

            # Parse the JSON response
            try:
                parsed = json.loads(response_text)
                match_result = parsed.get("match", False)
                confidence = parsed.get("confidence", 0.0)

                if self.debug_mode:
                    logger.debug(
                        f"{self.id}: Address match result: {match_result}, "
                        f"confidence: {confidence}, reason: {parsed.get('reason', '')}"
                    )

                return bool(match_result)
            except json.JSONDecodeError:
                # If response isn't valid JSON, look for keywords
                lower_response = response_text.lower()
                return "true" in lower_response or "match" in lower_response

        except Exception as e:
            logger.warning(
                f"{self.id}: AI address match failed, falling back to string comparison: {e}",
                exc_info=True
            )
            return self._values_match(address1, address2)

    def _values_match(self, fetched: str, provided: str) -> bool:
        """Compare two string values with normalization."""
        if not fetched or not provided:
            return False
        f = fetched.strip()
        p = provided.strip()
        if not self.case_sensitive:
            f = f.upper()
            p = p.upper()
        # Exact match
        if f == p:
            return True
        # Contained match (one contains the other)
        if f in p or p in f:
            return True
        return False

    def _names_match(self, fetched: str, provided: str) -> bool:
        """
        Compare names with flexible matching.
        Handles: "LASTNAME, FIRSTNAME" vs "FIRSTNAME LASTNAME" formats,
        and partial name matching.
        """
        if not fetched or not provided:
            return False

        f = fetched.strip().upper()
        p = provided.strip().upper()

        # Direct match
        if f == p:
            return True

        # Normalize comma-separated format ("OROZCO DONES, CARMEN" → "CARMEN OROZCO DONES")
        f_normalized = self._normalize_name(f)
        p_normalized = self._normalize_name(p)

        if f_normalized == p_normalized:
            return True

        # Check if all parts of one name appear in the other
        f_parts = set(f_normalized.split())
        p_parts = set(p_normalized.split())

        # If all parts of the shorter name are in the longer name
        if f_parts.issubset(p_parts) or p_parts.issubset(f_parts):
            return True

        # Check significant overlap (at least first+last name match)
        common = f_parts.intersection(p_parts)
        if len(common) >= 2:
            return True

        return False

    def _normalize_name(self, name: str) -> str:
        """Normalize name format: 'LAST, FIRST' → 'FIRST LAST'."""
        if "," in name:
            parts = name.split(",", 1)
            return f"{parts[1].strip()} {parts[0].strip()}"
        return name

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date to YYYY-MM-DD format."""
        formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%d %b %Y", "%b %d, %Y"]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    async def _write_results_to_blob(self, prefix: str, results: dict) -> None:
        """Write results.json back to the same blob folder."""
        blob_path = f"{prefix}{self.output_filename}"
        content_bytes = json.dumps(results, indent=2, ensure_ascii=False).encode("utf-8")
        await self.blob_connector.upload_blob(
            container_name=self.blob_container_name,
            blob_path=blob_path,
            data=content_bytes,
            overwrite=True
        )
        logger.info(f"{self.id}: Wrote validation results to {blob_path}")
