"""Base executor for cross-document analysis operations."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from agent_framework import WorkflowContext

from .base import BaseExecutor
from ..models import Content, ExecutorLogEntry

logger = logging.getLogger("contentflow.executors.cross_document_executor")


class CrossDocumentExecutor(BaseExecutor, ABC):
    """
    Base executor for cross-document analysis operations.
    
    Operates on Content items produced by DocumentSetCollectorExecutor,
    each containing consolidated data from all documents in a set under
    a configurable key (default: 'document_set').
    
    Accepts a single Content or a List[Content] (one per document set).
    Each item is processed independently via process_document_set().
    Returns a single Content when one set is processed, or a List[Content]
    when multiple sets are processed.
    
    Subclasses implement process_document_set() instead of process_input().
    The base class extracts the set data, calls the subclass, and writes
    results back to the Content item.
    
    Configuration (settings dict):
        - set_data_key (str): Key in Content.data for consolidated set data.
          Default: "document_set"
        - output_key (str): Key in Content.data for analysis results.
          Default: "cross_document_analysis"
        
        Also settings from BaseExecutor apply.
    
    Example:
        ```python
        class MyAnalysisExecutor(CrossDocumentExecutor):
            async def process_document_set(
                self,
                set_data: Dict[str, Any],
                content: Content,
                ctx: WorkflowContext
            ) -> Content:
                # Access ordered documents
                docs = self.get_documents_ordered(set_data)
                
                # Extract field across all documents
                revenues = self.extract_field_across_documents(
                    set_data, "data.financial_metrics.revenue"
                )
                
                # Build comparison matrix
                matrix = self.build_comparison_matrix(
                    set_data, ["data.revenue", "data.expenses"]
                )
                
                # Store results
                content.data[self.output_key] = {
                    "revenues": revenues,
                    "matrix": matrix,
                }
                return content
        ```
    
    Provided utility methods:
        - get_documents_ordered(set_data) -> List[dict]
        - get_document_by_role(set_data, role) -> Optional[dict]
        - extract_field_across_documents(set_data, field_path) -> List[Tuple[str, Any]]
        - build_comparison_matrix(set_data, field_paths) -> Dict[str, Dict[str, Any]]
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        self.set_data_key = self.get_setting("set_data_key", default="document_set")
        self.output_key = self.get_setting("output_key", default="cross_document_analysis")
        
        if self.debug_mode:
            logger.debug(
                f"CrossDocumentExecutor {self.id} initialized: "
                f"set_data_key={self.set_data_key}, output_key={self.output_key}"
            )
    
    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """
        Process consolidated document set data.
        
        Accepts a single Content item or a list of Content items (e.g. when
        DocumentSetCollectorExecutor produces one consolidated Content per
        document set).  Each Content item is processed independently via
        ``process_document_set()``.
        
        Args:
            input: Content item or list of Content items, each containing
                consolidated set data under ``set_data_key``.
            ctx: Workflow context
            
        Returns:
            A single Content when only one item is processed, or a
            List[Content] when multiple items are processed.
        """
        start_time = datetime.now()
        
        # Normalize to list
        if isinstance(input, Content):
            content_items = [input]
        else:
            content_items = list(input)
        
        if not content_items:
            raise ValueError(
                f"{self.id}: Received empty input, nothing to process."
            )
        
        results: List[Content] = []
        
        for content in content_items:
            result = await self._process_single_set(content, ctx, start_time)
            results.append(result)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"{self.id}: Cross-document analysis completed for "
            f"{len(results)} document set(s) in {elapsed:.2f}s"
        )
        
        # Return a single Content when there is exactly one result
        if len(results) == 1:
            return results[0]
        return results
    
    async def _process_single_set(
        self,
        content: Content,
        ctx: WorkflowContext,
        start_time: datetime,
    ) -> Content:
        """
        Validate, delegate, and log processing for a single Content item.
        
        Args:
            content: Content item with consolidated set data.
            ctx: Workflow context.
            start_time: Timestamp when overall processing began (for logs).
            
        Returns:
            Content item enriched with cross-document analysis results.
        """
        # Extract set data
        set_data = content.data.get(self.set_data_key)
        if not set_data:
            raise ValueError(
                f"{self.id}: No document set data found at key '{self.set_data_key}' "
                f"in Content. Ensure DocumentSetCollectorExecutor runs before this executor."
            )
        
        if not isinstance(set_data, dict) or "documents" not in set_data:
            raise ValueError(
                f"{self.id}: Invalid document set data structure at key '{self.set_data_key}'. "
                f"Expected dict with 'documents' list."
            )
        
        doc_count = len(set_data.get("documents", []))
        set_name = set_data.get("set_name", "unknown")
        logger.info(
            f"{self.id}: Processing document set '{set_name}' "
            f"with {doc_count} documents"
        )
        
        # Delegate to subclass
        result = await self.process_document_set(set_data, content, ctx)
        
        # Add executor log entry
        elapsed = (datetime.now() - start_time).total_seconds()
        result.executor_logs.append(ExecutorLogEntry(
            executor_id=self.id,
            start_time=start_time,
            end_time=datetime.now(),
            status="completed",
            details={
                "set_id": set_data.get("set_id", ""),
                "set_name": set_name,
                "documents_analyzed": doc_count,
                "duration_seconds": elapsed,
            },
            errors=[]
        ))
        
        logger.info(
            f"{self.id}: Cross-document analysis completed for "
            f"'{set_name}' in {elapsed:.2f}s"
        )
        
        return result
    
    @abstractmethod
    async def process_document_set(
        self,
        set_data: Dict[str, Any],
        content: Content,
        ctx: WorkflowContext
    ) -> Content:
        """
        Process the consolidated document set.
        
        Subclasses must implement this method with their specific
        cross-document analysis logic.
        
        Args:
            set_data: The document set dict containing:
                - set_id (str): Unique set identifier
                - set_name (str): Human-readable name
                - total_documents (int): Number of documents
                - documents (list[dict]): Ordered list of document entries,
                  each with 'role', 'order', 'data', 'summary_data', etc.
            content: The parent Content item (modify and return)
            ctx: Workflow context
            
        Returns:
            Content with cross-document analysis results added
        """
        raise NotImplementedError("Subclasses must implement process_document_set")
    
    # --- Utility methods ---
    
    def get_documents_ordered(self, set_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Return documents sorted by set_order.
        
        Args:
            set_data: The consolidated document set data
            
        Returns:
            List of document dicts sorted by order
        """
        return sorted(
            set_data.get("documents", []),
            key=lambda d: d.get("order", 0)
        )
    
    def get_document_by_role(
        self, set_data: Dict[str, Any], role: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find a specific document by its role label.
        
        Args:
            set_data: The consolidated document set data
            role: The role label to search for
            
        Returns:
            Document dict if found, None otherwise
        """
        for doc in set_data.get("documents", []):
            if doc.get("role") == role:
                return doc
        return None
    
    def extract_field_across_documents(
        self, set_data: Dict[str, Any], field_path: str
    ) -> List[Tuple[str, Any]]:
        """
        Extract a specific field value from each document in order.
        
        Args:
            set_data: The consolidated document set data
            field_path: Dot-separated path to the field within each document
                        (e.g., "data.financial_metrics.revenue")
            
        Returns:
            List of (role, value) tuples in document order.
            Example: [("Q1_2024", 10500000), ("Q2_2024", 11200000), ...]
        """
        results = []
        for doc in self.get_documents_ordered(set_data):
            role = doc.get("role", f"doc_{doc.get('order', 0)}")
            value = self._extract_nested_value(doc, field_path)
            results.append((role, value))
        return results
    
    def build_comparison_matrix(
        self, set_data: Dict[str, Any], field_paths: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build a matrix of field values across all documents.
        
        Args:
            set_data: The consolidated document set data
            field_paths: List of dot-separated field paths to extract
            
        Returns:
            Dict mapping field names to dicts of {role: value}.
            Example: {
                "revenue": {"Q1_2024": 10500000, "Q2_2024": 11200000},
                "expenses": {"Q1_2024": 8200000, "Q2_2024": 8500000},
            }
        """
        matrix = {}
        for field_path in field_paths:
            # Use the last part of the path as the field name
            field_name = field_path.split(".")[-1]
            values = self.extract_field_across_documents(set_data, field_path)
            matrix[field_name] = {role: value for role, value in values}
        return matrix
    
    def _extract_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """
        Extract a nested value from a dict using dot notation.
        
        Args:
            data: Dict to extract from
            field_path: Dot-separated path (e.g., "data.metrics.revenue")
            
        Returns:
            Extracted value or None if path doesn't exist
        """
        parts = field_path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
