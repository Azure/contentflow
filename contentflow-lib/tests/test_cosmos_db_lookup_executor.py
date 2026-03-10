"""Unit tests for CosmosDBLookupExecutor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from contentflow.models import Content, ContentIdentifier
from contentflow.executors.cosmos_db_lookup_executor import CosmosDBLookupExecutor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_content(data: dict, canonical_id: str = "test-item") -> Content:
    return Content(
        id=ContentIdentifier(canonical_id=canonical_id, unique_id=canonical_id),
        data=data,
    )


def _base_settings(**overrides) -> dict:
    """Return minimal valid settings, merged with overrides."""
    settings = {
        "cosmos_endpoint": "https://fake-account.documents.azure.com:443/",
        "cosmos_key": "fake-key==",
        "cosmos_database": "testdb",
        "cosmos_container": "testcontainer",
        "lookup_mode": "query",
        "query_template": "SELECT * FROM c WHERE c.sku = @sku",
        "field_mappings": {"@sku": "product.sku"},
        "output_field": "lookup_result",
    }
    settings.update(overrides)
    return settings


# ---------------------------------------------------------------------------
# Initialisation tests
# ---------------------------------------------------------------------------

def test_init_with_valid_settings():
    """Executor initialises without error given valid settings."""
    executor = CosmosDBLookupExecutor(id="t", settings=_base_settings())
    assert executor.lookup_mode == "query"
    assert executor.output_field == "lookup_result"
    assert executor.query_template == "SELECT * FROM c WHERE c.sku = @sku"


def test_init_invalid_lookup_mode():
    """Invalid lookup_mode raises ValueError."""
    with pytest.raises(ValueError, match="Invalid lookup_mode"):
        CosmosDBLookupExecutor(id="t", settings=_base_settings(lookup_mode="bad"))


def test_init_query_mode_requires_template():
    """query mode without query_template raises ValueError."""
    with pytest.raises(ValueError, match="query_template is required"):
        CosmosDBLookupExecutor(
            id="t",
            settings=_base_settings(query_template=None),
        )


def test_init_point_read_mode_no_template_needed():
    """point_read mode does not require query_template."""
    settings = _base_settings(
        lookup_mode="point_read",
        query_template=None,
        field_mappings={"id": "item_id", "partition_key": "pk"},
    )
    executor = CosmosDBLookupExecutor(id="t", settings=settings)
    assert executor.lookup_mode == "point_read"


# ---------------------------------------------------------------------------
# Field resolution
# ---------------------------------------------------------------------------

def test_resolve_field_value_simple():
    executor = CosmosDBLookupExecutor(id="t", settings=_base_settings())
    content = _make_content({"product": {"sku": "ABC-123"}})
    assert executor._resolve_field_value(content, "product.sku") == "ABC-123"


def test_resolve_field_value_missing():
    executor = CosmosDBLookupExecutor(id="t", settings=_base_settings())
    content = _make_content({"other": "value"})
    assert executor._resolve_field_value(content, "product.sku") is None


def test_build_query_parameters():
    executor = CosmosDBLookupExecutor(id="t", settings=_base_settings())
    content = _make_content({"product": {"sku": "X-99"}})
    params = executor._build_query_parameters(content)
    assert params == [{"name": "@sku", "value": "X-99"}]


def test_build_query_parameters_adds_at_prefix():
    settings = _base_settings(field_mappings={"sku": "product.sku"})
    executor = CosmosDBLookupExecutor(id="t", settings=settings)
    content = _make_content({"product": {"sku": "Y-1"}})
    params = executor._build_query_parameters(content)
    assert params == [{"name": "@sku", "value": "Y-1"}]


# ---------------------------------------------------------------------------
# process_content_item — query mode
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_query_mode_returns_all():
    """Query mode with result_mode='all' returns a list."""
    executor = CosmosDBLookupExecutor(
        id="t",
        settings=_base_settings(result_mode="all"),
    )

    fake_items = [{"sku": "ABC", "name": "Widget"}, {"sku": "ABC", "name": "Widget v2"}]

    mock_connector = AsyncMock()
    mock_connector.query_items.return_value = fake_items
    executor._connector = mock_connector

    content = _make_content({"product": {"sku": "ABC"}})
    result = await executor.process_content_item(content)

    assert result.data["lookup_result"] == fake_items
    assert result.summary_data["cosmos_lookup_status"] == "success"
    mock_connector.query_items.assert_awaited_once()


@pytest.mark.asyncio
async def test_query_mode_returns_first():
    """Query mode with result_mode='first' returns a single dict."""
    executor = CosmosDBLookupExecutor(
        id="t",
        settings=_base_settings(result_mode="first"),
    )

    fake_items = [{"sku": "ABC", "name": "Widget"}, {"sku": "ABC", "name": "v2"}]

    mock_connector = AsyncMock()
    mock_connector.query_items.return_value = fake_items
    executor._connector = mock_connector

    content = _make_content({"product": {"sku": "ABC"}})
    result = await executor.process_content_item(content)

    assert result.data["lookup_result"] == {"sku": "ABC", "name": "Widget"}


@pytest.mark.asyncio
async def test_query_mode_first_empty():
    """result_mode='first' returns None when no items match."""
    executor = CosmosDBLookupExecutor(
        id="t",
        settings=_base_settings(result_mode="first"),
    )

    mock_connector = AsyncMock()
    mock_connector.query_items.return_value = []
    executor._connector = mock_connector

    content = _make_content({"product": {"sku": "ZZZ"}})
    result = await executor.process_content_item(content)

    assert result.data["lookup_result"] is None


@pytest.mark.asyncio
async def test_query_mode_flatten_single():
    """flatten_single unwraps a single-element list."""
    executor = CosmosDBLookupExecutor(
        id="t",
        settings=_base_settings(result_mode="all", flatten_single=True),
    )

    mock_connector = AsyncMock()
    mock_connector.query_items.return_value = [{"sku": "X", "price": 10}]
    executor._connector = mock_connector

    content = _make_content({"product": {"sku": "X"}})
    result = await executor.process_content_item(content)

    assert result.data["lookup_result"] == {"sku": "X", "price": 10}


# ---------------------------------------------------------------------------
# process_content_item — point-read mode
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_point_read_found():
    """Point read returns the item when found."""
    settings = _base_settings(
        lookup_mode="point_read",
        query_template=None,
        field_mappings={"id": "item_id", "partition_key": "category"},
    )
    executor = CosmosDBLookupExecutor(id="t", settings=settings)

    expected = {"id": "abc", "category": "tools", "name": "Hammer"}
    mock_connector = AsyncMock()
    mock_connector.point_read.return_value = expected
    executor._connector = mock_connector

    content = _make_content({"item_id": "abc", "category": "tools"})
    result = await executor.process_content_item(content)

    assert result.data["lookup_result"] == expected
    mock_connector.point_read.assert_awaited_once_with(
        item_id="abc", partition_key="tools"
    )


@pytest.mark.asyncio
async def test_point_read_not_found():
    """Point read returns None when item is missing."""
    settings = _base_settings(
        lookup_mode="point_read",
        query_template=None,
        field_mappings={"id": "item_id", "partition_key": "category"},
    )
    executor = CosmosDBLookupExecutor(id="t", settings=settings)

    mock_connector = AsyncMock()
    mock_connector.point_read.return_value = None
    executor._connector = mock_connector

    content = _make_content({"item_id": "missing", "category": "tools"})
    result = await executor.process_content_item(content)

    assert result.data["lookup_result"] is None
    assert result.summary_data["cosmos_lookup_status"] == "success"


@pytest.mark.asyncio
async def test_point_read_missing_field():
    """Point read returns None and warns when lookup fields are missing."""
    settings = _base_settings(
        lookup_mode="point_read",
        query_template=None,
        field_mappings={"id": "item_id", "partition_key": "category"},
    )
    executor = CosmosDBLookupExecutor(id="t", settings=settings)

    mock_connector = AsyncMock()
    executor._connector = mock_connector

    # content.data missing 'category'
    content = _make_content({"item_id": "abc"})
    result = await executor.process_content_item(content)

    assert result.data["lookup_result"] is None
    mock_connector.point_read.assert_not_awaited()


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_error_sets_status_and_continues():
    """On error with continue_on_error, status is 'error' and no exception raised."""
    executor = CosmosDBLookupExecutor(
        id="t",
        settings=_base_settings(continue_on_error=True),
    )

    mock_connector = AsyncMock()
    mock_connector.query_items.side_effect = RuntimeError("boom")
    executor._connector = mock_connector

    content = _make_content({"product": {"sku": "X"}})
    result = await executor.process_content_item(content)

    assert result.data["lookup_result"] is None
    assert result.summary_data["cosmos_lookup_status"] == "error"
    assert "boom" in result.summary_data["cosmos_lookup_error"]


@pytest.mark.asyncio
async def test_error_raises_when_fail_pipeline():
    """With fail_pipeline_on_error=True, exception is re-raised."""
    executor = CosmosDBLookupExecutor(
        id="t",
        settings=_base_settings(fail_pipeline_on_error=True),
    )

    mock_connector = AsyncMock()
    mock_connector.query_items.side_effect = RuntimeError("critical")
    executor._connector = mock_connector

    content = _make_content({"product": {"sku": "X"}})
    with pytest.raises(RuntimeError, match="critical"):
        await executor.process_content_item(content)
