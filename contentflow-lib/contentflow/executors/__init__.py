"""Executor implementations for content processing workflows."""

from .base import BaseExecutor

# Parallel processing executor
from .parallel_executor import ParallelExecutor

# Input executor
from .input_executor import InputExecutor

# Specialized executors
from .azure_blob_input_discovery import AzureBlobInputDiscoveryExecutor
from .azure_blob_content_retriever import AzureBlobContentRetrieverExecutor
from .azure_blob_output_executor import AzureBlobOutputExecutor
from .content_retriever import ContentRetrieverExecutor
from .ai_search_index_output import AISearchIndexOutputExecutor
from .azure_document_intelligence_extractor import AzureDocumentIntelligenceExtractorExecutor
from .azure_content_understanding_extractor import AzureContentUnderstandingExtractorExecutor
from .pdf_extractor import PDFExtractorExecutor
from .recursive_text_chunker_executor import RecursiveTextChunkerExecutor
from .word_extractor import WordExtractorExecutor
from .powerpoint_extractor import PowerPointExtractorExecutor
from .excel_extractor import ExcelExtractorExecutor
from .csv_extractor import CSVExtractorExecutor
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
from .field_mapper_executor import FieldMapperExecutor
from .field_selector_executor import FieldSelectorExecutor
from .gptrag_search_index_doc_generator import GPTRAGSearchIndexDocumentGeneratorExecutor
from .web_scraping_executor import WebScrapingExecutor
from .pass_through import PassThroughExecutor

# Document Set executors
from .document_set_initializer import DocumentSetInitializerExecutor
from .document_set_collector import DocumentSetCollectorExecutor
from .cross_document_executor import CrossDocumentExecutor
from .cross_document_comparison import CrossDocumentComparisonExecutor
from .cross_document_field_aggregator import CrossDocumentFieldAggregatorExecutor

# Control Flow executors
from .for_each_content import ForEachContentExecutor

# # Knowledge Graph executors
# from .knowledge_graph_entity_extractor import KnowledgeGraphEntityExtractorExecutor
# from .knowledge_graph_writer import KnowledgeGraphWriterExecutor
# from .knowledge_graph_query import KnowledgeGraphQueryExecutor
# from .knowledge_graph_enrichment import KnowledgeGraphEnrichmentExecutor

from .executor_registry import ExecutorRegistry
from .executor_config import ExecutorConfig, ExecutorInstanceConfig

__all__ = [
    # Base
    "BaseExecutor",
    "InputExecutor",
    # Parallel processing
    "ParallelExecutor",
    # Specialized executors
    "AzureBlobInputDiscoveryExecutor",
    "AzureBlobContentRetrieverExecutor",
    "AzureBlobOutputExecutor",
    "ContentRetrieverExecutor",
    "AISearchIndexOutputExecutor",
    "AzureDocumentIntelligenceExtractorExecutor",
    "AzureContentUnderstandingExtractorExecutor",
    "PDFExtractorExecutor",
    "WebScrapingExecutor",
    "RecursiveTextChunkerExecutor",
    "WordExtractorExecutor",
    "PowerPointExtractorExecutor",
    "ExcelExtractorExecutor",
    "CSVExtractorExecutor",
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
    "FieldMapperExecutor",
    "FieldSelectorExecutor",
    "GPTRAGSearchIndexDocumentGeneratorExecutor",
    "PassThroughExecutor",
    # Document Set
    "DocumentSetInitializerExecutor",
    "DocumentSetCollectorExecutor",
    "CrossDocumentExecutor",
    "CrossDocumentComparisonExecutor",
    "CrossDocumentFieldAggregatorExecutor",
    # Control Flow
    "ForEachContentExecutor",
    # # Knowledge Graph
    # "KnowledgeGraphEntityExtractorExecutor",
    # "KnowledgeGraphWriterExecutor",
    # "KnowledgeGraphQueryExecutor",
    # "KnowledgeGraphEnrichmentExecutor",
    # Registry and config
    "ExecutorRegistry",
    "ExecutorConfig",
    "ExecutorInstanceConfig",
]
