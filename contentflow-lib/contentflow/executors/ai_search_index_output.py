"""AI Search index output executor for indexing documents to Azure AI Search."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import json

from . import ParallelExecutor
from ..models import Content
from ..connectors import AISearchConnector

logger = logging.getLogger(__name__)


class AISearchIndexOutputExecutor(ParallelExecutor):
    """
    Index documents or chunks to Azure AI Search.
    
    This executor indexes document data into Azure AI Search, supporting
    both full document indexing and chunk-level indexing for semantic search
    and RAG applications.
    
    Configuration (settings dict):
        - ai_search_account (str): Azure AI Search service name
          Default: None
        - ai_search_credential_type (str): Credential type for authentication
          Default: "default_azure_credential"
        - ai_search_api_key (str): Azure AI Search API key
          Default: None
        - ai_search_api_version (str): Azure AI Search API version
          Default: "2025-11-01-preview"
        - ai_search_index (str): Azure AI Search index name
        - index_mode (str): "document" or "chunks". Defines if full document or
          chunks are indexed.
          Default: "chunks"
        - chunk_iterator_field (str): Field path to iterate chunks from content
          Default: "chunks"
        - content_to_index_mappings (str): JSON string mapping content fields to index fields,
          prefix with "chunk." for chunk fields.
          Default: None
        - index_action_type (str): Azure Search action type
          Default: "mergeOrUpload"
          Options: "upload", "merge", "mergeOrUpload", "delete"
        - batch_size (int): Number of documents to index per batch
          Default: 100
        - add_timestamp (bool): Add indexed_at timestamp
          Default: True
        - max_retries (int): Maximum retry attempts for failed indexing
          Default: 3
        - retry_delay (float): Delay between retries in seconds
          Default: 1.0
        - max_concurrent (int): Max concurrent processing
          Default: 3
        - continue_on_error (bool): Continue if an item fails
          Default: True
    
    Required Connectors:
        - AISearchConnector: For Azure AI Search operations
    
    Example:
        ```python
        # Index chunks to AI Search with basic settings
        executor = AISearchIndexOutputExecutor(
            id="index_writer",
            settings={
                "ai_search_account": "my-search-account",
                "ai_search_credential_type": "default_azure_credential",
                "ai_search_api_key": None,
                "ai_search_api_version": "2025-11-01-preview",
                "ai_search_index": "my-index",
                "index_mode": "documents",
                "content_to_index_mappings": {
                    "id.canonical_id": "id",
                    "text": "content",
                    "text_embedding": "vector"
                },
                "batch_size": 100
            }
        )
        
        # Index with vector fields for semantic search
        executor = AISearchIndexOutputExecutor(
            id="index_writer",
            settings={
                "ai_search_account": "my-search-account",
                "ai_search_credential_type": "default_azure_credential",
                "ai_search_api_key": None,
                "ai_search_api_version": "2025-11-01-preview",
                "ai_search_index": "my-index",
                "index_mode": "chunks",
                "chunk_iterator_field": "chunks",
                "content_to_index_mappings": {
                    "chunk.text": "content",
                    "chunk.embedding": "vector",
                    "id.canonical_id": "document_id",
                    "id.path": "filepath",
                    "id.filename": "filename",
                    "metadata.source": "source",
                    "metadata.author": "author"
                },
                "index_action_type": "mergeOrUpload",
                "batch_size": 50,
                "add_timestamp": True
            }
        )
        
        # Index full documents with retry logic
        executor = AISearchIndexOutputExecutor(
            id="index_writer",
            settings={
                "ai_search_account": "my-search-account",
                "ai_search_credential_type": "default_azure_credential",
                "ai_search_api_key": None,
                "ai_search_api_version": "2025-11-01-preview",
                "ai_search_index": "my-index",
                "index_mode": "documents",
                "content_to_index_mappings": {
                    "id.canonical_id": "document_id",
                    "content": "content",
                    "metadata.source": "source",
                    "metadata.author": "author"
                },
                "index_action_type": "upload",
                "max_retries": 3,
                "retry_delay": 2.0
            }
        )
        ```
    
    Input:
        Content or List[Content] with:
        - id: Content identifier
        - data: Dict containing content/chunks
        
    Output:
        Content or List[Content] with added summary_data:
        - indexed_count: Number of items indexed
        - index_status: "success" or "error"
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        fail_on_error: bool = False,
        debug_mode: bool = False,
        **kwargs
    ):
        super().__init__(
            id=id,
            settings=settings,
            enabled=enabled,
            fail_on_error=fail_on_error,
            debug_mode=debug_mode,
            **kwargs
        )
       
        # Connector configuration
        self.ai_search_account = self.get_setting("ai_search_account", default=None)
        self.ai_search_credential_type = self.get_setting("ai_search_credential_type", default="default_azure_credential")
        self.ai_search_api_key = self.get_setting("ai_search_api_key", default=None)
        self.ai_search_api_version = self.get_setting("ai_search_api_version", default="2025-11-01-preview")
        self.ai_search_index = self.get_setting("ai_search_index", default=None)
       
        # Indexing mode
        self.index_mode = self.get_setting("index_mode", default="chunks")
        
        # Field mappings
        self.chunk_iterator_field = self.get_setting("chunk_iterator_field", default="chunks")

        self.content_to_index_mappings = self.get_setting("content_to_index_mappings", default=None, required=True)
        if not isinstance(self.content_to_index_mappings, str):
            raise ValueError("'content_to_index_mappings' must be a JSON string of source -> target field paths")
        try:
            self.content_to_index_mappings = json.loads(self.content_to_index_mappings)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse 'content_to_index_mappings' JSON string: {e}")
        
        # Indexing options
        self.index_action_type = self.get_setting("index_action_type", default="mergeOrUpload")
        valid_actions = ["upload", "merge", "mergeOrUpload", "delete"]
        if self.index_action_type not in valid_actions:
            raise ValueError(
                f"Invalid index_action_type: {self.index_action_type}. "
                f"Must be one of {valid_actions}"
            )
        
        self.batch_size = self.get_setting("batch_size", default=100)
        self.add_timestamp = self.get_setting("add_timestamp", default=True)

        # Retry configuration
        self.max_retries = self.get_setting("max_retries", default=3)
        self.retry_delay = self.get_setting("retry_delay", default=1.0)
       
        # Connector instance (will be initialized on first use)
        self._connector = None
        
        if self.debug_mode:
            logger.debug(
                f"AISearchIndexWriterExecutor {self.id} initialized: "
                f"ai_search_account={self.ai_search_account}, "
                f"batch_size={self.batch_size}, action_type={self.index_action_type}"
            )
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """
        Get value from nested dictionary using dot notation.
        
        Args:
            data: Dictionary to extract value from
            field_path: Dot-separated path (e.g., "id.unique_id" or "metadata.author")
        
        Returns:
            Value at the field path, or None if not found
        """
        if not field_path:
            return None
        
        # Remove 'chunk.' prefix if present
        keys = field_path.replace('chunk.', '').split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _apply_mappings(
        self,
        source_data: Dict[str, Any],
        mappings: Dict[str, str],
        target_doc: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply field mappings from source data to target document.
        
        Args:
            source_data: Source dictionary to extract values from
            mappings: Dictionary mapping source field paths to target field names
            target_doc: Optional existing target document to update
        
        Returns:
            Target document with mapped fields
        """
        if target_doc is None:
            target_doc = {}
        
        for source_path, target_field in mappings.items():
            value = self._get_nested_value(source_data, source_path)
            if value is not None:
                # Convert complex types to strings if needed
                if isinstance(value, (dict, list)):
                    target_doc[target_field] = json.dumps(value)
                else:
                    target_doc[target_field] = value
        
        return target_doc
    
    async def _get_connector(self) -> AISearchConnector:
        """
        Get or initialize the AI Search connector.
        
        Returns:
            AISearchConnector instance
        """
        if self._connector is None:
            
            self._connector = AISearchConnector(
                name=f"ai_search_connector_{self.id}",
                settings={
                    "account_name": self.ai_search_account,
                    "credential_type": self.ai_search_credential_type,
                    "api_key": self.ai_search_api_key,
                    "api_version": self.ai_search_api_version,
                    "index_name": self.ai_search_index
                },
            )
            
            # Ensure connector is initialized
            await self._connector.initialize()
        
        return self._connector
    
    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """Index content item into AI Search."""
        
        if not content or not content.data:
            raise ValueError("Content must have data")
        
        # Get search connector
        search = await self._get_connector()
        
        try:
            if self.index_mode == "chunks":
                indexed_count = await self._index_chunks(content, search)
            else:
                indexed_count = await self._index_document(content, search)
            
            content.summary_data['indexed_count'] = indexed_count
            content.summary_data['index_status'] = "success"
            
            if self.debug_mode:
                logger.debug(
                    f"Indexed {indexed_count} items for content {content.id.canonical_id if content.id else 'unknown'}"
                )
            
        except Exception as e:
            content_id = content.id.canonical_id if content.id else 'unknown'
            logger.error(f"Error indexing content {content_id}: {e}")
            content.summary_data['index_status'] = "error"
            content.summary_data['index_error'] = str(e)
            
            # raise the exception to be handled upstream if needed
            raise
        
        return content
    
    async def _index_chunks(
        self,
        content: Content,
        search: AISearchConnector
    ) -> int:
        """Index content chunks as separate search documents."""
        
        # Get chunks
        chunks = content.data.get(self.chunk_iterator_field, [])
        if not chunks:
            logger.warning(
                f"No chunks found in field '{self.chunk_iterator_field}' for content "
                f"{content.id.canonical_id if content.id else 'unknown'}"
            )
            return 0
        
        # Build search documents for each chunk
        search_docs = []
        
        # Create combined source data for content-level mappings
        content_source = {}
        if content.id:
            content_source['id'] = {
                'unique_id': content.id.unique_id,
                'canonical_id': content.id.canonical_id,
                'filename': content.id.filename
            }
        content_source.update(content.data)
        content_source.update(content.summary_data)
                
        for i, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                logger.warning(f"Chunk {i} is not a dict, skipping")
                continue
            
            # Start with empty search doc
            search_doc = {}
            
            # Apply content-level mappings (document metadata)
            self._apply_mappings(content_source, self.content_to_index_mappings, search_doc)
            
            # Apply chunk-level mappings (chunk-specific data)
            self._apply_mappings(chunk, self.content_to_index_mappings, search_doc)
            
            # Add chunk index
            search_doc['chunk_index'] = i
            
            # Add timestamp
            if self.add_timestamp:
                search_doc['indexed_at'] = datetime.now(timezone.utc).isoformat()
            
            search_docs.append(search_doc)
        
        if not search_docs:
            logger.warning(
                f"No valid chunks to index for content "
                f"{content.id.canonical_id if content.id else 'unknown'}"
            )
            return 0
        
        # Index chunks in batches with retry logic
        total_indexed = 0
        for i in range(0, len(search_docs), self.batch_size):
            batch = search_docs[i:i + self.batch_size]
            await self._index_with_retry(search, batch)
            total_indexed += len(batch)
            
            if self.debug_mode:
                logger.debug(
                    f"Indexed batch {i // self.batch_size + 1}: "
                    f"{len(batch)} chunks ({total_indexed}/{len(search_docs)})"
                )
        
        return total_indexed
    
    async def _index_document(
        self,
        content: Content,
        search: AISearchConnector
    ) -> int:
        """Index the entire content item as a single document."""
        
        # Create combined source data
        content_source = {}
        if content.id:
            content_source['id'] = {
                'unique_id': content.id.unique_id,
                'canonical_id': content.id.canonical_id,
                'filename': content.id.filename
            }
        content_source.update(content.data)
        content_source.update(content.summary_data)
        
        # Start with empty search doc
        search_doc = {}
        
        # Apply content-level mappings
        self._apply_mappings(content_source, self.content_to_index_mappings, search_doc)
        
        # Add timestamp
        if self.add_timestamp:
            search_doc['indexed_at'] = datetime.now(timezone.utc).isoformat()
        
        # Index document with retry logic
        await self._index_with_retry(search, [search_doc])
        
        return 1
    
    async def _index_with_retry(
        self,
        search: AISearchConnector,
        documents: List[Dict[str, Any]]
    ) -> None:
        """
        Index documents with retry logic.
        
        Args:
            search: AISearchConnector instance
            documents: List of documents to index
        """
        import asyncio
        
        for attempt in range(self.max_retries):
            try:
                # Determine action based on index_action_type
                if self.index_action_type == "mergeOrUpload":
                    await search.index_documents(
                        documents=documents,
                        merge_or_upload=True
                    )
                elif self.index_action_type == "upload":
                    await search.index_documents(
                        documents=documents,
                        merge_or_upload=False
                    )
                else:
                    # For merge and delete, we'd need to extend the connector
                    # For now, fall back to mergeOrUpload
                    logger.warning(
                        f"Action type '{self.index_action_type}' not fully supported. "
                        f"Using mergeOrUpload."
                    )
                    await search.index_documents(
                        documents=documents,
                        merge_or_upload=True
                    )
                
                # Success - break retry loop
                return
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"Indexing failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {self.retry_delay}s..."
                    )
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(
                        f"Indexing failed after {self.max_retries} attempts: {e}"
                    )
                    raise
    
    