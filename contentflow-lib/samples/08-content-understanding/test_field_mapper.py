"""
Test script to verify field_mapper_executor list merging and object mapping functionality
"""
import json
from packages.executors.field_mapper_executor import FieldMapperExecutor
from packages.models import Content, DocumentIdentifier

# Sample nested data structure similar to content understanding result
test_data = {
    "result": {
        "contents": [
            {
                "pages": [
                    {
                        "pageNumber": 1,
                        "lines": [
                            {"content": "Line 1 Page 1"},
                            {"content": "Line 2 Page 1"}
                        ]
                    },
                    {
                        "pageNumber": 2,
                        "lines": [
                            {"content": "Line 1 Page 2"},
                            {"content": "Line 2 Page 2"}
                        ]
                    }
                ]
            }
        ]
    }
}

# Create a Content object
content = Content(
    id=DocumentIdentifier(
        canonical_id="test_doc",
        unique_id="test_doc",
        source_name="test",
        source_type="test"
    ),
    data=test_data
)

# Test 1: Merge mode (flatten all nested lists)
print("Test 1: list_handling='merge'")
print("-" * 50)
executor_merge = FieldMapperExecutor(
    id="test_merge",
    settings={
        "mappings": json.dumps({
            "result.contents.pages.lines.content": "merged_lines"
        }),
        "list_handling": "merge",
        "merge_filter_empty": True,
        "copy_mode": "copy"
    }
)

import asyncio
result = asyncio.run(executor_merge.process_content_item(content))
print(f"Merged lines: {result.data.get('merged_lines')}")
print()

# Test 2: Object mapping - combine page numbers with their lines
print("Test 2: object_mappings - combine page numbers with lines")
print("-" * 50)
content2 = Content(
    id=DocumentIdentifier(
        canonical_id="test_doc2",
        unique_id="test_doc2",
        source_name="test",
        source_type="test"
    ),
    data=test_data.copy()
)

executor_object = FieldMapperExecutor(
    id="test_object",
    settings={
        "object_mappings": json.dumps({
            "pages_with_content": {
                "page_number": "result.contents.pages.pageNumber",
                "lines": "result.contents.pages.lines.content"
            }
        }),
        "list_handling": "merge",
        "copy_mode": "copy"
    }
)

result2 = asyncio.run(executor_object.process_content_item(content2))
print(f"Pages with content:")
for page in result2.data.get('pages_with_content', []):
    print(f"  Page {page.get('page_number')}: {len(page.get('lines', []))} lines")
    print(f"    Lines: {page.get('lines')}")
print()

# Test 3: Combined - both object mappings and regular mappings
print("Test 3: Combined object_mappings + regular mappings")
print("-" * 50)
test_data_combined = {
    "result": {
        "contents": [
            {
                "mimeType": "application/pdf",
                "pages": [
                    {
                        "pageNumber": 1,
                        "lines": [{"content": "Page 1 Line 1"}, {"content": "Page 1 Line 2"}]
                    },
                    {
                        "pageNumber": 2,
                        "lines": [{"content": "Page 2 Line 1"}]
                    }
                ]
            }
        ]
    }
}

content3 = Content(
    id=DocumentIdentifier(
        canonical_id="test_doc3",
        unique_id="test_doc3",
        source_name="test",
        source_type="test"
    ),
    data=test_data_combined
)

executor_combined = FieldMapperExecutor(
    id="test_combined",
    settings={
        "object_mappings": json.dumps({
            "pages": {
                "page_num": "result.contents.pages.pageNumber",
                "text_lines": "result.contents.pages.lines.content"
            }
        }),
        "mappings": json.dumps({
            "result.contents.mimeType": "document_type"
        }),
        "list_handling": "merge",
        "copy_mode": "copy"
    }
)

result3 = asyncio.run(executor_combined.process_content_item(content3))
print(f"Document type: {result3.data.get('document_type')}")
print(f"Pages: {result3.data.get('pages')}")
print()

print("✅ All tests completed successfully!")
