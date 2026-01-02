"""
Result aggregation executors.

This module provides executors that aggregate results from parallel
or batch processing operations.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from agent_framework import WorkflowContext

from .base import DocumentExecutor

try:
    from doc.proc.models import Document
except ImportError as e:
    raise ImportError(f"Failed to import doc-proc-lib models: {e}")

logger = logging.getLogger("doc_proc_workflow.executors.batch_aggregator")


class ResultAggregator(DocumentExecutor):
    """
    Aggregate results from parallel processing operations.
    
    Collects results from multiple documents and combines them using
    various aggregation strategies.
    
    Configuration:
        aggregation_strategy (str): How to aggregate results (default: "merge_list")
            - "merge_list": Combine all results into a list
            - "concatenate": Concatenate text content
            - "summarize": Combine summary statistics
            - "first": Return first result only
            - "last": Return last result only
        results_key (str): Key containing results to aggregate (default: "result")
        output_key (str): Key to store aggregated results (default: "aggregated_results")
    
    Example:
        ```yaml
        - id: aggregator
          type: result_aggregator
          settings:
            aggregation_strategy: merge_list
            results_key: processed_data
        ```
    """
    
    def __init__(self, settings: Dict[str, Any] = None, **kwargs):
        super().__init__(id=kwargs.get("id", "result_aggregator"), settings=settings)
        
        self.aggregation_strategy = self.get_setting("aggregation_strategy", default="merge_list")
        self.results_key = self.get_setting("results_key", default="result")
        self.output_key = self.get_setting("output_key", default="aggregated_results")
        
        logger.info(f"Initialized ResultAggregator: strategy={self.aggregation_strategy}")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        """
        Aggregate results from document.
        
        Expects document.data to contain a list of results or documents to aggregate.
        
        Args:
            document: Document containing results to aggregate
            ctx: Workflow context
            
        Returns:
            Document with aggregated results
        """
        # Check for various possible result locations
        results = None
        
        # Try common keys for results
        for key in [self.results_key, "results", "documents", "chunks", "rows", "batches"]:
            if key in document.data:
                results = document.data[key]
                break
        
        if not results:
            logger.warning(f"No results found in document {document.id}")
            document.data[self.output_key] = []
            document.summary_data["aggregation_count"] = 0
            return document
        
        # Apply aggregation strategy
        if self.aggregation_strategy == "merge_list":
            aggregated = self._merge_list(results)
        elif self.aggregation_strategy == "concatenate":
            aggregated = self._concatenate(results)
        elif self.aggregation_strategy == "summarize":
            aggregated = self._summarize(results)
        elif self.aggregation_strategy == "first":
            aggregated = results[0] if results else None
        elif self.aggregation_strategy == "last":
            aggregated = results[-1] if results else None
        else:
            logger.warning(f"Unknown aggregation strategy: {self.aggregation_strategy}, using merge_list")
            aggregated = self._merge_list(results)
        
        document.data[self.output_key] = aggregated
        document.summary_data["aggregation_strategy"] = self.aggregation_strategy
        document.summary_data["aggregation_count"] = len(results) if isinstance(results, list) else 1
        
        logger.info(
            f"Aggregated {len(results) if isinstance(results, list) else 1} results "
            f"using {self.aggregation_strategy} strategy"
        )
        
        return document
    
    def _merge_list(self, results: List[Any]) -> List[Any]:
        """Merge results into a flat list."""
        merged = []
        for result in results:
            if isinstance(result, dict):
                # If result has a 'data' or 'content' key, extract that
                if "data" in result:
                    merged.append(result["data"])
                elif "content" in result:
                    merged.append(result["content"])
                else:
                    merged.append(result)
            else:
                merged.append(result)
        return merged
    
    def _concatenate(self, results: List[Any]) -> str:
        """Concatenate text content from results."""
        parts = []
        for result in results:
            if isinstance(result, str):
                parts.append(result)
            elif isinstance(result, dict):
                # Try common content keys
                for key in ["content", "text", "data", "chunk_content"]:
                    if key in result:
                        parts.append(str(result[key]))
                        break
            else:
                parts.append(str(result))
        
        return "\n\n".join(parts)
    
    def _summarize(self, results: List[Any]) -> Dict[str, Any]:
        """Summarize statistics from results."""
        summary = {
            "total_count": len(results),
            "aggregated_at": str(logger._cache),  # Timestamp placeholder
        }
        
        # Collect numeric statistics
        numeric_fields = {}
        for result in results:
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, (int, float)):
                        if key not in numeric_fields:
                            numeric_fields[key] = []
                        numeric_fields[key].append(value)
        
        # Calculate aggregates for numeric fields
        for field, values in numeric_fields.items():
            summary[f"{field}_sum"] = sum(values)
            summary[f"{field}_avg"] = sum(values) / len(values) if values else 0
            summary[f"{field}_min"] = min(values) if values else None
            summary[f"{field}_max"] = max(values) if values else None
        
        return summary


class ChunkAggregator(DocumentExecutor):
    """
    Aggregate processed document chunks back into complete document.
    
    Combines chunks that were split by DocumentSplitter after they've
    been processed.
    
    Configuration:
        chunks_key (str): Key in document.data containing chunks (default: "chunks")
        merge_strategy (str): How to merge chunks (default: "concatenate")
            - "concatenate": Join text content
            - "merge_summaries": Combine summary data
            - "preserve_chunks": Keep chunks separate
        chunk_separator (str): Separator between chunks (default: "\n\n")
    
    Example:
        ```yaml
        - id: chunk_merger
          type: chunk_aggregator
          settings:
            merge_strategy: concatenate
            chunk_separator: "\n---\n"
        ```
    """
    
    def __init__(self, settings: Dict[str, Any] = None, **kwargs):
        super().__init__(id=kwargs.get("id", "chunk_aggregator"), settings=settings)
        
        self.chunks_key = self.get_setting("chunks_key", default="chunks")
        self.merge_strategy = self.get_setting("merge_strategy", default="concatenate")
        self.chunk_separator = self.get_setting("chunk_separator", default="\n\n")
        
        logger.info(f"Initialized ChunkAggregator: merge_strategy={self.merge_strategy}")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        """
        Aggregate processed chunks.
        
        Args:
            document: Document containing processed chunks
            ctx: Workflow context
            
        Returns:
            Document with merged chunks
        """
        chunks = document.data.get(self.chunks_key, [])
        
        if not chunks:
            logger.warning(f"No chunks found in document {document.id}")
            return document
        
        if self.merge_strategy == "concatenate":
            merged_content = self._concatenate_chunks(chunks)
            document.data["merged_content"] = merged_content
            document.summary_data["chunks_merged"] = len(chunks)
            
        elif self.merge_strategy == "merge_summaries":
            merged_summary = self._merge_chunk_summaries(chunks)
            document.summary_data.update(merged_summary)
            
        elif self.merge_strategy == "preserve_chunks":
            document.data["processed_chunks"] = chunks
            document.summary_data["chunks_preserved"] = len(chunks)
        
        logger.info(f"Aggregated {len(chunks)} chunks using {self.merge_strategy} strategy")
        
        return document
    
    def _concatenate_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """Concatenate chunk content in order."""
        # Sort chunks by index to maintain order
        sorted_chunks = sorted(chunks, key=lambda c: c.get("chunk_index", 0))
        
        parts = []
        for chunk in sorted_chunks:
            content = chunk.get("content") or chunk.get("processed_content") or ""
            if content:
                parts.append(str(content))
        
        return self.chunk_separator.join(parts)
    
    def _merge_chunk_summaries(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge summary data from all chunks."""
        merged = {"total_chunks": len(chunks)}
        
        for chunk in chunks:
            # If chunk has summary_data, merge it
            if isinstance(chunk, dict) and "summary_data" in chunk:
                for key, value in chunk["summary_data"].items():
                    if isinstance(value, (int, float)):
                        if key not in merged:
                            merged[key] = 0
                        merged[key] += value
        
        return merged


class BatchResultCollector(DocumentExecutor):
    """
    Collect and organize results from batch processing.
    
    Organizes results from batches, tracking success/failure rates
    and collecting errors.
    
    Configuration:
        batches_key (str): Key in document.data containing batch results (default: "batches")
        collect_errors (bool): Whether to collect error details (default: True)
        calculate_stats (bool): Whether to calculate statistics (default: True)
    
    Example:
        ```yaml
        - id: batch_collector
          type: batch_result_collector
          settings:
            collect_errors: true
            calculate_stats: true
        ```
    """
    
    def __init__(self, settings: Dict[str, Any] = None, **kwargs):
        super().__init__(id=kwargs.get("id", "batch_result_collector"), settings=settings)
        
        self.batches_key = self.get_setting("batches_key", default="batches")
        self.collect_errors = self.get_setting("collect_errors", default=True)
        self.calculate_stats = self.get_setting("calculate_stats", default=True)
        
        logger.info(f"Initialized BatchResultCollector")
    
    async def process_document(
        self,
        document: Document,
        ctx: WorkflowContext
    ) -> Document:
        """
        Collect batch results.
        
        Args:
            document: Document containing batch results
            ctx: Workflow context
            
        Returns:
            Document with organized results and statistics
        """
        batches = document.data.get(self.batches_key, [])
        
        if not batches:
            logger.warning(f"No batches found in document {document.id}")
            return document
        
        # Collect results
        all_results = []
        errors = []
        success_count = 0
        failure_count = 0
        
        for batch in batches:
            batch_results = batch.get("results", [])
            all_results.extend(batch_results)
            
            # Track success/failure
            for result in batch_results:
                if isinstance(result, dict):
                    if result.get("error") or result.get("failed"):
                        failure_count += 1
                        if self.collect_errors:
                            errors.append({
                                "batch_id": batch.get("batch_id"),
                                "error": result.get("error"),
                                "result_id": result.get("id")
                            })
                    else:
                        success_count += 1
        
        # Store collected results
        document.data["collected_results"] = all_results
        if self.collect_errors and errors:
            document.data["errors"] = errors
        
        # Calculate statistics
        if self.calculate_stats:
            total = success_count + failure_count
            document.summary_data.update({
                "total_batches": len(batches),
                "total_results": total,
                "successful_results": success_count,
                "failed_results": failure_count,
                "success_rate": success_count / total if total > 0 else 0,
                "failure_rate": failure_count / total if total > 0 else 0
            })
        
        logger.info(
            f"Collected {len(all_results)} results from {len(batches)} batches: "
            f"{success_count} successful, {failure_count} failed"
        )
        
        return document
