# ContentFlow Web

A modern, React-based web interface for building and managing intelligent document processing pipelines using ContentFlow. This application provides a visual pipeline builder, pre-built templates, and document vault management for enterprise content processing workflows.

## Overview

ContentFlow Web is a comprehensive platform for creating, managing, and executing data processing pipelines. It features:

- **Visual Pipeline Builder**: Drag-and-drop interface to design complex processing workflows
- **Pre-built Templates**: 10+ enterprise-ready pipeline templates for common use cases
- **Document Vaults**: Organize and manage your processed content
- **Real-time Execution**: Execute pipelines and track progress
- **YAML Editor**: Advanced users can edit pipeline definitions directly

## Tech Stack

- **Frontend**: React 18 with TypeScript
- **UI Components**: Shadcn/ui with Radix UI
- **Styling**: Tailwind CSS with PostCSS
- **Build Tool**: Vite
- **Graph Visualization**: ReactFlow
- **State Management**: React Query (TanStack Query)
- **Formatting**: js-yaml for pipeline definitions
- **Code Editor**: Monaco Editor for YAML editing

## Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- ContentFlow API running (typically on `http://localhost:8000`)

### Installation

```bash
cd contentflow-web
npm install
```

### Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```dotenv
# API Configuration (required)
VITE_API_BASE_URL=http://localhost:8000/api

```

### Development Server

```bash
npm run dev
```

The application will start on `http://localhost:8080` by default.

### Production Build

```bash
npm run build
```

Output files are generated in the `dist/` directory.

## Application Structure

```
contentflow-web/
├── src/
│   ├── components/           # React components
│   │   ├── pipeline/        # Pipeline builder components
│   │   ├── vaults/          # Vault management components
│   │   ├── knowledge/       # Knowledge graph components
│   │   ├── templates/       # Template components
│   │   ├── ui/              # Shadcn/ui component library
│   │   ├── PipelineBuilder.tsx
│   │   ├── KnowledgeGraph.tsx
│   │   └── ...
│   ├── pages/                # Page components
│   │   ├── Index.tsx         # Main home/dashboard page
│   │   ├── Templates.tsx     # Templates gallery page
│   │   └── Vaults.tsx        # Vault management page
│   ├── lib/                  # Utility functions and API clients
│   │   ├── api/              # API client functions
│   │   ├── pipelineYamlConverter.ts
│   │   ├── executorUiMapper.tsx
│   │   └── utils.ts
│   ├── data/                 # Static data
│   │   ├── pipelineTemplates.ts  # Pre-built pipeline templates
│   │   ├── executorTypes.tsx
│   │   └── knowledgeGraphData.ts
│   ├── types/                # TypeScript type definitions
│   │   ├── pipeline.ts
│   │   └── components.ts
│   ├── hooks/                # Custom React hooks
│   ├── App.tsx               # Root component
│   └── main.tsx              # Application entry point
├── public/                   # Static assets
├── index.html                # HTML entry point
├── vite.config.ts            # Vite configuration
├── tailwind.config.ts        # Tailwind CSS configuration
└── package.json              # Dependencies
```

## Page Flow & Navigation

### 1. **Home Page** (`/`)

The landing page provides the main navigation hub for the application.

**Components:**
- Navigation bar with links to all major features
- Hero section with call-to-action
- Quick start information

**Navigation Options:**
- **Home**: Return to landing page
- **Pipeline Builder**: Access the visual pipeline designer
- **Vaults**: Manage document repositories
- **Templates**: Browse pre-built pipeline templates

### 2. **Pipeline Builder** (`/?view=pipeline`)

The core of ContentFlow Web where users design and execute processing pipelines.

**Key Features:**
- Visual canvas with nodes and edges
- Executor catalog sidebar with searchable executors
- Real-time pipeline execution
- Save and load functionality
- YAML editor for advanced users

**Workflow:**

```
Start → Select Executors → Configure Settings → Connect Nodes → 
Test/Execute → View Results → Save Pipeline
```

**Main Actions:**

- **Add Executor**: Click "Add Executor" or drag from the executor list
- **Connect Nodes**: Drag from node output to another node's input
- **Configure**: Click a node to open configuration dialog
- **Execute**: Click "Execute" to run the pipeline
- **Save**: Save pipeline with custom name
- **Load**: Load previously saved pipelines
- **Toggle View**: Switch between visual canvas and YAML editor

### 3. **Templates Gallery** (`/templates`)

Pre-built pipeline templates for common use cases.

**Features:**
- Search functionality
- Category filtering (Extraction, Analysis, Knowledge)
- Template preview with visual representation
- One-click "Use Template" to load in pipeline builder
- Detailed use case descriptions
- Feature highlights

### 4. **Vaults** (`/?view=vaults`)

Manage document repositories and executions.

**Features:**
- Create new vaults
- Upload content
- View execution history
- Delete vaults
- Search and filter

**Vault Operations:**
- **Create Vault**: Set name, description, and tags
- **Upload Content**: Add documents to vault
- **View Executions**: See pipeline runs on vault content
- **Delete Vault**: Remove vault and associated data


## Building a Pipeline

### Step-by-Step Guide

#### 1. **Start with a Template** (Recommended for Beginners)

```
Home → Templates → Search for your use case → Click "Use Template" → Pipeline Builder
```

This loads a pre-configured pipeline that you can customize.

#### 2. **Create from Scratch**

```
Home → Pipeline Builder → Start building
```

#### 3. **Add Executors**

In the Pipeline Builder:

1. Click **"Add Executor"** or search in the left sidebar
2. Select an executor type from the catalog
3. Configure executor settings:
   - **Name**: Descriptive name for this step
   - **Settings**: Executor-specific configuration
   - **Description**: Document the purpose

Example executor types:
- `azure_blob_input`: Read files from Azure Blob Storage
- `azure_document_intelligence_extractor`: Extract text from PDFs
- `text_summarizer`: Summarize text content
- `entity_extractor`: Extract named entities
- `embedding_generator`: Generate vector embeddings
- `azure_blob_output`: Write results to Blob Storage

#### 4. **Connect Executors**

1. Click and drag from one node's output port to another node's input port
2. Edges represent data flow between executors
3. For **parallel execution**: One node → Multiple nodes
4. For **merging**: Multiple nodes → One node

#### 5. **Configure Settings**

For each executor node:

1. Click the node to open configuration dialog
2. Enter **executor-specific settings** (varies by type)
3. Example settings:
   - File filters (`.pdf`, `.docx`, etc.)
   - AI model parameters
   - Chunk size and overlap
   - Output format preferences

#### 6. **View Pipeline as YAML**

1. Click **"View YAML"** button to see the pipeline definition
2. Toggle between canvas and YAML editor
3. Edit YAML directly for advanced configurations

#### 7. **Test & Execute**

1. Click **"Execute"** button
2. Select input parameters if needed
3. Monitor execution status in real-time
4. View results after completion

#### 8. **Save Pipeline**

1. Click **"Save"** button
2. Enter pipeline name and description
3. Save as new or update existing
4. Use **"Load"** button to retrieve saved pipelines

## Pipeline Templates

ContentFlow Web includes 10 production-ready templates for common document processing scenarios:

| # | Template | ID | Category | Steps | Time | Key Features |
|---|----------|----|---------|----|------|--------------|
| 1 | PDF Document Extraction | `pdf-extraction` | Extraction | 4 | 2-3 min | Document Intelligence, table detection, chunking, Blob storage |
| 2 | Image & Visual Analysis | `image-content-extraction` | Extraction | 6 | 2-4 min | OCR, visual analysis, entity extraction, metadata |
| 3 | GPT-RAG Document Ingestion | `gpt-rag-ingestion` | Extraction | 6 | 3-5 min | Multi-format support, intelligent chunking, embeddings, AI Search |
| 4 | Multi-Format Processing | `multi-format-processing` | Extraction | 7 | 3-5 min | Parallel processing, format-specific extractors, batch operations |
| 5 | Article Summarization | `article-summarization` | Analysis | 5 | 1-2 min | AI summarization, key points, entity recognition, parallel processing |
| 6 | Email Content Analysis | `email-content-analysis` | Analysis | 6 | 1-2 min | Sentiment analysis, action items, categorization, priority detection |
| 7 | Content Classification | `content-classification` | Analysis | 7 | 2-3 min | Document classification, sentiment, entity extraction, keywords |
| 8 | PII Detection & Redaction | `pii-detection` | Analysis | 5 | 1-2 min | PII detection, auto redaction, multiple types, compliance reporting |
| 9 | Language Translation | `language-translation` | Analysis | 5 | 2-3 min | Language detection, high-quality translation, format preservation |
| 10 | Entity & Knowledge Mapping | `entity-mapping` | Knowledge | 5 | 3-5 min | NER, relationship extraction, knowledge graphs, graph export |


## Advanced Features

### YAML Editor

For advanced users, switch to YAML editor for direct pipeline definition:

1. Click **"View YAML"** in Pipeline Builder
2. Edit pipeline structure directly
3. Validate YAML syntax
4. Changes sync to visual canvas

### Pipeline Execution

Execute pipelines with:

1. **Input Selection**: Choose input files or parameters
2. **Real-time Monitoring**: Track execution progress
3. **Error Handling**: View detailed error messages
4. **Result Export**: Download processed results

### Execution History

View and manage previous executions:

1. Click **"View Executions"** button
2. Filter by date, status, or pipeline
3. View execution logs and results
4. Re-run previous executions

## Troubleshooting

### Common Issues

**Issue**: API connection fails
- **Solution**: Check `VITE_API_BASE_URL` in `.env`
- Ensure ContentFlow API is running on the specified address

**Issue**: Executors not loading
- **Solution**: Verify API is accessible and returning executor definitions
- Check browser console for error messages

**Issue**: Pipeline execution fails
- **Solution**: Check executor configurations for required parameters
- Review execution logs for detailed error information

**Issue**: Cannot save/load pipelines
- **Solution**: Ensure API has persistence layer configured
- Check database connectivity

### Debugging

Enable debug logging:

1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Check Network tab for API calls
4. Review Redux DevTools if installed

## Development

### Build Commands

```bash
# Development build with source maps
npm run build:dev

# Production build (optimized)
npm run build

# Preview production build locally
npm run preview
```

### Code Organization

- **Components**: UI components and feature components
- **Pages**: Full page components for routing
- **Types**: TypeScript definitions for type safety
- **Lib**: Utility functions and API clients
- **Hooks**: Reusable React hooks
- **Data**: Static data and constants

## API Integration

ContentFlow Web communicates with the ContentFlow API for:

- **Executors**: Fetch available executor types and schemas
- **Pipelines**: Save, load, and manage pipeline definitions
- **Execution**: Execute pipelines and track progress
- **Vaults**: Manage document repositories
- **Results**: Retrieve and display execution results

### API Endpoints Used

- `GET /api/executors`: List available executors
- `GET /api/pipelines`: List saved pipelines
- `POST /api/pipelines`: Create/save new pipeline
- `POST /api/pipelines/{id}/execute`: Execute pipeline
- `GET /api/pipelines/{id}/executions`: Get execution history
- `GET /api/vaults`: List vaults
- `POST /api/vaults`: Create vault
- `POST /api/vaults/{id}/upload`: Upload content

## Contributing

When contributing to ContentFlow Web:

1. Follow existing code style and patterns
2. Use TypeScript for type safety
3. Document complex logic with comments
4. Test changes locally before submitting
5. Update README if adding new features

## License

See the main ContentFlow repository for license information.

## Support & Documentation

- **Main Repository**: See [parent contentflow repository](../README.md)
- **API Documentation**: Check [contentflow-api README](../contentflow-api/README.md)
- **Architecture**: See [infra/README.md](../infra/README.md) for deployment details

## Next Steps

1. **Try a Template**: Start with a pre-built template matching your use case
2. **Build Custom Pipeline**: Create a pipeline from scratch using the builder
3. **Explore Vaults**: Create a document repository and manage content
4. **Integrate with API**: Connect to ContentFlow API for execution
5. **Scale for Production**: Deploy with proper configuration and monitoring

