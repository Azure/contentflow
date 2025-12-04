# PowerPoint Extractor Example

This example demonstrates how to extract text, slides, tables, notes, and images from PowerPoint presentations (.pptx) using the `PowerPointExtractorExecutor`.

## Features

The pipeline extracts:
- **Full text** from all slides in the presentation
- **Slides** with individual chunks and shape information
- **Tables** with cell data in a structured format
- **Speaker notes** from each slide
- **Presentation properties** (title, author, dates, slide dimensions, etc.)
- **Images** embedded in slides (optional)

## Pipeline Configuration

The pipeline consists of three executors:

1. **ContentRetrieverExecutor**: Retrieves PowerPoint presentations from local storage
2. **PowerPointExtractorExecutor**: Extracts content using python-pptx library
3. **PassThroughExecutor**: Passes the results through (for demonstration)

## Setup

1. Install required dependencies:
```bash
pip install python-pptx
```

2. Place your PowerPoint presentations (.pptx files) in `/Users/nadeemis/temp/test_files/`

## Running the Example

```bash
python run.py
```

## Configuration Options

Edit `pipeline_config.yaml` to customize extraction:

```yaml
extract_text: true              # Extract full text
extract_slides: true            # Extract slide chunks
extract_tables: true            # Extract table data
extract_notes: true             # Extract speaker notes
extract_properties: true        # Extract metadata
extract_images: false           # Extract embedded images
include_slide_layouts: false    # Include layout info
```

## Output

Results are saved to `output/pipeline_result.json` containing:

- **text**: Complete presentation text (all slides)
- **slides**: Array of slide objects with text, shapes, and optional tables
- **tables**: Array of table objects with cell data
- **notes**: Array of speaker notes objects
- **properties**: Presentation metadata (author, title, dates, dimensions)
- **images**: Array of image objects (if enabled)

## Sample Output Structure

```json
{
  "pptx_output": {
    "text": "Full presentation text...",
    "slides": [
      {
        "slide_number": 1,
        "text": "Slide content...",
        "char_count": 150,
        "shape_count": 5,
        "layout": "Title Slide"
      }
    ],
    "tables": [
      {
        "slide_number": 2,
        "rows": 4,
        "columns": 3,
        "data": [
          ["Header 1", "Header 2", "Header 3"],
          ["Cell 1", "Cell 2", "Cell 3"],
          ["Cell 4", "Cell 5", "Cell 6"],
          ["Cell 7", "Cell 8", "Cell 9"]
        ]
      }
    ],
    "notes": [
      {
        "slide_number": 1,
        "text": "Speaker notes for slide 1...",
        "char_count": 75
      }
    ],
    "properties": {
      "title": "Presentation Title",
      "author": "Author Name",
      "created": "2025-01-01T00:00:00",
      "modified": "2025-01-15T10:30:00",
      "slide_count": 10,
      "slide_width": 9144000,
      "slide_height": 6858000
    }
  }
}
```

## Use Cases

- **Presentation analysis**: Extract and analyze content from PowerPoint presentations
- **Content migration**: Convert presentations to other formats
- **Metadata extraction**: Gather presentation properties for indexing
- **Table extraction**: Extract structured data from presentation tables
- **Notes extraction**: Extract speaker notes for documentation
- **Batch processing**: Process multiple presentations efficiently

## Comparison with Other Extractors

| Feature | PowerPoint | Word | PDF |
|---------|-----------|------|-----|
| Slide-level chunks | Yes | N/A | Page-level |
| Tables | Yes | Yes | No |
| Speaker notes | Yes | N/A | N/A |
| Images | Yes | Yes | Yes |
| Properties | Yes | Yes | Limited |
| Layout info | Yes | Styles | No |

## Tips

- Enable `extract_notes` to capture speaker notes for presentations
- Use `include_slide_layouts` to identify slide types (title, content, etc.)
- Extract tables to get structured data from presentation content
- Process presentations in batches for efficiency
