# Word Extractor Example

This example demonstrates how to extract text, paragraphs, tables, and properties from Word documents (.docx) using the `WordExtractorExecutor`.

## Features

The pipeline extracts:
- **Full text** from the entire document
- **Paragraphs** with individual chunks and style information
- **Tables** with cell data in a structured format
- **Document properties** (title, author, dates, etc.)
- **Images** embedded in the document (optional)

## Pipeline Configuration

The pipeline consists of three executors:

1. **ContentRetrieverExecutor**: Retrieves Word documents from local storage
2. **WordExtractorExecutor**: Extracts content using python-docx library
3. **PassThroughExecutor**: Passes the results through (for demonstration)

## Setup

1. Install required dependencies:
```bash
pip install python-docx
```

2. Place your Word documents (.docx files) in `/Users/nadeemis/temp/test_files/`

## Running the Example

```bash
python run.py
```

## Configuration Options

Edit `pipeline_config.yaml` to customize extraction:

```yaml
extract_text: true              # Extract full text
extract_paragraphs: true        # Extract paragraph chunks
extract_tables: true            # Extract table data
extract_properties: true        # Extract metadata
extract_images: false           # Extract embedded images
include_empty_paragraphs: false # Skip empty paragraphs
```

## Output

Results are saved to `output/pipeline_result.json` containing:

- **text**: Complete document text
- **paragraphs**: Array of paragraph objects with text and style
- **tables**: Array of table objects with cell data
- **properties**: Document metadata (author, title, dates, etc.)
- **images**: Array of image objects (if enabled)

## Sample Output Structure

```json
{
  "word_output": {
    "text": "Full document text...",
    "paragraphs": [
      {
        "paragraph_number": 1,
        "text": "Paragraph content...",
        "char_count": 50,
        "style": "Heading 1"
      }
    ],
    "tables": [
      {
        "table_number": 1,
        "rows": 3,
        "columns": 2,
        "data": [
          ["Header 1", "Header 2"],
          ["Cell 1", "Cell 2"],
          ["Cell 3", "Cell 4"]
        ]
      }
    ],
    "properties": {
      "title": "Document Title",
      "author": "Author Name",
      "created": "2025-01-01T00:00:00",
      "modified": "2025-01-15T10:30:00"
    }
  }
}
```

## Use Cases

- **Document analysis**: Extract and analyze content from Word documents
- **Content migration**: Convert Word documents to other formats
- **Metadata extraction**: Gather document properties for indexing
- **Table extraction**: Extract structured data from tables
- **Batch processing**: Process multiple Word documents efficiently
