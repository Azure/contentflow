"""
Example usage and test of the Field Mapper Executor.

This example demonstrates various field mapping scenarios including:
- Simple field renaming
- Nested field mapping
- Field moving vs copying
- Template-based field naming
- Case transformation
"""

import asyncio
import logging
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from contentflow.pipeline import PipelineExecutor, PipelineResult
from contentflow.executors import FieldMapperExecutor
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
            "document_title": "Test Document",
            "document_text": "This is the content of the document.",
            "author_name": "John Doe",
            "metadata": {
                "created_date": "2024-01-01",
                "file_size": 1024,
                "department": "Engineering"
            },
            "user": {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@example.com"
            },
            "source_type": "pdf",
            "temp_processing_data": "Should be removed in move mode"
        }
    )


async def example_basic_renaming():
    """Example: Basic field renaming."""
    print("=" * 60)
    print("\n\n=== Example 1: Basic Field Renaming ===")
    
    executor = FieldMapperExecutor(
        id="basic_rename",
        settings={
            "mappings": """{
                "document_title": "title",
                "document_text": "content",
                "author_name": "author"
            }""",
            "copy_mode": "move"
        }
    )
    
    content = create_sample_content()
    print(f"Before mapping: {list(content.data.keys())}")
    
    result = await executor.process_content_item(content, None)
    
    print(f"After mapping: {list(result.data.keys())}")
    print(f"New fields: title={result.data.get('title')}, "
                f"content={result.data.get('content')[:30]}...")


async def example_nested_restructure():
    """Example: Restructure nested fields."""
    print("=" * 60)
    print("\n\n=== Example 2: Nested Field Restructuring ===")
    
    executor = FieldMapperExecutor(
        id="nested_restructure",
        settings={
            "mappings": """{
                "user.first_name": "author.name.first",
                "user.last_name": "author.name.last",
                "user.email": "author.contact.email",
                "metadata.department": "author.department"
            }""",
            "copy_mode": "move",
            "create_nested": True
        }
    )
    
    content = create_sample_content()
    print(f"Before mapping - user: {content.data.get('user')}")
    
    result = await executor.process_content_item(content, None)
    
    print(f"After mapping - author: {result.data.get('author')}")
    print(f"User field removed: {'user' not in result.data}")


async def example_copy_mode():
    """Example: Copy mode - preserve source fields."""
    print("=" * 60)
    print("\n\n=== Example 3: Copy Mode (Preserve Sources) ===")
    
    executor = FieldMapperExecutor(
        id="copy_mode",
        settings={
            "mappings": """{
                "document_title": "backup_title",
                "document_text": "backup_content"
            }""",
            "copy_mode": "copy"  # Keep source fields
        }
    )
    
    content = create_sample_content()
    print(f"Before mapping: {list(content.data.keys())}")
    
    result = await executor.process_content_item(content, None)
    
    print(f"After mapping: {list(result.data.keys())}")
    print(f"Original fields preserved: "
                f"document_title exists = {'document_title' in result.data}, "
                f"backup_title exists = {'backup_title' in result.data}")


async def example_template_fields():
    """Example: Template-based dynamic field naming."""
    print("=" * 60)
    print("\n\n=== Example 4: Template-Based Field Naming ===")
    
    executor = FieldMapperExecutor(
        id="template_mapper",
        settings={
            "mappings": """{
                "document_text": "{source_type}_content",
                "metadata": "{source_type}_metadata"
            }""",
            "template_fields": True,
            "copy_mode": "copy"
        }
    )
    
    content = create_sample_content()
    print(f"Source type: {content.data.get('source_type')}")
    print(f"Before mapping: {list(content.data.keys())}")
    
    result = await executor.process_content_item(content, None)
    
    print(f"After mapping: {list(result.data.keys())}")
    print(f"Template-generated fields: "
                f"pdf_content exists = {'pdf_content' in result.data}, "
                f"pdf_metadata exists = {'pdf_metadata' in result.data}")


async def example_case_transformation():
    """Example: Case transformation during mapping."""
    print("=" * 60)
    print("\n\n=== Example 5: Case Transformation ===")
    
    executor = FieldMapperExecutor(
        id="case_transform",
        settings={
            "mappings": """{
                "document_title": "DOCUMENT_TITLE",
                "author_name": "AUTHOR_NAME"
            }""",
            "case_transform": "snake",  # Convert to snake_case
            "copy_mode": "move"
        }
    )
    
    content = create_sample_content()
    print(f"Before mapping: {list(content.data.keys())}")
    
    result = await executor.process_content_item(content, None)
    
    print(f"After mapping: {list(result.data.keys())}")
    print(f"Case-transformed fields: "
                f"{[k for k in result.data.keys() if 'document' in k or 'author' in k]}")


async def example_complex_workflow():
    """Example: Complex multi-stage mapping workflow."""
    print("=" * 60)
    print("\n=== Example 6: Complex Multi-Stage Mapping ===")
    
    # Stage 1: Standardize field names
    stage1 = FieldMapperExecutor(
        id="standardize",
        settings={
            "mappings": """{
                "document_title": "title",
                "document_text": "content",
                "author_name": "author"
            }""",
            "copy_mode": "move"
        }
    )
    
    # Stage 2: Extract user info to author structure
    stage2 = FieldMapperExecutor(
        id="extract_author",
        settings={
            "mappings": """{
                "user.first_name": "author_info.name.first",
                "user.last_name": "author_info.name.last",
                "user.email": "author_info.contact.email"
            }""",
            "copy_mode": "move",
            "create_nested": True
        }
    )
    
    # Stage 3: Clean up temporary fields
    stage3 = FieldMapperExecutor(
        id="cleanup",
        settings={
            "mappings": """{
                "temp_processing_data": "_archived.temp_data"
            }""",
            "copy_mode": "move"
        }
    )
    
    content = create_sample_content()
    print(f"Initial structure: {list(content.data.keys())}")
    
    # Process through stages
    result = await stage1.process_content_item(content, None)
    print(f"After stage 1: {list(result.data.keys())}")
    
    result = await stage2.process_content_item(result, None)
    print(f"After stage 2: {list(result.data.keys())}")
    
    result = await stage3.process_content_item(result, None)
    print(f"Final structure: {list(result.data.keys())}")
    print(f"Final data: {result.data}")

async def main():
    """Run all examples."""
    print("=" * 60)
    print("Field Mapper Executor Examples")
    print("=" * 60)
    
    await example_basic_renaming()
    await example_nested_restructure()
    await example_copy_mode()
    await example_template_fields()
    await example_case_transformation()
    await example_complex_workflow()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
