# Validación de Salud de Servicios en ContentFlow

> **Documento técnico** — Arquitectura completa del sistema de health checks, flujo de validación servicio por servicio, y configuraciones necesarias para que funcione correctamente en modo `ailz-integrated` (conectividad privada).

---

## Tabla de Contenidos

1. [Resumen del Sistema de Health Checks](#1-resumen-del-sistema-de-health-checks)
2. [Arquitectura del Flujo de Validación](#2-arquitectura-del-flujo-de-validación)
3. [Componente Web: Footer y Diálogo de System Health](#3-componente-web-footer-y-diálogo-de-system-health)
4. [API: Router de Health y Endpoint `/api/health`](#4-api-router-de-health-y-endpoint-apihealth)
5. [API: HealthService — Lógica de Validación por Servicio](#5-api-healthservice--lógica-de-validación-por-servicio)
   - [5.1 App Configuration](#51-app-configuration)
   - [5.2 Cosmos DB](#52-cosmos-db)
   - [5.3 Blob Storage](#53-blob-storage)
   - [5.4 Storage Queue](#54-storage-queue)
   - [5.5 Worker Engine](#55-worker-engine)
6. [Worker: Validación de Startup y Endpoint `/status`](#6-worker-validación-de-startup-y-endpoint-status)
7. [Container Apps: Liveness Probes (Infraestructura)](#7-container-apps-liveness-probes-infraestructura)
8. [Configuración de la Variable `VITE_API_BASE_URL`](#8-configuración-de-la-variable-vite_api_base_url)
9. [Diagnóstico en Modo AILZ-Integrated](#9-diagnóstico-en-modo-ailz-integrated)
   - [9.1 Problema: Todos los Servicios Aparecen Offline](#91-problema-todos-los-servicios-aparecen-offline)
   - [9.2 Problema: API Conectada pero Servicios Backend en Error](#92-problema-api-conectada-pero-servicios-backend-en-error)
   - [9.3 Problema: Worker Engine en Error](#93-problema-worker-engine-en-error)
10. [Requisitos de Conectividad por Servicio](#10-requisitos-de-conectividad-por-servicio)
11. [Configuraciones Requeridas para AILZ](#11-configuraciones-requeridas-para-ailz)
12. [Comandos de Verificación Manual](#12-comandos-de-verificación-manual)

---

## 1. Resumen del Sistema de Health Checks

ContentFlow implementa un sistema de validación de salud en **tres niveles**:

| Nivel | Componente | Propósito | Frecuencia |
|---|---|---|---|
| **UI (Frontend)** | `Footer.tsx` | Muestra estado visual de cada servicio al usuario | Cada 10 minutos + al cargar |
| **API (Backend)** | `HealthService` | Valida conectividad real a cada servicio Azure | Bajo demanda (llamada de la UI) |
| **Infraestructura** | Liveness Probes | Container Apps valida que los containers estén vivos | Cada 60 segundos |

### Servicios Validados

El sistema valida **6 componentes**:

| Servicio | Qué Valida | Método de Validación |
|---|---|---|
| **API Service** | Que el frontend puede alcanzar el API | HTTP GET a `/api/health` |
| **App Configuration** | Conectividad al store de configuración | Listar keys con prefijo `contentflow.app.*` |
| **Cosmos DB** | Conectividad a la base de datos | Leer propiedades del database |
| **Blob Storage** | Acceso al container de documentos | Obtener propiedades del container |
| **Storage Queue** | Acceso a la cola de trabajo | Obtener propiedades de la queue |
| **Worker Engine** | Que el worker está corriendo | HTTP GET a `https://{worker-fqdn}/status` |

### Estados Posibles

| Estado | Indicador Visual | Significado |
|---|---|---|
| **connected** | 🟢 Verde | Todos los servicios responden correctamente |
| **degraded** | 🟡 Amarillo | Algunos servicios están con error pero no todos |
| **offline** | 🔴 Rojo | Todos los servicios con error o API inalcanzable |

---

## 2. Arquitectura del Flujo de Validación

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              NAVEGADOR                                   │
│                                                                         │
│  Footer.tsx                                                             │
│  ┌─────────────────┐                                                    │
│  │ System Health ●  │  ← Indicador visual en el footer                  │
│  └────────┬────────┘                                                    │
│           │ click                                                       │
│  ┌────────▼────────┐                                                    │
│  │ Dialog con 6    │  ← Muestra detalle por servicio                    │
│  │ ServiceHealth   │                                                    │
│  │ Items           │                                                    │
│  └────────┬────────┘                                                    │
│           │ HTTP GET                                                    │
│           │ {VITE_API_BASE_URL}/health                                  │
└───────────┼─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  API Container App (api-{token})                                         │
│  Puerto: 8090                                                            │
│                                                                         │
│  FastAPI Router: /api/health                                             │
│  ┌──────────────────────────────┐                                       │
│  │ health_router.get("/")      │                                        │
│  │ → HealthService              │                                       │
│  │   .check_all_services()      │                                       │
│  └──────────┬───────────────────┘                                       │
│             │ asyncio.gather (5 checks en paralelo)                     │
│             │                                                           │
│  ┌──────────▼───────────────────────────────────────────┐               │
│  │                                                       │              │
│  │  ┌─────────────┐  ┌──────────┐  ┌───────────────┐    │              │
│  │  │ App Config  │  │ Cosmos DB│  │ Blob Storage  │    │              │
│  │  │ list keys   │  │ read db  │  │ get container │    │              │
│  │  └──────┬──────┘  └────┬─────┘  └──────┬────────┘    │              │
│  │         │              │               │              │              │
│  │  ┌──────┴──────┐  ┌───┴────────────┐                 │              │
│  │  │ Storage Q   │  │ Worker Engine  │                  │              │
│  │  │ get props   │  │ GET /status    │                  │              │
│  │  └──────┬──────┘  └───┬────────────┘                  │              │
│  └─────────┼──────────────┼───────────────────────────────┘              │
└────────────┼──────────────┼──────────────────────────────────────────────┘
             │              │
             ▼              ▼
┌────────────────┐  ┌─────────────────────────────────────┐
│ Azure Services │  │ Worker Container App (worker-{token})│
│ (via PE en     │  │ Puerto: 8099                         │
│  AILZ mode)    │  │ GET /status → WorkerStatusResponse   │
└────────────────┘  └─────────────────────────────────────┘
```

---

## 3. Componente Web: Footer y Diálogo de System Health

**Archivo:** `contentflow-web/src/components/Footer.tsx`

### Cómo Funciona

1. El componente `Footer` se monta al cargar la aplicación
2. Después de **5 segundos** de espera inicial, ejecuta el primer health check
3. Luego repite el check cada **10 minutos** (600,000 ms)
4. El usuario puede forzar un refresh manual desde el diálogo

### Flujo del Check

```typescript
// Footer.tsx — Lógica principal
const checkHealth = async () => {
  try {
    const healthData = await getHealthCheck();  // GET {VITE_API_BASE_URL}/health
    
    // Si llegamos aquí, el API es alcanzable
    setSystemHealth({
      api: "connected",
      systemOverall: healthData.status,    // "connected" | "degraded" | "offline"
      appConfig: healthData.services.app_config?.status,
      cosmosDB: healthData.services.cosmos_db?.status,
      blobStorage: healthData.services.blob_storage?.status,
      storageQueue: healthData.services.storage_queue?.status,
      worker: healthData.services.worker?.status,
      serviceDetails: { ... }  // Detalles expandibles por servicio
    });
  } catch (error) {
    // Si el fetch falla → TODO se marca como offline
    // Esto significa que el navegador no puede alcanzar el API
    setSystemHealth({ api: "offline", systemOverall: "offline", ... });
  }
};
```

### Qué Muestra el Diálogo

Cada servicio se muestra como un item expandible (`ServiceHealthItem`) que incluye:

- **Nombre del servicio** y indicador de color (verde/rojo)
- **Endpoint** consultado (expandible)
- **Tiempo de respuesta** en milisegundos
- **Mensaje** de resultado
- **Error** detallado si falló (en rojo)
- **Detalles** adicionales (JSON con metadatos del servicio)
- **Última verificación** (timestamp)

### URL de Conexión al API

La Web UI construye la URL del API usando la variable de entorno **`VITE_API_BASE_URL`**:

```typescript
// apiClient.ts
const defaultConfig: ApiConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8090/api/',
};
```

**Esto es crítico en modo AILZ** — ver [sección 8](#8-configuración-de-la-variable-vite_api_base_url).

---

## 4. API: Router de Health y Endpoint `/api/health`

**Archivo:** `contentflow-api/app/routers/health.py`

### Endpoints Disponibles

| Endpoint | Método | Descripción |
|---|---|---|
| `GET /api/health/` | GET | Validación completa de **todos** los servicios |
| `GET /api/health/{service_name}` | GET | Validación de un servicio específico |

### Respuesta del Endpoint `/api/health/`

```json
{
  "status": "connected | degraded | error",
  "services": {
    "app_config": {
      "name": "app_config",
      "status": "connected | error",
      "message": "Connected successfully",
      "error": null,
      "details": { "config_items_count": 5, "credential_type": "azure_credential" },
      "response_time_ms": 120,
      "last_checked": "2026-03-28T10:30:00Z",
      "endpoint": "https://appcs-r7b6gtdiob4em.azconfig.io"
    },
    "cosmos_db": { "..." },
    "blob_storage": { "..." },
    "storage_queue": { "..." },
    "worker": { "..." }
  },
  "checked_at": "2026-03-28T10:30:00Z",
  "summary": { "connected": 5, "error": 0, "total": 5 }
}
```

### Lógica de Estado General

```python
# Determinación del estado overall
statuses = [service.status for service in services.values()]
if all(status == "connected" for status in statuses):
    overall_status = "connected"      # TODO bien → 🟢
elif all(status == "error" for status in statuses):
    overall_status = "error"          # TODO mal → 🔴
else:
    overall_status = "degraded"       # Algunos bien, algunos mal → 🟡
```

### Inyección de Dependencias

El `HealthService` se construye con los valores de configuración de App Config:

```python
# dependencies.py
def get_health_service():
    app_settings = get_settings()
    return HealthService(
        cosmos_endpoint=app_settings.COSMOS_DB_ENDPOINT,
        cosmos_db_name=app_settings.COSMOS_DB_NAME,
        blob_storage_account=app_settings.BLOB_STORAGE_ACCOUNT_NAME,
        blob_storage_container=app_settings.BLOB_STORAGE_CONTAINER_NAME,
        storage_account_worker_queue_url=app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
        storage_worker_queue_name=app_settings.STORAGE_WORKER_QUEUE_NAME,
        worker_engine_api_endpoint=app_settings.WORKER_ENGINE_API_ENDPOINT
    )
```

Estos valores se cargan de **Azure App Configuration** al iniciar la API, usando las keys con prefijo `contentflow.common.*` y `contentflow.api.*`.

---

## 5. API: HealthService — Lógica de Validación por Servicio

**Archivo:** `contentflow-api/app/services/health_service.py`

Todos los checks se ejecutan **en paralelo** usando `asyncio.gather()`, lo que minimiza el tiempo de respuesta total.

---

### 5.1 App Configuration

**Método:** `_check_app_config_health()`

**Qué valida:**
1. Que `AZURE_APP_CONFIG_ENDPOINT` o `AZURE_APP_CONFIG_CONNECTION_STRING` existan como variable de entorno
2. Que se pueda conectar al store
3. Que se puedan listar keys con filtro `contentflow.app.*`

**Cómo se conecta:**
- Si existe `AZURE_APP_CONFIG_CONNECTION_STRING` → usa connection string
- Si existe `AZURE_APP_CONFIG_ENDPOINT` → usa `DefaultAzureCredential` (Managed Identity)

**Qué puede fallar en AILZ:**
- App Config tiene `publicNetworkAccess: Disabled`
- La API container app necesita resolver `appcs-{token}.azconfig.io` → IP privada del Private Endpoint
- Si la Private DNS Zone `privatelink.azconfig.io` no tiene el A record correcto, falla

**Ejemplo de error típico:**
```json
{
  "status": "error",
  "message": "Connection failed: ServiceRequestError",
  "error": "Cannot connect to host appcs-r7b6gtdiob4em.azconfig.io:443"
}
```

---

### 5.2 Cosmos DB

**Método:** `_check_cosmos_db_health()`

**Qué valida:**
1. Que `COSMOS_DB_ENDPOINT` esté configurado (no vacío)
2. Conectividad al endpoint de Cosmos DB
3. Que el database especificado (`contentflow`) exista
4. Lectura de propiedades del database (operación de solo lectura)

**Cómo se conecta:**
- Usa `CosmosClient` con `DefaultAzureCredential` (Managed Identity del Container App)
- Endpoint: `https://cosmos-{token}.documents.azure.com:443/`

**Qué puede fallar en AILZ:**
- Cosmos DB tiene `publicNetworkAccess: Disabled`
- Requiere Private Endpoint resolviendo a IP privada via `privatelink.documents.azure.com`
- Requiere que la Managed Identity tenga rol `Cosmos DB Built-in Data Contributor`

**Ejemplo de error típico:**
```json
{
  "status": "error",
  "message": "Connection failed: CosmosHttpResponseError",
  "error": "Request blocked by network rules"
}
```

---

### 5.3 Blob Storage

**Método:** `_check_blob_storage_health()`

**Qué valida:**
1. Que `BLOB_STORAGE_ACCOUNT_NAME` y `BLOB_STORAGE_CONTAINER_NAME` estén configurados
2. Conectividad a la cuenta de storage
3. Que el container `content` exista
4. Lee propiedades del container (last_modified, lease_status)

**Cómo se conecta:**
- Construye URL: `https://{account}.blob.core.windows.net`
- Usa `BlobServiceClient` con `DefaultAzureCredential`

**Qué puede fallar en AILZ:**
- Storage tiene `publicNetworkAccess: Disabled`
- Requiere Private Endpoint blob resolviendo via `privatelink.blob.core.windows.net`
- Requiere rol `Storage Blob Data Contributor` en la Managed Identity

---

### 5.4 Storage Queue

**Método:** `_check_storage_queue_health()`

**Qué valida:**
1. Que `STORAGE_ACCOUNT_WORKER_QUEUE_URL` esté configurado
2. Conectividad al servicio de colas
3. Que la queue `contentflow-execution-requests` exista
4. Lee propiedades de la queue (approximate_message_count)

**Cómo se conecta:**
- Usa `QueueServiceClient` con `DefaultAzureCredential`
- URL: `https://{account}.queue.core.windows.net`

**Qué puede fallar en AILZ:**
- Requiere Private Endpoint queue resolviendo via `privatelink.queue.core.windows.net`
- Si la DNS Zone Group del queue PE no se creó correctamente, no hay A record
- Requiere rol `Storage Queue Data Contributor`

**Nota importante:** La Private DNS Zone para queue (`privatelink.queue.core.windows.net`) puede no haberse pasado al Bicep si `existingQueuePrivateDnsZoneId` no estaba en `main.parameters.json`. Es un gap conocido — ver [sección 11](#11-configuraciones-requeridas-para-ailz).

---

### 5.5 Worker Engine

**Método:** `_check_worker_health()`

**Qué valida:**
1. Que el Worker Container App esté corriendo y responda
2. Llama a `GET https://{worker-fqdn}/status`
3. Valida que el response tenga status 200
4. Extrae: `running`, `worker_name`, `processing_workers`, `source_workers`

**Cómo se conecta:**
- Usa `aiohttp` para hacer HTTP GET al FQDN interno del Worker
- Endpoint configurado en App Config: `contentflow.api.WORKER_ENGINE_API_ENDPOINT`
- Valor típico: `https://worker-{token}.internal.{domain}.azurecontainerapps.io`
- Timeout: 5 segundos

**Qué puede fallar en AILZ:**
- El API Container App necesita resolver el FQDN interno del Worker Container App
- En AILZ, los FQDNs tienen formato `*.internal.{defaultDomain}`, resolubles solo dentro del CAE o del VNet con Private DNS Zone
- La comunicación entre Container Apps **dentro del mismo CAE** funciona sin necesidad de DNS Zone externa — el CAE resuelve internamente
- Si la key `WORKER_ENGINE_API_ENDPOINT` en App Config tiene un FQDN incorrecto, falla

**Ejemplo de error típico:**
```json
{
  "status": "error",
  "message": "Worker health check failed: ClientConnectorError",
  "error": "Cannot connect to host worker-r7b6gtdiob4em.internal.delightfulwave-2b288efe.eastus2.azurecontainerapps.io:443"
}
```

---

## 6. Worker: Validación de Startup y Endpoint `/status`

**Archivos:** `contentflow-worker/app/startup.py`, `contentflow-worker/app/api.py`

### Validación al Iniciar (StartupValidator)

Antes de aceptar trabajo, el Worker ejecuta 4 validaciones:

| Check | Qué Valida | Consecuencia si Falla |
|---|---|---|
| **Settings Validation** | Que todas las configuraciones requeridas existen | Worker no inicia |
| **Cosmos DB Connectivity** | Conexión al endpoint, database existe | Worker no inicia |
| **Cosmos DB Containers** | Que los 5 containers requeridos existen | Worker no inicia |
| **Storage Queue Connectivity** | Conexión a la queue, queue existe | Worker no inicia |

Si cualquier check falla, el Worker **no inicia** y loguea los errores detallados.

### Health Endpoints del Worker

| Endpoint | Descripción |
|---|---|
| `GET /` | Info básica del servicio |
| `GET /health` | Health check simple (solo verifica que el API responde) |
| `GET /status` | Estado detallado del engine (workers running, counts) |

El endpoint `/status` es el que usa el API `HealthService` para validar el Worker.

### Monitoreo Interno de Workers

El `WorkerEngine` tiene un loop que cada **30 segundos** verifica si los worker processes siguen vivos:

```python
def _check_worker_health(self):
    # Si un processing worker murió, lo reinicia
    for i, worker in enumerate(self.processing_workers):
        if not worker.is_alive() and not self.stop_event.is_set():
            new_worker = self._create_processing_worker(i)
            new_worker.start()
    
    # Lo mismo para source workers
```

---

## 7. Container Apps: Liveness Probes (Infraestructura)

**Archivo:** `infra/bicep/modules/container-app.bicep`

### Configuración del Liveness Probe

Cada Container App tiene un probe HTTP configurado por Bicep:

```bicep
probes: [
  {
    type: 'Liveness'
    httpGet: {
      path: livenessProbePath   // '/' para los 3 servicios
      port: targetPort          // 8090 (API), 8099 (Worker), 8080 (Web)
    }
    initialDelaySeconds: 5      // Espera 5s antes del primer check
    periodSeconds: 60           // Verifica cada 60 segundos
  }
]
```

| Container App | Probe Path | Puerto | Qué Responde |
|---|---|---|---|
| API (`api-{token}`) | `/` | 8090 | FastAPI root endpoint |
| Worker (`worker-{token}`) | `/` | 8099 | FastAPI root endpoint |
| Web (`web-{token}`) | `/` | 8080 | nginx sirve `index.html` |

### Diferencia con el Health Check de la UI

- **Liveness Probe**: Lo ejecuta Azure Container Apps. Si falla 3 veces consecutivas, reinicia el container. Solo verifica que el proceso responde.
- **Health Check de la UI**: Lo ejecuta el navegador del usuario → API → servicios backend. Verifica conectividad a cada servicio Azure.

---

## 8. Configuración de la Variable `VITE_API_BASE_URL`

Esta variable es **el puente fundamental** entre la Web UI y el API. Si está mal configurada, todos los servicios aparecen offline.

### Cómo se Configura

**En Bicep** (al crear el Web Container App):
```bicep
// main.bicep, línea ~663
environmentVariables: [
  {
    name: 'VITE_API_BASE_URL'
    value: 'https://${apiContainerApp.outputs.fqdn}/api/'
  }
]
```

**En el Dockerfile** (runtime replacement):
```dockerfile
# Build time: se escribe placeholder
RUN echo "VITE_API_BASE_URL=API_URL" > .env

# Runtime: entrypoint.sh reemplaza el placeholder en los JS compilados
sed -i "s|API_URL|${VITE_API_BASE_URL:-}|g" "$file"
```

### Valor en Modo AILZ

En modo `ailz-integrated`, el FQDN del API tiene formato interno:
```
https://api-r7b6gtdiob4em.internal.delightfulwave-2b288efe.eastus2.azurecontainerapps.io/api/
```

**El problema:** Este FQDN solo es resolvible dentro del VNet (o si existe la Private DNS Zone del CAE). Cuando el usuario abre la Web UI en su navegador:

1. El **navegador** (corriendo en el JumpBox o máquina del usuario) intenta hacer `fetch()` a esa URL
2. La resolución DNS de ese FQDN debe funcionar **desde la máquina del navegador**
3. Si la Private DNS Zone para `delightfulwave-2b288efe.eastus2.azurecontainerapps.io` no existe o no está vinculada al VNet → DNS falla → todo aparece offline

### Con Application Gateway

Cuando hay un App Gateway como intermediario, el flujo cambia:

```
Navegador → App Gateway IP → /api/* → API Container App (interno)
```

En este escenario, `VITE_API_BASE_URL` debería apuntar al **App Gateway**, no directamente al API Container App. Esto requiere:

1. El App Gateway tiene una IP (pública o privada) accesible desde el navegador
2. La Web UI está configurada para llamar al App Gateway
3. El App Gateway hace path-based routing: `/api/*` → API backend

**Opciones de configuración:**

| Escenario | `VITE_API_BASE_URL` | Funciona Desde |
|---|---|---|
| AILZ sin App Gateway | `https://api-{token}.internal.{domain}/api/` | Solo JumpBox (si DNS resuelve) |
| AILZ con App Gateway (IP privada) | `https://{appgw-private-ip}/api/` o dominio custom | Dentro del VNet |
| AILZ con App Gateway (IP pública) | `https://{dominio-publico}/api/` | Cualquier lugar |
| Relativo (recomendado con AppGW) | `/api/` | Donde sea que el usuario acceda |

**Recomendación para AILZ con App Gateway:** Usar path relativo `/api/` como `VITE_API_BASE_URL`, así el navegador usa el mismo host por el que accedió a la web. Esto funciona porque el App Gateway enruta `/*` → Web y `/api/*` → API.

---

## 9. Diagnóstico en Modo AILZ-Integrated

### 9.1 Problema: Todos los Servicios Aparecen Offline

**Síntoma:** El indicador en el footer está 🔴, el diálogo muestra todo en rojo.

**Causa más probable:** El navegador **no puede alcanzar** el API Container App.

**Verificación:**

```bash
# Desde el JumpBox, verificar que el FQDN del API resuelve
nslookup api-r7b6gtdiob4em.internal.delightfulwave-2b288efe.eastus2.azurecontainerapps.io

# Si NO resuelve → falta Private DNS Zone para el dominio del CAE
# Si SÍ resuelve → verificar que el API responde
curl -k https://api-r7b6gtdiob4em.internal.delightfulwave-2b288efe.eastus2.azurecontainerapps.io/api/health
```

**Causa raíz:** No existe Private DNS Zone para `delightfulwave-2b288efe.eastus2.azurecontainerapps.io` (el dominio dinámico del CAE) vinculada al VNet.

**Solución:** El equipo de plataforma debe crear:
1. Private DNS Zone: `delightfulwave-2b288efe.eastus2.azurecontainerapps.io`
2. A record: `*` → `10.0.195.200` (CAE static IP)
3. VNet link al VNet del AILZ

**Nota:** La DNS Zone `privatelink.azurecontainerapps.io` que ya existe en el AILZ es para el **management plane** de Container Apps, no para los FQDNs de las aplicaciones. Los FQDNs de las apps usan el dominio dinámico del CAE.

---

### 9.2 Problema: API Conectada pero Servicios Backend en Error

**Síntoma:** API está 🟢, pero Cosmos DB, Storage, App Config están 🔴.

**Causa más probable:** Los Private Endpoints no tienen A records en las DNS Zones, o la Managed Identity no tiene los roles RBAC correctos.

**Verificación:**

```bash
# Verificar que los A records existen en cada DNS Zone
az network private-dns record-set a list \
  -g {AILZ_RG} -z "privatelink.documents.azure.com" -o table

az network private-dns record-set a list \
  -g {AILZ_RG} -z "privatelink.blob.core.windows.net" -o table

az network private-dns record-set a list \
  -g {AILZ_RG} -z "privatelink.azconfig.io" -o table
```

**Si faltan A records:** Los DNS Zone Groups no se crearon correctamente. Los módulos en `main.bicep` incluyen DNS Zone Groups explícitos como workaround por incompatibilidades de AVM. Verificar que se ejecutaron:

```bash
# Verificar DNS Zone Groups de private endpoints
az network private-endpoint dns-zone-group list \
  --endpoint-name "{storageAccountName}-blob-pe" \
  -g {CF_RG} -o table
```

**Si los A records existen pero sigue fallando:** Verificar RBAC:

```bash
# Listar roles de la Managed Identity
az role assignment list \
  --assignee {MANAGED_IDENTITY_PRINCIPAL_ID} \
  --scope "/subscriptions/{sub}/resourceGroups/{CF_RG}" \
  -o table
```

---

### 9.3 Problema: Worker Engine en Error

**Síntoma:** Todos los servicios están 🟢 excepto Worker Engine que está 🔴.

**Causa más probable:** El API Container App no puede alcanzar el Worker Container App, o el valor de `WORKER_ENGINE_API_ENDPOINT` en App Config es incorrecto.

**Verificación:**

```bash
# Verificar qué valor tiene WORKER_ENGINE_API_ENDPOINT en App Config
az appconfig kv show \
  --name {APP_CONFIG_NAME} \
  --key "contentflow.api.WORKER_ENGINE_API_ENDPOINT" \
  --auth-mode login \
  -o tsv --query value
```

**Debe ser:** `https://worker-{token}.internal.{defaultDomain}` (en modo AILZ el FQDN incluye `.internal.`).

**Si el valor es correcto:** La comunicación entre containers del mismo CAE es interna y no requiere DNS Zone externa. Verificar que el Worker está corriendo:

```bash
# Ver logs del Worker
az containerapp logs show \
  -n worker-{token} -g {CF_RG} --type system

# Ver si el container está healthy
az containerapp show -n worker-{token} -g {CF_RG} \
  --query "properties.runningStatus"
```

**Nota sobre post-provision.sh:** En modo AILZ, la key `WORKER_ENGINE_API_ENDPOINT` se configura via `post-provision.sh` que corre desde el JumpBox. Este script toma el valor de `azd env get-value WORKER_ENDPOINT` y lo sube a App Config. Si `post-provision.sh` no corrió o se saltó, esta key puede estar vacía o con un valor incorrecto.

---

## 10. Requisitos de Conectividad por Servicio

Mapa completo de lo que necesita cada health check para funcionar en modo AILZ:

| Servicio | Endpoint que Contacta | DNS Zone Requerida | RBAC Requerido | PE Name |
|---|---|---|---|---|
| App Config | `appcs-{token}.azconfig.io` | `privatelink.azconfig.io` | `App Configuration Data Reader` | `{appcs}-pe` |
| Cosmos DB | `cosmos-{token}.documents.azure.com` | `privatelink.documents.azure.com` | `Cosmos DB Built-in Data Contributor` | `{cosmos}-pe` |
| Blob Storage | `{storage}.blob.core.windows.net` | `privatelink.blob.core.windows.net` | `Storage Blob Data Contributor` | `{storage}-blob-pe` |
| Storage Queue | `{storage}.queue.core.windows.net` | `privatelink.queue.core.windows.net` | `Storage Queue Data Contributor` | `{storage}-queue-pe` |
| Worker | `worker-{token}.internal.{domain}` | N/A (intra-CAE) | N/A | N/A |
| API (desde Web) | `api-{token}.internal.{domain}` | `{defaultDomain}` del CAE | N/A | N/A |

### Cadena Completa para que el Health Check Funcione

```
1. Navegador → puede resolver FQDN del API (o IP del App Gateway)
2. Navegador → HTTPS al API container
3. API → puede resolver endpoints de cada servicio Azure via Private DNS
4. API → Managed Identity tiene roles RBAC para leer cada servicio
5. API → puede resolver FQDN del Worker (intra-CAE, automático)
6. Worker → está corriendo y respondiendo en /status
```

Si **cualquier** eslabón de esta cadena falla, el servicio aparece en error.

---

## 11. Configuraciones Requeridas para AILZ

### Checklist de Configuración

#### Infraestructura (Bicep/equipo de plataforma)

- [ ] Private Endpoint creado para cada servicio (Storage blob, Storage queue, Cosmos, App Config, ACR)
- [ ] DNS Zone Group existente en cada Private Endpoint (crea A record automáticamente)
- [ ] Private DNS Zones vinculadas al VNet del AILZ
- [ ] Private DNS Zone para el dominio dinámico del CAE (`{defaultDomain}`)
- [ ] Wildcard A record (`*`) apuntando al CAE static IP en la DNS Zone del CAE
- [ ] Container Apps Environment configurado como `internal: true`
- [ ] Managed Identity con roles RBAC necesarios asignados

#### App Configuration Keys (post-provision.sh)

Estas keys deben existir en App Config para que `HealthService` funcione:

| Key | Valor Esperado |
|---|---|
| `contentflow.common.COSMOS_DB_ENDPOINT` | `https://cosmos-{token}.documents.azure.com:443/` |
| `contentflow.common.COSMOS_DB_NAME` | `contentflow` |
| `contentflow.common.BLOB_STORAGE_ACCOUNT_NAME` | `st{token}` |
| `contentflow.common.BLOB_STORAGE_CONTAINER_NAME` | `content` |
| `contentflow.common.STORAGE_ACCOUNT_WORKER_QUEUE_URL` | `https://st{token}.queue.core.windows.net/` |
| `contentflow.common.STORAGE_WORKER_QUEUE_NAME` | `contentflow-execution-requests` |
| `contentflow.api.WORKER_ENGINE_API_ENDPOINT` | `https://worker-{token}.internal.{domain}` |

#### Variables de Entorno del Container App

| Container App | Variable | Valor |
|---|---|---|
| API | `AZURE_APP_CONFIG_ENDPOINT` | `https://appcs-{token}.azconfig.io` |
| API | `AZURE_CLIENT_ID` | Client ID de la Managed Identity |
| Worker | `AZURE_APP_CONFIG_ENDPOINT` | `https://appcs-{token}.azconfig.io` |
| Worker | `AZURE_CLIENT_ID` | Client ID de la Managed Identity |
| Web | `VITE_API_BASE_URL` | `https://api-{token}.internal.{domain}/api/` (o `/api/` si usa App Gateway) |

### Gap Conocido: Queue Private DNS Zone

El parámetro `existingQueuePrivateDnsZoneId` existe en `main.bicep` pero **no está mapeado** en `main.parameters.json`. Esto puede causar que el Private Endpoint de queue no tenga A record en la DNS Zone, haciendo que el health check de Storage Queue falle. Solución: agregar el mapeo al parameters file o configurar vía `azd env set`.

---

## 12. Comandos de Verificación Manual

### Desde el JumpBox: Verificar DNS de Todos los Servicios

```bash
#!/bin/bash
# verify-health-dns.sh
# Ejecutar desde el JumpBox para verificar que todos los endpoints resuelven

RESOURCE_TOKEN="r7b6gtdiob4em"
CAE_DOMAIN="delightfulwave-2b288efe.eastus2.azurecontainerapps.io"

echo "=== Verificación DNS para Health Checks ==="

echo ""
echo "[1/7] API Container App (Web → API)"
nslookup api-${RESOURCE_TOKEN}.internal.${CAE_DOMAIN}

echo ""
echo "[2/7] Worker Container App (API → Worker)"
nslookup worker-${RESOURCE_TOKEN}.internal.${CAE_DOMAIN}

echo ""
echo "[3/7] Web Container App (Navegador → Web)"
nslookup web-${RESOURCE_TOKEN}.internal.${CAE_DOMAIN}

echo ""
echo "[4/7] App Configuration"
nslookup appcs-${RESOURCE_TOKEN}.azconfig.io

echo ""
echo "[5/7] Cosmos DB"
nslookup cosmos-${RESOURCE_TOKEN}.documents.azure.com

echo ""
echo "[6/7] Blob Storage"
STORAGE_NAME=$(echo "st${RESOURCE_TOKEN}" | cut -c1-24)
nslookup ${STORAGE_NAME}.blob.core.windows.net

echo ""
echo "[7/7] Queue Storage"
nslookup ${STORAGE_NAME}.queue.core.windows.net

echo ""
echo "=== Todos los endpoints deben resolver a IPs privadas (10.x.x.x) ==="
```

### Desde el JumpBox: Probar Health Check Directamente

```bash
# Probar el endpoint de health del API
curl -sk https://api-r7b6gtdiob4em.internal.delightfulwave-2b288efe.eastus2.azurecontainerapps.io/api/health/ | python3 -m json.tool

# Probar un servicio específico
curl -sk https://api-r7b6gtdiob4em.internal.delightfulwave-2b288efe.eastus2.azurecontainerapps.io/api/health/cosmos_db | python3 -m json.tool

# Probar el worker directamente
curl -sk https://worker-r7b6gtdiob4em.internal.delightfulwave-2b288efe.eastus2.azurecontainerapps.io/status | python3 -m json.tool
```

### Verificar App Config Keys

```bash
APP_CONFIG_NAME="appcs-r7b6gtdiob4em"

# Listar todas las keys relevantes
az appconfig kv list \
  --name $APP_CONFIG_NAME \
  --key "contentflow.*" \
  --auth-mode login \
  --query "[].{key:key, value:value}" \
  -o table
```

### Verificar A Records en DNS Zones

```bash
AILZ_RG="rg-mini-ailz"  # Ajustar al nombre real

DNS_ZONES=(
  "privatelink.blob.core.windows.net"
  "privatelink.queue.core.windows.net"
  "privatelink.documents.azure.com"
  "privatelink.azconfig.io"
  "privatelink.azurecr.io"
)

for ZONE in "${DNS_ZONES[@]}"; do
  echo "=== $ZONE ==="
  az network private-dns record-set a list -g $AILZ_RG -z "$ZONE" \
    --query "[].{name:name, ip:aRecords[0].ipv4Address}" -o table
  echo ""
done
```

---

**Última actualización:** Marzo 2026  
**Aplica a:** ContentFlow v0.1.0, modo `ailz-integrated`
