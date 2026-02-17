"""
Sample 20: Static Document Set Processing with Real Files

Demonstrates the document set processing pipeline using real quarterly
financial report files from 99-assets/doc-set/. Each file is read from
disk and parsed for key financial metrics (simulating what a real
extraction pipeline would produce), then processed through the full
document set pipeline.

Pipeline steps:
1. Read real .txt report files from 99-assets/doc-set/
2. Parse financial metrics from each file
3. DocumentSetInitializerExecutor — stamps set metadata
4. DocumentSetCollectorExecutor — consolidates into single Content
5. CrossDocumentFieldAggregatorExecutor — computes trends, aggregations

No Azure services required — runs entirely locally with real files.

Usage:
    python run.py
"""

import asyncio
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


def parse_dollar_amount(text: str, label: str) -> float | None:
    """Extract a dollar amount following a label, e.g. 'Revenue:  $10,500,000'."""
    pattern = rf"{re.escape(label)}:\s*\$?([\d,]+(?:\.\d+)?)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def parse_percentage(text: str, label: str) -> float | None:
    """Extract a percentage value following a label, e.g. 'Profit Margin: 21.9%'."""
    pattern = rf"{re.escape(label)}:\s*([\d.]+)%"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def parse_integer(text: str, label: str) -> int | None:
    """Extract an integer value following a label, e.g. 'Headcount: 245'."""
    pattern = rf"{re.escape(label)}:\s*([\d,]+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


def extract_metrics_from_report(file_path: Path) -> dict:
    """
    Parse a quarterly financial report text file and extract key metrics.

    This simulates what a real extraction pipeline (content_retriever →
    pdf_extractor → ai_analysis) would produce as structured output.
    """
    text = file_path.read_text(encoding="utf-8")

    metrics = {
        "revenue": parse_dollar_amount(text, "Revenue") or parse_dollar_amount(text, "Total Revenue"),
        "cost_of_goods_sold": parse_dollar_amount(text, "Cost of Goods Sold"),
        "gross_profit": parse_dollar_amount(text, "Gross Profit"),
        "operating_expenses": parse_dollar_amount(text, "Total Operating Expenses") or parse_dollar_amount(text, "Operating Expenses"),
        "ebitda": parse_dollar_amount(text, "EBITDA"),
        "net_income": parse_dollar_amount(text, "Net Income"),
        "profit_margin": parse_percentage(text, "Profit Margin"),
        "headcount": parse_integer(text, "Headcount"),
        "customer_count": parse_integer(text, "Customer Count"),
    }

    return {k: v for k, v in metrics.items() if v is not None}


def load_documents_from_disk() -> list[Content]:
    """
    Load quarterly financial report files from 99-assets/doc-set/.

    Each .txt file is read, parsed for financial metrics, and wrapped
    in a Content object with both the raw text and structured data.
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
                **metrics,
                "text": raw_text,
            },
        )
        documents.append(content)

    return documents


async def run_static_document_set():
    """Run the static document set processing pipeline with real files."""
    print("=" * 70)
    print("Sample 20: Static Document Set - Real Files + Field Aggregation")
    print("=" * 70)

    config_path = Path(__file__).parent / "pipeline_config.yaml"
    executor_catalog_path = samples_dir.parent / "executor_catalog.yaml"

    # Load real files from disk
    documents = load_documents_from_disk()
    print(f"\n✓ Loaded {len(documents)} report files from 99-assets/doc-set/")
    for doc in documents:
        rev = doc.data.get("revenue")
        margin = doc.data.get("profit_margin")
        rev_str = f"${rev:,.0f}" if rev else "N/A"
        margin_str = f"{margin:.1f}%" if margin else "N/A"
        print(f"  📄 {doc.id.filename}: revenue={rev_str}, margin={margin_str}")

    async with PipelineExecutor.from_config_file(
        config_path=config_path,
        pipeline_name="static_document_set_aggregation",
        executor_catalog_path=executor_catalog_path,
    ) as pipeline_executor:

        print(f"\n✓ Initialized pipeline")

        # Execute the pipeline
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

            # Show aggregation results
            aggregations = content.data.get("field_aggregations", {})
            if aggregations:
                print(f"\n📊 Field Aggregation Results:")
                print(f"  Set: {aggregations.get('set_name', 'N/A')}")
                print(f"  Documents: {aggregations.get('total_documents', 0)}")

                for key, agg in aggregations.get("aggregations", {}).items():
                    print(f"\n  📈 {key}:")
                    print(f"    Field: {agg.get('field_path', 'N/A')}")

                    for stat in ("sum", "avg", "min", "max"):
                        val = agg.get(stat)
                        if val is not None:
                            if val > 10000:
                                print(f"    {stat.capitalize():6s}: ${val:,.0f}")
                            else:
                                print(f"    {stat.capitalize():6s}: {val:,.2f}")

                    if "trend" in agg and agg["trend"] is not None:
                        trend = agg["trend"]
                        print(
                            f"    Trend: {trend.get('direction', 'N/A')} "
                            f"(confidence: {trend.get('confidence', 0):.0%})"
                        )
                        if trend.get("overall_pct_change") is not None:
                            print(
                                f"    Overall Change: {trend['overall_pct_change']:+.1f}%"
                            )

                    if "pct_change" in agg and agg["pct_change"]:
                        print(f"    Period Changes:")
                        for change in agg["pct_change"]:
                            pct = change.get("pct_change")
                            if pct is not None:
                                print(
                                    f"      {change['from']} → {change['to']}: {pct:+.1f}%"
                                )

            # Show document set info
            doc_set = content.data.get("document_set", {})
            if doc_set:
                print(f"\n📋 Document Set Summary:")
                print(f"  Set ID: {doc_set.get('set_id', 'N/A')}")
                print(f"  Set Name: {doc_set.get('set_name', 'N/A')}")
                print(f"  Documents: {doc_set.get('total_documents', 0)}")
                for d in doc_set.get("documents", []):
                    print(
                        f"    [{d.get('order', '?')}] {d.get('role', 'N/A')} "
                        f"({d.get('filename', 'N/A')})"
                    )

        # Write results to output folder
        output_folder = Path(__file__).parent / "output"
        output_folder.mkdir(exist_ok=True)
        output_file = output_folder / "static_document_set_result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
        print(f"\n✓ Wrote output to {output_file}")

        # Show processing events
        print(f"\n📊 Processing Events:")
        for i, event in enumerate(result.events):
            print(
                f"  Event {i + 1}: {event.event_type} (executor: {event.executor_id})"
            )

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_static_document_set())
