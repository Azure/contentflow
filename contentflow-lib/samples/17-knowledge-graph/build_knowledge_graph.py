"""
Build Knowledge Graph from Content

This script demonstrates building a knowledge graph from business documents
using Azure Cosmos DB Graph API (Gremlin).
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_framework import WorkflowContext
from contentflow.models import Content
from contentflow.executors import (
    KnowledgeGraphEntityExtractorExecutor,
    KnowledgeGraphWriterExecutor
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Build knowledge graph from sample documents."""
    
    logger.info("=" * 80)
    logger.info("Knowledge Graph Construction Demo")
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
        logger.error("Please set all required variables. See README.md for details.")
        return
    
    # Create sample business documents
    documents = [
        Content(
            content_id="doc-001",
            title="Company Overview - Acme Corporation",
            text_content="""
            Acme Corporation is a leading technology company founded in 2010 by CEO John Doe.
            The company specializes in cloud computing solutions and AI-powered analytics.
            
            Our flagship product, CloudPlatform, helps enterprises manage their infrastructure
            using Kubernetes and Docker. The platform is used by over 500 companies worldwide.
            
            The Engineering Department, led by VP of Engineering Jane Smith, consists of 150
            engineers working across three offices: San Francisco, New York, and London.
            
            In Q4 2024, we launched AutoML Suite, an automated machine learning platform that
            integrates with CloudPlatform. This product was developed by the Data Science team
            under Dr. Alice Johnson.
            """,
            source_uri="sample://company-overview.txt",
            summary_data={}
        ),
        Content(
            content_id="doc-002",
            title="Product Announcement - AutoML Suite",
            text_content="""
            We're excited to announce AutoML Suite, our latest innovation in machine learning.
            This product enables data scientists to build, train, and deploy models with minimal
            code, leveraging TensorFlow and PyTorch under the hood.
            
            AutoML Suite was created through a partnership between our Data Science team and
            the CloudPlatform engineering group. Lead architect Bob Williams designed the
            system architecture, while Dr. Alice Johnson led the machine learning research.
            
            Key features include:
            - Automated feature engineering
            - Model selection and hyperparameter tuning
            - Integration with CloudPlatform for deployment
            - Support for popular ML frameworks
            
            The product is available as part of CloudPlatform Enterprise subscription.
            """,
            source_uri="sample://automl-announcement.txt",
            summary_data={}
        ),
        Content(
            content_id="doc-003",
            title="Team Structure - Engineering Department",
            text_content="""
            The Engineering Department at Acme Corporation is organized into several teams:
            
            1. Platform Team (20 engineers)
               - Led by Senior Manager Sarah Chen
               - Focus: CloudPlatform core infrastructure
               - Technologies: Kubernetes, Docker, Go, Python
            
            2. Data Science Team (15 engineers)
               - Led by Dr. Alice Johnson
               - Focus: Machine learning and AI products
               - Technologies: TensorFlow, PyTorch, Python, R
            
            3. Frontend Team (25 engineers)
               - Led by Director Mike Rodriguez
               - Focus: User interfaces and customer portals
               - Technologies: React, TypeScript, Next.js
            
            4. DevOps Team (10 engineers)
               - Led by Manager Tom Anderson
               - Focus: CI/CD, monitoring, reliability
               - Technologies: Jenkins, Prometheus, Grafana
            
            All teams report to VP of Engineering Jane Smith, who reports to CTO David Lee.
            The CTO works closely with CEO John Doe on technology strategy.
            """,
            source_uri="sample://team-structure.txt",
            summary_data={}
        )
    ]
    
    # Step 1: Extract entities and relationships
    logger.info("\n" + "=" * 80)
    logger.info("Step 1: Extracting Entities and Relationships")
    logger.info("=" * 80)
    
    entity_extractor = KnowledgeGraphEntityExtractorExecutor(
        id="entity_extractor",
        settings={
            "ai_endpoint": os.getenv("AI_ENDPOINT"),
            "ai_credential_type": "azure_key_credential",
            "ai_api_key": os.getenv("AI_API_KEY"),
            "model_name": os.getenv("AI_MODEL_NAME"),
            "entity_types": [
                "Organization", "Person", "Product", "Technology",
                "Location", "Department", "Role", "Team"
            ],
            "confidence_threshold": 0.6,
            "output_field": "knowledge_graph_entities"
        }
    )
    
    ctx = WorkflowContext(workflow_id="kg_build", run_id="run-001")
    
    # Process each document
    for i, doc in enumerate(documents):
        logger.info(f"\nProcessing document {i+1}/{len(documents)}: {doc.title}")
        processed_doc = await entity_extractor.process_content_item(doc, ctx)
        
        # Display extracted entities
        kg_data = processed_doc.summary_data.get("knowledge_graph_entities", {})
        entities = kg_data.get("entities", [])
        relationships = kg_data.get("relationships", [])
        
        logger.info(f"  Extracted {len(entities)} entities and {len(relationships)} relationships")
        
        # Show sample entities
        if entities:
            logger.info("  Sample entities:")
            for entity in entities[:3]:
                logger.info(f"    - {entity.get('label')}: {entity.get('name')}")
        
        documents[i] = processed_doc
    
    # Step 2: Write to knowledge graph
    logger.info("\n" + "=" * 80)
    logger.info("Step 2: Writing to Knowledge Graph (Cosmos DB Gremlin)")
    logger.info("=" * 80)
    
    graph_writer = KnowledgeGraphWriterExecutor(
        id="graph_writer",
        settings={
            "gremlin_endpoint": os.getenv("COSMOS_GREMLIN_ENDPOINT"),
            "gremlin_database": os.getenv("COSMOS_GREMLIN_DATABASE"),
            "gremlin_collection": os.getenv("COSMOS_GREMLIN_COLLECTION"),
            "gremlin_password": os.getenv("COSMOS_GREMLIN_KEY"),
            "input_field": "knowledge_graph_entities",
            "merge_strategy": "merge",
            "enable_deduplication": True,
            "add_timestamps": True
        }
    )
    
    # Write each document's entities to the graph
    for i, doc in enumerate(documents):
        logger.info(f"\nWriting document {i+1}/{len(documents)} to graph: {doc.title}")
        result_doc = await graph_writer.process_content_item(doc, ctx)
        
        # Display write statistics
        stats = result_doc.summary_data.get("graph_write_stats", {})
        logger.info(f"  Entities written: {stats.get('entities_written', 0)}/{stats.get('entities_total', 0)}")
        logger.info(f"  Relationships written: {stats.get('relationships_written', 0)}/{stats.get('relationships_total', 0)}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Knowledge Graph Construction Complete!")
    logger.info("=" * 80)
    logger.info(f"Processed {len(documents)} documents")
    logger.info("Knowledge graph is now available in Cosmos DB for querying and analysis")
    logger.info("\nNext steps:")
    logger.info("  1. Run enrich_knowledge_graph.py to add AI-generated insights")
    logger.info("  2. Run query_knowledge_graph.py to explore the graph")
    logger.info("  3. Use Azure Cosmos DB Data Explorer to visualize the graph")


if __name__ == "__main__":
    asyncio.run(main())
