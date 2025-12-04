"""AI Search index writer executor for indexing documents to Azure AI Search."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from . import ParallelExecutor
from ..models import Content
from ..connectors import AISearchConnector

logger = logging.getLogger(__name__)


class AISearchIndexWriterExecutor(ParallelExecutor):
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
        - index_mode (str): "documents" or "chunks". Defines if full documents or
          chunks are indexed.
          Default: "chunks"
        - field_to_index_mappings (Dict): JSON configuration for field mappings
          Default: {
            "id_field": "id",
            "key_field": "id",
            "content_field": "content",
            "chunk_field": "chunks",
            "chunk_text_field": "text",
            "metadata_fields": [],
            "chunk_metadata_fields": ["page_numbers", "chunk_index"]
          }
          Fields:
            - id_field: Field name for document ID in search index
            - key_field: Field name for document key in source data
            - content_field: Field name for searchable content in search index
            - chunk_field: Field containing chunks (for chunks mode)
            - chunk_text_field: Field within chunk containing text
            - metadata_fields: Document fields to include as metadata
            - chunk_metadata_fields: Chunk fields to include as metadata
        - index_action_type (str): Azure Search action type
          Default: "mergeOrUpload"
          Options: "upload", "merge", "mergeOrUpload", "delete"
        - batch_size (int): Number of documents to index per batch
          Default: 100
        - add_timestamp (bool): Add indexed_at timestamp
          Default: True
        - generate_id (bool): Auto-generate IDs if missing
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
        executor = AISearchIndexWriterExecutor(
            id="index_writer",
            settings={
                "ai_search_account": "my-search-account",
                "ai_search_credential_type": "default_azure_credential",
                "ai_search_api_key": None,
                "ai_search_api_version": "2025-11-01-preview",
                "ai_search_index": "my-index",
                "field_to_index_mappings": {
                    "chunk_field": "chunks",
                    "content_field": "content",
                    "metadata_fields": ["source", "file_type", "author"],
                    "chunk_metadata_fields": ["page_numbers", "chunk_index"]
                },
                "batch_size": 100
            }
        )
        
        # Index with vector fields for semantic search
        executor = AISearchIndexWriterExecutor(
            id="index_writer",
            settings={
                "ai_search_account": "my-search-account",
                "ai_search_credential_type": "default_azure_credential",
                "ai_search_api_key": None,
                "ai_search_api_version": "2025-11-01-preview",
                "ai_search_index": "my-index",
            }
        )
        
        # Index full documents with retry logic
        executor = AISearchIndexWriterExecutor(
            id="index_writer",
            settings={
                "ai_search_account": "my-search-account",
                "ai_search_credential_type": "default_azure_credential",
                "ai_search_api_key": None,
                "ai_search_api_version": "2025-11-01-preview",
                "ai_search_index": "my-index",
                "index_mode": "documents",
                "field_to_index_mappings": {
                    "content_field": "text",
                    "metadata_fields": ["title", "category", "date"]
                },
                "index_action_type": "upload",
                "max_retries": 5,
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
        - index_batch_results: Results from batch indexing (if available)
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
        self.id_field = self.get_setting("index_id_field", default="id.unique_id")
        self.chunk_field = self.get_setting("chunk_iterator_field", default="chunks")
        
        chunk_mappings = {
            "chunk_id": "chunk_id",
            "text": "content",
        }
        self.chunk_to_index_mappings = self.get_setting("chunk_to_index_mappings", default=chunk_mappings)
        
        content_mappings = {
            "id.unique_id": "id",
            "id.canonical_id": "filepath",
            "id.filename": "filename",
            "size": "size",
            "last_modified": "last_modified",
            "content_type": "content_type"
        }
        self.content_to_index_mappings = self.get_setting("content_to_index_mappings", default=content_mappings)
        
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
                f"ai_search_account={self.ai_search_account}, content_field={self.content_field}, "
                f"batch_size={self.batch_size}, action_type={self.index_action_type}"
            )
    
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
    
    async def _index_document(
        self,
        content: Content,
        search: AISearchConnector
    ) -> int:
        """Index the entire content item as a single document."""
        
        # Build search document
        content_id = content.id.canonical_id if content.id else None
        
        if self.generate_id and not content_id:
            content_id = self.generate_sha1_hash(str(content.data))
        
        search_doc = {
            self.id_field: str(content_id)
        }
        
        # Add content field
        text_content = content.data.get(self.content_field, "")
        if not text_content:
            logger.warning(f"No content found in field '{self.content_field}'")
        
        search_doc[self.content_field] = str(text_content)
        
        # Add metadata fields
        for field in self.metadata_fields:
            if field in content.data:
                search_doc[field] = content.data[field]
            elif field in content.summary_data:
                search_doc[field] = content.summary_data[field]
        
        # Add timestamp
        if self.add_timestamp:
            search_doc['indexed_at'] = datetime.utcnow().isoformat()
        
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
    
    async def _index_chunks(
        self,
        content: Content,
        search: AISearchConnector
    ) -> int:
        """Index content chunks as separate search documents."""
        
        # Get chunks
        chunks = content.data.get(self.chunk_field, [])
        if not chunks:
            logger.warning(
                f"No chunks found in field '{self.chunk_field}' for content "
                f"{content.id.canonical_id if content.id else 'unknown'}"
            )
            return 0
        
        # Build search documents for each chunk
        search_docs = []
        content_id = content.id.canonical_id if content.id else None
        
        if self.generate_id and not content_id:
            content_id = self.generate_sha1_hash(str(content.data))
        
        base_id = str(content_id)
        
        for i, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                logger.warning(f"Chunk {i} is not a dict, skipping")
                continue
            
            # Build chunk search doc
            chunk_id = f"{base_id}_chunk_{i}"
            search_doc = {
                self.id_field: chunk_id,
                "document_id": base_id,
                "chunk_index": i
            }
            
            # Add content from chunk
            chunk_text = chunk.get(self.chunk_text_field, "")
            if not chunk_text:
                # Try alternative content fields
                for alt_field in ["text", "markdown", "content"]:
                    if alt_field in chunk and chunk[alt_field]:
                        chunk_text = chunk[alt_field]
                        break
            
            if not chunk_text:
                logger.warning(f"Chunk {i} has no content, skipping")
                continue
            
            search_doc[self.content_field] = str(chunk_text)
            
            # Add chunk metadata fields
            for field in self.chunk_metadata_fields:
                if field in chunk:
                    value = chunk[field]
                    # Convert complex types to strings
                    if isinstance(value, (dict, list)):
                        search_doc[field] = str(value)
                    else:
                        search_doc[field] = value
            
            # Add document-level metadata
            for field in self.metadata_fields:
                if field in content.data and field not in search_doc:
                    search_doc[field] = content.data[field]
                elif field in content.summary_data and field not in search_doc:
                    search_doc[field] = content.summary_data[field]
            
            # Add timestamp
            if self.add_timestamp:
                search_doc['indexed_at'] = datetime.utcnow().isoformat()
            
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
