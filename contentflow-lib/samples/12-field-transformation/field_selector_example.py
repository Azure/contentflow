"""
Example usage and test of the Field Selector Executor.

This example demonstrates various field selection scenarios including:
- Basic field inclusion (keep only specific fields)
- Field exclusion (remove unwanted fields)
- Wildcard pattern matching
- Nested field selection
- Privacy-focused field removal
- Conditional field selection
"""

import asyncio
import logging
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from contentflow.executors import FieldSelectorExecutor
from contentflow.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent.parent

logger = logging.getLogger(__name__)

setup_logging()


def create_sample_content() -> Content:
    """Create a sample content item with nested data."""
    content_id = ContentIdentifier(
        canonical_id="test-doc-001",
        unique_id="test-doc-001-v1",
        source="test",
        content_type="document"
    )
    
    return Content(
        id=content_id,
        data={
            "title": "Test Document",
            "content": "This is the content of the document.",
            "author": "John Doe",
            "status": "approved",
            "metadata": {
                "created_date": "2024-01-01",
                "file_size": 1024,
                "department": "Engineering",
                "version": "1.0"
            },
            "personal_info": {
                "ssn": "123-45-6789",
                "credit_card": "4111-1111-1111-1111",
                "email": "john.doe@example.com"
            },
            "temp_processing_id": "tmp_12345",
            "temp_cache_data": {"key": "value"},
            "internal_metadata": {
                "processor": "v2",
                "timestamp": "2024-01-01T12:00:00Z"
            },
            "processing_stats": {
                "duration_ms": 150,
                "retries": 0
            }
        }
    )


async def example_basic_inclusion():
    """Example: Basic field inclusion - keep only specific fields."""
    print("=" * 60)
    print("\n=== Example 1: Basic Field Inclusion ===")
    
    executor = FieldSelectorExecutor(
        id="basic_include",
        settings={
            "mode": "include",
            "fields": '["title", "content", "author", "status"]'
        }
    )
    
    content = create_sample_content()
    print(f"Before selection: {list(content.data.keys())}")
    
    result = await executor.process_content_item(content, None)
    
    print(f"After selection: {list(result.data.keys())}")
    print(f"Fields kept: {len(result.data)} (expected 4)")


async def example_wildcard_exclusion():
    """Example: Exclude fields using wildcard patterns."""
    print("=" * 60)
    print("\n=== Example 2: Wildcard Exclusion (Remove temp_* fields) ===")
    
    executor = FieldSelectorExecutor(
        id="remove_temp",
        settings={
            "mode": "exclude",
            "fields": '["temp_*", "internal_*", "processing_stats"]'
        }
    )
    
    content = create_sample_content()
    print(f"Before exclusion: {list(content.data.keys())}")
    
    result = await executor.process_content_item(content, None)
    
    print(f"After exclusion: {list(result.data.keys())}")
    print(f"Temp fields removed: {'temp_processing_id' not in result.data}")
    print(f"Internal fields removed: {'internal_metadata' not in result.data}")


async def example_nested_field_selection():
    """Example: Select specific nested fields."""
    print("=" * 60)
    print("\n=== Example 3: Nested Field Selection ===")
    
    executor = FieldSelectorExecutor(
        id="nested_select",
        settings={
            "mode": "include",
            "fields": '["title", "content", "metadata.created_date", "metadata.version"]',
            "preserve_structure": True
        }
    )
    
    content = create_sample_content()
    print(f"Before selection - metadata: {content.data.get('metadata')}")
    
    result = await executor.process_content_item(content, None)
    
    print(f"After selection - metadata: {result.data.get('metadata')}")
    print(f"Only selected nested fields kept: {list(result.data.get('metadata', {}).keys())}")


async def example_privacy_filtering():
    """Example: Privacy-focused field removal (remove PII)."""
    print("=" * 60)
    print("\n=== Example 4: Privacy Filtering (Remove PII) ===")
    
    executor = FieldSelectorExecutor(
        id="privacy_filter",
        settings={
            "mode": "exclude",
            "fields": '["personal_info", "*.ssn", "*.credit_card"]',
            "keep_id_fields": True
        }
    )
    
    content = create_sample_content()
    print(f"Before filtering: {list(content.data.keys())}")
    print(f"Personal info exists: {'personal_info' in content.data}")
    
    result = await executor.process_content_item(content, None)
    
    print(f"After filtering: {list(result.data.keys())}")
    print(f"Personal info removed: {'personal_info' not in result.data}")
    print(f"Core fields preserved: ID fields intact")


async def example_conditional_selection():
    """Example: Conditional field selection based on field value."""
    print("=" * 60)
    print("\n=== Example 5: Conditional Selection (status=approved) ===")
    
    executor = FieldSelectorExecutor(
        id="conditional_select",
        settings={
            "mode": "include",
            "fields": '["title", "content", "author", "metadata"]',
            "conditional_selection": True,
            "condition_field": "status",
            "condition_operator": "equals",
            "condition_value": "approved"
        }
    )
    
    content = create_sample_content()
    print(f"Content status: {content.data.get('status')}")
    print(f"Before selection: {list(content.data.keys())}")
    
    result = await executor.process_content_item(content, None)
    
    print(f"After selection: {list(result.data.keys())}")
    print(f"Selection applied (status was 'approved'): {len(result.data) < len(content.data)}")


async def example_flat_structure():
    """Example: Flatten structure when selecting fields."""
    print("=" * 60)
    print("\n=== Example 6: Flattened Structure ===")
    
    executor = FieldSelectorExecutor(
        id="flatten_select",
        settings={
            "mode": "include",
            "fields": '["title", "metadata.created_date", "metadata.department"]',
            "preserve_structure": False  # Flatten the output
        }
    )
    
    content = create_sample_content()
    print(f"Before selection (nested): metadata = {content.data.get('metadata')}")
    
    result = await executor.process_content_item(content, None)
    
    print(f"After selection (flattened): {list(result.data.keys())}")
    print(f"Flattened keys: {result.data.keys()}")


async def example_with_metadata():
    """Example: Add selection metadata to output."""
    print("=" * 60)
    print("\n=== Example 7: With Selection Metadata ===")
    
    executor = FieldSelectorExecutor(
        id="with_metadata",
        settings={
            "mode": "exclude",
            "fields": '["temp_*", "processing_*"]',
            "add_selection_metadata": True
        }
    )
    
    content = create_sample_content()
    original_count = len(content.data)
    
    result = await executor.process_content_item(content, None)
    
    print(f"Selection metadata: {result.summary_data.get('field_selection')}")
    print(f"Fields removed: {result.summary_data.get('field_selection', {}).get('fields_removed')}")


async def example_include_all_nested():
    """Example: Include all fields under a nested path."""
    print("=" * 60)
    print("\n=== Example 8: Include All Nested Fields ===")
    
    executor = FieldSelectorExecutor(
        id="nested_all",
        settings={
            "mode": "include",
            "fields": '["title", "metadata"]',  # Includes all metadata.* fields
            "preserve_structure": True
        }
    )
    
    content = create_sample_content()
    print(f"Before selection: {list(content.data.keys())}")
    
    result = await executor.process_content_item(content, None)
    
    print(f"After selection: {list(result.data.keys())}")
    print(f"All metadata fields included: {result.data.get('metadata')}")


async def run_all_examples():
    """Run all field selector examples."""
    print("\n" + "=" * 60)
    print("FIELD SELECTOR EXECUTOR EXAMPLES")
    print("=" * 60 + "\n")
    
    await example_basic_inclusion()
    await example_wildcard_exclusion()
    await example_nested_field_selection()
    await example_privacy_filtering()
    await example_conditional_selection()
    await example_flat_structure()
    await example_with_metadata()
    await example_include_all_nested()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
