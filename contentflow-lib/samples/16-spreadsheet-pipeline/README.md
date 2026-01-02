# Spreadsheet Data Processing Pipeline

Process Excel/CSV files with automatic schema detection, data validation, field transformation, and structured output generation to Azure Blob Storage.

## Overview

This sample demonstrates a complete ETL (Extract, Transform, Load) workflow for spreadsheet data processing, suitable for:
- Customer data imports and normalization
- Financial report processing and transformation
- Multi-sheet dataset extraction and consolidation
- Data migration and format standardization
- Automated data validation and cleaning

## Pipeline Flow

```
Excel File Loading → Content Extraction → Row Splitting → 
Field Mapping → Field Selection → Azure Blob Output
```

### Pipeline Steps

1. **Content Loader** - Loads Excel files from local or cloud storage
   - Support for XLSX, XLS, XLSM formats
   - Parallel file retrieval
   - Temporary file management

2. **Excel Extractor** - Extracts structured data with schema detection
   - Multi-sheet processing
   - Table and data range extraction
   - Automatic header detection
   - Formula and formatting extraction (optional)
   - Cell validation and type detection

3. **Table Row Splitter** - Splits table data into individual content items
   - Each row becomes a separate content item
   - Preserves row metadata and lineage
   - Configurable row filtering
   - Empty row handling

4. **Field Mapper** - Normalizes and transforms field names
   - Rename columns for standardization
   - Case transformation (snake_case, camelCase, etc.)
   - Nested structure creation
   - Field copying or moving

5. **Field Selector** - Filters fields for output
   - Include/exclude specific fields
   - Wildcard pattern support
   - Privacy-focused field removal
   - Conditional field selection

6. **Azure Blob Output** - Writes processed data to blob storage
   - JSON output with pretty printing
   - Configurable path templating
   - Metadata preservation
   - Compression support
   - Batch writing with retry logic

## Features

- **Automatic Schema Detection**: Identify column types and data patterns
- **Multi-Sheet Support**: Process all sheets or select specific ones
- **Data Validation**: Validate row data and skip invalid entries
- **Field Normalization**: Standardize column names and formats
- **Flexible Output**: JSON files with configurable structure
- **Metadata Preservation**: Track source file, sheet, and row information
- **Error Handling**: Continue processing on errors with detailed logging

## Prerequisites

- Azure subscription with:
  - Azure Blob Storage account and container
- Python 3.8+
- Contentflow library installed
- Excel files to process

## Configuration

### Environment Variables

Create or update `samples/.env` with the following:

```bash
# Azure Storage
AZURE_STORAGE_ACCOUNT=your-storage-account
AZURE_OUTPUT_CONTAINER_NAME=processed-data
```

### Pipeline Configuration

The pipeline is configured in `pipeline-config.yaml`. Key settings:

**Excel Extraction:**
- `extract_sheets`: true (extract all sheets)
- `extract_tables`: true (detect and extract tables)
- `first_row_as_header`: true (use first row as column names)
- `auto_detect_headers`: true (automatically find header row)
- `skip_hidden_sheets`: true (ignore hidden sheets)

**Row Splitting:**
- `output_mode`: "content_items" (each row as separate item)
- `skip_empty_rows`: true (ignore blank rows)
- `include_row_number`: true (track original row numbers)
- `validate_row_data`: true (validate row integrity)

**Field Mapping:**
- Customize the `mappings` dictionary for your column names
- `case_transform`: "snake" (convert to snake_case)
- `copy_mode`: "move" (rename, not copy)

**Field Selection:**
- Update the `fields` list to include/exclude specific columns
- `mode`: "include" (keep only specified fields)
- `keep_id_fields`: true (preserve content identifiers)

**Blob Output:**
- `path_template`: "processed-data/{year}/{month}/{day}/"
- `filename_template`: "record_{row_number}_{timestamp}.json"
- `pretty_print`: true (format JSON output)

## Usage

### Basic Execution

```bash
cd samples/16-spreadsheet-pipeline
python run.py
```

### Processing Custom Spreadsheets

Update `run.py` to process your own Excel files:

```python
# Single file
document = Content(
    id=ContentIdentifier(
        canonical_id="my_excel",
        unique_id="my_excel",
        source_id="spreadsheets",
        source_name="My Data",
        source_type="file",
        path="/path/to/your-spreadsheet.xlsx",
    )
)

# Multiple files
excel_files = [
    "data/customers.xlsx",
    "data/orders.xlsx",
    "data/products.xlsx",
]

documents = []
for idx, file_path in enumerate(excel_files):
    document = Content(
        id=ContentIdentifier(
            canonical_id=f"excel_{idx:03d}",
            unique_id=f"excel_{idx:03d}",
            source_id="excel_batch",
            source_name=Path(file_path).stem,
            source_type="file",
            path=file_path,
        )
    )
    documents.append(document)
```

### Expected Output

```
================================================================================
Spreadsheet Data Processing Pipeline
================================================================================

✓ Initialized spreadsheet processing pipeline
  - Output: Azure Blob Storage (processed-data)
  - Field Mapping: Enabled (normalize column names)
  - Data Validation: Enabled

✓ Created 1 spreadsheet document for processing

🔄 Starting spreadsheet processing...
  Processing steps:
    1. Load Excel file
    2. Extract sheets and tables
    3. Split into individual rows
    4. Map and normalize field names
    5. Select relevant fields
    6. Write to Azure Blob Storage

✓ Wrote detailed results to output/spreadsheet_result.json

================================================================================
✓ Spreadsheet Processing Completed
================================================================================
  Total documents processed: 150
  Successfully processed: 150
  Failed: 0
  Total duration: 12.34s
  Avg per document: 0.08s

================================================================================
📊 Processing Results
================================================================================

✓ Total rows extracted and processed: 150

📄 Sample Records (First 5):

────────────────────────────────────────────────────────────────────────────────
Record 1:
  name        : John Smith
  email       : john.smith@example.com
  phone       : 555-0123
  date        : 2024-01-15
  amount      : 1250.00
  status      : completed
  row_number  : 2

────────────────────────────────────────────────────────────────────────────────
Record 2:
  name        : Jane Doe
  email       : jane.doe@example.com
  phone       : 555-0124
  date        : 2024-01-16
  amount      : 890.50
  status      : pending
  row_number  : 3

================================================================================
📈 Processing Statistics
================================================================================

📊 Status Distribution:
  completed      : 120 ( 80.0%)
  pending        :  25 ( 16.7%)
  cancelled      :   5 (  3.3%)

💰 Financial Summary:
  Total Amount: $125,450.00
  Average Amount: $836.33
  Records with Amount: 150

🎉 Spreadsheet data has been processed and exported to Azure Blob Storage!
================================================================================

📦 Output Location:
  Container: processed-data
  Path Pattern: processed-data/{year}/{month}/{day}/
  File Pattern: record_{row_number}_{timestamp}.json
```

## Output

### File Structure

Each row is saved as a separate JSON file in Azure Blob Storage:

```
processed-data/
  └── 2024/
      └── 12/
          └── 05/
              ├── record_2_20241205_143022.json
              ├── record_3_20241205_143022.json
              ├── record_4_20241205_143022.json
              └── ...
```

### JSON Output Format

Each file contains a processed row:

```json
{
  "id": {
    "canonical_id": "excel_001_row_2",
    "unique_id": "excel_001_row_2",
    "source_id": "sample_spreadsheets",
    "source_name": "Customer Orders",
    "source_type": "file"
  },
  "data": {
    "name": "John Smith",
    "email": "john.smith@example.com",
    "phone": "555-0123",
    "date": "2024-01-15",
    "amount": 1250.00,
    "status": "completed",
    "row_number": 2
  },
  "metadata": {
    "name": "John Smith",
    "email": "john.smith@example.com",
    "status": "completed",
    "written_at": "2024-12-05T14:30:22Z"
  }
}
```

## Use Cases

- **Customer Data Import**: Normalize and validate customer records from Excel
- **Financial Report Processing**: Extract and transform financial data
- **Order Processing**: Split order spreadsheets into individual records
- **Data Migration**: Convert Excel data to JSON for database import
- **ETL Workflows**: Extract, transform, and load spreadsheet data
- **Data Validation**: Verify and clean imported datasets

## Customization

### Process Specific Sheets

```yaml
specific_sheets: ["Sheet1", "Orders"]  # Only process these sheets
exclude_sheets: ["Template", "Archive"]  # Skip these sheets
```

### Custom Field Mappings

Update mappings based on your spreadsheet columns:

```yaml
mappings: '{
  "Customer Name": "customer_name",
  "E-mail": "email",
  "Phone #": "phone",
  "Order Date": "order_date",
  "Total ($)": "amount",
  "Order Status": "status",
  "Delivery Address": "address",
  "Notes": "comments"
}'
```

### Filter Rows by Criteria

```yaml
# In field_selector settings
conditional_selection: true
condition_field: "status"
condition_operator: "equals"
condition_value: "completed"
```

### Change Output Format

```yaml
# Compress output
compression: gzip

# Custom filename
filename_template: "{name}_{date}_{timestamp}.json"

# Write to nested structure
path_template: "{status}/{year}-{month}/"
```

### Extract Formulas

```yaml
# In excel_extractor settings
extract_formulas: true  # Include cell formulas
include_cell_formatting: true  # Preserve formatting
```

## Advanced Features

### Multi-Sheet Processing

Process all sheets and combine data:

```yaml
extract_sheets: true
include_sheet_names: true
```

Each sheet will create separate row items with sheet metadata.

### Data Validation

Enable validation to skip invalid rows:

```yaml
validate_row_data: true
skip_rows_with_empty_key: true
key_field: "customer_id"  # Require this field
```

### Nested Field Creation

Create nested JSON structures:

```yaml
mappings: '{
  "Customer Name": "customer.name",
  "Customer Email": "customer.email",
  "Order ID": "order.id",
  "Order Date": "order.date"
}'
create_nested: true
```

Output:
```json
{
  "customer": {
    "name": "John Smith",
    "email": "john@example.com"
  },
  "order": {
    "id": "ORD-001",
    "date": "2024-01-15"
  }
}
```

## Troubleshooting

**No data extracted:**
- Check `first_row_as_header` and `auto_detect_headers` settings
- Verify spreadsheet has data in expected format
- Check `specific_sheets` filter

**Field mapping errors:**
- Ensure source field names match exactly
- Set `fail_on_missing_source: false` to skip missing fields
- Check case sensitivity in field names

**Blob write failures:**
- Verify storage account and container exist
- Check authentication (DefaultAzureCredential)
- Ensure sufficient permissions

**Too many files:**
- Consider writing to single file instead of per-row
- Adjust `batch_size` for fewer files
- Use custom `filename_template` to consolidate

## Performance Optimization

- **Parallel Processing**: Set `max_concurrent: 10` for faster processing
- **Row Filtering**: Skip unnecessary rows early in pipeline
- **Field Selection**: Remove unused fields before blob write
- **Batch Writing**: Increase `batch_size` for blob output

## Next Steps

After processing, you can:
- **Import to Database**: Load JSON files into SQL/NoSQL databases
- **Data Analysis**: Analyze exported data with analytics tools
- **API Integration**: Feed data to downstream APIs
- **Reporting**: Generate reports from normalized data

## Related Samples

- `10-table-row-splitter`: Table row splitting details
- `11-excel-extractor`: Excel extraction features
- `12-field-transformation`: Field transformation patterns
- `13-blob-output-sample`: Blob storage output options

## Resources

- [openpyxl Documentation](https://openpyxl.readthedocs.io/)
- [Azure Blob Storage](https://learn.microsoft.com/azure/storage/blobs/)
- [ETL Best Practices](https://learn.microsoft.com/azure/architecture/data-guide/relational-data/etl)
- [Data Validation Patterns](https://learn.microsoft.com/azure/architecture/best-practices/data-partitioning)
