"""Tests for AzureContentUnderstandingExtractorExecutor."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from contentflow.executors.azure_content_understanding_extractor import (
    AzureContentUnderstandingExtractorExecutor,
)
from contentflow.models import Content, ContentIdentifier


def test_processes_document_url():
    executor = AzureContentUnderstandingExtractorExecutor(
        id="content-understanding",
        settings={
            "content_understanding_endpoint": "https://example.test",
            "content_understanding_model_mappings": "{}",
        },
    )
    connector = MagicMock()
    connector.initialize = AsyncMock()
    connector.analyze_document_url = AsyncMock(return_value={"status": "Succeeded"})
    executor.content_understanding_connector = connector
    content = Content(
        id=ContentIdentifier(canonical_id="document", unique_id="document"),
        data={"url": "https://example.test/document.pdf"},
    )

    result = asyncio.run(executor.process_content_item(content))

    connector.analyze_document_url.assert_awaited_once_with(
        url="https://example.test/document.pdf",
        analyzer_id="prebuilt-documentSearch",
    )
    assert result.data["content_understanding_output"] == {"status": "Succeeded"}
    assert result.summary_data["extraction_status"] == "success"