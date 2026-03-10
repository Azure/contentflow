"""
Cosmos DB Lookup Executor.

Performs per-content-item lookups against an Azure Cosmos DB NoSQL container
and enriches content with the query results.  Supports both point-reads (by
id + partition key) and parameterised SQL queries whose values are drawn from
``content.data`` fields.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from agent_framework import WorkflowContext

from .parallel_executor import ParallelExecutor
from ..connectors.cosmos_nosql_connector import CosmosNoSQLConnector
from ..models import Content

logger = logging.getLogger("contentflow.executors.cosmos_db_lookup_executor")


class CosmosDBLookupExecutor(ParallelExecutor):
    """
    Look up records in Azure Cosmos DB NoSQL and enrich content items.

    For every incoming content item the executor:

    1. Extracts lookup key(s) from ``content.data`` using configurable field
       mappings.
    2. Queries Cosmos DB — either a direct point-read, or a parameterised SQL
       query.
    3. Writes the result(s) back into ``content.data[output_field]``.

    This is useful for validating / cross-referencing content fields against
    reference data stored in Cosmos DB (e.g. product catalogs, customer
    records, allowed-value lists).

    Configuration (settings dict):
        Connection:
            - cosmos_endpoint (str): Cosmos DB account endpoint URL.  Required.
              Supports ``${ENV_VAR}`` syntax.
            - cosmos_key (str): Cosmos DB account key.  Required when
              ``credential_type`` is ``"key"``.  Supports ``${ENV_VAR}`` syntax.
            - credential_type (str): ``"key"`` (default) or
              ``"default_azure_credential"``.
            - cosmos_database (str): Database name.  Required.
            - cosmos_container (str): Container name.  Required.

        Lookup behaviour:
            - lookup_mode (str): ``"point_read"`` or ``"query"``
              (default: ``"query"``).
            - query_template (str): Cosmos DB SQL query with ``@param``
              placeholders.  Used when ``lookup_mode`` is ``"query"``.
              Example: ``"SELECT * FROM c WHERE c.sku = @sku"``
            - field_mappings (dict): Maps ``@param`` names (or point-read
              keys) to dot-separated paths inside ``content.data``.
              Example: ``{"@sku": "product.sku", "@region": "region"}``
              For ``point_read`` mode the keys ``"id"`` and
              ``"partition_key"`` are expected.
            - partition_key_field (str): Dot-path in ``content.data`` whose
              value is used as the partition key for ``query`` mode (optional,
              enables single-partition queries).

        Output:
            - output_field (str): Field name under ``content.data`` where
              results are stored (default: ``"cosmos_lookup_result"``).
            - result_mode (str): ``"first"`` returns only the first match,
              ``"all"`` returns the full list (default: ``"all"``).
            - flatten_single (bool): When ``result_mode`` is ``"all"`` and
              there is exactly one result, store the dict directly rather than
              a one-element list (default: ``false``).

        Limits:
            - max_results (int): Maximum items to return per query
              (default: 50).

        Also inherits ParallelExecutor settings:
            - max_concurrent (int): default 5
            - timeout_secs (int): default 300
            - continue_on_error (bool): default True

    Example workflow YAML:
        ```yaml
        - id: cosmos_lookup
          type: cosmos_db_lookup
          settings:
            cosmos_endpoint: "${COSMOS_ENDPOINT}"
            cosmos_key: "${COSMOS_KEY}"
            cosmos_database: "reference-data"
            cosmos_container: "products"
            lookup_mode: "query"
            query_template: "SELECT * FROM c WHERE c.sku = @sku"
            field_mappings:
              "@sku": "product.sku"
            output_field: "product_lookup"
            result_mode: "first"
            max_concurrent: 10
        ```
    """

    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(id=id, settings=settings, **kwargs)

        # ---- Connection settings ----
        self._cosmos_endpoint = self.get_setting("cosmos_endpoint", required=True)
        self._cosmos_key = self.get_setting("cosmos_key", default=None)
        self._credential_type = self.get_setting("credential_type", default="key")
        self._cosmos_database = self.get_setting("cosmos_database", required=True)
        self._cosmos_container = self.get_setting("cosmos_container", required=True)

        # ---- Lookup settings ----
        self.lookup_mode = self.get_setting("lookup_mode", default="query")
        if self.lookup_mode not in ("point_read", "query"):
            raise ValueError(
                f"Invalid lookup_mode '{self.lookup_mode}'. "
                "Must be 'point_read' or 'query'."
            )

        self.query_template = self.get_setting("query_template", default=None)
        if self.lookup_mode == "query" and not self.query_template:
            raise ValueError(
                "query_template is required when lookup_mode is 'query'."
            )

        self.field_mappings: Dict[str, str] = self.get_setting("field_mappings", default={})
        self.partition_key_field: Optional[str] = self.get_setting("partition_key_field", default=None)
        self.output_field: str = self.get_setting("output_field", default="cosmos_lookup_result")
        self.result_mode: str = self.get_setting("result_mode", default="all")
        self.flatten_single: bool = self.get_setting("flatten_single", default=False)
        self.max_results: int = self.get_setting("max_results", default=50)

        # Lazy-initialised connector
        self._connector: Optional[CosmosNoSQLConnector] = None

        if self.debug_mode:
            logger.debug(
                f"CosmosDBLookupExecutor '{self.id}' initialised: "
                f"mode={self.lookup_mode}, output_field={self.output_field}"
            )

    # ------------------------------------------------------------------
    # Connector lifecycle
    # ------------------------------------------------------------------

    async def _get_connector(self) -> CosmosNoSQLConnector:
        """Return (and lazily create) the Cosmos NoSQL connector."""
        if self._connector is None:
            connector_settings: Dict[str, Any] = {
                "endpoint": self._cosmos_endpoint,
                "database": self._cosmos_database,
                "container": self._cosmos_container,
                "credential_type": self._credential_type,
            }
            if self._cosmos_key:
                connector_settings["key"] = self._cosmos_key

            self._connector = CosmosNoSQLConnector(
                name=f"cosmos_nosql_{self.id}",
                settings=connector_settings,
            )
            await self._connector.initialize()
        return self._connector

    # ------------------------------------------------------------------
    # Field extraction helpers
    # ------------------------------------------------------------------

    def _resolve_field_value(self, content: Content, field_path: str) -> Any:
        """
        Walk a dot-separated path into ``content.data`` and return the value.

        Returns ``None`` when any segment of the path is missing.
        """
        return self.try_extract_nested_field_from_content(content, field_path)

    def _build_query_parameters(self, content: Content) -> List[Dict[str, Any]]:
        """
        Build ``[{"name": "@param", "value": <resolved>}, ...]`` from
        ``field_mappings`` and the current content item.
        """
        params: List[Dict[str, Any]] = []
        for param_name, field_path in self.field_mappings.items():
            value = self._resolve_field_value(content, field_path)
            # Ensure parameter name starts with @
            name = param_name if param_name.startswith("@") else f"@{param_name}"
            params.append({"name": name, "value": value})
        return params

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    async def process_content_item(self, content: Content) -> Content:
        """
        Look up a single content item against Cosmos DB.

        Called in parallel by ``ParallelExecutor`` for each item in the batch.
        """
        connector = await self._get_connector()

        try:
            if self.lookup_mode == "point_read":
                result = await self._do_point_read(connector, content)
            else:
                result = await self._do_query(connector, content)

            # Store result
            content.data[self.output_field] = result
            content.summary_data["cosmos_lookup_status"] = "success"

            if self.debug_mode:
                count = 1 if isinstance(result, dict) else (len(result) if isinstance(result, list) else 0)
                logger.debug(
                    f"[{content.id.canonical_id}] Cosmos lookup returned "
                    f"{count} result(s)"
                )

        except Exception as exc:
            logger.error(
                f"[{content.id.canonical_id}] Cosmos lookup failed: {exc}",
                exc_info=True,
            )
            content.data[self.output_field] = None
            content.summary_data["cosmos_lookup_status"] = "error"
            content.summary_data["cosmos_lookup_error"] = str(exc)

            if self.get_setting("fail_pipeline_on_error", default=False):
                raise

        return content

    # ------------------------------------------------------------------
    # Lookup strategies
    # ------------------------------------------------------------------

    async def _do_point_read(
        self,
        connector: CosmosNoSQLConnector,
        content: Content,
    ) -> Optional[Dict[str, Any]]:
        """Perform a direct item read by ``id`` + ``partition_key``."""
        id_path = self.field_mappings.get("id")
        pk_path = self.field_mappings.get("partition_key")

        if not id_path or not pk_path:
            raise ValueError(
                "field_mappings must contain 'id' and 'partition_key' "
                "entries for point_read mode."
            )

        item_id = self._resolve_field_value(content, id_path)
        partition_key = self._resolve_field_value(content, pk_path)

        if item_id is None or partition_key is None:
            logger.warning(
                f"[{content.id.canonical_id}] Skipping point_read — "
                f"id or partition_key resolved to None "
                f"(id_path='{id_path}', pk_path='{pk_path}')"
            )
            return None

        return await connector.point_read(
            item_id=str(item_id),
            partition_key=partition_key,
        )

    async def _do_query(
        self,
        connector: CosmosNoSQLConnector,
        content: Content,
    ) -> Any:
        """Execute a parameterised SQL query against the container."""
        parameters = self._build_query_parameters(content)

        # Resolve optional per-item partition key
        partition_key: Optional[Any] = None
        if self.partition_key_field:
            partition_key = self._resolve_field_value(content, self.partition_key_field)

        if self.debug_mode:
            logger.debug(
                f"[{content.id.canonical_id}] query='{self.query_template}', "
                f"params={json.dumps(parameters, default=str)}"
            )

        items = await connector.query_items(
            query=self.query_template,
            parameters=parameters,
            partition_key=partition_key,
            max_item_count=self.max_results,
        )

        # Apply result_mode
        if self.result_mode == "first":
            return items[0] if items else None

        if self.flatten_single and len(items) == 1:
            return items[0]

        return items
