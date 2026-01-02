# Knowledge Graph Construction Sample

This sample demonstrates how to build a comprehensive and evolving knowledge graph from content using Azure Cosmos DB Graph API (Gremlin).

## Overview

The knowledge graph workflow extracts business entities and relationships from documents and persists them in a graph database, enabling:
- Entity discovery and classification
- Relationship mapping
- Graph-based insights
- Semantic search and recommendations
- Business intelligence and analytics

## Prerequisites

1. **Azure Cosmos DB Account** with Gremlin API enabled
   - Create a database and graph collection
   - Note the endpoint, database name, collection name, and primary key

2. **Azure AI Endpoint** for entity extraction
   - Deploy a GPT-4 or similar model
   - Note the endpoint URL and API key

3. **Environment Variables**:
   ```bash
   export COSMOS_GREMLIN_ENDPOINT="wss://your-account.gremlin.cosmos.azure.com:443/"
   export COSMOS_GREMLIN_DATABASE="knowledge"
   export COSMOS_GREMLIN_COLLECTION="entities"
   export COSMOS_GREMLIN_KEY="your-primary-key"
   export AI_ENDPOINT="https://your-ai-endpoint.azure.com/"
   export AI_API_KEY="your-api-key"
   export AI_MODEL_NAME="gpt-4"
   ```

4. **Python Dependencies**:
   ```bash
   pip install gremlinpython
   ```

## Workflows

### 1. Build Knowledge Graph (`knowledge_graph_build.yaml`)

This workflow extracts entities and relationships from content and builds the knowledge graph:

1. **Content Retrieval**: Load documents from blob storage
2. **Entity Extraction**: Use AI to identify entities and relationships
3. **Graph Writing**: Persist entities and relationships to Cosmos DB

### 2. Enrich Knowledge Graph (`knowledge_graph_enrichment.yaml`)

This workflow enhances the existing graph with additional insights:

1. **AI Property Enrichment**: Add AI-generated descriptions and categories
2. **Relationship Inference**: Discover implicit connections
3. **Metrics Computation**: Calculate graph analytics (degree, centrality)

### 3. Query Knowledge Graph (`knowledge_graph_query.yaml`)

This workflow demonstrates various graph queries:

1. **Entity Search**: Find specific entities
2. **Relationship Traversal**: Explore connections
3. **Pattern Matching**: Discover paths and patterns

## Entity Types

The knowledge graph supports various entity types:
- **Organization**: Companies, departments, teams
- **Person**: Employees, authors, stakeholders
- **Product**: Products, services, offerings
- **Technology**: Tools, platforms, systems
- **Location**: Offices, regions, facilities
- **Event**: Meetings, projects, milestones
- **Concept**: Topics, themes, categories
- **Document**: Files, reports, contracts

## Relationship Types

Common relationships include:
- `works_at`: Person → Organization
- `manages`: Person → Person/Team
- `located_in`: Organization → Location
- `part_of`: Entity → Entity (hierarchy)
- `provides`: Organization → Product/Service
- `uses`: Organization → Technology
- `authored_by`: Document → Person
- `mentions`: Document → Entity
- `related_to`: Entity → Entity (general)

## Running the Sample

### Build the Knowledge Graph

```bash
python build_knowledge_graph.py
```

This will:
1. Process sample business documents
2. Extract entities and relationships
3. Create the knowledge graph in Cosmos DB

### Enrich the Graph

```bash
python enrich_knowledge_graph.py
```

This will:
1. Select entities from the graph
2. Add AI-generated properties
3. Infer implicit relationships
4. Compute graph metrics

### Query the Graph

```bash
python query_knowledge_graph.py
```

This demonstrates various queries:
1. Find all people in the organization
2. Discover products and their relationships
3. Traverse from a person to related entities
4. Find shortest paths between entities

## Sample Data

The `sample_data/` directory contains example business documents:
- Company overview
- Product descriptions
- Team structure
- Project documentation

## Expected Output

After running the build workflow, you'll have:
- Entities in Cosmos DB representing business concepts
- Relationships connecting related entities
- A queryable knowledge graph for insights

Example graph structure:
```
(Person: John Doe) -[works_at]-> (Organization: Acme Corp)
(Person: John Doe) -[manages]-> (Person: Jane Smith)
(Organization: Acme Corp) -[provides]-> (Product: CloudPlatform)
(Product: CloudPlatform) -[uses]-> (Technology: Kubernetes)
(Document: Q4Report) -[authored_by]-> (Person: John Doe)
(Document: Q4Report) -[mentions]-> (Product: CloudPlatform)
```

## Graph Visualization

You can visualize the graph using:
1. **Azure Cosmos DB Data Explorer**: Built-in graph visualization
2. **Gremlin Console**: Command-line interface
3. **Custom visualization tools**: Using graph data export

## Use Cases

1. **Semantic Search**: Find documents related to specific entities
2. **Recommendations**: Suggest related content based on graph connections
3. **Organization Intelligence**: Map company structure and relationships
4. **Product Analysis**: Understand product dependencies and usage
5. **Expert Finding**: Identify subject matter experts by entity connections
6. **Impact Analysis**: Trace entity relationships for change management

## Advanced Features

### Dynamic Entity Types

The graph can evolve to include new entity types discovered in content.

### Confidence Scoring

Each entity and relationship includes a confidence score from the AI extraction.

### Temporal Analysis

Track entity and relationship changes over time with timestamps.

### Multi-source Integration

Combine entities from multiple document sources for comprehensive coverage.

## Troubleshooting

### Connection Issues
- Verify Cosmos DB endpoint and credentials
- Check firewall settings
- Ensure Gremlin API is enabled

### Entity Extraction Issues
- Adjust confidence threshold
- Customize entity types list
- Review AI model configuration

### Performance Optimization
- Use batch operations for large datasets
- Implement entity caching
- Optimize Gremlin queries

## Next Steps

1. Integrate with your document pipeline
2. Customize entity types for your domain
3. Build graph-based search interfaces
4. Implement real-time graph updates
5. Add graph analytics and insights
