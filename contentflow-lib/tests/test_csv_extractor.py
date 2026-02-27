"""Unit tests for CSVExtractorExecutor."""

import os
import tempfile

import pytest

from contentflow.models import Content, ContentIdentifier
from contentflow.executors.csv_extractor import CSVExtractorExecutor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_content(data: dict, canonical_id: str = "test-csv") -> Content:
    return Content(
        id=ContentIdentifier(canonical_id=canonical_id, unique_id=canonical_id),
        data=data,
    )


SIMPLE_CSV = "name,age,city\nAlice,30,Seattle\nBob,25,Portland\n"

TSV_DATA = "col_a\tcol_b\n1\t2\n3\t4\n"

NO_HEADER_CSV = "x,10,yes\ny,20,no\n"

CSV_WITH_EMPTY_ROWS = "a,b\n1,2\n,,\n3,4\n"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_basic_csv_extraction():
    executor = CSVExtractorExecutor(id="t", settings={})
    content = _make_content({"content": SIMPLE_CSV})
    result = await executor.process_content_item(content)

    out = result.data["csv_output"]
    assert out["headers"] == ["name", "age", "city"]
    assert out["row_count"] == 2
    assert out["column_count"] == 3
    assert out["rows"][0] == {"name": "Alice", "age": "30", "city": "Seattle"}
    assert out["rows"][1] == {"name": "Bob", "age": "25", "city": "Portland"}
    assert result.summary_data["csv_extraction_status"] == "success"


@pytest.mark.asyncio
async def test_bytes_input():
    executor = CSVExtractorExecutor(id="t", settings={})
    content = _make_content({"content": SIMPLE_CSV.encode("utf-8")})
    result = await executor.process_content_item(content)

    assert result.data["csv_output"]["row_count"] == 2


@pytest.mark.asyncio
async def test_temp_file_input():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as f:
        f.write(SIMPLE_CSV)
        tmp_path = f.name

    try:
        executor = CSVExtractorExecutor(id="t", settings={})
        content = _make_content({"temp_file_path": tmp_path})
        result = await executor.process_content_item(content)
        assert result.data["csv_output"]["row_count"] == 2
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_tsv_delimiter():
    executor = CSVExtractorExecutor(id="t", settings={"delimiter": "\t"})
    content = _make_content({"content": TSV_DATA})
    result = await executor.process_content_item(content)

    out = result.data["csv_output"]
    assert out["headers"] == ["col_a", "col_b"]
    assert out["row_count"] == 2
    assert out["rows"][0] == {"col_a": "1", "col_b": "2"}


@pytest.mark.asyncio
async def test_no_header():
    executor = CSVExtractorExecutor(id="t", settings={"has_header": False})
    content = _make_content({"content": NO_HEADER_CSV})
    result = await executor.process_content_item(content)

    out = result.data["csv_output"]
    assert out["headers"] == ["col_0", "col_1", "col_2"]
    assert out["row_count"] == 2
    assert out["rows"][0] == {"col_0": "x", "col_1": "10", "col_2": "yes"}


@pytest.mark.asyncio
async def test_max_rows():
    executor = CSVExtractorExecutor(id="t", settings={"max_rows": 1})
    content = _make_content({"content": SIMPLE_CSV})
    result = await executor.process_content_item(content)

    assert result.data["csv_output"]["row_count"] == 1
    assert result.data["csv_output"]["rows"][0]["name"] == "Alice"


@pytest.mark.asyncio
async def test_skip_empty_rows():
    executor = CSVExtractorExecutor(id="t", settings={"skip_empty_rows": True})
    content = _make_content({"content": CSV_WITH_EMPTY_ROWS})
    result = await executor.process_content_item(content)

    assert result.data["csv_output"]["row_count"] == 2


@pytest.mark.asyncio
async def test_keep_empty_rows():
    executor = CSVExtractorExecutor(id="t", settings={"skip_empty_rows": False})
    content = _make_content({"content": CSV_WITH_EMPTY_ROWS})
    result = await executor.process_content_item(content)

    assert result.data["csv_output"]["row_count"] == 3


@pytest.mark.asyncio
async def test_infer_types():
    executor = CSVExtractorExecutor(id="t", settings={"infer_types": True})
    content = _make_content({"content": SIMPLE_CSV})
    result = await executor.process_content_item(content)

    row = result.data["csv_output"]["rows"][0]
    assert row["age"] == 30  # should be int, not "30"
    assert isinstance(row["age"], int)


@pytest.mark.asyncio
async def test_extract_text():
    executor = CSVExtractorExecutor(id="t", settings={"extract_text": True})
    content = _make_content({"content": SIMPLE_CSV})
    result = await executor.process_content_item(content)

    text = result.data["csv_output"]["text"]
    assert "name | age | city" in text
    assert "Alice | 30 | Seattle" in text


@pytest.mark.asyncio
async def test_missing_content_raises():
    executor = CSVExtractorExecutor(id="t", settings={})
    content = _make_content({"other_field": "nothing"})
    with pytest.raises(ValueError, match="CSV content missing"):
        await executor.process_content_item(content)


@pytest.mark.asyncio
async def test_empty_csv():
    executor = CSVExtractorExecutor(id="t", settings={})
    content = _make_content({"content": ""})
    result = await executor.process_content_item(content)

    out = result.data["csv_output"]
    assert out["headers"] == []
    assert out["rows"] == []
    assert out["row_count"] == 0


@pytest.mark.asyncio
async def test_custom_output_field():
    executor = CSVExtractorExecutor(id="t", settings={"output_field": "my_csv"})
    content = _make_content({"content": SIMPLE_CSV})
    result = await executor.process_content_item(content)

    assert "my_csv" in result.data
    assert result.data["my_csv"]["row_count"] == 2
