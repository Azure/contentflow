# ContentFlow API Client

This directory contains the complete API client implementation for the ContentFlow web application. It provides a type-safe, modular interface to interact with the FastAPI backend.

## Structure

```
lib/api/
├── index.ts              # Barrel export for all API modules
├── apiClient.ts          # Base axios client with interceptors
├── apiTypes.ts           # TypeScript type definitions
├── executorsApi.ts       # Executor catalog operations
├── pipelinesApi.ts       # Pipeline CRUD and execution
├── templatesApi.ts       # Pipeline templates management
├── vaultsApi.ts          # Secrets/vault management
├── connectorsApi.ts      # Connector configurations
├── systemApi.ts          # Health checks and system info
└── useApi.ts             # React hooks for API calls
```

## Features

- **Type-Safe**: Full TypeScript support with comprehensive type definitions
- **Native Fetch**: Uses browser's native fetch API (no external dependencies)
- **Error Handling**: Centralized error handling with custom error types
- **Timeout Support**: Configurable request timeouts
- **React Hooks**: Custom hooks for easy integration in components
- **Pagination**: Built-in pagination support
- **File Upload/Download**: Support for YAML import/export
- **Query Building**: Helper utilities for URL query parameters

## Installation

No external dependencies required! The API client uses the browser's native `fetch` API.

## Configuration

Create a `.env` file in the project root (see `.env.example`):

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## Usage

### Basic Import

```typescript
import { 
  getExecutors, 
  getPipelines, 
  createPipeline,
  getTemplates,
  getVaults,
  ApiError
} from '@/lib/api';
```

### Using API Functions

```typescript
// Fetch executors
try {
  const executors = await getExecutors();
  console.log(executors);
} catch (error) {
  const apiError = error as ApiError;
  console.error(apiError.message);
}

// Create a pipeline
const newPipeline = await createPipeline({
  name: "My Data Pipeline",
  description: "Processes customer data",
  yaml: "pipeline:\n  executors:\n    - ..."
});

// Get templates with filters
const templates = await getTemplates({
  category: 'data-processing',
  page: 1,
  pageSize: 10
});

// Execute a pipeline
const execution = await executePipeline({
  pipelineId: "pipeline-123",
  inputs: { file: "data.csv" }
});
```

### Using React Hooks

#### useApi Hook

For GET requests that should execute on component mount:

```typescript
import { useApi } from '@/lib/api';
import { getExecutors } from '@/lib/api';

function ExecutorList() {
  const { data, loading, error, refetch } = useApi(getExecutors);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {data?.map(executor => (
        <div key={executor.id}>{executor.name}</div>
      ))}
      <button onClick={refetch}>Refresh</button>
    </div>
  );
}
```

#### useMutation Hook

For POST/PUT/DELETE operations:

```typescript
import { useMutation } from '@/lib/api';
import { createPipeline, CreatePipelineRequest } from '@/lib/api';

function CreatePipelineForm() {
  const { mutate, loading, error } = useMutation(createPipeline);

  const handleSubmit = async (data: CreatePipelineRequest) => {
    try {
      const pipeline = await mutate(data);
      console.log('Pipeline created:', pipeline);
    } catch (err) {
      console.error('Failed to create pipeline');
    }
  };

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      handleSubmit({
        name: "New Pipeline",
        yaml: "..."
      });
    }}>
      {/* form fields */}
      <button disabled={loading}>
        {loading ? 'Creating...' : 'Create Pipeline'}
      </button>
      {error && <div>{error.message}</div>}
    </form>
  );
}
```

#### usePaginatedApi Hook

For paginated lists:

```typescript
import { usePaginatedApi } from '@/lib/api';
import { getPipelines } from '@/lib/api';

function PipelineList() {
  const {
    data,
    loading,
    error,
    page,
    totalPages,
    nextPage,
    prevPage,
    goToPage
  } = usePaginatedApi(
    (page, pageSize) => getPipelines({ page, pageSize }),
    1, // initial page
    20  // page size
  );

  return (
    <div>
      {data.map(pipeline => <div key={pipeline.id}>{pipeline.name}</div>)}
      <Pagination
        page={page}
        totalPages={totalPages}
        onNext={nextPage}
        onPrev={prevPage}
        onGoTo={goToPage}
      />
    </div>
  );
}
```

#### usePolling Hook

For real-time updates:

```typescript
import { usePolling } from '@/lib/api';
import { getExecutionStatus } from '@/lib/api';

function ExecutionMonitor({ executionId }: { executionId: string }) {
  const { data, loading, error } = usePolling(
    () => getExecutionStatus(executionId),
    3000, // poll every 3 seconds
    true  // enabled
  );

  return (
    <div>
      Status: {data?.status}
      {data?.status === 'running' && <Spinner />}
    </div>
  );
}
```

## API Modules

### Executors API

- `getExecutors()` - Get all executors
- `getExecutorCatalog()` - Get full catalog with metadata
- `getExecutorById(id)` - Get specific executor
- `getExecutorsByCategory(category)` - Filter by category
- `searchExecutors(query)` - Search executors
- `validateExecutorConfig(id, config)` - Validate configuration

### Pipelines API

- `getPipelines(query)` - List pipelines with filters
- `getPipelineById(id)` - Get specific pipeline
- `createPipeline(data)` - Create new pipeline
- `updatePipeline(id, data)` - Update pipeline
- `deletePipeline(id)` - Delete pipeline
- `getPipelineYaml(id)` - Get YAML configuration
- `updatePipelineYaml(id, yaml)` - Update YAML
- `validatePipeline(yaml)` - Validate YAML
- `executePipeline(request)` - Execute pipeline
- `getExecutionStatus(executionId)` - Check execution status
- `cancelExecution(executionId)` - Cancel running execution
- `duplicatePipeline(id, name)` - Clone pipeline
- `exportPipelineYaml(id)` - Export as file
- `importPipelineYaml(file)` - Import from file

### Templates API

- `getTemplates(query)` - List templates with filters
- `getTemplateById(id)` - Get specific template
- `getTemplatesByCategory(category)` - Filter by category
- `getTemplateCategories()` - Get all categories
- `searchTemplates(query)` - Search templates
- `getFeaturedTemplates(limit)` - Get featured templates
- `getRecentTemplates(limit)` - Get recent templates
- `createPipelineFromTemplate(id)` - Create pipeline from template
- `createTemplate(data)` - Create new template (admin)
- `updateTemplate(id, data)` - Update template (admin)
- `deleteTemplate(id)` - Delete template (admin)

### Vaults API

- `getVaults()` - List all vaults
- `getVaultById(id)` - Get specific vault
- `createVault(data)` - Create new vault
- `updateVault(id, data)` - Update vault
- `deleteVault(id)` - Delete vault
- `getDefaultVault()` - Get default vault
- `setDefaultVault(id)` - Set as default
- `testVaultConnection(id)` - Test connectivity
- `getVaultSecrets(vaultId)` - List secrets
- `getVaultSecret(vaultId, name)` - Get specific secret
- `createVaultSecret(vaultId, data)` - Create secret
- `updateVaultSecret(vaultId, name, data)` - Update secret
- `deleteVaultSecret(vaultId, name)` - Delete secret
- `rotateVaultSecret(vaultId, name)` - Rotate secret

### Connectors API

- `getConnectors()` - List all connectors
- `getConnectorById(id)` - Get specific connector
- `getConnectorsByType(type)` - Filter by type
- `createConnector(data)` - Create connector
- `updateConnector(id, data)` - Update connector
- `deleteConnector(id)` - Delete connector
- `testConnectorConnection(id)` - Test connection
- `activateConnector(id)` - Activate connector
- `deactivateConnector(id)` - Deactivate connector

### System API

- `getHealthCheck()` - Basic health check
- `getDetailedHealth()` - Detailed health with services
- `getSystemInfo()` - System information
- `getApiVersion()` - API version
- `ping()` - Connectivity test

## Error Handling

All API functions throw `ApiError` objects:

```typescript
interface ApiError {
  message: string;
  status?: number;
  detail?: any;
}
```

Example error handling:

```typescript
try {
  const pipeline = await createPipeline(data);
} catch (error) {
  const apiError = error as ApiError;
  
  if (apiError.status === 400) {
    console.error('Validation error:', apiError.detail);
  } else if (apiError.status === 401) {
    console.error('Unauthorized');
  } else {
    console.error('Unknown error:', apiError.message);
  }
}
```

## Authentication

The API client automatically includes authentication tokens from localStorage:

```typescript
// Set auth token (e.g., after login)
localStorage.setItem('authToken', 'your-jwt-token');

// Remove auth token (e.g., on logout)
localStorage.removeItem('authToken');
```

## Custom Configuration

Create a custom API client with different configuration:

```typescript
import { createApiClient } from '@/lib/api';

const customClient = createApiClient({
  baseURL: 'https://api.example.com',
  timeout: 60000,
  headers: {
    'X-Custom-Header': 'value'
  }
});
```

## Type Definitions

All types are exported from `apiTypes.ts`:

```typescript
import {
  Pipeline,
  ExecutorType,
  PipelineTemplate,
  Vault,
  Connector,
  CreatePipelineRequest,
  UpdatePipelineRequest,
  // ... and more
} from '@/lib/api';
```

## Testing

Mock API calls in tests:

```typescript
import { vi } from 'vitest';
import * as api from '@/lib/api';

vi.mock('@/lib/api', () => ({
  getExecutors: vi.fn(() => Promise.resolve([...])),
  createPipeline: vi.fn(() => Promise.resolve({ id: '123', ... }))
}));
```

## Backend Endpoints

The API client expects the following FastAPI endpoints:

- `/api/executors/*` - Executor operations
- `/api/pipelines/*` - Pipeline operations
- `/api/templates/*` - Template operations
- `/api/vaults/*` - Vault operations
- `/api/connectors/*` - Connector operations
- `/api/health` - Health checks
- `/api/system/*` - System information

## License

Part of the ContentFlow project.
