"""
Query Knowledge Graph

This script demonstrates various knowledge graph queries:
- Finding entities by criteria
- Traversing relationships
- Pattern matching
- Aggregations
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_framework import WorkflowContext
from packages.models import Content
from packages.executors import KnowledgeGraphQueryExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run various knowledge graph queries."""
    
    logger.info("=" * 80)
    logger.info("Knowledge Graph Query Demo")
    logger.info("=" * 80)
    
    # Verify environment variables
    required_vars = [
        "COSMOS_GREMLIN_ENDPOINT",
        "COSMOS_GREMLIN_DATABASE",
        "COSMOS_GREMLIN_COLLECTION",
        "COSMOS_GREMLIN_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return
    
    ctx = WorkflowContext(workflow_id="kg_query", run_id="run-001")
    
    # Placeholder content for queries
    content = Content(
        content_id="query-trigger",
        title="Knowledge Graph Query",
        text_content="",
        source_uri="internal://query",
        summary_data={}
    )
    
    # Query 1: Find all people in the organization
    logger.info("\n" + "=" * 80)
    logger.info("Query 1: Find All People")
    logger.info("=" * 80)
    
    person_finder = KnowledgeGraphQueryExecutor(
        id="person_finder",
        settings={
            "gremlin_endpoint": os.getenv("COSMOS_GREMLIN_ENDPOINT"),
            "gremlin_database": os.getenv("COSMOS_GREMLIN_DATABASE"),
            "gremlin_collection": os.getenv("COSMOS_GREMLIN_COLLECTION"),
            "gremlin_password": os.getenv("COSMOS_GREMLIN_KEY"),
            "query_type": "find_entity",
            "query_parameters": {"label": "Person"},
            "max_results": 50
        }
    )
    
    result = await person_finder.process_contents([content], ctx)
    query_results = result[0].summary_data.get("graph_query_results", {})
    people = query_results.get("results", [])
    
    logger.info(f"Found {len(people)} people in the knowledge graph")
    for person in people[:5]:
        person_props = person.get("properties", {})
        name = person_props.get("name", ["Unknown"])[0] if isinstance(person_props.get("name"), list) else person_props.get("name", "Unknown")
        logger.info(f"  - {name}")
    
    # Query 2: Find all products
    logger.info("\n" + "=" * 80)
    logger.info("Query 2: Find All Products")
    logger.info("=" * 80)
    
    product_finder = KnowledgeGraphQueryExecutor(
        id="product_finder",
        settings={
            "gremlin_endpoint": os.getenv("COSMOS_GREMLIN_ENDPOINT"),
            "gremlin_database": os.getenv("COSMOS_GREMLIN_DATABASE"),
            "gremlin_collection": os.getenv("COSMOS_GREMLIN_COLLECTION"),
            "gremlin_password": os.getenv("COSMOS_GREMLIN_KEY"),
            "query_type": "find_entity",
            "query_parameters": {"label": "Product"},
            "max_results": 50
        }
    )
    
    result = await product_finder.process_contents([content], ctx)
    query_results = result[0].summary_data.get("graph_query_results", {})
    products = query_results.get("results", [])
    
    logger.info(f"Found {len(products)} products")
    for product in products:
        product_props = product.get("properties", {})
        name = product_props.get("name", ["Unknown"])[0] if isinstance(product_props.get("name"), list) else product_props.get("name", "Unknown")
        logger.info(f"  - {name}")
    
    # Query 3: Get graph statistics
    logger.info("\n" + "=" * 80)
    logger.info("Query 3: Graph Statistics")
    logger.info("=" * 80)
    
    stats_aggregator = KnowledgeGraphQueryExecutor(
        id="stats_aggregator",
        settings={
            "gremlin_endpoint": os.getenv("COSMOS_GREMLIN_ENDPOINT"),
            "gremlin_database": os.getenv("COSMOS_GREMLIN_DATABASE"),
            "gremlin_collection": os.getenv("COSMOS_GREMLIN_COLLECTION"),
            "gremlin_password": os.getenv("COSMOS_GREMLIN_KEY"),
            "query_type": "aggregate",
            "query_parameters": {
                "aggregation_type": "distribution"
            }
        }
    )
    
    result = await stats_aggregator.process_contents([content], ctx)
    query_results = result[0].summary_data.get("graph_query_results", {})
    stats = query_results.get("results", {})
    
    logger.info("Entity distribution by label:")
    label_dist = stats.get("label_distribution", {})
    for label, count in label_dist.items():
        logger.info(f"  {label}: {count}")
    
    # Query 4: Custom Gremlin query - Find most connected entities
    logger.info("\n" + "=" * 80)
    logger.info("Query 4: Most Connected Entities (Highest Degree)")
    logger.info("=" * 80)
    
    custom_query = KnowledgeGraphQueryExecutor(
        id="custom_query",
        settings={
            "gremlin_endpoint": os.getenv("COSMOS_GREMLIN_ENDPOINT"),
            "gremlin_database": os.getenv("COSMOS_GREMLIN_DATABASE"),
            "gremlin_collection": os.getenv("COSMOS_GREMLIN_COLLECTION"),
            "gremlin_password": os.getenv("COSMOS_GREMLIN_KEY"),
            "query_type": "custom",
            "query_parameters": {
                "query": "g.V().project('id', 'name', 'label', 'degree').by(id).by('name').by(label).by(bothE().count()).order().by('degree', desc).limit(10)"
            },
            "max_results": 10
        }
    )
    
    result = await custom_query.process_contents([content], ctx)
    query_results = result[0].summary_data.get("graph_query_results", {})
    top_entities = query_results.get("results", [])
    
    logger.info("Top 10 most connected entities:")
    for entity in top_entities:
        if isinstance(entity, dict):
            name = entity.get("name", ["Unknown"])[0] if isinstance(entity.get("name"), list) else entity.get("name", "Unknown")
            label = entity.get("label", "Unknown")
            degree = entity.get("degree", 0)
            logger.info(f"  {name} ({label}) - {degree} connections")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Knowledge Graph Query Demo Complete!")
    logger.info("=" * 80)
    logger.info("Demonstrated queries:")
    logger.info("  ✓ Entity search by type")
    logger.info("  ✓ Graph statistics and aggregations")
    logger.info("  ✓ Custom Gremlin queries")
    logger.info("\nNext steps:")
    logger.info("  - Explore more complex graph traversals")
    logger.info("  - Implement pattern matching for insights")
    logger.info("  - Build graph-based recommendations")


if __name__ == "__main__":
    asyncio.run(main())
