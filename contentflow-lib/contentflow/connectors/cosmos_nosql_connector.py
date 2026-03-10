"""
Cosmos DB NoSQL connector for querying containers.

Provides async access to Azure Cosmos DB NoSQL (SQL API) containers,
supporting point reads and parameterised queries with environment-variable
resolution for connection settings.
"""

import logging
from typing import Any, Dict, List, Optional

from .base import ConnectorBase

logger = logging.getLogger("contentflow.connectors.cosmos_nosql_connector")

# Guard the import so the rest of the framework stays usable without the SDK.
try:
    from azure.cosmos.aio import CosmosClient
    from azure.cosmos import exceptions as cosmos_exceptions
except ImportError:
    CosmosClient = None  # type: ignore[assignment,misc]
    cosmos_exceptions = None  # type: ignore[assignment]


class CosmosNoSQLConnector(ConnectorBase):
    """
    Connector for Azure Cosmos DB NoSQL (SQL API).

    Settings:
        endpoint (str): Cosmos DB account endpoint URL.
                         Supports ``${ENV_VAR}`` syntax.
        key (str):       Cosmos DB account key (or use ``credential_type``).
                         Supports ``${ENV_VAR}`` syntax.
        credential_type (str): ``"key"`` (default) or ``"default_azure_credential"``.
        database (str):  Database name.
        container (str): Container name.
    """

    def __init__(
        self,
        name: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(name=name, connector_type="cosmos_nosql", settings=settings, **kwargs)

        if CosmosClient is None:
            raise ImportError(
                "azure-cosmos is required for Cosmos DB NoSQL lookups. "
                "Install it with: pip install azure-cosmos"
            )

        self._endpoint: str = self._resolve_setting("endpoint", required=True)
        self._database_name: str = self._resolve_setting("database", required=True)
        self._container_name: str = self._resolve_setting("container", required=True)
        self._credential_type: str = self._resolve_setting("credential_type", required=False, default="key")

        if self._credential_type == "key":
            self._key: Optional[str] = self._resolve_setting("key", required=True)
        else:
            self._key = None

        # Lazily initialised
        self._client: Optional[Any] = None
        self._container_proxy: Optional[Any] = None

    async def initialize(self) -> None:
        """Create the Cosmos client and obtain a container reference."""
        if self._container_proxy is not None:
            return

        if self._credential_type == "default_azure_credential":
            from azure.identity.aio import DefaultAzureCredential
            credential = DefaultAzureCredential()
        else:
            credential = self._key

        self._client = CosmosClient(url=self._endpoint, credential=credential)
        database_proxy = self._client.get_database_client(self._database_name)
        self._container_proxy = database_proxy.get_container_client(self._container_name)

        logger.info(
            f"CosmosNoSQLConnector '{self.name}' initialised — "
            f"database={self._database_name}, container={self._container_name}"
        )

    async def close(self) -> None:
        """Close the underlying Cosmos client."""
        if self._client is not None:
            await self._client.close()
            self._client = None
            self._container_proxy = None

    # ------------------------------------------------------------------
    # Public query helpers
    # ------------------------------------------------------------------

    async def point_read(
        self,
        item_id: str,
        partition_key: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Perform a point-read by item ``id`` and partition key.

        Returns the item dict or ``None`` if not found.
        """
        await self.initialize()
        try:
            item = await self._container_proxy.read_item(item=item_id, partition_key=partition_key)
            return dict(item)
        except cosmos_exceptions.CosmosResourceNotFoundError:
            return None

    async def query_items(
        self,
        query: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        partition_key: Optional[Any] = None,
        max_item_count: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query against the container.

        Args:
            query: Cosmos DB SQL query string.
                   Example: ``"SELECT * FROM c WHERE c.status = @status"``
            parameters: Optional list of parameter dicts
                        (``[{"name": "@status", "value": "active"}]``).
            partition_key: Optional partition key value for scoping.
            max_item_count: Maximum items to return.

        Returns:
            List of matching item dicts.
        """
        await self.initialize()

        kwargs: Dict[str, Any] = {
            "query": query,
            "max_item_count": max_item_count,
            "enable_cross_partition_query": partition_key is None,
        }
        if parameters:
            kwargs["parameters"] = parameters
        if partition_key is not None:
            kwargs["partition_key"] = partition_key

        results: List[Dict[str, Any]] = []
        async for item in self._container_proxy.query_items(**kwargs):
            results.append(dict(item))
            if len(results) >= max_item_count:
                break

        return results
