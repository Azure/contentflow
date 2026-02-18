"""
Sample 22: Dynamic Document Set Processing via External Orchestration

Demonstrates the dynamic document set pattern where document sets are
discovered at runtime from the filesystem. This uses the "external
orchestration" approach (Option B from the design document).

Use case: Vendor onboarding application review. Each subfolder under
99-assets/dynamics-doc-set/ is an independent application containing
its own set of documents (application form, insurance certificate,
financial statements). The orchestration script:

1. Discovers application folders from 99-assets/dynamics-doc-set/
2. Reads all document files within each folder
3. Parses key fields from each document (simulating extraction)
4. Runs the same document set pipeline once per application folder

Pattern highlights:
- Real files read from disk — no mock data
- Folder discovery simulates what AzureBlobInputDiscoveryExecutor
  with discover_mode="virtual_folders" would do in production
- Same pipeline config reused for every application
- Each application processed independently with full aggregation

No Azure services required — runs entirely locally.

Usage:
    python run.py
"""

import asyncio
import json
import logging
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.setup_logger import setup_logging
from contentflow.pipeline import PipelineExecutor
from contentflow.models import Content, ContentIdentifier

# Get the current directory
samples_dir = Path(__file__).parent.parent

# Load environment variables
load_dotenv(f'{samples_dir}/.env')

logger = logging.getLogger(__name__)

setup_logging()


# ---------------------------------------------------------------------------
# File parsing utilities
# ---------------------------------------------------------------------------

def parse_dollar_amount(text: str, label: str) -> float | None:
    """Extract a dollar amount following a label."""
    pattern = rf"{re.escape(label)}:\s*\$?([\d,]+(?:\.\d+)?)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def parse_percentage(text: str, label: str) -> float | None:
    """Extract a percentage value following a label."""
    pattern = rf"{re.escape(label)}:\s*([\d.]+)%"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def parse_field(text: str, label: str) -> str | None:
    """Extract a text field value following a label."""
    pattern = rf"{re.escape(label)}:\s*(.+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def parse_yes_no(text: str, label: str) -> bool | None:
    """Extract a Yes/No field as boolean."""
    val = parse_field(text, label)
    if val:
        return val.lower().startswith("yes")
    return None


def extract_application_fields(file_path: Path) -> dict:
    """Extract structured fields from an application form."""
    text = file_path.read_text(encoding="utf-8")
    return {
        "doc_type": "application_form",
        "company_name": parse_field(text, "Legal Entity Name"),
        "ein": parse_field(text, "EIN / Tax ID"),
        "employees": parse_dollar_amount(text, "Number of Employees"),
        "annual_revenue": parse_dollar_amount(text, "Annual Revenue"),
        "year_established": parse_dollar_amount(text, "Year Established"),
        "primary_contact": parse_field(text, "Name"),
        "naics_code": parse_field(text, "Primary NAICS Code"),
        "has_conflict_of_interest": parse_yes_no(text, "Conflict of Interest"),
        "has_pending_litigation": parse_yes_no(text, "Pending Litigation"),
        "has_tax_delinquency": parse_yes_no(text, "Tax Delinquency"),
        "text": text,
    }


def extract_insurance_fields(file_path: Path) -> dict:
    """Extract structured fields from an insurance certificate."""
    text = file_path.read_text(encoding="utf-8")
    return {
        "doc_type": "insurance_certificate",
        "policy_number": parse_field(text, "Policy Number"),
        "insurer": parse_field(text, "Insurer"),
        "am_best_rating": parse_field(text, "AM Best Rating"),
        "gl_each_occurrence": parse_dollar_amount(text, "Each Occurrence"),
        "gl_general_aggregate": parse_dollar_amount(text, "General Aggregate"),
        "eo_each_claim": parse_dollar_amount(text, "Each Claim"),
        "cyber_each_incident": parse_dollar_amount(text, "Each Incident"),
        "text": text,
    }


def extract_financial_fields(file_path: Path) -> dict:
    """Extract structured fields from a financial statement."""
    text = file_path.read_text(encoding="utf-8")
    return {
        "doc_type": "financial_statement",
        "total_revenue": parse_dollar_amount(text, "Total Revenue"),
        "net_income": parse_dollar_amount(text, "Net Income"),
        "net_margin": parse_percentage(text, "Net Margin"),
        "total_assets": parse_dollar_amount(text, "TOTAL ASSETS"),
        "total_liabilities": parse_dollar_amount(text, "TOTAL LIABILITIES"),
        "current_ratio": parse_dollar_amount(text, "Current Ratio"),
        "debt_to_equity": parse_dollar_amount(text, "Debt-to-Equity"),
        "ebitda": parse_dollar_amount(text, "EBITDA"),
        "ebitda_margin": parse_percentage(text, "EBITDA Margin"),
        "revenue_growth": parse_percentage(text, "Revenue Growth"),
        "dso": parse_dollar_amount(text, "Days Sales Outstanding"),
        "text": text,
    }


def extract_document_fields(file_path: Path) -> dict:
    """
    Route to the appropriate parser based on filename.

    Simulates what a real extraction pipeline (content_retriever →
    pdf_extractor → ai_analysis) would produce.
    """
    name_lower = file_path.name.lower()
    if "application" in name_lower:
        return extract_application_fields(file_path)
    elif "insurance" in name_lower:
        return extract_insurance_fields(file_path)
    elif "financial" in name_lower:
        return extract_financial_fields(file_path)
    else:
        # Generic: just read the text
        text = file_path.read_text(encoding="utf-8")
        return {"doc_type": "unknown", "text": text}


# ---------------------------------------------------------------------------
# Folder discovery and document loading
# ---------------------------------------------------------------------------

def discover_application_folders() -> dict[str, Path]:
    """
    Discover application folders from 99-assets/dynamics-doc-set/.

    In production, this would use AzureBlobInputDiscoveryExecutor with
    discover_mode="virtual_folders" to list blob prefixes.

    Returns:
        Dict mapping application ID → folder path
    """
    base_dir = samples_dir / "99-assets" / "dynamics-doc-set"

    if not base_dir.exists():
        raise FileNotFoundError(
            f"Dynamics doc-set directory not found: {base_dir}"
        )

    folders = {}
    for child in sorted(base_dir.iterdir()):
        if child.is_dir():
            # Folder names like "app-123#1" → application ID
            folders[child.name] = child

    if not folders:
        raise FileNotFoundError(
            f"No application folders found in {base_dir}\n"
            f"Expected subfolders like app-123#1/, app-123#2/"
        )

    return folders


def load_application_documents(app_id: str, folder_path: Path) -> list[Content]:
    """
    Load all document files from an application folder and create Content items.

    Each file is read, parsed for structured fields, and wrapped in a Content
    object with both raw text and extracted data.
    """
    files = sorted(folder_path.glob("*.txt"))
    if not files:
        logger.warning(f"No .txt files found in {folder_path}")
        return []

    documents = []
    for file_path in files:
        fields = extract_document_fields(file_path)

        content = Content(
            id=ContentIdentifier(
                canonical_id=f"dynamics-doc-set/{app_id}/{file_path.name}",
                unique_id=f"{app_id}_{file_path.name}",
                source_name="local_file",
                source_type="local_file",
                path=str(file_path),
                filename=file_path.name,
            ),
            data=fields,
        )
        documents.append(content)

    return documents


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

async def process_single_application(
    config_path: Path,
    executor_catalog_path: Path,
    app_id: str,
    folder_path: Path,
) -> dict:
    """
    Process a single application folder through the document set pipeline.

    Returns a summary dict with processing results.
    """
    documents = load_application_documents(app_id, folder_path)

    if not documents:
        return {
            "app_id": app_id,
            "status": "skipped",
            "reason": "no documents found",
            "document_count": 0,
            "duration_seconds": 0.0,
        }

    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="single_set_processing",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:

        result = await pipeline_executor.execute(documents)

    # Build summary
    summary = {
        "app_id": app_id,
        "status": result.status,
        "duration_seconds": result.duration_seconds,
        "document_count": len(documents),
        "document_types": [d.data.get("doc_type", "unknown") for d in documents],
    }

    if result.content:
        content = (
            result.content
            if isinstance(result.content, Content)
            else result.content[0]
        )

        # Extract aggregation highlights
        aggregations = content.data.get("field_aggregations", {})
        if aggregations:
            summary["aggregations"] = {}
            for key, agg in aggregations.get("aggregations", {}).items():
                summary["aggregations"][key] = {
                    k: v
                    for k, v in agg.items()
                    if k in ("sum", "avg", "min", "max", "count", "values")
                    and v is not None
                }

        # Extract collected document set info
        doc_set = content.data.get("document_set", {})
        if doc_set:
            summary["set_name"] = doc_set.get("set_name")
            summary["total_in_set"] = doc_set.get("total_documents")

    return summary


async def run_dynamic_document_sets():
    """Run the dynamic document set processing with external orchestration."""
    print("=" * 70)
    print("Sample 22: Dynamic Document Sets - External Orchestration")
    print("=" * 70)

    config_path = Path(__file__).parent / "pipeline_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"

    # Discover application folders from disk
    app_folders = discover_application_folders()
    print(f"\n✓ Discovered {len(app_folders)} application folders "
          f"in 99-assets/dynamics-doc-set/:")

    for app_id, folder in app_folders.items():
        files = list(folder.glob("*.txt"))
        print(f"  📁 {app_id}: {len(files)} documents")
        for f in files:
            print(f"     - {f.name}")

    # Process each application folder through the same pipeline
    all_results = []

    print(f"\n🔄 Processing each application folder...")

    for app_id, folder in app_folders.items():
        print(f"\n  Processing {app_id}...")

        summary = await process_single_application(
            config_path, executor_catalog_path, app_id, folder
        )
        all_results.append(summary)

        status_icon = "✓" if summary["status"] == "completed" else "✗"
        print(
            f"  {status_icon} {app_id}: {summary['status']} "
            f"({summary['duration_seconds']:.2f}s, "
            f"{summary['document_count']} docs)"
        )

        if "document_types" in summary:
            print(f"    Document types: {', '.join(summary['document_types'])}")

        if "aggregations" in summary:
            for key, agg in summary["aggregations"].items():
                vals = {k: v for k, v in agg.items() if v is not None}
                if vals:
                    formatted = ", ".join(
                        f"{k}=${v:,.0f}" if isinstance(v, (int, float)) and v > 100
                        else f"{k}={v}"
                        for k, v in vals.items()
                        if k != "values"
                    )
                    if formatted:
                        print(f"    {key}: {formatted}")

    # Overall summary
    print(f"\n" + "=" * 70)
    print(f"📋 Overall Summary:")
    print(f"  Applications processed: {len(all_results)}")
    print(
        f"  Successful: "
        f"{sum(1 for r in all_results if r['status'] == 'completed')}"
    )
    print(
        f"  Failed/Skipped: "
        f"{sum(1 for r in all_results if r['status'] != 'completed')}"
    )
    print(
        f"  Total documents: {sum(r['document_count'] for r in all_results)}"
    )
    print(
        f"  Total time: "
        f"{sum(r['duration_seconds'] for r in all_results):.2f}s"
    )

    for r in all_results:
        status_icon = "✓" if r["status"] == "completed" else "✗"
        print(f"\n  {status_icon} {r['app_id']}:")
        print(f"    Documents: {r['document_count']}")
        if "document_types" in r:
            print(f"    Types: {', '.join(r['document_types'])}")

    # Write combined results
    output_folder = Path(__file__).parent / "output"
    output_folder.mkdir(exist_ok=True)
    output_file = output_folder / "dynamic_document_sets_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n✓ Wrote combined results to {output_file}")

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_dynamic_document_sets())
