# Azure Content Understanding Extractor Example

This example demonstrates how to use the `AzureContentUnderstandingExtractorExecutor` to extract content from documents using Azure AI Content Understanding service.

## Overview

Azure AI Content Understanding provides advanced document analysis capabilities:

- **Content Extraction**: Extract text, markdown, tables, and layout information
- **Field Extraction**: Extract structured fields from documents (invoices, receipts, forms, etc.)
- **70+ Prebuilt Analyzers**: Ready-to-use analyzers for common document types
- **RAG-Optimized**: Specialized analyzers for Retrieval-Augmented Generation workflows
- **Multi-Modal Support**: Process documents, images, audio, and video

## Prerequisites

1. **Azure AI Content Understanding Resource**
   - Create an Azure AI Content Understanding resource in the Azure Portal
   - Note the endpoint URL

2. **Authentication**
   - Azure Active Directory (recommended for production)
   - Subscription key (simpler for development)

3. **Environment Variables**
   ```bash
   export CONTENT_UNDERSTANDING_ENDPOINT="https://your-resource.cognitiveservices.azure.com"
   # For subscription key auth (optional):
   export AZURE_SUBSCRIPTION_KEY="your-subscription-key"
   ```

## Available Analyzers

### Content Extraction (RAG-Optimized)
- `prebuilt-documentSearch` - Document content for RAG scenarios
- `prebuilt-imageSearch` - Image analysis for RAG
- `prebuilt-audioSearch` - Audio transcription for RAG
- `prebuilt-videoSearch` - Video analysis for RAG
- `prebuilt-layout` - Advanced layout analysis
- `prebuilt-read` - OCR and text extraction

### Financial Documents
- `prebuilt-invoice` - Invoice field extraction
- `prebuilt-receipt` - Receipt field extraction
- `prebuilt-bankStatement.us` - US bank statements
- `prebuilt-creditCard` - Credit card statements
- `prebuilt-check.us` - US checks

### Identity & Healthcare
- `prebuilt-idDocument` - ID documents (passports, licenses)
- `prebuilt-healthInsuranceCard.us` - US health insurance cards

### Tax Documents (US)
- `prebuilt-tax.us.1040` - US Form 1040
- `prebuilt-tax.us.w2` - US W-2 forms
- `prebuilt-tax.us.1099` - US 1099 variants
- And many more...

### Business Documents
- `prebuilt-contract` - Contracts
- `prebuilt-marriageContract.us` - Marriage contracts
- `prebuilt-businessCard` - Business cards

## Examples Included

### 1. Basic Content Extraction
Extract text, markdown, tables, and pages from a document file.

```python
executor = AzureContentUnderstandingExtractorExecutor(
    id="content_understanding_extractor",
    settings={
        "analyzer_id": "prebuilt-documentSearch",
        "extract_text": True,
        "extract_markdown": True,
        "extract_tables": True,
        "extract_pages": True,
        "content_understanding_endpoint": os.getenv("CONTENT_UNDERSTANDING_ENDPOINT"),
        "content_understanding_credential_type": "default_azure_credential",
    }
)
```

### 2. URL Document Extraction
Process documents directly from publicly accessible URLs.

```python
content = Content(
    id="url_document",
    data={
        "url": "https://example.com/document.pdf"
    }
)
```

### 3. Invoice Field Extraction
Extract structured fields from invoices automatically.

```python
executor = AzureContentUnderstandingExtractorExecutor(
    id="invoice_extractor",
    settings={
        "analyzer_id": "prebuilt-invoice",
        "extract_fields": True,  # Enable field extraction
        "content_understanding_endpoint": os.getenv("CONTENT_UNDERSTANDING_ENDPOINT"),
    }
)
```

### 4. Batch Processing
Process multiple documents concurrently with automatic parallelization.

```python
executor = AzureContentUnderstandingExtractorExecutor(
    settings={
        "max_concurrent": 3,  # Process up to 3 documents at once
        "continue_on_error": True,  # Don't stop on errors
    }
)
```

## Configuration Options

### Required Settings
- `content_understanding_endpoint`: Your Azure Content Understanding endpoint

### Optional Settings
- `analyzer_id`: Analyzer to use (default: "prebuilt-documentSearch")
- `extract_text`: Extract plain text (default: True)
- `extract_markdown`: Extract markdown (default: True)
- `extract_tables`: Extract tables (default: True)
- `extract_fields`: Extract fields (default: False)
- `extract_pages`: Extract page chunks (default: True)
- `max_concurrent`: Max concurrent operations (default: 3)
- `continue_on_error`: Continue on error (default: True)
- `content_understanding_credential_type`: "default_azure_credential" or "subscription_key"
- `content_understanding_subscription_key`: Subscription key if using key auth
- `content_understanding_api_version`: API version (default: "2025-11-01")

### Input Options
The executor supports three input methods (in priority order):
1. **URL**: Document URL in `data['url']`
2. **File Path**: Temp file path in `data['temp_file_path']`
3. **Bytes**: Document bytes in `data['content']`

### Output Structure
Extracted data is stored in `data['content_understanding_output']`:

```python
{
    "text": "Extracted plain text...",
    "markdown": "# Extracted markdown...",
    "tables": [
        {
            "row_count": 5,
            "column_count": 3,
            "cells": [...]
        }
    ],
    "fields": {
        "InvoiceTotal": "1234.56",
        "VendorName": "Acme Corp",
        ...
    },
    "pages": [
        {
            "page_number": 1,
            "text": "Page 1 text...",
            "markdown": "# Page 1..."
        }
    ]
}
```

## Running the Example

```bash
# Set environment variables
export CONTENT_UNDERSTANDING_ENDPOINT="https://your-resource.cognitiveservices.azure.com"

# Run the example
cd samples/08-content-understanding
python content_understanding_example.py
```

## Comparison with Document Intelligence

| Feature | Content Understanding | Document Intelligence |
|---------|----------------------|----------------------|
| **Primary Use Case** | RAG, multi-modal analysis, field extraction | Document layout, OCR, forms |
| **Prebuilt Analyzers** | 70+ specialized analyzers | ~20 prebuilt models |
| **Multi-Modal** | Documents, images, audio, video | Documents only |
| **RAG Optimization** | Built-in RAG-optimized analyzers | Manual configuration |
| **Field Extraction** | Advanced field extraction with AI | Form recognizer approach |
| **API Style** | REST API with polling | Azure SDK (async) |

## Additional Resources

- [Azure Content Understanding Documentation](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/)
- [Content Understanding Studio](https://aka.ms/cu-studio)
- [Python Samples Repository](https://github.com/Azure-Samples/azure-ai-content-understanding-python)
- [Analyzer Reference](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/concepts/analyzer-reference)
- [Prebuilt Analyzers List](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/concepts/prebuilt-analyzers)

## Troubleshooting

### Authentication Issues
- Ensure you're logged in with `az login` for default Azure credential
- Verify subscription key is correct if using key-based auth
- Check that your Azure identity has proper permissions

### Endpoint Issues
- Verify endpoint URL is correct (should end with `.cognitiveservices.azure.com`)
- Ensure the resource is in a supported region
- Check that the Content Understanding service is enabled

### API Errors
- **400 Bad Request**: Check analyzer ID and input format
- **401 Unauthorized**: Authentication failure - check credentials
- **404 Not Found**: Verify analyzer ID exists
- **429 Too Many Requests**: Rate limit exceeded - implement backoff

## License

This sample is part of the contentflow library.
