"""
Sample 21: Document Set with AI Cross-Document Comparison (Real Files)

Demonstrates the full document set pipeline with AI-powered cross-document
comparison using Azure OpenAI, reading real quarterly financial reports
from 99-assets/doc-set/.

Pipeline steps:
1. Read real .txt report files from 99-assets/doc-set/
2. Parse financial metrics from each file
3. DocumentSetInitializerExecutor — stamps set metadata
4. Per-document sub-pipeline (pass-through since data is pre-extracted)
5. DocumentSetCollectorExecutor — consolidates into single Content
6. CrossDocumentFieldAggregatorExecutor — deterministic aggregations
7. CrossDocumentComparisonExecutor — AI-powered comparative analysis

Requirements:
    - AZURE_OPENAI_ENDPOINT environment variable
    - AZURE_OPENAI_DEPLOYMENT_NAME environment variable (e.g., "gpt-4.1")
    - Azure OpenAI access with DefaultAzureCredential

Usage:
    python run.py
"""

import asyncio
import json
import logging
import os
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
    """Extract a dollar amount following a label, e.g. 'Revenue:  $10,500,000'."""
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


def parse_integer(text: str, label: str) -> int | None:
    """Extract an integer value following a label."""
    pattern = rf"{re.escape(label)}:\s*([\d,]+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


def extract_metrics_from_report(file_path: Path) -> dict:
    """
    Parse a quarterly financial report and extract structured metrics.

    Simulates what a real content_retriever → pdf_extractor → ai_analysis
    pipeline would produce.
    """
    text = file_path.read_text(encoding="utf-8")

    financial_metrics = {
        "revenue": parse_dollar_amount(text, "Revenue") or parse_dollar_amount(text, "Total Revenue"),
        "cost_of_goods_sold": parse_dollar_amount(text, "Cost of Goods Sold"),
        "gross_profit": parse_dollar_amount(text, "Gross Profit"),
        "ebitda": parse_dollar_amount(text, "EBITDA"),
        "net_income": parse_dollar_amount(text, "Net Income"),
        "profit_margin": parse_percentage(text, "Profit Margin"),
        "headcount": parse_integer(text, "Headcount"),
        "customer_count": parse_integer(text, "Customer Count"),
    }

    return {k: v for k, v in financial_metrics.items() if v is not None}


def load_documents_from_disk() -> list[Content]:
    """
    Load quarterly financial report files from 99-assets/doc-set/.

    Returns Content items with both raw text and structured financial_metrics.
    """
    assets_dir = samples_dir / "99-assets" / "doc-set"

    if not assets_dir.exists():
        raise FileNotFoundError(
            f"Assets directory not found: {assets_dir}\n"
            f"Expected quarterly report .txt files in this folder."
        )

    files = sorted(assets_dir.glob("*.txt"))
    if not files:
        raise FileNotFoundError(
            f"No .txt files found in {assets_dir}\n"
            f"Expected files like Q1_Financial_Report_2024.txt"
        )

    documents = []
    for file_path in files:
        raw_text = file_path.read_text(encoding="utf-8")
        metrics = extract_metrics_from_report(file_path)

        content = Content(
            id=ContentIdentifier(
                canonical_id=file_path.name,
                unique_id=file_path.name,
                source_name="local_file",
                source_type="local_file",
                path=str(file_path),
                filename=file_path.name,
            ),
            data={
                "financial_metrics": metrics,
                "text": raw_text,
            },
        )
        documents.append(content)

    return documents


# ---------------------------------------------------------------------------
# Main pipeline runner
# ---------------------------------------------------------------------------

async def run_ai_comparison():
    """Run the AI-powered document set comparison pipeline with real files."""
    print("=" * 70)
    print("Sample 21: Document Set - AI Comparison (Real Files)")
    print("=" * 70)

    # Check required environment variables
    required_vars = {
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "AZURE_OPENAI_DEPLOYMENT_NAME": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    }

    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        print("\nQuick setup:")
        print("  export AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/")
        print("  export AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1")
        return

    config_path = Path(__file__).parent / "pipeline_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"

    # Load real files from disk
    documents = load_documents_from_disk()
    print(f"\n✓ Loaded {len(documents)} report files from 99-assets/doc-set/")
    for doc in documents:
        metrics = doc.data["financial_metrics"]
        rev = metrics.get("revenue")
        margin = metrics.get("profit_margin")
        rev_str = f"${rev:,.0f}" if rev else "N/A"
        margin_str = f"{margin:.1f}%" if margin else "N/A"
        print(f"  📄 {doc.id.filename}: revenue={rev_str}, margin={margin_str}")

    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="document_set_ai_comparison",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:

        print(f"\n✓ Initialized pipeline")

        # Execute the pipeline
        print(f"\n🔄 Running pipeline...")
        result = await pipeline_executor.execute(documents)

        print(f"\n✓ Pipeline completed with status: {result.status}")
        print(f"  Duration: {result.duration_seconds:.2f}s")

        # Display results
        if result.content:
            content = (
                result.content
                if isinstance(result.content, Content)
                else result.content[0]
            )

            # Show field aggregations
            aggregations = content.data.get("field_aggregations", {})
            if aggregations:
                print(f"\n📊 Deterministic Aggregations:")
                for key, agg in aggregations.get("aggregations", {}).items():
                    print(f"\n  {key}:")
                    if "sum" in agg and agg["sum"] is not None:
                        print(f"    Total: ${agg['sum']:,.0f}")
                    if "avg" in agg and agg["avg"] is not None:
                        if agg["avg"] > 1000:
                            print(f"    Average: ${agg['avg']:,.0f}")
                        else:
                            print(f"    Average: {agg['avg']:.2f}")
                    if "trend" in agg and agg["trend"]:
                        trend = agg["trend"]
                        pct = trend.get("overall_pct_change", "N/A")
                        print(
                            f"    Trend: {trend.get('direction', 'N/A')} "
                            f"({pct}% overall)"
                        )

            # Show AI comparison
            ai_analysis = content.data.get("cross_document_analysis", {})
            if ai_analysis:
                print(f"\n🤖 AI Cross-Document Analysis:")
                print(f"  Type: {ai_analysis.get('type', 'N/A')}")
                print(f"  Documents Compared: {ai_analysis.get('documents_compared', 0)}")

                analysis = ai_analysis.get("analysis", {})
                if isinstance(analysis, dict):
                    print(f"\n  Analysis (structured):")
                    print(f"  {json.dumps(analysis, indent=4, default=str)[:3000]}")
                else:
                    print(f"\n  Analysis (text):")
                    print(f"  {str(analysis)[:3000]}")

        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "ai_comparison_result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
        print(f"\n✓ Wrote output to {output_file}")

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_ai_comparison())
