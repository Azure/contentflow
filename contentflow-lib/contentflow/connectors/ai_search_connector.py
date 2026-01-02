"""
Azure AI Search connector for indexing and search operations.

This connector provides access to Azure AI Search for document indexing,
querying, and search operations during workflow execution.
"""

import logging
from typing import List, Dict, Any, Optional

import aiohttp

from .base import ConnectorBase
from ..utils.credential_provider import get_azure_credential_async

logger = logging.getLogger("contentflow.lib.connectors.ai_search")


class AISearchConnector(ConnectorBase):
    """
    Azure AI Search connector.
    
    Provides async access to Azure AI Search for document indexing and search.
    Supports both Azure Key Credential and Default Azure Credential authentication.
    
    Configuration:
        - account_name: Search service name (supports ${ENV_VAR})
        - credential_type: 'azure_key_credential' or 'default_azure_credential'
        - api_key: Search admin key (required for azure_key_credential)
        - api_version: API version (e.g., '2023-11-01')
        - index_name: Target index name
    
    Example:
        ```python
        connector = AISearchConnector(
            name="search",
            settings={
                "account_name": "${SEARCH_SERVICE}",
                "credential_type": "default_azure_credential",
                "api_version": "2023-11-01",
                "index_name": "documents"
            }
        )
        
        await connector.initialize()
        
        # Index documents
        await connector.index_documents([
            {"id": "1", "content": "Document text", "metadata": {...}}
        ])
        
        # Search
        results = await connector.search("query text", top=10)
        ```
    """
    
    def __init__(self, name: str, settings: Dict[str, Any], **kwargs):
        super().__init__(name=name, connector_type="ai_search", settings=settings, **kwargs)
        
        # Validate and resolve settings
        account_name = self._resolve_setting("account_name", required=True)
        self.endpoint = f"https://{account_name}.search.windows.net"
        
        self.credential_type = self._resolve_setting("credential_type", required=True)
        
        # Validate credential type
        if self.credential_type not in ['azure_key_credential', 'default_azure_credential']:
            raise ValueError(
                f"Unsupported credential type: {self.credential_type}. "
                f"Supported types are 'azure_key_credential' and 'default_azure_credential'."
            )
        
        # Get API key if using key-based auth
        self.api_key = None
        if self.credential_type == 'azure_key_credential':
            self.api_key = self._resolve_setting("api_key", required=True)
        
        self.api_version = self._resolve_setting("api_version", required=True)
        self.index_name = self._resolve_setting("index_name", required=True)
        
        # Initialize credential reference
        self.credential = None
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self) -> None:
        """Initialize the search connector."""
        if self.credential_type == 'default_azure_credential' and not self.credential:
            self.credential = await get_azure_credential_async()
        
        if not self._session:
            self._session = aiohttp.ClientSession()
        
        logger.info(f"Initialized AISearchConnector '{self.name}' for index '{self.index_name}'")
    
    async def _get_auth_header(self) -> Dict[str, str]:
        """Get authorization header for API requests."""
        if self.credential_type == 'azure_key_credential':
            return {"api-key": self.api_key}
        else:
            # Get token from DefaultAzureCredential
            if not self.credential:
                self.credential = await get_azure_credential_async()
            
            token = await self.credential.get_token("https://search.azure.com/.default")
            return {"Authorization": f"Bearer {token.token}"}
    
    async def test_connection(self) -> bool:
        """Test the search service connection."""
        try:
            if not self._session:
                await self.initialize()
            
            # Try to get index definition
            headers = await self._get_auth_header()
            url = f"{self.endpoint}/indexes/{self.index_name}?api-version={self.api_version}"
            
            async with self._session.get(url, headers=headers) as response:
                if response.status == 200:
                    logger.info(f"AISearchConnector '{self.name}' connection test successful")
                    return True
                else:
                    error_text = await response.text()
                    raise Exception(f"Connection test failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"AISearchConnector '{self.name}' connection test failed: {e}")
            raise
    
    async def index_documents(
        self,
        documents: List[Dict[str, Any]],
        merge_or_upload: bool = True
    ) -> Dict[str, Any]:
        """
        Index or update documents in the search index.
        
        Args:
            documents: List of document dicts to index
            merge_or_upload: If True, merge with existing docs; if False, replace
            
        Returns:
            Dict with indexing results
        """
        if not self._session:
            await self.initialize()
        
        headers = await self._get_auth_header()
        headers["Content-Type"] = "application/json"
        
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/index?api-version={self.api_version}"
        
        # Prepare batch payload
        actions = []
        for doc in documents:
            action = {
                "@search.action": "mergeOrUpload" if merge_or_upload else "upload",
                **doc
            }
            actions.append(action)
        
        payload = {"value": actions}
        
        async with self._session.post(url, headers=headers, json=payload) as response:
            result = await response.json()
            
            if response.status not in [200, 201]:
                logger.error(f"Indexing failed: {response.status} - {result}")
                raise Exception(f"Indexing failed: {result}")
            
            logger.debug(f"Indexed {len(documents)} documents to '{self.index_name}'")
            return result
    
    async def search(
        self,
        query: str,
        top: int = 10,
        select_fields: Optional[List[str]] = None,
        filter_expr: Optional[str] = None,
        order_by: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search the index.
        
        Args:
            query: Search query text
            top: Number of results to return
            select_fields: Fields to return
            filter_expr: OData filter expression
            order_by: Fields to sort by
            
        Returns:
            Dict with search results
        """
        if not self._session:
            await self.initialize()
        
        headers = await self._get_auth_header()
        headers["Content-Type"] = "application/json"
        
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
        
        payload = {
            "search": query,
            "top": top
        }
        
        if select_fields:
            payload["select"] = ",".join(select_fields)
        
        if filter_expr:
            payload["filter"] = filter_expr
        
        if order_by:
            payload["orderby"] = ",".join(order_by)
        
        async with self._session.post(url, headers=headers, json=payload) as response:
            result = await response.json()
            
            if response.status != 200:
                logger.error(f"Search failed: {response.status} - {result}")
                raise Exception(f"Search failed: {result}")
            
            logger.debug(f"Search returned {len(result.get('value', []))} results")
            return result
    
    async def delete_documents(self, document_ids: List[str], key_field: str = "id") -> Dict[str, Any]:
        """
        Delete documents from the index.
        
        Args:
            document_ids: List of document IDs to delete
            key_field: Name of the key field (default: "id")
            
        Returns:
            Dict with deletion results
        """
        if not self._session:
            await self.initialize()
        
        headers = await self._get_auth_header()
        headers["Content-Type"] = "application/json"
        
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/index?api-version={self.api_version}"
        
        actions = [
            {"@search.action": "delete", key_field: doc_id}
            for doc_id in document_ids
        ]
        
        payload = {"value": actions}
        
        async with self._session.post(url, headers=headers, json=payload) as response:
            result = await response.json()
            
            if response.status not in [200, 201, 207]:
                logger.error(f"Deletion failed: {response.status} - {result}")
                raise Exception(f"Deletion failed: {result}")
            
            logger.debug(f"Deleted {len(document_ids)} documents from '{self.index_name}'")
            return result
    
    async def count_documents(self) -> int:
        """
        Get the count of documents in the index.
        
        Returns:
            Integer count of documents
        """
        if not self._session:
            await self.initialize()
        
        headers = await self._get_auth_header()
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/$count?api-version={self.api_version}"
        
        async with self._session.get(url, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Count failed: {response.status} - {error_text}")
                raise Exception(f"Count failed: {error_text}")
            
            count = await response.json()
            logger.debug(f"Document count in '{self.index_name}': {count}")
            return count
    
    async def lookup_document(
        self,
        key: str,
        select_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve a specific document by key.
        
        Args:
            key: The document key
            select_fields: Optional list of fields to retrieve
            
        Returns:
            Dict containing the document
        """
        if not self._session:
            await self.initialize()
        
        headers = await self._get_auth_header()
        
        # URL encode the key
        from urllib.parse import quote
        encoded_key = quote(str(key), safe='')
        
        url = f"{self.endpoint}/indexes/{self.index_name}/docs('{encoded_key}')?api-version={self.api_version}"
        
        if select_fields:
            url += f"&$select={','.join(select_fields)}"
        
        async with self._session.get(url, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Lookup failed: {response.status} - {error_text}")
                raise Exception(f"Lookup failed: {error_text}")
            
            result = await response.json()
            logger.debug(f"Retrieved document with key '{key}' from '{self.index_name}'")
            return result
    
    async def suggest(
        self,
        search_text: str,
        suggester_name: str,
        top: int = 5,
        select_fields: Optional[List[str]] = None,
        filter_expr: Optional[str] = None,
        use_fuzzy_matching: bool = False
    ) -> Dict[str, Any]:
        """
        Get search suggestions based on partial input.
        
        Args:
            search_text: Partial search text (1-100 characters)
            suggester_name: Name of the suggester configuration
            top: Number of suggestions to return (1-100)
            select_fields: Fields to return in suggestions
            filter_expr: OData filter expression
            use_fuzzy_matching: Enable fuzzy matching
            
        Returns:
            Dict with suggestion results
        """
        if not self._session:
            await self.initialize()
        
        headers = await self._get_auth_header()
        headers["Content-Type"] = "application/json"
        
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/search.post.suggest?api-version={self.api_version}"
        
        payload = {
            "search": search_text,
            "suggesterName": suggester_name,
            "top": top
        }
        
        if select_fields:
            payload["select"] = ",".join(select_fields)
        
        if filter_expr:
            payload["filter"] = filter_expr
        
        if use_fuzzy_matching:
            payload["fuzzy"] = True
        
        async with self._session.post(url, headers=headers, json=payload) as response:
            result = await response.json()
            
            if response.status != 200:
                logger.error(f"Suggest failed: {response.status} - {result}")
                raise Exception(f"Suggest failed: {result}")
            
            logger.debug(f"Suggestions returned {len(result.get('value', []))} results")
            return result
    
    async def autocomplete(
        self,
        search_text: str,
        suggester_name: str,
        autocomplete_mode: str = "oneTerm",
        top: int = 5,
        filter_expr: Optional[str] = None,
        use_fuzzy_matching: bool = False
    ) -> Dict[str, Any]:
        """
        Get autocomplete suggestions for incomplete query terms.
        
        Args:
            search_text: Incomplete search text
            suggester_name: Name of the suggester configuration
            autocomplete_mode: Mode - "oneTerm", "twoTerms", or "oneTermWithContext"
            top: Number of suggestions (1-100)
            filter_expr: OData filter expression
            use_fuzzy_matching: Enable fuzzy matching
            
        Returns:
            Dict with autocomplete results
        """
        if not self._session:
            await self.initialize()
        
        headers = await self._get_auth_header()
        headers["Content-Type"] = "application/json"
        
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/search.post.autocomplete?api-version={self.api_version}"
        
        payload = {
            "search": search_text,
            "suggesterName": suggester_name,
            "autocompleteMode": autocomplete_mode,
            "top": top
        }
        
        if filter_expr:
            payload["filter"] = filter_expr
        
        if use_fuzzy_matching:
            payload["fuzzy"] = True
        
        async with self._session.post(url, headers=headers, json=payload) as response:
            result = await response.json()
            
            if response.status != 200:
                logger.error(f"Autocomplete failed: {response.status} - {result}")
                raise Exception(f"Autocomplete failed: {result}")
            
            logger.debug(f"Autocomplete returned {len(result.get('value', []))} results")
            return result
    
    async def cleanup(self) -> None:
        """Cleanup connector resources."""
        if self._session:
            await self._session.close()
        
        if self.credential:
            await self.credential.close()
        
        logger.info(f"Cleaned up AISearchConnector '{self.name}'")
