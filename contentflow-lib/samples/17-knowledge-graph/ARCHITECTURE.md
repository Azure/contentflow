# Knowledge Graph Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KNOWLEDGE GRAPH PIPELINE                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Input Content   │
│  ┌──────────┐   │
│  │ Documents│   │
│  │  Reports │   │
│  │   PDFs   │   │
│  │   Text   │   │
│  └──────────┘   │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENTITY EXTRACTION PHASE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │  KnowledgeGraphEntityExtractorExecutor                      │            │
│  ├────────────────────────────────────────────────────────────┤            │
│  │                                                             │            │
│  │  Input:  Content with text                                 │            │
│  │                                                             │            │
│  │  Process:                                                   │            │
│  │  1. Build AI prompt with entity/relationship types         │            │
│  │  2. Call Azure AI model (GPT-4)                            │◄──────────┤
│  │  3. Parse JSON response                                     │  Azure AI │
│  │  4. Filter by confidence threshold                         │  Endpoint │
│  │  5. Add source document references                         │           │
│  │                                                             │            │
│  │  Output: Extracted entities and relationships              │            │
│  │  {                                                          │            │
│  │    "entities": [                                            │            │
│  │      {                                                      │            │
│  │        "id": "person-john-doe",                            │            │
│  │        "label": "Person",                                  │            │
│  │        "name": "John Doe",                                 │            │
│  │        "properties": {                                      │            │
│  │          "role": "CEO",                                    │            │
│  │          "source_document_id": "doc-001"                   │            │
│  │        },                                                   │            │
│  │        "confidence": 0.95                                  │            │
│  │      }                                                      │            │
│  │    ],                                                       │            │
│  │    "relationships": [                                       │            │
│  │      {                                                      │            │
│  │        "from_entity_id": "person-john-doe",               │            │
│  │        "to_entity_id": "org-acme-corp",                   │            │
│  │        "relationship_type": "works_at",                   │            │
│  │        "confidence": 0.90                                  │            │
│  │      }                                                      │            │
│  │    ]                                                        │            │
│  │  }                                                          │            │
│  └────────────────────────────────────────────────────────────┘            │
│                                                                              │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GRAPH STORAGE PHASE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │  KnowledgeGraphWriterExecutor                              │            │
│  ├────────────────────────────────────────────────────────────┤            │
│  │                                                             │            │
│  │  Process:                                                   │            │
│  │  1. Connect to Cosmos DB Gremlin API                       │            │
│  │  2. For each entity:                                        │            │
│  │     - Check if exists (by ID)                              │            │
│  │     - Apply merge strategy:                                │            │
│  │       • merge: Update properties                           │            │
│  │       • overwrite: Delete and recreate                     │            │
│  │       • skip: Leave unchanged                              │            │
│  │     - Add timestamps                                        │            │
│  │  3. For each relationship:                                  │            │
│  │     - Verify both vertices exist                           │            │
│  │     - Create edge with properties                          │            │
│  │                                                             │            │
│  │  Gremlin Queries Used:                                      │            │
│  │  • g.addV('Person').property('id', 'person-123')...        │            │
│  │  • g.V('person-123').property('role', 'CEO')               │            │
│  │  • g.V('from').addE('works_at').to(g.V('to'))             │            │
│  └────────────────────────────────────────────────────────────┘            │
│                                   │                                          │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐               │
│  │         Azure Cosmos DB Graph (Gremlin API)             │               │
│  ├─────────────────────────────────────────────────────────┤               │
│  │                                                          │               │
│  │   Vertices (Entities):                                   │               │
│  │   ┌────────────┐   ┌────────────┐   ┌────────────┐    │  Cosmos DB    │
│  │   │  Person    │   │Organization│   │  Product   │    │  Backend      │
│  │   │ John Doe   │   │ Acme Corp  │   │CloudPlatform│   │               │
│  │   └──────┬─────┘   └─────┬──────┘   └──────┬─────┘    │               │
│  │          │                │                  │          │               │
│  │   Edges (Relationships):  │                  │          │               │
│  │          │ works_at       │ provides         │          │               │
│  │          └────────────────┴──────────────────┘          │               │
│  │                                                          │               │
│  │   Properties:                                            │               │
│  │   - id, label, name                                      │               │
│  │   - Custom properties (role, description, etc.)          │               │
│  │   - Timestamps (created_at, updated_at)                 │               │
│  │   - Metadata (source_document_id, confidence)           │               │
│  └─────────────────────────────────────────────────────────┘               │
│                                                                              │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENRICHMENT PHASE (Optional)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │  KnowledgeGraphEnrichmentExecutor                          │            │
│  ├────────────────────────────────────────────────────────────┤            │
│  │                                                             │            │
│  │  Three Enrichment Types:                                    │            │
│  │                                                             │            │
│  │  1. AI Properties (enrichment_type: ai_properties)        │            │
│  │     - Generate entity descriptions                         │◄──────────┤
│  │     - Assign categories and tags                           │  Azure AI │
│  │     - Extract key attributes                               │  Model    │
│  │     - Add to vertex properties                             │           │
│  │                                                             │            │
│  │  2. Infer Relationships (enrichment_type: infer_relationships)         │
│  │     - Find entities with shared properties                 │            │
│  │     - Create "similar_to" edges                            │            │
│  │     - Pattern-based connections                            │            │
│  │                                                             │            │
│  │  3. Compute Metrics (enrichment_type: compute_metrics)     │            │
│  │     - Calculate in/out/total degree                        │            │
│  │     - Store as vertex properties                           │            │
│  │     - Enable centrality-based queries                      │            │
│  │                                                             │            │
│  │  Gremlin Queries:                                           │            │
│  │  • g.V('entity').property('ai_description', '...')         │            │
│  │  • g.V().has('tag', 'X').addE('similar_to').to(...)       │            │
│  │  • g.V('entity').bothE().count()                           │            │
│  └────────────────────────────────────────────────────────────┘            │
│                                                                              │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          QUERY & ANALYSIS PHASE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │  KnowledgeGraphQueryExecutor                               │            │
│  ├────────────────────────────────────────────────────────────┤            │
│  │                                                             │            │
│  │  Query Types:                                               │            │
│  │                                                             │            │
│  │  1. Find Entity (query_type: find_entity)                 │            │
│  │     Parameters:                                             │            │
│  │     - label: Entity type filter                            │            │
│  │     - property_name/value: Property filter                 │            │
│  │     Query: g.V().hasLabel('Person').has('role', 'CEO')    │            │
│  │                                                             │            │
│  │  2. Traverse (query_type: traverse)                        │            │
│  │     Parameters:                                             │            │
│  │     - start_entity_id: Starting point                      │            │
│  │     - edge_label: Relationship type                        │            │
│  │     - direction: out/in/both                               │            │
│  │     - max_depth: Traversal depth                           │            │
│  │     Query: g.V('id').repeat(out()).times(2)               │            │
│  │                                                             │            │
│  │  3. Pattern Match (query_type: pattern_match)             │            │
│  │     - Shortest path between entities                       │            │
│  │     - Common neighbors                                      │            │
│  │     - Similar entities                                      │            │
│  │                                                             │            │
│  │  4. Aggregate (query_type: aggregate)                      │            │
│  │     - Count vertices/edges                                  │            │
│  │     - Group by properties                                   │            │
│  │     - Label distribution                                    │            │
│  │                                                             │            │
│  │  5. Custom (query_type: custom)                            │            │
│  │     - Execute raw Gremlin queries                          │            │
│  │     - Full Gremlin language support                        │            │
│  └────────────────────────────────────────────────────────────┘            │
│                                                                              │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            OUTPUT & INTEGRATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Query Results → Multiple Destinations:                                      │
│                                                                              │
│  ┌─────────────────┐   ┌──────────────────┐   ┌─────────────────┐         │
│  │  Search Index   │   │  BI Dashboards   │   │  Applications   │         │
│  │  (AI Search)    │   │  (Power BI)      │   │  (Custom Apps)  │         │
│  └─────────────────┘   └──────────────────┘   └─────────────────┘         │
│                                                                              │
│  ┌─────────────────┐   ┌──────────────────┐   ┌─────────────────┐         │
│  │ Recommendations │   │   Analytics      │   │   RAG Systems   │         │
│  │    Systems      │   │   Pipelines      │   │   (Q&A Bots)    │         │
│  └─────────────────┘   └──────────────────┘   └─────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPONENT DEPENDENCIES                               │
└─────────────────────────────────────────────────────────────────────────────┘

CosmosGremlinConnector (packages/connectors/)
  │
  ├─► Base connection management
  ├─► Vertex operations (add, update, delete, get)
  ├─► Edge operations (add, delete)
  ├─► Query execution (Gremlin)
  └─► Traversal utilities

KnowledgeGraphEntityExtractorExecutor (packages/executors/)
  │
  ├─► Uses: AIInferenceConnector
  ├─► Inherits: ParallelExecutor
  ├─► Output: entities + relationships in Content.summary_data
  └─► Configurable: entity types, confidence threshold

KnowledgeGraphWriterExecutor (packages/executors/)
  │
  ├─► Uses: CosmosGremlinConnector
  ├─► Inherits: ParallelExecutor
  ├─► Input: Content with entities from extraction
  └─► Features: merge strategies, deduplication, timestamps

KnowledgeGraphQueryExecutor (packages/executors/)
  │
  ├─► Uses: CosmosGremlinConnector
  ├─► Inherits: BaseExecutor
  ├─► Query types: 5 (find, traverse, pattern, aggregate, custom)
  └─► Output: query results in Content.summary_data

KnowledgeGraphEnrichmentExecutor (packages/executors/)
  │
  ├─► Uses: CosmosGremlinConnector + AIInferenceConnector
  ├─► Inherits: ParallelExecutor
  ├─► Enrichment types: 3 (AI properties, infer relationships, metrics)
  └─► Selector: all, by_label, by_property

```

## Data Flow Example

```
Input Document:
┌──────────────────────────────────────────────────────────────┐
│ "John Doe is the CEO of Acme Corporation, which provides    │
│  CloudPlatform using Kubernetes technology."                 │
└──────────────────────────────────────────────────────────────┘
                          ↓
         [Entity Extraction with AI]
                          ↓
Extracted Entities:
┌─────────────┬─────────────────┬──────────────────┐
│ Person      │ Organization    │ Product          │
│ John Doe    │ Acme Corp       │ CloudPlatform    │
│ role: CEO   │ type: company   │ category: saas   │
└─────────────┴─────────────────┴──────────────────┘
             ↓                ↓              ↓
Extracted Relationships:
┌────────────────────────────────────────────────────┐
│ John Doe ---[works_at]---> Acme Corp               │
│ Acme Corp ---[provides]---> CloudPlatform          │
│ CloudPlatform ---[uses]---> Kubernetes             │
└────────────────────────────────────────────────────┘
                          ↓
            [Write to Graph Database]
                          ↓
Knowledge Graph in Cosmos DB:
┌────────────────────────────────────────────────────┐
│        (Person)          (Organization)            │
│      ┌─────────┐        ┌───────────┐            │
│      │John Doe │───────▶│ Acme Corp │            │
│      └─────────┘ works_at└───────────┘            │
│           ↑                    │                   │
│      authored_by          provides                │
│           │                    ▼                   │
│      ┌─────────┐        ┌──────────────┐         │
│      │Document │        │CloudPlatform │          │
│      │ Q4 Report│       │  (Product)   │          │
│      └─────────┘        └──────────────┘         │
│                                │                   │
│                              uses                  │
│                                ▼                   │
│                         ┌────────────┐            │
│                         │ Kubernetes │            │
│                         │(Technology)│            │
│                         └────────────┘            │
└────────────────────────────────────────────────────┘
```
