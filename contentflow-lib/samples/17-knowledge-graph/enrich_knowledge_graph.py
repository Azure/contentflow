"""
Enrich Knowledge Graph with AI Insights

This script demonstrates enriching the knowledge graph with:
- AI-generated properties (descriptions, categories)
- Inferred relationships
- Graph metrics
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_framework import WorkflowContext
from packages.models import Content
from packages.executors import KnowledgeGraphEnrichmentExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Enrich the knowledge graph with AI-generated insights."""
    
    logger.info("=" * 80)
    logger.info("Knowledge Graph Enrichment Demo")
    logger.info("=" * 80)
    
    # Verify environment variables
    required_vars = [
        "COSMOS_GREMLIN_ENDPOINT",
        "COSMOS_GREMLIN_DATABASE",
        "COSMOS_GREMLIN_COLLECTION",
        "COSMOS_GREMLIN_KEY",
        "AI_ENDPOINT",
        "AI_MODEL_NAME"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return
    
    ctx = WorkflowContext(workflow_id="kg_enrich", run_id="run-001")
    
    # Placeholder content (enrichment operates on the graph directly)
    content = Content(
        content_id="enrichment-trigger",
        title="Knowledge Graph Enrichment",
        text_content="",
        source_uri="internal://enrichment",
        summary_data={}
    )
    
    # Enrichment 1: Add AI-generated properties
    logger.info("\n" + "=" * 80)
    logger.info("Enrichment 1: Adding AI-Generated Properties")
    logger.info("=" * 80)
    logger.info("Adding descriptions, categories, and tags to entities...")
    
    ai_enricher = KnowledgeGraphEnrichmentExecutor(
        id="ai_enricher",
        settings={
            "gremlin_endpoint": os.getenv("COSMOS_GREMLIN_ENDPOINT"),
            "gremlin_database": os.getenv("COSMOS_GREMLIN_DATABASE"),
            "gremlin_collection": os.getenv("COSMOS_GREMLIN_COLLECTION"),
            "gremlin_password": os.getenv("COSMOS_GREMLIN_KEY"),
            "enrichment_type": "ai_properties",
            "ai_endpoint": os.getenv("AI_ENDPOINT"),
            "ai_credential_type": "azure_key_credential",
            "ai_api_key": os.getenv("AI_API_KEY"),
            "model_name": os.getenv("AI_MODEL_NAME"),
            "entity_selector": "by_label",
            "selector_criteria": {"label": "Person"}
        }
    )
    
    result = await ai_enricher.process_content_item(content, ctx)
    stats = result.summary_data.get("graph_enrichment_stats", {})
    logger.info(f"Enriched {stats.get('entities_enriched', 0)} Person entities with AI properties")
    
    # Enrichment 2: Infer relationships
    logger.info("\n" + "=" * 80)
    logger.info("Enrichment 2: Inferring Implicit Relationships")
    logger.info("=" * 80)
    logger.info("Finding entities with similar properties and creating relationships...")
    
    relationship_inferrer = KnowledgeGraphEnrichmentExecutor(
        id="relationship_inferrer",
        settings={
            "gremlin_endpoint": os.getenv("COSMOS_GREMLIN_ENDPOINT"),
            "gremlin_database": os.getenv("COSMOS_GREMLIN_DATABASE"),
            "gremlin_collection": os.getenv("COSMOS_GREMLIN_COLLECTION"),
            "gremlin_password": os.getenv("COSMOS_GREMLIN_KEY"),
            "enrichment_type": "infer_relationships",
            "entity_selector": "all"
        }
    )
    
    result = await relationship_inferrer.process_content_item(content, ctx)
    stats = result.summary_data.get("graph_enrichment_stats", {})
    logger.info(f"Processed {stats.get('entities_processed', 0)} entities for relationship inference")
    
    # Enrichment 3: Compute graph metrics
    logger.info("\n" + "=" * 80)
    logger.info("Enrichment 3: Computing Graph Metrics")
    logger.info("=" * 80)
    logger.info("Calculating degree centrality for all entities...")
    
    metrics_computer = KnowledgeGraphEnrichmentExecutor(
        id="metrics_computer",
        settings={
            "gremlin_endpoint": os.getenv("COSMOS_GREMLIN_ENDPOINT"),
            "gremlin_database": os.getenv("COSMOS_GREMLIN_DATABASE"),
            "gremlin_collection": os.getenv("COSMOS_GREMLIN_COLLECTION"),
            "gremlin_password": os.getenv("COSMOS_GREMLIN_KEY"),
            "enrichment_type": "compute_metrics",
            "entity_selector": "all"
        }
    )
    
    result = await metrics_computer.process_content_item(content, ctx)
    stats = result.summary_data.get("graph_enrichment_stats", {})
    logger.info(f"Computed metrics for {stats.get('entities_enriched', 0)} entities")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Knowledge Graph Enrichment Complete!")
    logger.info("=" * 80)
    logger.info("The knowledge graph has been enhanced with:")
    logger.info("  ✓ AI-generated entity properties")
    logger.info("  ✓ Inferred relationships")
    logger.info("  ✓ Graph analytics metrics")
    logger.info("\nUse query_knowledge_graph.py to explore the enriched graph")


if __name__ == "__main__":
    asyncio.run(main())
