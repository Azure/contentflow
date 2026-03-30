# ContentFlow — Arquitectura Detallada de Componentes

> **Documentación técnica completa**: componentes, interconexiones, flujos de datos, SKUs, configuración y diagramas de la plataforma ContentFlow.

---

## Índice

- [1. Visión general de la arquitectura](#1-visión-general-de-la-arquitectura)
  - [1.1 Diagrama de arquitectura completa](#11-diagrama-de-arquitectura-completa)
  - [1.2 Principios arquitectónicos](#12-principios-arquitectónicos)
- [2. Componente: Interfaz Web (contentflow-web)](#2-componente-interfaz-web-contentflow-web)
  - [2.1 Stack tecnológico](#21-stack-tecnológico)
  - [2.2 Estructura de la aplicación](#22-estructura-de-la-aplicación)
  - [2.3 Rutas y navegación](#23-rutas-y-navegación)
  - [2.4 Componentes principales de la UI](#24-componentes-principales-de-la-ui)
  - [2.5 Gestión de estado y datos](#25-gestión-de-estado-y-datos)
  - [2.6 Diagrama de componentes Web](#26-diagrama-de-componentes-web)
- [3. Componente: API REST (contentflow-api)](#3-componente-api-rest-contentflow-api)
  - [3.1 Stack tecnológico](#31-stack-tecnológico)
  - [3.2 Endpoints del API](#32-endpoints-del-api)
  - [3.3 Capa de servicios](#33-capa-de-servicios)
  - [3.4 Capa de base de datos](#34-capa-de-base-de-datos)
  - [3.5 Modelos de datos](#35-modelos-de-datos)
  - [3.6 Inyección de dependencias](#36-inyección-de-dependencias)
  - [3.7 Configuración y arranque](#37-configuración-y-arranque)
  - [3.8 Diagrama de capas del API](#38-diagrama-de-capas-del-api)
- [4. Componente: Worker Service (contentflow-worker)](#4-componente-worker-service-contentflow-worker)
  - [4.1 Stack tecnológico](#41-stack-tecnológico)
  - [4.2 Arquitectura multi-proceso](#42-arquitectura-multi-proceso)
  - [4.3 Worker de entrada (Input Source Worker)](#43-worker-de-entrada-input-source-worker)
  - [4.4 Worker de procesamiento (Content Processing Worker)](#44-worker-de-procesamiento-content-processing-worker)
  - [4.5 Cliente de cola](#45-cliente-de-cola)
  - [4.6 Ciclo de vida de una tarea](#46-ciclo-de-vida-de-una-tarea)
  - [4.7 Configuración del Worker](#47-configuración-del-worker)
  - [4.8 Diagrama del motor de workers](#48-diagrama-del-motor-de-workers)
- [5. Componente: Librería Core (contentflow-lib)](#5-componente-librería-core-contentflow-lib)
  - [5.1 Motor de pipelines](#51-motor-de-pipelines)
  - [5.2 Jerarquía de clases de ejecutores](#52-jerarquía-de-clases-de-ejecutores)
  - [5.3 Catálogo completo de ejecutores](#53-catálogo-completo-de-ejecutores)
  - [5.4 Modelo de contenido (Content)](#54-modelo-de-contenido-content)
  - [5.5 Conectores de Azure](#55-conectores-de-azure)
  - [5.6 Diagrama del motor de pipelines](#56-diagrama-del-motor-de-pipelines)
- [6. Infraestructura de Azure (infra)](#6-infraestructura-de-azure-infra)
  - [6.1 Recursos desplegados](#61-recursos-desplegados)
  - [6.2 SKUs y niveles de servicio](#62-skus-y-niveles-de-servicio)
  - [6.3 Módulos Bicep](#63-módulos-bicep)
  - [6.4 Cosmos DB — Estructura de base de datos](#64-cosmos-db--estructura-de-base-de-datos)
  - [6.5 Storage Account — Blobs y colas](#65-storage-account--blobs-y-colas)
  - [6.6 Container Apps — Configuración de servicios](#66-container-apps--configuración-de-servicios)
  - [6.7 AI Foundry — Modelos de IA](#67-ai-foundry--modelos-de-ia)
  - [6.8 Diagrama de infraestructura Azure](#68-diagrama-de-infraestructura-azure)
- [7. Interconexión entre componentes](#7-interconexión-entre-componentes)
  - [7.1 Flujo de datos completo](#71-flujo-de-datos-completo)
  - [7.2 Flujo de mensajes por cola](#72-flujo-de-mensajes-por-cola)
  - [7.3 Flujo de autenticación](#73-flujo-de-autenticación)
  - [7.4 Matriz de comunicación entre servicios](#74-matriz-de-comunicación-entre-servicios)
  - [7.5 Diagrama de secuencia: Ejecución de pipeline](#75-diagrama-de-secuencia-ejecución-de-pipeline)
- [8. Modos de despliegue](#8-modos-de-despliegue)
  - [8.1 Modo básico](#81-modo-básico)
  - [8.2 Modo AILZ (AI Landing Zone)](#82-modo-ailz-ai-landing-zone)
  - [8.3 Proceso de despliegue con azd](#83-proceso-de-despliegue-con-azd)
  - [8.4 Diagrama comparativo de modos](#84-diagrama-comparativo-de-modos)
- [9. Seguridad y autenticación](#9-seguridad-y-autenticación)
  - [9.1 Modelo de identidad](#91-modelo-de-identidad)
  - [9.2 Roles RBAC asignados](#92-roles-rbac-asignados)
  - [9.3 Diagrama de seguridad](#93-diagrama-de-seguridad)
- [10. Configuración centralizada](#10-configuración-centralizada)
  - [10.1 Azure App Configuration](#101-azure-app-configuration)
  - [10.2 Variables de entorno por servicio](#102-variables-de-entorno-por-servicio)
- [11. Monitoreo y observabilidad](#11-monitoreo-y-observabilidad)
- [12. Resumen de dependencias entre componentes](#12-resumen-de-dependencias-entre-componentes)

---

## 1. Visión general de la arquitectura

ContentFlow implementa una **arquitectura de microservicios event-driven (basada en eventos)** con los siguientes patrones clave:

- **Microservicios**: 3 servicios independientes (API, Worker, Web) desplegados como contenedores
- **Event-Driven**: Comunicación asíncrona mediante colas de mensajes
- **Cloud-Native**: Diseñado para Azure Container Apps con escalado automático
- **Declarativo**: Pipelines definidos en YAML, infraestructura definida en Bicep

### 1.1 Diagrama de arquitectura completa

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         AZURE CONTAINER APPS ENVIRONMENT                         │
│                                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐           │
│  │  contentflow-web │    │ contentflow-api  │    │contentflow-worker│           │
│  │                  │    │                  │    │                  │           │
│  │  React 18        │    │  FastAPI         │    │  Multi-process   │           │
│  │  TypeScript      │───▶│  Python 3.12+   │    │  Python 3.12+   │           │
│  │  Vite            │    │  Puerto: 8090   │    │  Puerto: 8099   │           │
│  │  ReactFlow       │    │                  │    │                  │           │
│  │  Monaco Editor   │    │  ┌────────────┐  │    │ ┌──────────────┐ │           │
│  │                  │    │  │  Routers   │  │    │ │Source Workers│ │           │
│  │                  │    │  │  Services  │  │    │ │Process Worker│ │           │
│  │                  │    │  │  Models    │  │    │ │Queue Client  │ │           │
│  │                  │    │  └────────────┘  │    │ └──────────────┘ │           │
│  │  CPU: 1 | 2Gi   │    │  CPU: 1 | 2Gi   │    │  CPU: 1 | 2Gi   │           │
│  │  Réplicas: 1-2   │    │  Réplicas: 1-2   │    │  Réplicas: 1-2   │           │
│  └──────────────────┘    └───────┬──────────┘    └────────┬─────────┘           │
│                                  │                         │                     │
└──────────────────────────────────┼─────────────────────────┼─────────────────────┘
                                   │                         │
           ┌───────────────────────┼─────────────────────────┼──────────────┐
           │                       ▼                         ▼              │
           │  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐     │
           │  │  Cosmos DB  │ │    Blob     │ │   Storage Queue      │     │
           │  │ (Serverless)│ │  Storage    │ │ (contentflow-        │     │
           │  │             │ │ (Standard   │ │  execution-requests) │     │
           │  │ 7 containers│ │  LRS, Hot)  │ │                      │     │
           │  └─────────────┘ └─────────────┘ └──────────────────────┘     │
           │                                                                │
           │  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐    │
           │  │  App Config  │ │ App Insights │ │  AI Foundry (S0)  │    │
           │  │  (Standard)  │ │ + Log Analyt.│ │  GPT-4.1          │    │
           │  │              │ │ (PerGB2018)  │ │  GPT-4.1-mini     │    │
           │  └──────────────┘ └──────────────┘ └────────────────────┘    │
           │                                                                │
           │  ┌──────────────┐ ┌──────────────┐                           │
           │  │  Container   │ │  Managed     │                           │
           │  │  Registry    │ │  Identity    │                           │
           │  │ (Standard)   │ │ (User Assign)│                           │
           │  └──────────────┘ └──────────────┘                           │
           │                                                                │
           │                    SERVICIOS DE AZURE                          │
           └────────────────────────────────────────────────────────────────┘
```

### 1.2 Principios arquitectónicos

| Principio | Implementación |
|-----------|---------------|
| **Desacoplamiento** | Los servicios se comunican a través de colas y base de datos compartida, no llamadas directas |
| **Escalabilidad horizontal** | Workers pueden escalarse independientemente (1-2 réplicas con autoescalado) |
| **Procesamiento asíncrono** | Las tareas se encolan y procesan en segundo plano |
| **Resiliencia** | Reintentos configurables (3 por defecto), timeouts, y manejo de errores por ejecutor |
| **Seguridad Zero-Trust** | Managed Identity, sin contraseñas compartidas, RBAC para cada recurso |
| **Configuración centralizada** | Azure App Configuration como fuente única de verdad |
| **Observabilidad** | Application Insights + Log Analytics para trazabilidad distribuida |

---

## 2. Componente: Interfaz Web (contentflow-web)

### 2.1 Stack tecnológico

| Tecnología | Versión | Rol |
|------------|---------|-----|
| React | 18.3.1 | Framework UI |
| TypeScript | 5.8.3 | Lenguaje tipado |
| Vite | 7.1.5 | Empaquetador y servidor de desarrollo |
| Tailwind CSS | 3.4.17 | Framework de estilos utilitarios |
| ReactFlow | 11.11.4 | Visualización de grafos (pipeline builder) |
| Monaco Editor | 4.7.0 | Editor de código YAML |
| TanStack Query | 5.83.0 | Gestión de estado del servidor |
| React Hook Form | 7.61.1 | Formularios con validación |
| Zod | 3.25.76 | Esquemas de validación TypeScript |
| Shadcn/ui + Radix UI | Múltiples | Componentes UI accesibles |
| Recharts | 2.15.4 | Gráficas y visualizaciones |
| Lucide React | 0.462.0 | Iconografía |
| js-yaml | 4.1.1 | Parsing YAML |
| date-fns | 3.6.0 | Utilidades de fecha |

### 2.2 Estructura de la aplicación

```
contentflow-web/src/
├── main.tsx                 # Punto de entrada de React
├── App.tsx                  # Componente raíz con providers y rutas
├── index.css                # Estilos globales (Tailwind)
├── components/
│   ├── ui/                  # Componentes base Shadcn/ui
│   │   ├── button.tsx       #   Botones
│   │   ├── dialog.tsx       #   Diálogos modales
│   │   ├── input.tsx        #   Campos de entrada
│   │   ├── select.tsx       #   Selectores
│   │   ├── toast.tsx        #   Notificaciones
│   │   ├── tabs.tsx         #   Pestañas
│   │   ├── card.tsx         #   Tarjetas
│   │   └── ...              #   +20 componentes más
│   ├── pipeline/            # Componentes del constructor de pipelines
│   ├── vaults/              # Componentes de gestión de vaults
│   ├── dashboard/           # Componentes del panel principal
│   ├── knowledge/           # Componentes del grafo de conocimiento
│   ├── templates/           # Componentes de plantillas
│   ├── Hero.tsx             # Sección de bienvenida
│   ├── PipelineBuilder.tsx  # Constructor visual de pipelines
│   ├── KnowledgeGraph.tsx   # Visualizador de grafos
│   ├── Footer.tsx           # Pie de página
│   └── NavLink.tsx          # Enlace de navegación
├── pages/
│   ├── Index.tsx            # Página principal (home, pipeline, vaults)
│   ├── Templates.tsx        # Galería de plantillas
│   ├── Vaults.tsx           # Gestión de vaults (ruta directa)
│   └── NotFound.tsx         # Página 404
├── hooks/                   # Custom hooks de React
├── types/                   # Definiciones de tipos TypeScript
├── lib/                     # Utilidades y configuración (cn, utils)
└── data/                    # Datos mock y constantes
```

### 2.3 Rutas y navegación

| Ruta | Componente | Vista | Descripción |
|------|-----------|-------|-------------|
| `/` | Index | home | Página principal con hero y navegación |
| `/?view=pipeline` | Index | pipeline | Constructor visual de pipelines |
| `/?view=graph` | Index | graph | Visualizador de grafos de conocimiento |
| `/?view=vaults` | Index | vaults | Gestión de bóvedas de documentos |
| `/templates` | Templates | — | Galería de plantillas pre-construidas |
| `/*` | NotFound | — | Página 404 |

### 2.4 Componentes principales de la UI

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Barra de Navegación                                     │  │
│  │  [Logo] ContentFlow  |  Home  |  Pipeline  |  Vaults  |  │  │
│  │                       Templates                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  CONTENIDO PRINCIPAL (según vista activa)                │  │
│  │                                                          │  │
│  │  ┌─ Home ──────────────────────────────────────────┐    │  │
│  │  │  Hero: Bienvenida y métricas del sistema        │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  ┌─ Pipeline Builder ──────────────────────────────┐    │  │
│  │  │  ┌───────────┐  ┌───────────────────────────┐   │    │  │
│  │  │  │ Catálogo  │  │   Lienzo ReactFlow        │   │    │  │
│  │  │  │ de        │  │   (Nodos + Aristas)       │   │    │  │
│  │  │  │ ejecutores│  │                           │   │    │  │
│  │  │  │           │  │   [Nodo A] ──▶ [Nodo B]  │   │    │  │
│  │  │  │ • Input   │  │       │                   │   │    │  │
│  │  │  │ • Extract │  │       ▼                   │   │    │  │
│  │  │  │ • Process │  │   [Nodo C] ──▶ [Nodo D]  │   │    │  │
│  │  │  │ • Output  │  │                           │   │    │  │
│  │  │  └───────────┘  └───────────────────────────┘   │    │  │
│  │  │  ┌─────────────────────────────────────────────┐│    │  │
│  │  │  │  Editor YAML (Monaco)                       ││    │  │
│  │  │  └─────────────────────────────────────────────┘│    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  ┌─ Vaults ────────────────────────────────────────┐    │  │
│  │  │  Lista de bóvedas │ Detalle │ Ejecuciones       │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Footer                                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 2.5 Gestión de estado y datos

| Librería | Responsabilidad | Patrón |
|----------|----------------|--------|
| **TanStack Query** | Estado del servidor (datos de la API) | Cache con invalidación automática |
| **React Hook Form** | Estado de formularios | Formularios controlados con validación |
| **Zod** | Validación de esquemas | Validación en tiempo de ejecución |
| **URL Query Params** | Navegación y vista activa | Estado en la URL (ej. `?view=pipeline`) |
| **React Context** | Estado global de la app (si aplica) | Provider pattern |

### 2.6 Diagrama de componentes Web

```
                 App.tsx
                    │
        ┌───────────┼───────────────┐
        │           │               │
  QueryClient   BrowserRouter   Providers
  Provider         │            (Tooltip,
        │          │             Toast,
        │    ┌─────┴──────┐     Sonner)
        │    │            │
        │  Route /     Route /templates
        │    │            │
        │  Index      Templates
        │    │
        │    ├── Hero
        │    ├── PipelineBuilder ──▶ ReactFlow + Monaco
        │    ├── KnowledgeGraph ──▶ Visualización de grafos
        │    └── Vaults ──▶ CRUD de bóvedas
        │
        └── Comunicación con API vía fetch/httpx
            (GET/POST/PUT/DELETE → /api/*)
```

---

## 3. Componente: API REST (contentflow-api)

### 3.1 Stack tecnológico

| Tecnología | Versión | Rol |
|------------|---------|-----|
| Python | 3.12+ | Runtime |
| FastAPI | 0.128.0 | Framework web asíncrono |
| Uvicorn | 0.40.0 | Servidor ASGI |
| Pydantic | 2.12+ | Validación de datos y modelos |
| pydantic-settings | 2.12.0 | Gestión de configuración |
| azure-identity | 1.25.1 | Autenticación con Managed Identity |
| azure-cosmos | 4.14.3 | Cliente Cosmos DB NoSQL |
| azure-storage-blob | 12.27.1 | Cliente Blob Storage |
| azure-storage-queue | 12.14.1 | Cliente Storage Queue |
| azure-appconfiguration-provider | 2.3.1 | Configuración centralizada |
| httpx | 0.28.1 | Cliente HTTP asíncrono |
| aiohttp | 3.13.3+ | Cliente HTTP asíncrono alternativo |
| PyYAML | 6.0.3+ | Parsing YAML |
| python-dotenv | 1.2.1+ | Variables de entorno locales |
| contentflow-lib | local | Librería de procesamiento (editable) |

### 3.2 Endpoints del API

#### Salud del sistema

| Método | Ruta | Descripción | Respuesta |
|--------|------|-------------|-----------|
| `GET` | `/api/health/` | Verificación completa de todos los servicios | `SystemHealth` |
| `GET` | `/api/health/{service}` | Verificar un servicio específico | `ServiceHealth` |

Servicios verificados: `cosmos_db`, `storage_queue`, `app_config`

#### Gestión de Pipelines

| Método | Ruta | Descripción | Request Body | Respuesta |
|--------|------|-------------|-------------|-----------|
| `GET` | `/api/pipelines/` | Listar todos los pipelines | — | `List[Pipeline]` |
| `GET` | `/api/pipelines/{id_or_name}` | Obtener por ID o nombre | — | `Pipeline` |
| `POST` | `/api/pipelines/` | Crear o actualizar pipeline | `SavePipelineRequest` | `Pipeline` |
| `DELETE` | `/api/pipelines/{id}` | Eliminar pipeline | — | `bool` |
| `POST` | `/api/pipelines/{id}/execute` | Ejecutar pipeline | `ExecutePipelineRequest` | `ExecutePipelineResponse` |

#### Gestión de Vaults

| Método | Ruta | Descripción | Parámetros | Respuesta |
|--------|------|-------------|-----------|-----------|
| `GET` | `/api/vaults/` | Listar vaults | `search`, `tags` | `List[Vault]` |
| `GET` | `/api/vaults/{id}` | Obtener vault por ID | — | `Vault` |
| `POST` | `/api/vaults/` | Crear vault | Body: `VaultCreateRequest` | `Vault` |
| `PUT` | `/api/vaults/{id}` | Actualizar vault | Body: `VaultUpdateRequest` | `Vault` |
| `DELETE` | `/api/vaults/{id}` | Eliminar vault | — | `bool` |

#### Catálogo de Ejecutores

| Método | Ruta | Descripción | Respuesta |
|--------|------|-------------|-----------|
| `GET` | `/api/executors/` | Listar todos los ejecutores | `List[ExecutorCatalogDefinition]` |
| `GET` | `/api/executors/{id}` | Obtener ejecutor por ID | `ExecutorCatalogDefinition` |

#### Raíz

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Mensaje de bienvenida y versión del API |

### 3.3 Capa de servicios

Cada servicio implementa lógica de negocio específica heredando de `BaseService`:

```
BaseService (CRUD genérico sobre Cosmos DB)
    │
    ├── PipelineService
    │   ├── get_pipelines() → List[Pipeline]
    │   ├── get_pipeline_by_id(id) → Pipeline
    │   ├── get_pipeline_by_name(name) → Pipeline
    │   ├── create_pipeline(data) → Pipeline
    │   ├── create_or_save_pipeline(data) → Pipeline
    │   ├── update_by_id(id, data) → Pipeline
    │   └── delete_pipeline_by_id(id) → bool
    │
    ├── VaultService
    │   ├── create_vault(request, pipeline_name) → Vault
    │   ├── get_vault(id) → Vault
    │   ├── list_vaults(search, tags) → List[Vault]
    │   ├── update_vault(id, request) → Vault
    │   └── delete_vault(id) → bool
    │
    ├── VaultExecutionService
    │   ├── get_vault_executions(vault_id, start, end) → List[VaultExecution]
    │   ├── get_vault_crawl_checkpoints(vault_id) → List[Checkpoint]
    │   ├── delete_vault_executions(vault_id)
    │   └── delete_vault_crawl_checkpoints(vault_id)
    │
    ├── PipelineExecutionService
    │   └── Seguimiento de ejecuciones de pipeline
    │
    ├── ExecutorCatalogService
    │   └── Gestión del catálogo de ejecutores
    │
    └── HealthService
        ├── check_all_services() → SystemHealth
        └── check_service_health(name) → ServiceHealth
```

### 3.4 Capa de base de datos

**CosmosDBClient** — Wrapper asíncrono sobre el SDK oficial de Azure Cosmos DB:

```
CosmosDBClient
    │
    ├── connect()              # Inicializar conexión con credenciales
    ├── close()                # Cerrar conexión
    │
    ├── create(container, item)           # Crear documento
    ├── get_by_id(container, id)          # Obtener por ID
    ├── list_all(container, query)        # Listar con consulta SQL
    ├── query(container, query, params)   # Consulta parametrizada
    ├── update(container, item)           # Upsert (crear o actualizar)
    ├── delete(container, id)             # Eliminar
    └── batch_upsert(container, items)    # Actualización masiva
```

**Características**:
- Autenticación via `ChainedTokenCredential` (Managed Identity)
- Creación automática de la base de datos si no existe
- Consultas cross-partition habilitadas
- Pool de conexiones compartido

### 3.5 Modelos de datos

```
CosmosBaseModel (Base)
    │
    ├── id: str (UUID v4 auto-generado)
    ├── created_at: datetime
    └── modified_at: datetime

Pipeline (Definición de pipeline)
    ├── name: str
    ├── description: str
    ├── yaml: str (definición YAML del pipeline)
    ├── nodes: List[Any] (nodos del grafo visual)
    ├── edges: List[Any] (aristas del grafo visual)
    ├── tags: List[str]
    ├── enabled: bool
    ├── retry_delay: int (segundos, default: 5)
    ├── timeout: int (segundos, default: 600)
    ├── retries: int (default: 3)
    └── version: str

PipelineExecution (Ejecución de pipeline)
    ├── pipeline_id: str
    ├── pipeline_name: str
    ├── status: ExecutionStatus (pending|running|completed|failed|cancelled)
    ├── inputs: Dict
    ├── configuration: Dict
    ├── outputs: Dict
    ├── started_at: str (ISO)
    ├── completed_at: str (ISO)
    ├── duration_seconds: float
    ├── error: str
    ├── executor_outputs: Dict[str, ExecutorOutput]
    └── events: List[PipelineExecutionEvent]

Vault (Bóveda de documentos)
    ├── name: str (1-100 caracteres)
    ├── description: str (max 500)
    ├── pipeline_id: str
    ├── pipeline_name: str
    ├── tags: List[str]
    ├── save_execution_output: bool
    ├── enabled: bool
    └── created_by: str

VaultExecution (Ejecución de vault)
    ├── pipeline_id / vault_id: str
    ├── status: pending|running|completed|failed
    ├── task_id: str
    ├── source_worker_id / processing_worker_id: str
    ├── executor_outputs: Dict
    ├── events: List[Dict]
    ├── content: List[Dict]
    └── number_of_items: int

VaultCrawlCheckpoint (Punto de control de rastreo)
    ├── pipeline_id / vault_id / executor_id: str
    ├── checkpoint_timestamp: str
    └── worker_id: str
```

### 3.6 Inyección de dependencias

FastAPI utiliza inyección de dependencias para proporcionar clientes compartidos a los routers:

```
get_config_provider() ──▶ ConfigurationProvider (Azure App Config)
        │                              │
        ▼                              ▼
get_cosmos_client() ──▶ CosmosDBClient (singleton)
        │
        ├──▶ get_pipeline_service() ──▶ PipelineService
        ├──▶ get_vault_service() ──▶ VaultService
        ├──▶ get_vault_execution_service() ──▶ VaultExecutionService
        ├──▶ get_executor_catalog_service() ──▶ ExecutorCatalogService
        ├──▶ get_pipeline_execution_service() ──▶ PipelineExecutionService
        └──▶ get_health_service() ──▶ HealthService

Todas las dependencias usan un TTL de caché de 10 minutos.
```

### 3.7 Configuración y arranque

**Fuentes de configuración** (en orden de prioridad):

1. **Variables de entorno** (ej. `.env` para desarrollo local)
2. **Azure App Configuration** (producción)
3. **Valores por defecto** (hardcoded en `settings.py`)

**Secuencia de arranque del API**:

```
main.py
  │
  ├── 1. Crear aplicación FastAPI
  ├── 2. Configurar CORS (allow_origins: ["*"])
  ├── 3. Registrar routers (/api/health, /api/pipelines, /api/vaults, /api/executors)
  │
  └── Lifespan (async context manager):
      ├── STARTUP:
      │   ├── initialize_cosmos()      → Conectar a Cosmos DB
      │   ├── initialize_blob_storage() → Inicializar Blob Storage
      │   └── initialize_executor_catalog() → Cargar catálogo de ejecutores
      │
      └── SHUTDOWN:
          └── Limpieza de recursos
```

**Configuración del servidor**:

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| Host | `0.0.0.0` | Escuchar en todas las interfaces |
| Puerto | `8090` | Puerto HTTP |
| Workers | `1` | Un proceso Uvicorn |
| Reload | `True` (en DEBUG) | Recarga automática en desarrollo |
| OpenAPI docs | `/docs` | Documentación interactiva Swagger |
| ReDoc | `/redoc` | Documentación alternativa |

### 3.8 Diagrama de capas del API

```
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                   │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ /health  │ │/pipelines│ │ /vaults  │ │/executors │  │
│  │  Router  │ │  Router  │ │  Router  │ │  Router   │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘  │
│       │            │            │              │         │
├───────┼────────────┼────────────┼──────────────┼─────────┤
│       ▼            ▼            ▼              ▼         │
│                    CAPA DE SERVICIOS                      │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ Health   │ │ Pipeline │ │  Vault   │ │ Catalog   │  │
│  │ Service  │ │ Service  │ │ Service  │ │ Service   │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘  │
│       │            │            │              │         │
├───────┼────────────┼────────────┼──────────────┼─────────┤
│       ▼            ▼            ▼              ▼         │
│                   CAPA DE DATOS                          │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              CosmosDBClient (Async)               │   │
│  │  ┌─────────────────────────────────────────────┐  │   │
│  │  │ ChainedTokenCredential (Managed Identity)   │  │   │
│  │  └─────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ BlobStorage  │  │ StorageQueue │  │  AppConfig    │  │
│  │ Client       │  │ Client       │  │  Provider     │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Componente: Worker Service (contentflow-worker)

### 4.1 Stack tecnológico

| Tecnología | Versión | Rol |
|------------|---------|-----|
| Python | 3.12+ | Runtime |
| multiprocessing | stdlib | Paralelismo de procesos |
| FastAPI | 0.128.0 | API de salud (opcional) |
| azure-storage-queue | 12.14.1 | Consumir tareas de la cola |
| azure-cosmos | 4.14.3 | Leer pipelines y actualizar estados |
| azure-storage-blob | 12.27.1 | Acceso a documentos |
| contentflow-lib | local | Motor de pipelines |

### 4.2 Arquitectura multi-proceso

El Worker utiliza el módulo `multiprocessing` de Python para ejecutar múltiples procesos independientes:

```
┌──────────────────────────────────────────────────────────┐
│                    WORKER ENGINE                          │
│                                                          │
│  ┌────────────────────────────┐                          │
│  │   Proceso Principal        │                          │
│  │   (main.py)                │                          │
│  │                            │                          │
│  │   ├── Signal Handler       │                          │
│  │   ├── WorkerEngine.run()   │                          │
│  │   └── API Thread (8099)    │                          │
│  └─────────────┬──────────────┘                          │
│                │                                          │
│    ┌───────────┴───────────────────────────┐             │
│    │                                       │             │
│    ▼                                       ▼             │
│  ┌────────────────────────┐  ┌────────────────────────┐  │
│  │  Source Worker(s)      │  │  Processing Worker(s)  │  │
│  │  (InputSourceWorker)   │  │  (ContentProcessing    │  │
│  │                        │  │   Worker)              │  │
│  │  Cantidad: N_SOURCE    │  │  Cantidad: N_PROCESS   │  │
│  │  Default: 1            │  │  Default: 0            │  │
│  │                        │  │                        │  │
│  │  Ciclo:                │  │  Ciclo:                │  │
│  │  1. Leer vaults        │  │  1. Poll cola          │  │
│  │  2. Ejecutar inputs    │  │  2. Recibir tarea      │  │
│  │  3. Descubrir contenido│  │  3. Leer pipeline      │  │
│  │  4. Crear tareas       │  │  4. Ejecutar pipeline  │  │
│  │  5. Dormir (300s)      │  │  5. Actualizar estado  │  │
│  └────────────────────────┘  └────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐   │
│  │  multiprocessing.Event (stop_event)               │   │
│  │  → Señal compartida para apagado coordinado       │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### 4.3 Worker de entrada (Input Source Worker)

**Responsabilidad**: Descubrir contenido nuevo en los orígenes de datos configurados.

**Flujo de ejecución**:

```
┌─ Bucle principal ────────────────────────────────┐
│                                                   │
│  1. Consultar Cosmos DB → vaults habilitados      │
│  2. Para cada vault:                              │
│     a. Leer pipeline asociado                     │
│     b. Obtener checkpoint más reciente            │
│     c. Ejecutar ejecutor(es) de input             │
│     d. Descubrir documentos nuevos                │
│     e. Por cada documento nuevo:                  │
│        - Crear ContentProcessingTask              │
│        - Encolar en Storage Queue                 │
│     f. Guardar nuevo checkpoint                   │
│  3. Dormir (DEFAULT_POLLING_INTERVAL_SECONDS)     │
│  4. Repetir hasta stop_event                      │
│                                                   │
└───────────────────────────────────────────────────┘
```

**Gestión de checkpoints**: El sistema implementa **rastreo incremental** para evitar reprocesar documentos:
- En la primera ejecución, no hay checkpoint (se descubren todos los documentos)
- En ejecuciones posteriores, solo se descubren documentos nuevos o modificados desde el último checkpoint
- Los checkpoints se almacenan en el contenedor `vault_crawl_checkpoints` de Cosmos DB

### 4.4 Worker de procesamiento (Content Processing Worker)

**Responsabilidad**: Ejecutar pipelines completos sobre elementos de contenido individuales.

**Flujo de ejecución**:

```
┌─ Bucle principal ────────────────────────────────┐
│                                                   │
│  1. Poll Azure Storage Queue                      │
│     (max 32 mensajes, visibilidad 300s)           │
│  2. Para cada mensaje:                            │
│     a. Deserializar ContentProcessingTask         │
│     b. Obtener bloqueo distribuido                │
│     c. Leer pipeline de Cosmos DB                 │
│     d. Crear PipelineExecutor                     │
│     e. Ejecutar pipeline (sin ejecutores input)   │
│     f. Actualizar estado en Cosmos DB             │
│     g. Eliminar mensaje de la cola                │
│  3. Si no hay mensajes → dormir (5s)              │
│  4. Repetir hasta stop_event                      │
│                                                   │
└───────────────────────────────────────────────────┘
```

### 4.5 Cliente de cola

**TaskQueueClient** — Abstracción sobre Azure Storage Queue:

```
TaskQueueClient
    │
    ├── ensure_queue_exists()
    │   → Crea la cola si no existe
    │
    ├── send_content_processing_task(task: ContentProcessingTask)
    │   → Serializa tarea → JSON → Base64 → Envía a cola
    │
    ├── send_input_source_task(task: InputSourceTask)
    │   → Serializa tarea → JSON → Base64 → Envía a cola
    │
    └── _send_message(message, visibility_timeout)
        → Envío interno con manejo de errores
```

**Formato del mensaje en cola**:
```json
{
  "task_type": "CONTENT_PROCESSING",
  "payload": {
    "pipeline_id": "abc-123",
    "vault_id": "def-456",
    "content": { ... }
  }
}
```

### 4.6 Ciclo de vida de una tarea

```
                  ┌──────────┐
                  │ PENDING  │ ← Tarea creada y encolada
                  └────┬─────┘
                       │
                  ┌────▼─────┐
                  │ RUNNING  │ ← Worker toma la tarea
                  └────┬─────┘
                       │
              ┌────────┼────────┐
              │        │        │
         ┌────▼───┐ ┌──▼───┐ ┌─▼──────┐
         │COMPLETED│ │FAILED│ │CANCELLED│
         └────────┘ └──────┘ └────────┘
              │        │
              │   ┌────▼────┐
              │   │ RETRY?  │ (max 3 reintentos)
              │   └────┬────┘
              │        │ Sí
              │   ┌────▼─────┐
              │   │ PENDING  │
              │   └──────────┘
              │
         Resultado almacenado
         en Cosmos DB + Blob
```

### 4.7 Configuración del Worker

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `WORKER_NAME` | `contentflow-worker` | Nombre del worker |
| `NUM_PROCESSING_WORKERS` | `0` | Cantidad de workers de procesamiento |
| `NUM_SOURCE_WORKERS` | `1` | Cantidad de workers de entrada |
| `QUEUE_POLL_INTERVAL_SECONDS` | `5` | Intervalo de consulta a la cola |
| `QUEUE_VISIBILITY_TIMEOUT_SECONDS` | `300` | Timeout de visibilidad (5 min) |
| `QUEUE_MAX_MESSAGES` | `32` | Máximo de mensajes por poll |
| `DEFAULT_POLLING_INTERVAL_SECONDS` | `300` | Intervalo de descubrimiento (5 min) |
| `LOCK_TTL_SECONDS` | `300` | Tiempo de vida del bloqueo distribuido |
| `MAX_TASK_RETRIES` | `3` | Reintentos máximos por tarea |
| `TASK_TIMEOUT_SECONDS` | `600` | Timeout por tarea (10 min) |
| `API_ENABLED` | `true` | Habilitar API de salud |
| `API_PORT` | `8099` | Puerto del API de salud |

### 4.8 Diagrama del motor de workers

```
┌─────────────────────────────────────────────────────────────┐
│                      WORKER ENGINE                           │
│                                                              │
│   Señales del SO ──▶ Signal Handler ──▶ stop_event.set()    │
│   (SIGINT/SIGTERM)                                          │
│                                                              │
│   ┌────────────────────────────────────────────────────┐    │
│   │  WorkerEngine.run()                                 │    │
│   │  ├── start()                                        │    │
│   │  │   ├── Crear N source workers (mp.Process)       │    │
│   │  │   └── Crear N processing workers (mp.Process)   │    │
│   │  │                                                  │    │
│   │  └── monitor loop (mientras no stop_event):         │    │
│   │      ├── Verificar procesos activos                 │    │
│   │      ├── Reemplazar workers caídos                  │    │
│   │      └── sleep(1 segundo)                          │    │
│   └────────────────────────────────────────────────────┘    │
│                                                              │
│   Apagado:                                                   │
│   1. stop_event.set()                                        │
│   2. join(timeout=30s) por cada worker                      │
│   3. terminate() workers que no respondieron                │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Componente: Librería Core (contentflow-lib)

### 5.1 Motor de pipelines

El motor de pipelines es el cerebro de ContentFlow. Convierte definiciones YAML declarativas en grafos de ejecución:

```
YAML Pipeline Definition
         │
         ▼
┌─────────────────┐
│ PipelineFactory │ ← Parsea YAML y crea instancias de ejecutores
│                 │
│ parse_yaml()    │
│ create_pipeline()│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DAG (Grafo      │ ← Grafo dirigido acíclico de ejecutores
│  Dirigido       │
│  Acíclico)      │
│                 │
│ Nodos: Ejecutors│
│ Aristas: Depend.│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│PipelineExecutor │ ← Ejecuta el DAG resolviendo dependencias
│                 │
│ execute()       │   Características:
│                 │   • Ejecución asíncrona (asyncio)
│                 │   • Resolución de dependencias
│                 │   • Evaluación de condiciones
│                 │   • Manejo de errores por ejecutor
│                 │   • Eventos de ejecución
│                 │   • Estadísticas de rendimiento
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PipelineResult  │ ← Resultado final de la ejecución
│                 │
│ status: Success │
│ outputs: {...}  │
│ events: [...]   │
│ duration: 45.2s │
└─────────────────┘
```

### 5.2 Jerarquía de clases de ejecutores

```
Executor (Agent Framework)
    │
    └── BaseExecutor (ABC) ─── contentflow/executors/base.py
        │
        │  Propiedades comunes:
        │  ├── id: str
        │  ├── settings: Dict
        │  ├── enabled: bool
        │  ├── condition: str (evaluación condicional)
        │  ├── fail_pipeline_on_error: bool
        │  └── debug_mode: bool
        │
        │  Métodos:
        │  ├── get_setting(key, default)
        │  ├── resolve_env_vars(value)
        │  ├── _evaluate_condition(content)
        │  └── process_input(input, ctx) → Content | List[Content]  [ABSTRACTO]
        │
        ├── InputExecutor (ABC) ─── contentflow/executors/input_executor.py
        │   │
        │   │  Propiedades adicionales:
        │   │  ├── polling_interval_seconds: int (300)
        │   │  ├── max_results: int (1000)
        │   │  └── batch_size: int (100)
        │   │
        │   │  Métodos:
        │   │  ├── crawl(checkpoint) → (List[Content], token)  [ABSTRACTO]
        │   │  └── crawl_all(checkpoint) → List[Content]
        │   │
        │   └── Implementaciones:
        │       └── AzureBlobInputDiscoveryExecutor
        │
        └── Ejecutores concretos (35+):
            ├── Extracción
            ├── Procesamiento IA
            ├── Transformación
            ├── Salida
            ├── Enrutamiento
            └── Especializados
```

### 5.3 Catálogo completo de ejecutores

#### Entrada y recuperación de contenido

| ID | Nombre | Descripción |
|----|--------|-------------|
| `azure_blob_input_discovery` | Azure Blob Input Discovery | Descubre archivos en contenedores Blob Storage |
| `azure_blob_content_retriever` | Azure Blob Content Retriever | Recupera el contenido de blobs descubiertos |
| `content_retriever` | Content Retriever | Recuperador genérico de contenido |

#### Extracción de documentos

| ID | Nombre | Descripción |
|----|--------|-------------|
| `pdf_extractor` | PDF Extractor | Extrae texto de documentos PDF |
| `word_extractor` | Word Extractor | Extrae texto de documentos Word (.docx) |
| `excel_extractor` | Excel Extractor | Extrae datos de hojas de cálculo Excel |
| `powerpoint_extractor` | PowerPoint Extractor | Extrae texto de presentaciones PowerPoint |
| `csv_extractor` | CSV Extractor | Extrae datos de archivos CSV |
| `azure_document_intelligence_extractor` | Azure Document Intelligence | Extracción inteligente con OCR y modelos pre-entrenados |
| `azure_content_understanding_extractor` | Azure Content Understanding | Análisis avanzado de contenido con AI |

#### Procesamiento con IA

| ID | Nombre | Descripción |
|----|--------|-------------|
| `azure_openai_agent` | Azure OpenAI Agent | Procesamiento con modelos GPT (análisis, generación) |
| `azure_openai_embeddings` | Azure OpenAI Embeddings | Genera vectores de embedding para búsqueda semántica |
| `text_summarizer` | Text Summarizer | Genera resúmenes de texto usando IA |
| `entity_extractor` | Entity Extractor | Extrae entidades nombradas (personas, organizaciones, lugares) |
| `sentiment_analyser` | Sentiment Analyser | Análisis de sentimiento (positivo, negativo, neutro) |
| `content_classifier` | Content Classifier | Clasifica contenido en categorías definidas |
| `pii_detector` | PII Detector | Detecta información personal identificable |
| `keyword_extractor` | Keyword Extractor | Extrae palabras clave y frases importantes |
| `language_detector` | Language Detector | Detecta el idioma del contenido |
| `content_translator` | Content Translator | Traduce contenido entre idiomas |

#### Transformación de datos

| ID | Nombre | Descripción |
|----|--------|-------------|
| `recursive_text_chunker` | Recursive Text Chunker | Divide texto en fragmentos con solapamiento configurable |
| `table_row_splitter` | Table Row Splitter | Divide tablas en filas individuales para procesamiento |
| `field_mapper` | Field Mapper | Mapea y transforma campos entre el modelo de contenido |
| `field_selector` | Field Selector | Selecciona campos específicos del contenido |
| `fan_in_aggregator` | Fan-In Aggregator | Agrega resultados de procesamiento paralelo |

#### Salida y almacenamiento

| ID | Nombre | Descripción |
|----|--------|-------------|
| `azure_blob_output` | Azure Blob Output | Escribe contenido procesado a Blob Storage |
| `ai_search_index_output` | AI Search Index Output | Indexa contenido en Azure AI Search |
| `gptrag_search_index_document_generator` | GPT RAG Index Generator | Genera documentos para índices RAG |

#### Enrutamiento y orquestación

| ID | Nombre | Descripción |
|----|--------|-------------|
| `subpipeline` | Sub-Pipeline | Ejecuta un sub-pipeline anidado |
| `for_each_content` | For Each Content | Itera sobre una lista de contenidos |
| `pass_through` | Pass Through | Pasa contenido sin modificar (debug/testing) |

#### Conjuntos de documentos

| ID | Nombre | Descripción |
|----|--------|-------------|
| `document_set_initializer` | Document Set Initializer | Inicializa un conjunto de documentos para procesamiento cruzado |
| `document_set_collector` | Document Set Collector | Recopila documentos en un conjunto |
| `cross_document_comparison` | Cross-Document Comparison | Compara contenido entre múltiples documentos |
| `cross_document_field_aggregator` | Cross-Document Field Aggregator | Agrega campos de múltiples documentos |

#### Especializados

| ID | Nombre | Descripción |
|----|--------|-------------|
| `web_scraper` | Web Scraper | Extrae contenido de páginas web (Playwright) |
| `cosmos_db_lookup` | Cosmos DB Lookup | Consulta datos en Azure Cosmos DB |

### 5.4 Modelo de contenido (Content)

El modelo `Content` es la estructura de datos central que fluye por los pipelines:

```
Content
│
├── Identificación
│   ├── id: str (UUID único)
│   └── source: str (origen: blob://container/path/file.pdf)
│
├── Datos extraídos
│   ├── content: str (texto completo extraído)
│   ├── content_type: str (MIME type)
│   └── content_hash: str (hash para detección de cambios)
│
├── Metadatos
│   ├── metadata: Dict[str, Any]
│   │   ├── filename, size, last_modified
│   │   ├── page_count, language
│   │   └── custom fields...
│   │
│   └── tags: List[str]
│
├── Fragmentos y embeddings
│   ├── chunks: List[Dict] (fragmentos de texto)
│   └── embeddings: List[float] (vectores numéricos)
│
├── Resultados de análisis
│   ├── analysis: Dict[str, Any]
│   │   ├── entities, sentiment, keywords
│   │   ├── summary, classification
│   │   └── pii_detected, language
│   │
│   └── executor_outputs: Dict[str, Any]
│       └── {executor_id: output_data}
│
└── Registro de ejecución
    └── log_entries: List[ExecutorLogEntry]
        └── {executor_id, timestamp, status, duration_ms}
```

### 5.5 Conectores de Azure

```
contentflow/connectors/
│
├── Azure Blob Storage Connector
│   ├── Listar blobs en contenedores
│   ├── Descargar contenido de blobs
│   ├── Subir contenido a blobs
│   └── Gestionar metadatos de blobs
│
├── Azure AI Search Connector
│   ├── Crear/actualizar índices
│   ├── Indexar documentos
│   └── Búsqueda híbrida (texto + vectores)
│
├── Azure Document Intelligence Connector
│   ├── Analizar documentos (OCR)
│   ├── Modelos pre-entrenados (facturas, recibos, etc.)
│   └── Modelos personalizados
│
├── Azure OpenAI Connector
│   ├── Completions (GPT-4.1, GPT-4.1-mini)
│   ├── Embeddings (text-embedding-3-small)
│   └── Chat completions
│
└── Azure Cosmos DB Connector
    ├── Consultas SQL NoSQL
    ├── CRUD de documentos
    └── Bulk operations
```

### 5.6 Diagrama del motor de pipelines

```
Definición YAML del Pipeline
┌──────────────────────────────────────────────────┐
│ name: procesar-documentos                         │
│ steps:                                            │
│   - executor: blob_input    ─────────┐            │
│   - executor: pdf_extractor ──────┐  │            │
│   - executor: chunker ─────────┐  │  │            │
│   - executor: embeddings ────┐ │  │  │            │
│   - executor: blob_output ─┐ │ │  │  │            │
└────────────────────────────┼─┼─┼──┼──┼────────────┘
                             │ │ │  │  │
                    PipelineFactory.parse()
                             │
                             ▼
              ┌─ DAG de ejecución ────────────┐
              │                                │
              │  [blob_input]                  │
              │       │                        │
              │       ▼                        │
              │  [pdf_extractor]               │
              │       │                        │
              │       ▼                        │
              │  [chunker]                     │
              │       │                        │
              │       ▼                        │
              │  [embeddings]                  │
              │       │                        │
              │       ▼                        │
              │  [blob_output]                 │
              │                                │
              └────────────────────────────────┘
                             │
                    PipelineExecutor.execute()
                             │
                             ▼
              ┌─ Ejecución paso a paso ───────┐
              │                                │
              │  Content ──▶ blob_input        │
              │  Content ──▶ pdf_extractor     │
              │  Content ──▶ chunker           │
              │  Content ──▶ embeddings        │
              │  Content ──▶ blob_output       │
              │                                │
              │  Cada paso:                    │
              │  1. Evaluar condición          │
              │  2. Si enabled: ejecutar       │
              │  3. Capturar resultado/error   │
              │  4. Emitir evento              │
              │  5. Pasar al siguiente         │
              │                                │
              └────────────────────────────────┘
                             │
                             ▼
                      PipelineResult
                    (status, outputs,
                     events, duration)
```

---

## 6. Infraestructura de Azure (infra)

### 6.1 Recursos desplegados

ContentFlow despliega los siguientes recursos de Azure:

```
Resource Group
│
├── User-Assigned Managed Identity (id-${token})
│
├── Log Analytics Workspace (log-${token})
│   └── Recolección de logs de todos los servicios
│
├── Application Insights (appi-${token})
│   └── Monitoreo, métricas y trazas distribuidas
│
├── Cosmos DB Account (cosmos-${token})
│   └── Database: contentflow
│       ├── executor_catalog
│       ├── pipelines
│       ├── vaults
│       ├── vault_executions
│       ├── vault_exec_locks
│       ├── vault_crawl_checkpoints
│       └── pipeline_executions
│
├── Storage Account (st${token})
│   ├── Blob Container: content
│   └── Queue: contentflow-execution-requests
│
├── Container Registry (cr${token})
│   └── Imágenes Docker de los 3 servicios
│
├── App Configuration Store (appcs-${token})
│   └── 25+ claves de configuración
│
├── Container Apps Environment (cae-${token})
│   ├── Container App: api-${token} (Puerto 8090)
│   ├── Container App: worker-${token} (Puerto 8099)
│   └── Container App: web-${token}
│
└── AI Foundry (opcional)
    ├── AI Services (S0)
    └── Deployments:
        ├── gpt-4.1-mini (GlobalStandard, Cap: 100)
        └── gpt-4.1 (GlobalStandard, Cap: 100)
```

### 6.2 SKUs y niveles de servicio

| Recurso | SKU / Nivel | Detalles |
|---------|------------|----------|
| **Cosmos DB** | Serverless | Pago por consumo, sin capacidad reservada |
| **Storage Account** | Standard_LRS | Locally Redundant Storage, Hot tier |
| **Container Registry** | Standard | Premium si se usan endpoints privados |
| **App Configuration** | Standard | Configuración centralizada |
| **Log Analytics** | PerGB2018 | Pago por GB ingerido |
| **Application Insights** | Workspace-based | Conectado a Log Analytics |
| **AI Foundry / AI Services** | S0 | Tier estándar de servicios cognitivos |
| **GPT-4.1** | GlobalStandard | Capacidad: 100 TPM |
| **GPT-4.1-mini** | GlobalStandard | Capacidad: 100 TPM |
| **Container Apps** | Consumption | Serverless, perfil de carga de trabajo por consumo |
| **Managed Identity** | User-Assigned | N/A (sin SKU, es un recurso de identidad) |

### 6.3 Módulos Bicep

| Módulo | Archivo | Azure Verified Module (AVM) | Versión AVM |
|--------|---------|----------------------------|-------------|
| Identidad administrada | `user-assigned-identity.bicep` | `avm/res/managed-identity/user-assigned-identity` | 0.4.1 |
| Log Analytics | `log-analytics-ws.bicep` | Built-in | — |
| Application Insights | `app-insights.bicep` | Built-in | — |
| Cosmos DB | `cosmos.bicep` | `avm/res/document-db/database-account` | 0.16.0 |
| Storage Account | `storage.bicep` | `avm/res/storage/storage-account` | 0.27.1 |
| Container Registry | `container-registry.bicep` | `avm/res/container-registry` | Built-in |
| Container Apps Environment | `container-apps-environment.bicep` | `avm/res/app/managed-environment` | 0.11.3 |
| Container App | `container-app.bicep` | `avm/res/app/container-app` | 0.19.0 |
| App Configuration | `app-config-store.bicep` | Built-in | — |
| AI Foundry | `ai-foundry.bicep` | `avm/ptn/ai-ml/ai-foundry` | 0.5.0 |
| Static Web App | `static-web-app.bicep` | Built-in (no activo) | — |

### 6.4 Cosmos DB — Estructura de base de datos

```
Cosmos DB Account (cosmos-${token})
│
├── Tipo: NoSQL (SQL API)
├── Consistencia: Session
├── Replicación: Región única (automaticFailover: false)
├── Backup: Continuous7Days (hasta 30 días de retención)
├── Autenticación: Solo Managed Identity (contraseñas deshabilitadas)
│
└── Database: "contentflow"
    │
    ├── executor_catalog (/id)
    │   └── Definiciones de ejecutores del catálogo
    │
    ├── pipelines (/id)
    │   └── Configuración y YAML de cada pipeline
    │
    ├── vaults (/id)
    │   └── Definiciones de bóvedas de documentos
    │
    ├── vault_executions (/id)
    │   └── Registro de ejecuciones por vault
    │
    ├── vault_exec_locks (/id)
    │   └── Bloqueos distribuidos para evitar ejecuciones duplicadas
    │
    ├── vault_crawl_checkpoints (/id)
    │   └── Puntos de control para rastreo incremental
    │
    └── pipeline_executions (/id)
        └── Historial detallado de ejecuciones de pipelines
```

### 6.5 Storage Account — Blobs y colas

```
Storage Account (st${token})
│
├── Tipo: StorageV2
├── SKU: Standard_LRS
├── Acceso: Hot tier
├── Autenticación: Solo Managed Identity (sharedKeyAccess: false)
├── Retención de eliminados: 7 días (blobs y contenedores)
│
├── Blob Containers:
│   └── "content" (acceso público: None)
│       ├── Documentos originales
│       └── Contenido procesado
│
└── Queues:
    └── "contentflow-execution-requests"
        └── Mensajes de tareas (InputSource y ContentProcessing)
```

### 6.6 Container Apps — Configuración de servicios

| Configuración | API | Worker | Web |
|---------------|-----|--------|-----|
| **Puerto** | 8090 | 8099 | HTTP estándar |
| **CPU** | 1 core | 1 core | 1 core |
| **Memoria** | 2 GiB | 2 GiB | 2 GiB |
| **Réplicas mínimas** | 1 | 1 | 1 |
| **Réplicas máximas** | 2 | 2 | 2 |
| **Ingress** | Externo | Externo | Externo |
| **Escalado** | HTTP (10 concurrentes) | HTTP (10 concurrentes) | HTTP (10 concurrentes) |
| **Health check** | `/health` (60s intervalo) | — | — |
| **CORS** | GET, POST, PUT, DELETE, OPTIONS, PATCH | GET, POST, PUT, DELETE, OPTIONS, PATCH | GET, POST, PUT, DELETE, OPTIONS, PATCH |
| **Perfil** | Consumption | Consumption | Consumption |

### 6.7 AI Foundry — Modelos de IA

```
AI Foundry
│
├── AI Services Account (S0)
│   └── Nombre del proyecto: "contentflow-project"
│
└── Model Deployments:
    │
    ├── gpt-4.1-mini
    │   ├── Formato: OpenAI
    │   ├── Versión: 2025-04-14
    │   ├── SKU: GlobalStandard
    │   └── Capacidad: 100 (TPM)
    │
    └── gpt-4.1
        ├── Formato: OpenAI
        ├── Versión: 2025-04-14
        ├── SKU: GlobalStandard
        └── Capacidad: 100 (TPM)
```

### 6.8 Diagrama de infraestructura Azure

```
┌──────────────────────────────────────────────────────────────────────┐
│                        RESOURCE GROUP                                │
│                                                                      │
│  ┌─ Identidad ─────────────┐   ┌─ Monitoreo ────────────────────┐  │
│  │                          │   │                                 │  │
│  │  Managed Identity        │   │  Log Analytics   App Insights  │  │
│  │  (User-Assigned)         │   │  (PerGB2018)     (Workspace)   │  │
│  │                          │   │                                 │  │
│  │  RBAC Roles:             │   └─────────────────────────────────┘  │
│  │  • Blob Data Contributor │                                        │
│  │  • Queue Data Contributor│   ┌─ Configuración ────────────────┐  │
│  │  • Cosmos DB Data Contrib│   │                                 │  │
│  └──────────────────────────┘   │  App Configuration (Standard)  │  │
│                                  │  25+ claves de configuración   │  │
│  ┌─ Cómputo ───────────────────┐│                                 │  │
│  │                              ││  Claves:                       │  │
│  │  Container Apps Environment  ││  • COSMOS_DB_ENDPOINT          │  │
│  │  (Consumption workload)      ││  • BLOB_STORAGE_ACCOUNT_NAME   │  │
│  │                              ││  • STORAGE_WORKER_QUEUE_URL    │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ││  • ...                         │  │
│  │  │ API  │ │Worker│ │ Web  │ │└─────────────────────────────────┘  │
│  │  │ 8090 │ │ 8099 │ │  80  │ │                                     │
│  │  │ 1CPU │ │ 1CPU │ │ 1CPU │ │  ┌─ IA ────────────────────────┐   │
│  │  │ 2GiB │ │ 2GiB │ │ 2GiB │ │  │                             │   │
│  │  └──────┘ └──────┘ └──────┘ │  │  AI Foundry (S0)            │   │
│  │                              │  │  ├── gpt-4.1-mini (100 TPM)│   │
│  │  Container Registry (Std)    │  │  └── gpt-4.1 (100 TPM)    │   │
│  │  (Imágenes Docker)           │  │                             │   │
│  └──────────────────────────────┘  └─────────────────────────────┘   │
│                                                                      │
│  ┌─ Datos ──────────────────────────────────────────────────────┐   │
│  │                                                               │   │
│  │  Cosmos DB (Serverless)    Storage Account (Standard_LRS)    │   │
│  │  ┌─────────────────────┐   ┌────────────────────────────┐    │   │
│  │  │ DB: contentflow     │   │ Blob: "content"            │    │   │
│  │  │ ├── executor_catalog│   │ Queue: "contentflow-       │    │   │
│  │  │ ├── pipelines       │   │        execution-requests" │    │   │
│  │  │ ├── vaults          │   └────────────────────────────┘    │   │
│  │  │ ├── vault_executions│                                      │   │
│  │  │ ├── vault_exec_locks│                                      │   │
│  │  │ ├── vault_crawl_    │                                      │   │
│  │  │ │   checkpoints     │                                      │   │
│  │  │ └── pipeline_       │                                      │   │
│  │  │     executions      │                                      │   │
│  │  └─────────────────────┘                                      │   │
│  └───────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7. Interconexión entre componentes

### 7.1 Flujo de datos completo

```
┌─────────┐  HTTP    ┌─────────┐  Write   ┌──────────┐  Poll    ┌──────────┐
│  WEB    │────────▶│  API    │────────▶│  QUEUE   │────────▶│ WORKER   │
│ (React) │  REST   │(FastAPI)│  Queue  │ (Azure   │  Recv   │ (Python) │
└─────────┘         └────┬────┘         │ Storage) │         └────┬─────┘
                         │               └──────────┘              │
                         │                                         │
                    ┌────▼────┐                              ┌────▼─────┐
                    │COSMOS DB│◀─────────────────────────────│ PIPELINE │
                    │(Metadat)│  Lee pipelines, actualiza    │ ENGINE   │
                    └─────────┘  estados de ejecución        │ (Lib)    │
                         │                                    └────┬─────┘
                    ┌────▼────┐                                    │
                    │  BLOB   │◀─────────────────────────────      │
                    │STORAGE  │  Lee documentos, guarda            │
                    │(Content)│  resultados procesados             │
                    └─────────┘                                    │
                                                              ┌────▼─────┐
                                                              │AZURE AI  │
                                                              │SERVICES  │
                                                              │(GPT, Doc │
                                                              │ Intell.) │
                                                              └──────────┘
```

### 7.2 Flujo de mensajes por cola

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FLUJO DE MENSAJES POR COLA                          │
│                                                                         │
│  ① API recibe solicitud de ejecución                                   │
│     POST /api/pipelines/{id}/execute                                   │
│     │                                                                   │
│     ▼                                                                   │
│  ② API crea registro de ejecución en Cosmos DB                         │
│     PipelineExecution { status: "pending" }                            │
│     │                                                                   │
│     ▼                                                                   │
│  ③ API envía InputSourceTask a la cola                                 │
│     ┌───────────────────────────────────────────┐                      │
│     │ Queue: contentflow-execution-requests      │                      │
│     │ Message: { task_type: "INPUT_SOURCE",      │                      │
│     │            payload: { pipeline_id, ... } } │                      │
│     └────────────────────┬──────────────────────┘                      │
│                          │                                              │
│  ④ Source Worker consume la tarea                                      │
│     │                                                                   │
│     ▼                                                                   │
│  ⑤ Source Worker ejecuta ejecutores de input                           │
│     → Descubre N documentos                                            │
│     │                                                                   │
│     ▼                                                                   │
│  ⑥ Source Worker crea N tareas ContentProcessingTask                   │
│     ┌───────────────────────────────────────────┐                      │
│     │ Queue: contentflow-execution-requests      │                      │
│     │ Message × N:                               │                      │
│     │ { task_type: "CONTENT_PROCESSING",         │                      │
│     │   payload: { pipeline_id, content, ... } } │                      │
│     └────────────────────┬──────────────────────┘                      │
│                          │                                              │
│  ⑦ Processing Workers consumen tareas (en paralelo)                    │
│     │                                                                   │
│     ▼                                                                   │
│  ⑧ Cada worker ejecuta el pipeline completo sobre un documento         │
│     (excluyendo ejecutores de input)                                   │
│     │                                                                   │
│     ▼                                                                   │
│  ⑨ Resultados almacenados en Blob Storage / Cosmos DB                  │
│     PipelineExecution { status: "completed" }                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Flujo de autenticación

```
┌──────────────────────────────────────────────────────────────────┐
│              CADENA DE AUTENTICACIÓN                              │
│                                                                  │
│  User-Assigned Managed Identity                                  │
│  (id-${resourceToken})                                          │
│       │                                                          │
│       ├── DefaultAzureCredential                                 │
│       │   (Cadena de credenciales automática)                   │
│       │                                                          │
│       ├──▶ Cosmos DB ──── rol: "Cosmos DB SQL Data Contributor" │
│       │    (Lectura/escritura de documentos)                     │
│       │                                                          │
│       ├──▶ Blob Storage ─ rol: "Storage Blob Data Contributor"  │
│       │    (Lectura/escritura de blobs)                          │
│       │                                                          │
│       ├──▶ Storage Queue ─ rol: "Storage Queue Data Contributor"│
│       │    (Envío/recepción de mensajes)                        │
│       │                                                          │
│       └──▶ App Config ──── rol: "App Configuration Data Reader" │
│            (Lectura de configuración)                            │
│                                                                  │
│  Nota: Contraseñas y claves compartidas están DESHABILITADAS     │
│  (disableLocalAuthentication: true, allowSharedKeyAccess: false) │
└──────────────────────────────────────────────────────────────────┘
```

### 7.4 Matriz de comunicación entre servicios

| Origen | Destino | Protocolo | Propósito |
|--------|---------|-----------|-----------|
| **Web** → API | HTTP/REST | CRUD de pipelines, vaults, catálogo |
| **API** → Cosmos DB | SDK Azure (HTTPS) | Almacenar/leer metadatos |
| **API** → Blob Storage | SDK Azure (HTTPS) | Gestionar documentos |
| **API** → Storage Queue | SDK Azure (HTTPS) | Encolar tareas |
| **API** → App Configuration | SDK Azure (HTTPS) | Leer configuración |
| **Worker** → Storage Queue | SDK Azure (HTTPS) | Consumir tareas |
| **Worker** → Cosmos DB | SDK Azure (HTTPS) | Leer pipelines, actualizar estados |
| **Worker** → Blob Storage | SDK Azure (HTTPS) | Leer/escribir contenido |
| **Worker** → Azure AI Services | SDK Azure (HTTPS) | Procesamiento IA |
| **Worker** → App Configuration | SDK Azure (HTTPS) | Leer configuración |
| **Todos** → App Insights | SDK Azure (HTTPS) | Telemetría y trazas |

### 7.5 Diagrama de secuencia: Ejecución de pipeline

```
 Usuario         Web (React)     API (FastAPI)    Cosmos DB    Storage Queue  Source Worker  Processing Worker  Azure AI
    │                │                │               │              │              │               │              │
    │ ① Crear        │                │               │              │              │               │              │
    │ pipeline       │                │               │              │               │              │              │
    │───────────────▶│                │               │              │              │               │              │
    │                │ POST /pipeline │               │              │              │               │              │
    │                │───────────────▶│               │              │              │               │              │
    │                │                │──── save ────▶│              │              │               │              │
    │                │                │◀──── ok ──────│              │              │               │              │
    │                │◀───── 201 ─────│               │              │              │               │              │
    │◀───────────────│                │               │              │              │               │              │
    │                │                │               │              │              │               │              │
    │ ② Ejecutar     │                │               │              │              │               │              │
    │───────────────▶│                │               │              │              │               │              │
    │                │ POST /execute  │               │              │              │               │              │
    │                │───────────────▶│               │              │              │               │              │
    │                │                │── save exec ─▶│              │              │               │              │
    │                │                │── queue task ─┼─────────────▶│              │               │              │
    │                │◀─── 202 ──────│               │              │              │               │              │
    │◀───────────────│                │               │              │              │               │              │
    │                │                │               │              │              │               │              │
    │                │                │               │              │ ③ poll       │               │              │
    │                │                │               │              │◀─────────────│               │              │
    │                │                │               │              │── InputTask──▶               │              │
    │                │                │               │◀─── read pipeline ──────────│               │              │
    │                │                │               │──── pipeline data ─────────▶│               │              │
    │                │                │               │              │              │               │              │
    │                │                │               │              │  ④ descubrir │               │              │
    │                │                │               │              │  N documentos│               │              │
    │                │                │               │              │◀── N tasks ──│               │              │
    │                │                │               │              │              │               │              │
    │                │                │               │              │ ⑤ poll       │               │              │
    │                │                │               │              │◀─────────────┼───────────────│              │
    │                │                │               │              │─ ContentTask─┼──────────────▶│              │
    │                │                │               │◀────────── read pipeline ───┼───────────────│              │
    │                │                │               │                              │              │              │
    │                │                │               │              │              │  ⑥ ejecutar   │              │
    │                │                │               │              │              │  pipeline     │              │
    │                │                │               │              │              │──────────────▶│──── AI ─────▶│
    │                │                │               │              │              │              │◀─── result ──│
    │                │                │               │◀──────────── update status ─┼───────────────│              │
    │                │                │               │              │              │               │              │
    │ ⑦ Consultar    │                │               │              │              │               │              │
    │───────────────▶│ GET /executions│               │              │              │               │              │
    │                │───────────────▶│── query ─────▶│              │              │               │              │
    │                │                │◀── results ───│              │              │               │              │
    │                │◀──── 200 ──────│               │              │              │               │              │
    │◀───────────────│                │               │              │              │               │              │
```

---

## 8. Modos de despliegue

### 8.1 Modo básico

```
┌─────────────────────────────────────────────────────────────┐
│                   MODO BÁSICO                                │
│                                                              │
│  Ideal para: Desarrollo, pruebas, demos                     │
│                                                              │
│  Características:                                            │
│  ✓ Endpoints públicos (accesibles desde internet)           │
│  ✓ Todos los recursos creados nuevos                        │
│  ✓ Red virtual creada automáticamente                       │
│  ✓ Log Analytics + App Insights propios                     │
│  ✗ Sin endpoints privados                                   │
│  ✗ Sin integración con redes existentes                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    INTERNET                           │   │
│  │                       │                               │   │
│  │    ┌──────────────────┼───────────────────┐          │   │
│  │    │   Container Apps Environment          │          │   │
│  │    │                  │                    │          │   │
│  │    │   ┌──────┐  ┌───┴───┐  ┌──────┐     │          │   │
│  │    │   │ Web  │  │  API  │  │Worker│     │          │   │
│  │    │   │(pub) │  │(pub)  │  │(pub) │     │          │   │
│  │    │   └──────┘  └───────┘  └──────┘     │          │   │
│  │    └──────────────────────────────────────┘          │   │
│  │                       │                               │   │
│  │    ┌──────────────────┼───────────────────┐          │   │
│  │    │     Recursos con acceso público       │          │   │
│  │    │  ┌────────┐  ┌────────┐  ┌────────┐ │          │   │
│  │    │  │CosmosDB│  │Storage │  │AppConf  │ │          │   │
│  │    │  │(public)│  │(public)│  │(public) │ │          │   │
│  │    │  └────────┘  └────────┘  └────────┘ │          │   │
│  │    └──────────────────────────────────────┘          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Modo AILZ (AI Landing Zone)

```
┌─────────────────────────────────────────────────────────────────┐
│                   MODO AILZ (AI Landing Zone)                    │
│                                                                  │
│  Ideal para: Producción empresarial                             │
│                                                                  │
│  Características:                                                │
│  ✓ Endpoints privados para todos los datos                      │
│  ✓ Integración con VNet existente                               │
│  ✓ Zonas DNS privadas                                           │
│  ✓ Shared Log Analytics + App Insights (del Landing Zone)       │
│  ✓ Container Registry Premium (endpoints privados)              │
│  ✓ Cumplimiento de seguridad empresarial                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              AI Landing Zone VNet (Existente)             │   │
│  │                                                           │   │
│  │  ┌─ aca-env-subnet ────────────────────────────────────┐ │   │
│  │  │                                                      │ │   │
│  │  │  Container Apps Environment (internal VNet)          │ │   │
│  │  │  ┌──────┐  ┌──────┐  ┌──────┐                      │ │   │
│  │  │  │ Web  │  │ API  │  │Worker│                      │ │   │
│  │  │  └──────┘  └──────┘  └──────┘                      │ │   │
│  │  │                                                      │ │   │
│  │  └──────────────────────────────────────────────────────┘ │   │
│  │                                                           │   │
│  │  ┌─ pe-subnet (Private Endpoints) ─────────────────────┐ │   │
│  │  │                                                      │ │   │
│  │  │  ┌────────┐  ┌────────┐  ┌──────────┐  ┌────────┐ │ │   │
│  │  │  │CosmosDB│  │Blob PE │  │Queue PE  │  │ACR PE  │ │ │   │
│  │  │  │  PE    │  │        │  │          │  │        │ │ │   │
│  │  │  └────────┘  └────────┘  └──────────┘  └────────┘ │ │   │
│  │  │                                                      │ │   │
│  │  └──────────────────────────────────────────────────────┘ │   │
│  │                                                           │   │
│  │  Zonas DNS Privadas:                                      │   │
│  │  • *.documents.azure.com         (Cosmos DB)             │   │
│  │  • *.blob.core.windows.net       (Blob Storage)          │   │
│  │  • *.queue.core.windows.net      (Storage Queue)         │   │
│  │  • *.azurecr.io                  (Container Registry)    │   │
│  │  • *.azconfig.io                 (App Configuration)     │   │
│  │  • *.cognitiveservices.azure.com (AI Services)           │   │
│  │  • Container Apps custom domain                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Proceso de despliegue con azd

```
$ azd up
│
├── ① pre-provision.sh
│   ├── Validar Azure CLI instalado
│   ├── Validar azd instalado
│   └── Validar Docker instalado
│
├── ② Provisionar infraestructura (Bicep)
│   ├── Crear Managed Identity
│   ├── Crear Log Analytics + App Insights (básico)
│   ├── Crear Cosmos DB + containers
│   ├── Crear Storage Account + blob + queue
│   ├── Crear Container Registry
│   ├── Crear App Configuration + claves
│   ├── Crear Container Apps Environment
│   ├── Crear Container Apps (API, Worker, Web)
│   ├── Crear AI Foundry + deployments (opcional)
│   └── Asignar roles RBAC
│
├── ③ Build y Push de imágenes Docker
│   ├── docker build contentflow-api/
│   ├── docker build contentflow-worker/
│   ├── docker build contentflow-web/
│   └── docker push → Container Registry
│
├── ④ Desplegar servicios en Container Apps
│   ├── Actualizar imagen del API
│   ├── Actualizar imagen del Worker
│   └── Actualizar imagen del Web
│
├── ⑤ post-deploy-api.sh
│   └── Configuración post-despliegue del API
│
└── ⑥ post-deploy.sh
    └── Tareas finales interactivas

Resultado: URLs de los servicios desplegados
  → API:    https://api-xxxx.azurecontainerapps.io
  → Worker: https://worker-xxxx.azurecontainerapps.io
  → Web:    https://web-xxxx.azurecontainerapps.io
```

### 8.4 Diagrama comparativo de modos

```
             MODO BÁSICO                         MODO AILZ
     ┌─────────────────────┐           ┌─────────────────────────┐
     │                     │           │                         │
     │  ☁️ Internet         │           │  ☁️ Internet (limitado)  │
     │       │              │           │       │                 │
     │  ┌────▼────┐        │           │  ┌────▼────┐           │
     │  │Container│        │           │  │Container│           │
     │  │Apps     │        │           │  │Apps     │           │
     │  │(público)│        │           │  │(VNet    │           │
     │  └────┬────┘        │           │  │internal)│           │
     │       │              │           │  └────┬────┘           │
     │  ┌────▼───┐         │           │  ┌────▼────┐           │
     │  │Recursos│         │           │  │ Private │           │
     │  │público │         │           │  │Endpoints│           │
     │  │acceso  │         │           │  │(VNet)   │           │
     │  └────────┘         │           │  └─────────┘           │
     │                     │           │                         │
     │ ✅ Rápido            │           │ ✅ Seguro               │
     │ ✅ Simple            │           │ ✅ Empresarial          │
     │ ❌ No para prod.    │           │ ❌ Requiere VNet/LZ    │
     └─────────────────────┘           └─────────────────────────┘
```

---

## 9. Seguridad y autenticación

### 9.1 Modelo de identidad

ContentFlow utiliza **Azure Managed Identity** (identidad administrada asignada por el usuario) para toda la autenticación entre servicios. No se utilizan contraseñas, claves de acceso ni cadenas de conexión.

```
┌──────────────────────────────────────────────────────┐
│         USER-ASSIGNED MANAGED IDENTITY               │
│         (id-${resourceToken})                        │
│                                                      │
│  Utilizada por:                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ API      │  │ Worker   │  │ Web      │          │
│  │ Service  │  │ Service  │  │ (build)  │          │
│  └──────────┘  └──────────┘  └──────────┘          │
│                                                      │
│  Autenticación en código:                            │
│  DefaultAzureCredential() → cadena automática:       │
│  1. Environment variables                            │
│  2. Managed Identity                                 │
│  3. Azure CLI (desarrollo local)                     │
│  4. Azure PowerShell                                 │
└──────────────────────────────────────────────────────┘
```

### 9.2 Roles RBAC asignados

| Recurso | Rol RBAC | Asignado a | Permiso |
|---------|----------|-----------|---------|
| **Cosmos DB** | Cosmos DB SQL Data Contributor | Managed Identity | Leer/escribir datos |
| **Cosmos DB** | Cosmos DB SQL Data Contributor | Deployer (principal) | Leer/escribir datos |
| **Blob Storage** | Storage Blob Data Contributor | Managed Identity | Leer/escribir blobs |
| **Blob Storage** | Storage Blob Data Contributor | Deployer (principal) | Leer/escribir blobs |
| **Storage Queue** | Storage Queue Data Contributor | Managed Identity | Enviar/recibir mensajes |
| **Storage Queue** | Storage Queue Data Contributor | Deployer (principal) | Enviar/recibir mensajes |
| **App Configuration** | App Configuration Data Reader | Managed Identity | Leer configuración |
| **Container Registry** | AcrPull | Managed Identity | Descargar imágenes |

### 9.3 Diagrama de seguridad

```
┌────────────────────────────────────────────────────────────────────┐
│                        MODELO DE SEGURIDAD                         │
│                                                                    │
│  ┌─ Autenticación ─────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  ✅ Managed Identity (sin contraseñas)                       │  │
│  │  ✅ DefaultAzureCredential (cadena automática)              │  │
│  │  ✅ disableLocalAuthentication: true (Cosmos DB)            │  │
│  │  ✅ allowSharedKeyAccess: false (Storage)                   │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─ Autorización ──────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  ✅ RBAC (Role-Based Access Control) para cada recurso      │  │
│  │  ✅ Principio de mínimo privilegio                          │  │
│  │  ✅ Roles específicos por tipo de operación                 │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─ Red (modo AILZ) ──────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  ✅ Private Endpoints para datos                            │  │
│  │  ✅ Subnets dedicadas                                       │  │
│  │  ✅ DNS privado                                             │  │
│  │  ✅ Network rules: Deny por defecto                        │  │
│  │  ✅ Bypass: AzureServices                                  │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─ Datos ─────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  ✅ Encriptación en tránsito (HTTPS/TLS)                   │  │
│  │  ✅ Encriptación en reposo (Azure managed keys)            │  │
│  │  ✅ Backup continuo (Cosmos DB: 7-30 días)                 │  │
│  │  ✅ Soft delete (Blob Storage: 7 días retención)           │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 10. Configuración centralizada

### 10.1 Azure App Configuration

Todas las configuraciones de runtime se almacenan en **Azure App Configuration** y se leen tanto por el API como por el Worker:

```
App Configuration Store (appcs-${token})
│
├── Cosmos DB
│   ├── COSMOS_DB_ENDPOINT: https://cosmos-xxx.documents.azure.com
│   ├── COSMOS_DB_NAME: contentflow
│   ├── COSMOS_DB_CONTAINER_PIPELINES: pipelines
│   ├── COSMOS_DB_CONTAINER_VAULTS: vaults
│   ├── COSMOS_DB_CONTAINER_VAULT_EXECUTIONS: vault_executions
│   ├── COSMOS_DB_CONTAINER_VAULT_EXECUTION_LOCKS: vault_exec_locks
│   ├── COSMOS_DB_CONTAINER_CRAWL_CHECKPOINTS: vault_crawl_checkpoints
│   └── COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS: pipeline_executions
│
├── Storage
│   ├── BLOB_STORAGE_ACCOUNT_NAME: stxxxx
│   ├── BLOB_STORAGE_CONTAINER_NAME: content
│   ├── STORAGE_ACCOUNT_WORKER_QUEUE_URL: https://stxxxx.queue.core.windows.net
│   └── STORAGE_WORKER_QUEUE_NAME: contentflow-execution-requests
│
├── Worker
│   ├── WORKER_ENGINE_API_ENDPOINT: https://worker-xxx.azurecontainerapps.io
│   ├── NUM_PROCESSING_WORKERS: 0
│   └── NUM_SOURCE_WORKERS: 1
│
└── Application
    ├── API_SERVER_PORT: 8090
    ├── LOG_LEVEL: DEBUG
    └── DEBUG: true
```

### 10.2 Variables de entorno por servicio

| Variable | API | Worker | Descripción |
|----------|:---:|:------:|-------------|
| `COSMOS_DB_ENDPOINT` | ✅ | ✅ | Endpoint de Cosmos DB |
| `COSMOS_DB_NAME` | ✅ | ✅ | Nombre de la base de datos |
| `BLOB_STORAGE_ACCOUNT_NAME` | ✅ | ✅ | Nombre de la cuenta de storage |
| `BLOB_STORAGE_CONTAINER_NAME` | ✅ | ✅ | Nombre del contenedor blob |
| `STORAGE_ACCOUNT_WORKER_QUEUE_URL` | ✅ | ✅ | URL de la cola |
| `STORAGE_WORKER_QUEUE_NAME` | ✅ | ✅ | Nombre de la cola |
| `API_SERVER_PORT` | ✅ | — | Puerto del API (8090) |
| `API_PORT` | — | ✅ | Puerto de health del worker (8099) |
| `NUM_PROCESSING_WORKERS` | — | ✅ | Workers de procesamiento |
| `NUM_SOURCE_WORKERS` | — | ✅ | Workers de entrada |
| `QUEUE_POLL_INTERVAL_SECONDS` | — | ✅ | Intervalo de poll (5s) |
| `DEFAULT_POLLING_INTERVAL_SECONDS` | — | ✅ | Intervalo de descubrimiento (300s) |
| `MAX_TASK_RETRIES` | — | ✅ | Reintentos por tarea (3) |
| `TASK_TIMEOUT_SECONDS` | — | ✅ | Timeout por tarea (600s) |
| `LOG_LEVEL` | ✅ | ✅ | Nivel de logging (DEBUG) |
| `DEBUG` | ✅ | ✅ | Modo debug |

---

## 11. Monitoreo y observabilidad

```
┌─────────────────────────────────────────────────────────────┐
│                   STACK DE OBSERVABILIDAD                     │
│                                                              │
│  ┌─ Application Insights ─────────────────────────────────┐ │
│  │                                                         │ │
│  │  • Trazas distribuidas entre servicios                 │ │
│  │  • Métricas de rendimiento (latencia, errores)         │ │
│  │  • Logs de aplicación (Python + React)                 │ │
│  │  • Mapa de dependencias entre componentes              │ │
│  │  • Alertas configurables                               │ │
│  │                                                         │ │
│  └─────────────────────┬───────────────────────────────────┘ │
│                        │                                      │
│  ┌─ Log Analytics ─────▼──────────────────────────────────┐  │
│  │                                                         │  │
│  │  • Logs de Container Apps (stdout/stderr)              │  │
│  │  • Logs de sistema de Container Apps Environment       │  │
│  │  • Métricas de infraestructura                         │  │
│  │  • Consultas KQL personalizables                       │  │
│  │  • Retención configurable                              │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                              │
│  Fuentes de datos:                                           │
│  ├── API Service ──────▶ Logs HTTP, latencia, errores       │
│  ├── Worker Service ───▶ Logs de procesamiento, tareas      │
│  ├── Web Service ──────▶ Logs de build, errores client-side │
│  └── Container Apps ───▶ Escalado, arranques, health checks │
└─────────────────────────────────────────────────────────────┘
```

---

## 12. Resumen de dependencias entre componentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MAPA DE DEPENDENCIAS DE CONTENTFLOW                       │
│                                                                             │
│                                                                             │
│  contentflow-web ──────────────▶ contentflow-api                           │
│  (Frontend)          HTTP/REST   (Backend)                                  │
│                                      │                                      │
│                                      ├──── azure-cosmos (SDK)              │
│                                      ├──── azure-storage-blob (SDK)        │
│                                      ├──── azure-storage-queue (SDK)       │
│                                      ├──── azure-appconfiguration (SDK)    │
│                                      └──── contentflow-lib (local)         │
│                                                  │                          │
│  contentflow-worker ─────────────────────────────┤                          │
│  (Processing)                                    │                          │
│       │                                          │                          │
│       ├──── azure-cosmos (SDK)                   │                          │
│       ├──── azure-storage-queue (SDK)       contentflow-lib                │
│       ├──── azure-storage-blob (SDK)        (Core Engine)                  │
│       └──── contentflow-lib (local) ──┐          │                          │
│                                       │          ├── Pipeline Engine        │
│                                       └──────────├── 35+ Ejecutores        │
│                                                  ├── Content Model         │
│                                                  ├── Conectores Azure      │
│                                                  │   ├── Blob Storage      │
│                                                  │   ├── AI Search         │
│                                                  │   ├── Document Intel.   │
│                                                  │   ├── OpenAI            │
│                                                  │   └── Cosmos DB         │
│                                                  └── Utilidades            │
│                                                                             │
│  infra/ (Bicep)                                                             │
│       │                                                                     │
│       └──── Aprovisiona TODOS los recursos de Azure que los                │
│             servicios anteriores consumen                                   │
│                                                                             │
│  azure.yaml                                                                 │
│       │                                                                     │
│       └──── Orquesta el despliegue de infra/ + servicios                   │
│             via Azure Developer CLI (azd)                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

> **Este documento refleja el estado de la arquitectura a la fecha de generación. Consulte el código fuente para la información más actualizada.**
