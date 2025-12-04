"""Executor implementations for content processing workflows."""

from .base import BaseExecutor

# Parallel processing executor
from .parallel_executor import ParallelExecutor

# # Batch processing executors
# from .batch_splitter import (
#     DocumentSplitter,
#     BatchDocumentSplitter,
#     TableRowSplitter,
# )
# from .batch_aggregator import (
#     ResultAggregator,
#     ChunkAggregator,
#     BatchResultCollector,
# )
# from .batch_processor import (
#     BatchProcessor,
#     ParallelDocumentProcessor,
#     FilterProcessor,
# )

# # Sub-workflow executors
# from .subworkflow import (
#     SubWorkflowExecutor,
#     RowSubWorkflowExecutor,
#     ChunkSubWorkflowExecutor,
#     BatchSubWorkflowExecutor,
# )

# Specialized executors
from .azure_blob_input_executor import AzureBlobInputExecutor
from .content_retriever import ContentRetrieverExecutor
# from .custom_ai_prompt import CustomAIPromptExecutor
# from .ai_search_index_writer import AISearchIndexWriterExecutor
from .azure_document_intelligence_extractor import AzureDocumentIntelligenceExtractorExecutor
from .azure_content_understanding_extractor import AzureContentUnderstandingExtractorExecutor
from .pdf_extractor import PDFExtractorExecutor
from .recursive_text_chunker_executor import RecursiveTextChunkerExecutor
from .word_extractor import WordExtractorExecutor
from .powerpoint_extractor import PowerPointExtractorExecutor
from .excel_extractor import ExcelExtractorExecutor
from .table_row_splitter_executor import TableRowSplitterExecutor
from .azure_openai_agent_executor import AzureOpenAIAgentExecutor
from .azure_openai_embeddings_executor import AzureOpenAIEmbeddingsExecutor
from .summarization_executor import SummarizationExecutor
from .entity_extraction_executor import EntityExtractionExecutor
from .sentiment_analysis_executor import SentimentAnalysisExecutor
from .content_classifier_executor import ContentClassifierExecutor
from .pii_detector_executor import PIIDetectorExecutor
from .keyword_extractor_executor import KeywordExtractorExecutor
from .language_detector_executor import LanguageDetectorExecutor
from .translation_executor import TranslationExecutor
from .pass_through import PassThroughExecutor

from .executor_registry import ExecutorRegistry
from .executor_config import ExecutorInstanceConfig

__all__ = [
    # Base
    "BaseExecutor",
    # Parallel processing
    "ParallelExecutor",
    # # Batch splitters
    # "DocumentSplitter",
    # "BatchDocumentSplitter",
    # "TableRowSplitter",
    # # Batch aggregators
    # "ResultAggregator",
    # "ChunkAggregator",
    # "BatchResultCollector",
    # # Batch processors
    # "BatchProcessor",
    # "ParallelDocumentProcessor",
    # "FilterProcessor",
    # # Sub-workflow executors
    # "SubWorkflowExecutor",
    # "RowSubWorkflowExecutor",
    # "ChunkSubWorkflowExecutor",
    # "BatchSubWorkflowExecutor",
    # Specialized executors
    "AzureBlobInputExecutor",
    "ContentRetrieverExecutor",
    # "CustomAIPromptExecutor",
    # "AISearchIndexWriterExecutor"
    "AzureDocumentIntelligenceExtractorExecutor",
    "AzureContentUnderstandingExtractorExecutor",
    "PDFExtractorExecutor",
    "RecursiveTextChunkerExecutor",
    "WordExtractorExecutor",
    "PowerPointExtractorExecutor",
    "ExcelExtractorExecutor",
    "TableRowSplitterExecutor",
    "AzureOpenAIAgentExecutor",
    "AzureOpenAIEmbeddingsExecutor",
    "SummarizationExecutor",
    "EntityExtractionExecutor",
    "SentimentAnalysisExecutor",
    "ContentClassifierExecutor",
    "PIIDetectorExecutor",
    "KeywordExtractorExecutor",
    "LanguageDetectorExecutor",
    "TranslationExecutor",
    "PassThroughExecutor",
    # Registry and config
    "ExecutorRegistry",
    "ExecutorInstanceConfig",
]
