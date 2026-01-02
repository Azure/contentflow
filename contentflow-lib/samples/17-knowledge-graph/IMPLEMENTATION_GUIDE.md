# Knowledge Graph Implementation Documentation

## Overview

This implementation provides a complete solution for building comprehensive and evolving knowledge graphs from content using Azure Cosmos DB Graph API (Gremlin). The system extracts business entities and relationships using AI, stores them in a graph database, and enables rich querying and analysis.

## Architecture

### Components

1. **Cosmos DB Gremlin Connector** (`cosmos_gremlin_connector.py`)
   - Manages connections to Azure Cosmos DB Graph API
   - Provides CRUD operations for vertices and edges
   - Supports graph traversal and queries
   - Handles connection pooling and error recovery

2. **Knowledge Graph Entity Extractor** (`knowledge_graph_entity_extractor.py`)
   - Uses AI to extract entities from content
   - Identifies relationships between entities
   - Assigns confidence scores
   - Supports customizable entity and relationship types

3. **Knowledge Graph Writer** (`knowledge_graph_writer.py`)
   - Persists entities and relationships to the graph
   - Handles entity deduplication and merging
   - Supports multiple merge strategies
   - Tracks metadata and timestamps

4. **Knowledge Graph Query** (`knowledge_graph_query.py`)
   - Retrieves entities by criteria
   - Traverses relationships
   - Performs pattern matching
   - Executes aggregations and analytics

5. **Knowledge Graph Enrichment** (`knowledge_graph_enrichment.py`)
   - Adds AI-generated entity properties
   - Infers implicit relationships
   - Computes graph metrics
   - Supports entity classification

## Features

### Entity Extraction
- **Supported Entity Types**:
  - Organization (companies, departments, teams)
  - Person (employees, authors, stakeholders)
  - Product (products, services, offerings)
  - Technology (tools, platforms, frameworks)
  - Location (offices, cities, regions)
  - Event (meetings, projects, milestones)
  - Concept (topics, themes, categories)
  - Document (files, reports, contracts)
  - Custom types (extensible)

- **Relationship Types**:
  - `works_at`: Person → Organization
  - `manages`: Person → Person/Team
  - `located_in`: Entity → Location
  - `part_of`: Entity → Entity (hierarchy)
  - `provides`: Organization → Product/Service
  - `uses`: Entity → Technology
  - `authored_by`: Document → Person
  - `mentions`: Document → Entity
  - `related_to`: Entity → Entity
  - Custom relationships (extensible)

### Graph Operations

#### Writing
- **Merge Strategies**:
  - `merge`: Update existing entities with new properties
  - `overwrite`: Replace existing entities completely
  - `skip`: Keep existing entities unchanged

- **Features**:
  - Entity deduplication by ID
  - Automatic timestamp tracking
  - Batch operations for performance
  - Property sanitization for Cosmos DB limits

#### Querying
- **Query Types**:
  - `find_entity`: Search by ID, label, or properties
  - `traverse`: Follow relationships from starting point
  - `pattern_match`: Shortest path, common neighbors, similar entities
  - `aggregate`: Count, group by, distribution
  - `custom`: Execute raw Gremlin queries

- **Features**:
  - Parameterized queries
  - Result limiting and pagination
  - Direction control (in, out, both)
  - Depth-limited traversal

#### Enrichment
- **AI Properties**:
  - Generate entity descriptions
  - Assign categories and tags
  - Extract key attributes
  - Temperature-controlled generation

- **Relationship Inference**:
  - Find similar entities
  - Create similarity relationships
  - Pattern-based connections
  - Confidence-based filtering

- **Graph Metrics**:
  - Degree centrality (in/out/total)
  - Connection counts
  - Importance scoring
  - Custom analytics

## Configuration

### Connector Settings

```yaml
gremlin_endpoint: "wss://account.gremlin.cosmos.azure.com:443/"
gremlin_database: "knowledge"
gremlin_collection: "entities"
gremlin_username: "/dbs/knowledge/colls/entities"  # Auto-generated if not provided
gremlin_password: "${COSMOS_PRIMARY_KEY}"
enable_ssl: true
max_retries: 3
connection_pool_size: 4
```

### Entity Extractor Settings

```yaml
ai_endpoint: "${AI_ENDPOINT}"
ai_credential_type: "azure_key_credential"
ai_api_key: "${AI_API_KEY}"
model_name: "gpt-4"
entity_types: ["Organization", "Person", "Product", ...]
relationship_types: ["works_at", "manages", ...]
confidence_threshold: 0.6
max_entities_per_content: 50
temperature: 0.1
output_field: "knowledge_graph_entities"
```

### Writer Settings

```yaml
gremlin_endpoint: "${COSMOS_GREMLIN_ENDPOINT}"
gremlin_database: "knowledge"
gremlin_collection: "entities"
gremlin_password: "${COSMOS_GREMLIN_KEY}"
merge_strategy: "merge"  # merge, overwrite, skip
enable_deduplication: true
add_timestamps: true
batch_size: 20
```

## Usage Examples

### Building a Knowledge Graph

```python
from packages.executors import (
    KnowledgeGraphEntityExtractorExecutor,
    KnowledgeGraphWriterExecutor
)

# Extract entities
extractor = KnowledgeGraphEntityExtractorExecutor(
    id="extractor",
    settings={
        "ai_endpoint": os.getenv("AI_ENDPOINT"),
        "model_name": "gpt-4",
        "confidence_threshold": 0.6
    }
)

content = await extractor.process_content_item(document, ctx)

# Write to graph
writer = KnowledgeGraphWriterExecutor(
    id="writer",
    settings={
        "gremlin_endpoint": os.getenv("COSMOS_GREMLIN_ENDPOINT"),
        "gremlin_database": "knowledge",
        "gremlin_collection": "entities",
        "merge_strategy": "merge"
    }
)

result = await writer.process_content_item(content, ctx)
```

### Querying the Graph

```python
from packages.executors import KnowledgeGraphQueryExecutor

# Find all people
query = KnowledgeGraphQueryExecutor(
    id="find_people",
    settings={
        "query_type": "find_entity",
        "query_parameters": {"label": "Person"},
        "max_results": 100
    }
)

results = await query.process_contents([content], ctx)
```

### Enriching the Graph

```python
from packages.executors import KnowledgeGraphEnrichmentExecutor

# Add AI properties
enricher = KnowledgeGraphEnrichmentExecutor(
    id="enricher",
    settings={
        "enrichment_type": "ai_properties",
        "ai_endpoint": os.getenv("AI_ENDPOINT"),
        "model_name": "gpt-4",
        "entity_selector": "by_label",
        "selector_criteria": {"label": "Person"}
    }
)

result = await enricher.process_content_item(content, ctx)
```

## Sample Workflows

### Complete Pipeline

1. **Build Phase** (`samples/17-knowledge-graph/knowledge_graph_build.yaml`):
   - Extract entities from documents
   - Write to graph database
   - Create initial graph structure

2. **Enrichment Phase** (`knowledge_graph_enrichment.yaml`):
   - Add AI-generated properties
   - Infer relationships
   - Compute metrics

3. **Query Phase** (`knowledge_graph_queries.yaml`):
   - Search entities
   - Traverse relationships
   - Analyze patterns

## Best Practices

### Entity Extraction
1. Use specific entity types relevant to your domain
2. Adjust confidence threshold based on precision needs
3. Limit max entities to avoid information overload
4. Use lower temperature for consistent extraction

### Graph Writing
1. Use `merge` strategy for evolving graphs
2. Enable deduplication to avoid duplicate entities
3. Batch operations for large datasets
4. Monitor Cosmos DB RU consumption

### Querying
1. Limit traversal depth to avoid expensive queries
2. Use indexes on frequently queried properties
3. Implement caching for common queries
4. Monitor query performance

### Enrichment
1. Run enrichment in batches
2. Schedule periodic enrichment jobs
3. Track enrichment timestamps
4. Validate AI-generated properties

## Performance Considerations

### Cosmos DB Optimization
- **Partition Key**: Choose based on query patterns
- **Indexing**: Index frequently queried properties
- **RU Allocation**: Scale based on throughput needs
- **Batch Operations**: Use for bulk writes

### AI Model Selection
- **GPT-4**: Best accuracy, higher cost
- **GPT-3.5-Turbo**: Good balance
- **Custom Models**: Domain-specific entities

### Scaling
- **Horizontal**: Partition graph by domain
- **Vertical**: Increase Cosmos DB RUs
- **Caching**: Cache frequently accessed entities
- **Async**: Use parallel processing

## Monitoring and Debugging

### Logging
All executors provide detailed logging:
- Entity extraction results
- Graph write statistics
- Query performance metrics
- Enrichment progress

### Metrics
Track these key metrics:
- Entities extracted per document
- Graph write success rate
- Query response times
- Enrichment coverage

### Troubleshooting
- **Connection errors**: Verify Cosmos DB credentials
- **Extraction quality**: Adjust confidence threshold
- **Performance issues**: Optimize queries, increase RUs
- **Data quality**: Implement validation rules

## Security

### Authentication
- Use Azure Managed Identity when possible
- Rotate keys regularly
- Store credentials in Key Vault

### Authorization
- Implement role-based access
- Audit graph modifications
- Encrypt sensitive properties

### Data Privacy
- PII detection before extraction
- Property-level encryption
- Compliance with regulations (GDPR, etc.)

## Integration

### Upstream Systems
- Document processing pipelines
- Content management systems
- Data warehouses
- External APIs

### Downstream Consumers
- Search engines
- Recommendation systems
- Analytics dashboards
- Business intelligence tools

## Future Enhancements

1. **Advanced Analytics**
   - PageRank for entity importance
   - Community detection
   - Anomaly detection
   - Time-series analysis

2. **Machine Learning**
   - Link prediction
   - Entity resolution
   - Classification models
   - Embedding generation

3. **Visualization**
   - Interactive graph explorer
   - Real-time updates
   - Custom layouts
   - Export formats

4. **Integration**
   - Graph RAG for Q&A
   - Knowledge base APIs
   - External ontologies
   - Multi-modal graphs

## References

- [Azure Cosmos DB Gremlin API Documentation](https://docs.microsoft.com/azure/cosmos-db/graph-introduction)
- [Gremlin Query Language](https://tinkerpop.apache.org/gremlin.html)
- [Knowledge Graph Best Practices](https://www.w3.org/TR/swbp-vocab-pub/)
- [Graph Database Design Patterns](https://neo4j.com/developer/graph-data-modeling/)
