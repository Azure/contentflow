# Knowledge Graph Quick Reference

## Executors

### 1. Knowledge Graph Entity Extractor
**ID**: `knowledge_graph_entity_extractor`
**Purpose**: Extract entities and relationships from content using AI

```yaml
entity_extractor:
  type: knowledge_graph_entity_extractor
  settings:
    ai_endpoint: "${AI_ENDPOINT}"
    model_name: "gpt-4"
    confidence_threshold: 0.6
    entity_types: ["Organization", "Person", "Product"]
```

**Output**: `knowledge_graph_entities` field with entities and relationships

---

### 2. Knowledge Graph Writer
**ID**: `knowledge_graph_writer`
**Purpose**: Write entities and relationships to Cosmos DB Graph

```yaml
graph_writer:
  type: knowledge_graph_writer
  settings:
    gremlin_endpoint: "${COSMOS_GREMLIN_ENDPOINT}"
    gremlin_database: "knowledge"
    gremlin_collection: "entities"
    merge_strategy: "merge"  # merge | overwrite | skip
```

**Output**: `graph_write_stats` field with write statistics

---

### 3. Knowledge Graph Query
**ID**: `knowledge_graph_query`
**Purpose**: Query the knowledge graph

```yaml
# Find entities
find_people:
  type: knowledge_graph_query
  settings:
    query_type: "find_entity"
    query_parameters:
      label: "Person"

# Traverse relationships
traverse_from_person:
  type: knowledge_graph_query
  settings:
    query_type: "traverse"
    query_parameters:
      start_entity_id: "person-123"
      edge_label: "works_at"
      direction: "out"
      max_depth: 2

# Custom Gremlin
custom_query:
  type: knowledge_graph_query
  settings:
    query_type: "custom"
    query_parameters:
      query: "g.V().hasLabel('Person').count()"
```

**Output**: `graph_query_results` field with query results

---

### 4. Knowledge Graph Enrichment
**ID**: `knowledge_graph_enrichment`
**Purpose**: Enrich graph with AI insights and metrics

```yaml
# Add AI properties
ai_enrichment:
  type: knowledge_graph_enrichment
  settings:
    enrichment_type: "ai_properties"
    ai_endpoint: "${AI_ENDPOINT}"
    model_name: "gpt-4"
    entity_selector: "by_label"
    selector_criteria:
      label: "Person"

# Infer relationships
infer_relationships:
  type: knowledge_graph_enrichment
  settings:
    enrichment_type: "infer_relationships"
    entity_selector: "all"

# Compute metrics
compute_metrics:
  type: knowledge_graph_enrichment
  settings:
    enrichment_type: "compute_metrics"
    entity_selector: "all"
```

**Output**: `graph_enrichment_stats` field with enrichment statistics

---

## Entity Types

| Type | Description | Example |
|------|-------------|---------|
| Organization | Companies, departments | Acme Corp, Engineering Dept |
| Person | People, employees | John Doe, Jane Smith |
| Product | Products, services | CloudPlatform, AutoML Suite |
| Technology | Tools, platforms | Kubernetes, Docker |
| Location | Places, offices | San Francisco, Building A |
| Event | Meetings, projects | Q4 Planning, Launch Event |
| Concept | Topics, themes | Machine Learning, Security |
| Document | Files, reports | Q4 Report, Contract |
| Department | Org units | Sales, Marketing |
| Role | Job titles | CEO, Engineer |
| Team | Working groups | Platform Team, DevOps |

---

## Relationship Types

| Type | Direction | Description | Example |
|------|-----------|-------------|---------|
| works_at | Person → Org | Employment | John works_at Acme |
| manages | Person → Person | Management | Jane manages Tom |
| located_in | Entity → Location | Physical location | Office located_in SF |
| part_of | Entity → Entity | Hierarchy | Dept part_of Company |
| provides | Org → Product | Service offering | Acme provides CloudPlatform |
| uses | Entity → Tech | Technology usage | Product uses Kubernetes |
| authored_by | Doc → Person | Authorship | Report authored_by John |
| mentions | Doc → Entity | Reference | Report mentions Product |
| related_to | Entity → Entity | General relation | Product related_to Concept |

---

## Query Types

### 1. Find Entity
Find entities by criteria

```python
query_parameters:
  entity_id: "person-123"              # Find by ID
  label: "Person"                       # Find by type
  property_name: "role"                 # Filter by property
  property_value: "CEO"
```

### 2. Traverse
Follow relationships from starting point

```python
query_parameters:
  start_entity_id: "person-123"         # Required
  edge_label: "works_at"                # Optional
  direction: "out"                      # out | in | both
  max_depth: 2                          # Traversal depth
```

### 3. Pattern Match
Find patterns in the graph

```python
query_parameters:
  pattern_type: "shortest_path"         # shortest_path | common_neighbors | similar_entities
  entity_a_id: "person-123"
  entity_b_id: "person-456"
```

### 4. Aggregate
Get statistics

```python
query_parameters:
  aggregation_type: "count"             # count | group_by | distribution
  label: "Person"                       # Optional
  property_name: "role"                 # For group_by
```

### 5. Custom
Execute Gremlin query

```python
query_parameters:
  query: "g.V().hasLabel('Person').count()"
```

---

## Merge Strategies

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| `merge` | Update existing properties | Evolving graph, add new info |
| `overwrite` | Delete and recreate | Full replacement needed |
| `skip` | Keep existing unchanged | Preserve original data |

---

## Environment Variables

```bash
# Cosmos DB
export COSMOS_GREMLIN_ENDPOINT="wss://account.gremlin.cosmos.azure.com:443/"
export COSMOS_GREMLIN_DATABASE="knowledge"
export COSMOS_GREMLIN_COLLECTION="entities"
export COSMOS_GREMLIN_KEY="your-key"

# Azure AI
export AI_ENDPOINT="https://your-endpoint.azure.com/"
export AI_API_KEY="your-key"
export AI_MODEL_NAME="gpt-4"
```

---

## Common Workflows

### Build Knowledge Graph
```yaml
workflow:
  - Extract entities → Write to graph
  
executors:
  - knowledge_graph_entity_extractor
  - knowledge_graph_writer
```

### Enrich Graph
```yaml
workflow:
  - Add AI properties → Infer relationships → Compute metrics
  
executors:
  - knowledge_graph_enrichment (ai_properties)
  - knowledge_graph_enrichment (infer_relationships)
  - knowledge_graph_enrichment (compute_metrics)
```

### Query Graph
```yaml
workflow:
  - Find entities → Traverse → Analyze patterns
  
executors:
  - knowledge_graph_query (find_entity)
  - knowledge_graph_query (traverse)
  - knowledge_graph_query (pattern_match)
```

---

## Sample Gremlin Queries

```gremlin
// Count all vertices
g.V().count()

// Find all people
g.V().hasLabel('Person')

// Find person by name
g.V().hasLabel('Person').has('name', 'John Doe')

// Get all relationships from a person
g.V('person-123').outE()

// Traverse: Find organization where person works
g.V('person-123').out('works_at')

// Find all products provided by organizations
g.V().hasLabel('Organization').out('provides')

// Count entities by type
g.V().groupCount().by(label)

// Find most connected entities
g.V().project('name', 'degree').by('name').by(bothE().count()).order().by('degree', desc).limit(10)

// Shortest path
g.V('person-123').repeat(out().simplePath()).until(hasId('person-456')).path()

// Find common connections
g.V('person-123').out().where(__.in().hasId('person-456'))
```

---

## Performance Tips

1. **Entity Extraction**
   - Use lower temperature (0.1) for consistent results
   - Set appropriate confidence threshold
   - Limit max entities per document

2. **Graph Writing**
   - Use batch operations
   - Enable deduplication
   - Choose merge strategy wisely
   - Monitor Cosmos DB RUs

3. **Querying**
   - Limit traversal depth
   - Use max_results to control size
   - Index frequently queried properties
   - Cache common queries

4. **Enrichment**
   - Run in batches
   - Schedule periodic jobs
   - Select entities strategically
   - Monitor AI costs

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection failed | Verify endpoint and credentials |
| Low extraction quality | Adjust confidence threshold, review entity types |
| Slow queries | Limit depth, add indexes, check RU allocation |
| Duplicate entities | Enable deduplication, use consistent IDs |
| High costs | Batch operations, cache results, optimize queries |

---

## Quick Start

```bash
# 1. Setup
cd samples/17-knowledge-graph
bash setup.sh

# 2. Configure
vi .env  # Add your credentials

# 3. Run
python build_knowledge_graph.py
python enrich_knowledge_graph.py
python query_knowledge_graph.py
```

---

## Resources

- **Connector**: `packages/connectors/cosmos_gremlin_connector.py`
- **Executors**: `packages/executors/knowledge_graph_*.py`
- **Samples**: `samples/17-knowledge-graph/`
- **Catalog**: `executor_catalog.yaml` (search "knowledge_graph")
- **Docs**: `IMPLEMENTATION_GUIDE.md`, `ARCHITECTURE.md`
