# ContentFlow — Guía General de la Solución

> **Plataforma inteligente de procesamiento de documentos y contenido construida sobre Azure.**

---

## Índice

- [1. ¿Qué es ContentFlow?](#1-qué-es-contentflow)
- [2. ¿Qué problema resuelve?](#2-qué-problema-resuelve)
- [3. Conceptos clave](#3-conceptos-clave)
  - [3.1 Pipelines](#31-pipelines)
  - [3.2 Executors (Ejecutores)](#32-executors-ejecutores)
  - [3.3 Vaults (Bóvedas de documentos)](#33-vaults-bóvedas-de-documentos)
  - [3.4 Modelo de Contenido](#34-modelo-de-contenido)
- [4. Componentes principales](#4-componentes-principales)
  - [4.1 Interfaz Web (contentflow-web)](#41-interfaz-web-contentflow-web)
  - [4.2 API REST (contentflow-api)](#42-api-rest-contentflow-api)
  - [4.3 Workers de procesamiento (contentflow-worker)](#43-workers-de-procesamiento-contentflow-worker)
  - [4.4 Librería de procesamiento (contentflow-lib)](#44-librería-de-procesamiento-contentflow-lib)
  - [4.5 Infraestructura (infra)](#45-infraestructura-infra)
- [5. ¿Cómo funciona el flujo completo?](#5-cómo-funciona-el-flujo-completo)
  - [5.1 Paso a paso: De un documento a datos inteligentes](#51-paso-a-paso-de-un-documento-a-datos-inteligentes)
  - [5.2 Diagrama de flujo general](#52-diagrama-de-flujo-general)
- [6. Servicios de Azure utilizados](#6-servicios-de-azure-utilizados)
- [7. Modos de despliegue](#7-modos-de-despliegue)
  - [7.1 Modo Básico](#71-modo-básico)
  - [7.2 Modo AILZ (AI Landing Zone)](#72-modo-ailz-ai-landing-zone)
- [8. Ejemplo práctico: Pipeline de documentos PDF](#8-ejemplo-práctico-pipeline-de-documentos-pdf)
- [9. Resumen ejecutivo](#9-resumen-ejecutivo)

---

## 1. ¿Qué es ContentFlow?

**ContentFlow** es una plataforma empresarial cloud-native diseñada para transformar contenido no estructurado (PDFs, documentos Word, hojas de Excel, presentaciones PowerPoint, páginas web, etc.) en **datos inteligentes y accionables** mediante flujos de trabajo automatizados impulsados por servicios de inteligencia artificial de Azure.

Piensa en ContentFlow como una **fábrica de procesamiento de documentos**: introduces documentos crudos por un extremo y, tras pasar por una serie de estaciones de procesamiento configurables (extracción, análisis, enriquecimiento, etc.), obtienes datos estructurados, indexados y listos para consumir.

---

## 2. ¿Qué problema resuelve?

Las organizaciones enfrentan desafíos comunes con su contenido:

| Desafío | Cómo lo resuelve ContentFlow |
|---------|------------------------------|
| Documentos en múltiples formatos (PDF, Word, Excel...) | **Ejecutores de extracción** especializados para cada formato |
| Procesamiento manual y lento | **Pipelines automatizados** que procesan contenido sin intervención |
| Necesidad de análisis inteligente | **Integración con Azure AI** (GPT-4, Document Intelligence, embeddings) |
| Escalabilidad limitada | **Arquitectura distribuida** con workers paralelos y colas de mensajes |
| Dificultad para configurar flujos | **Editor visual** drag-and-drop + definición YAML |
| Seguridad empresarial | **Identidad administrada** (Managed Identity) sin contraseñas |

---

## 3. Conceptos clave

### 3.1 Pipelines

Un **pipeline** es la unidad fundamental de trabajo en ContentFlow. Define una secuencia de pasos (ejecutores) que el contenido debe recorrer para ser procesado. Se definen en formato YAML:

```yaml
name: procesar-pdfs
steps:
  - executor: azure_blob_input_discovery    # Descubre documentos
    settings:
      blob_container_name: documentos

  - executor: pdf_extractor                  # Extrae texto del PDF

  - executor: recursive_text_chunker         # Divide en fragmentos
    settings:
      chunk_size: 1000

  - executor: azure_openai_embeddings        # Genera vectores (embeddings)
    settings:
      model: text-embedding-3-small

  - executor: azure_blob_output              # Guarda resultados
    settings:
      blob_container_name: procesados
```

### 3.2 Executors (Ejecutores)

Los **ejecutores** son las unidades de procesamiento individuales dentro de un pipeline. Cada ejecutor realiza una tarea específica. ContentFlow incluye **más de 35 ejecutores** organizados en categorías:

| Categoría | Descripción | Ejemplos |
|-----------|-------------|----------|
| **Entrada** | Descubren contenido desde orígenes de datos | Blob Storage, sistema de archivos |
| **Extracción** | Parsean documentos y extraen texto | PDF, Word, Excel, PowerPoint, CSV |
| **Procesamiento IA** | Análisis inteligente con Azure AI | Embeddings, Document Intelligence, GPT-4 |
| **Transformación** | Manipulan y enriquecen datos | Chunking, mapeo de campos, agregación |
| **Salida** | Almacenan resultados procesados | Blob Storage, Azure AI Search |
| **Enrutamiento** | Lógica condicional y paralelismo | Fan-out/Fan-in, sub-pipelines |
| **Análisis de texto** | Procesamiento de lenguaje natural | Resumen, entidades, sentimiento, PII, idioma |
| **Especializado** | Tareas de dominio específico | Web scraping, grafos de conocimiento |

### 3.3 Vaults (Bóvedas de documentos)

Un **vault** es un contenedor lógico que agrupa documentos y los asocia a un pipeline específico. Cuando el vault está habilitado, los workers automáticamente descubren nuevos documentos y los procesan según el pipeline asociado.

```
Vault "Facturas 2024"
  ├── Pipeline asociado: "procesar-facturas"
  ├── Tags: [facturas, contabilidad]
  ├── Documentos descubiertos: 1,247
  └── Estado: Habilitado ✓
```

### 3.4 Modelo de Contenido

Todo el contenido que fluye por un pipeline utiliza un **modelo estandarizado** (`Content`) que acumula datos a medida que pasa por cada ejecutor:

```
Content
  ├── id: identificador único
  ├── source: origen del documento (ej. blob://container/archivo.pdf)
  ├── content: texto extraído
  ├── metadata: información adicional del documento
  ├── chunks: fragmentos de texto
  ├── embeddings: vectores numéricos para búsqueda semántica
  └── analysis: resultados de análisis IA
```

---

## 4. Componentes principales

ContentFlow se compone de **5 componentes principales** que trabajan de forma coordinada:

```
┌─────────────────────────────────────────────────────────────────┐
│                        ContentFlow                              │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌───────────┐  │
│  │   Web    │──▶│   API    │──▶│  Workers  │──▶│  Librería │  │
│  │  (React) │   │ (FastAPI)│   │ (Python)  │   │  (Python) │  │
│  └──────────┘   └────┬─────┘   └─────┬─────┘   └───────────┘  │
│                      │               │                          │
│                      ▼               ▼                          │
│               ┌──────────────────────────────┐                  │
│               │   Infraestructura Azure      │                  │
│               │  (Cosmos DB, Blob, Queue,    │                  │
│               │   AI Services, Container     │                  │
│               │   Apps, App Configuration)   │                  │
│               └──────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.1 Interfaz Web (contentflow-web)

La **interfaz web** es una aplicación React moderna que permite a los usuarios interactuar visualmente con ContentFlow:

- **Constructor visual de pipelines**: Editor drag-and-drop basado en ReactFlow para diseñar pipelines gráficamente
- **Editor YAML**: Editor de código Monaco con resaltado de sintaxis para definir pipelines
- **Gestión de Vaults**: Crear, editar y monitorear bóvedas de documentos
- **Galería de plantillas**: Pipelines pre-construidos listos para usar
- **Panel de ejecuciones**: Ver el estado y resultados del procesamiento en tiempo real

**Tecnologías**: React 18, TypeScript, Vite, Tailwind CSS, Shadcn/ui, ReactFlow, Monaco Editor

### 4.2 API REST (contentflow-api)

El **servicio API** es el punto central de coordinación. Recibe solicitudes de la interfaz web y orquesta las operaciones:

- **Gestión de pipelines**: Crear, leer, actualizar, eliminar y ejecutar pipelines
- **Gestión de vaults**: Administrar bóvedas de documentos
- **Catálogo de ejecutores**: Explorar los ejecutores disponibles y sus configuraciones
- **Verificación de salud**: Monitorear el estado de todos los servicios dependientes

**Tecnologías**: FastAPI, Python 3.12+, Uvicorn, Pydantic, Azure SDK

**Puerto**: 8090

### 4.3 Workers de procesamiento (contentflow-worker)

Los **workers** son el motor de ejecución distribuida. Procesan el contenido de forma asíncrona utilizando múltiples procesos:

- **Workers de entrada (Source Workers)**: Descubren contenido nuevo en los orígenes de datos configurados
- **Workers de procesamiento (Processing Workers)**: Ejecutan los pipelines sobre cada elemento de contenido

**Funcionamiento simplificado**:
```
Worker de Entrada                     Worker de Procesamiento
      │                                        │
      ├── Lee vaults habilitados               ├── Consulta la cola
      ├── Ejecuta ejecutores de entrada        ├── Recibe tarea
      ├── Descubre documentos nuevos           ├── Lee el pipeline
      └── Crea tareas en la cola               └── Ejecuta pipeline
                                                    sobre el contenido
```

**Tecnologías**: Python 3.12+, multiprocessing, Azure Storage Queue

**Puerto**: 8099 (API de salud)

### 4.4 Librería de procesamiento (contentflow-lib)

La **librería** es el corazón técnico de ContentFlow. Contiene:

- **Motor de pipelines**: Parsea YAML y ejecuta grafos dirigidos acíclicos (DAG)
- **+35 ejecutores**: Implementaciones listas para usar
- **Modelo de contenido**: Estructura de datos estandarizada
- **Conectores Azure**: Clientes para Blob, Cosmos DB, AI Search, OpenAI, Document Intelligence

Esta librería se instala como dependencia en el API y el Worker.

### 4.5 Infraestructura (infra)

Plantillas **Bicep** (Infrastructure as Code) para aprovisionar todos los recursos de Azure necesarios. Se despliega con un solo comando `azd up`.

---

## 5. ¿Cómo funciona el flujo completo?

### 5.1 Paso a paso: De un documento a datos inteligentes

```
 ① USUARIO                    ② API                        ③ COLA
 ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
 │ Crea o edita│  ─────────▶  │ Almacena en │  ─────────▶  │ Encola      │
 │ un pipeline │   REST API   │ Cosmos DB y │   Storage    │ tarea de    │
 │ y ejecuta   │              │ crea tarea  │   Queue      │ descubrir   │
 └─────────────┘              └─────────────┘              └──────┬──────┘
                                                                  │
 ⑥ RESULTADOS                 ⑤ PROCESAMIENTO              ④ DESCUBRIMIENTO
 ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
 │ Datos en    │  ◀─────────  │ Ejecuta cada│  ◀─────────  │ Worker lee  │
 │ Blob Storage│   Guardado   │ ejecutor del│   Cola de    │ el origen y │
 │ y Cosmos DB │              │ pipeline    │   tareas     │ lista docs  │
 └─────────────┘              └─────────────┘              └─────────────┘
```

**Flujo detallado**:

1. **El usuario** crea un pipeline (visualmente o en YAML) y lo ejecuta desde la interfaz web
2. **La API** recibe la solicitud, guarda la configuración en Cosmos DB y crea un registro de ejecución
3. **La API** envía una tarea de tipo `InputSource` a la cola de Azure Storage
4. **El Worker de Entrada** lee la tarea, ejecuta los ejecutores de entrada del pipeline y descubre los documentos disponibles
5. **Por cada documento** descubierto, el Worker de Entrada crea una tarea `ContentProcessing` en la cola
6. **Los Workers de Procesamiento** toman las tareas de la cola y ejecutan el pipeline completo (extracción → transformación → análisis → salida) sobre cada documento
7. **Los resultados** se almacenan en Blob Storage y/o Cosmos DB
8. **El usuario** puede monitorear el progreso y ver los resultados desde la interfaz web

### 5.2 Diagrama de flujo general

```
┌─────────────┐     HTTP/REST      ┌─────────────────┐
│             │ ──────────────────▶ │                 │
│  Frontend   │                    │    API Service   │
│  (React)    │ ◀────────────────── │    (FastAPI)    │
│             │     Respuestas     │                 │
└─────────────┘                    └───────┬─────────┘
                                           │
                           ┌───────────────┼──────────────────┐
                           │               │                  │
                           ▼               ▼                  ▼
                    ┌────────────┐  ┌────────────┐   ┌──────────────┐
                    │  Cosmos DB │  │    Blob    │   │ Storage      │
                    │ (Metadatos │  │  Storage   │   │ Queue        │
                    │ y estado)  │  │(Documentos)│   │ (Tareas)     │
                    └──────┬─────┘  └─────┬──────┘   └───────┬──────┘
                           │              │                   │
                           ▼              ▼                   ▼
                    ┌─────────────────────────────────────────────────┐
                    │               Worker Service                    │
                    │  ┌─────────────────┐  ┌──────────────────────┐ │
                    │  │ Source Workers   │  │ Processing Workers   │ │
                    │  │ (Descubrimiento) │  │ (Ejecución pipeline) │ │
                    │  └────────┬────────┘  └──────────┬───────────┘ │
                    │           │                       │             │
                    │           ▼                       ▼             │
                    │  ┌────────────────────────────────────────────┐ │
                    │  │        contentflow-lib                     │ │
                    │  │  (Motor de pipelines + 35+ Ejecutores)    │ │
                    │  └────────────────────┬───────────────────────┘ │
                    └───────────────────────┼─────────────────────────┘
                                            │
                                            ▼
                              ┌──────────────────────────┐
                              │    Azure AI Services     │
                              │  ┌──────┐  ┌──────────┐ │
                              │  │GPT-4 │  │ Document │ │
                              │  │OpenAI│  │ Intelli- │ │
                              │  │      │  │ gence    │ │
                              │  └──────┘  └──────────┘ │
                              └──────────────────────────┘
```

---

## 6. Servicios de Azure utilizados

| Servicio de Azure | Propósito en ContentFlow | SKU / Nivel |
|-------------------|--------------------------|-------------|
| **Azure Container Apps** | Hospeda los 3 servicios (API, Worker, Web) | Consumption (serverless) |
| **Azure Cosmos DB** | Base de datos para metadatos, pipelines, ejecuciones | Serverless |
| **Azure Blob Storage** | Almacena documentos y contenido procesado | Standard_LRS, Hot |
| **Azure Storage Queue** | Cola de mensajes para distribución de tareas | Incluido en Storage |
| **Azure App Configuration** | Configuración centralizada de todos los servicios | Standard |
| **Azure Container Registry** | Registro de imágenes Docker | Standard (Premium con endpoints privados) |
| **Azure Log Analytics** | Workspace de logs y telemetría | PerGB2018 |
| **Azure Application Insights** | Monitoreo y diagnósticos | Conectado a Log Analytics |
| **Azure AI Foundry** | Plataforma de modelos de IA | S0 |
| **GPT-4.1 / GPT-4.1-mini** | Modelos de lenguaje para análisis inteligente | GlobalStandard, Capacidad: 100 |
| **Azure Document Intelligence** | Extracción inteligente de documentos (OCR) | Según integración |
| **Managed Identity** | Autenticación sin contraseñas entre servicios | User-Assigned |

---

## 7. Modos de despliegue

ContentFlow soporta dos modos de despliegue para adaptarse a diferentes necesidades:

### 7.1 Modo Básico

Ideal para **desarrollo, pruebas y demos**:

- Endpoints públicos accesibles desde internet
- Red virtual creada automáticamente
- Todos los recursos se crean nuevos
- Sin endpoints privados
- Despliegue rápido y sencillo

```bash
DEPLOYMENT_MODE=basic
azd up
```

### 7.2 Modo AILZ (AI Landing Zone)

Diseñado para **entornos de producción empresarial**:

- Se integra con una Azure AI Landing Zone existente
- Endpoints privados para todos los servicios
- Red virtual compartida con subnets dedicadas
- Zonas DNS privadas para resolución interna
- Cumplimiento con estándares de seguridad empresarial

```bash
DEPLOYMENT_MODE=ailz-integrated
azd up
```

```
┌─────────────────────────────────────────────────────────┐
│                  AI Landing Zone VNet                     │
│                                                          │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │  aca-env-subnet  │    │    pe-subnet              │   │
│  │  ┌────────────┐  │    │  ┌──────┐  ┌──────────┐  │   │
│  │  │ Container  │  │    │  │Cosmos│  │ Storage  │  │   │
│  │  │ Apps (API, │  │    │  │  DB  │  │ Account  │  │   │
│  │  │ Worker,Web)│  │    │  │(PE)  │  │  (PE)    │  │   │
│  │  └────────────┘  │    │  └──────┘  └──────────┘  │   │
│  └──────────────────┘    └──────────────────────────┘   │
│                                                          │
│  PE = Private Endpoint                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Ejemplo práctico: Pipeline de documentos PDF

A continuación, un ejemplo concreto de cómo ContentFlow procesa un conjunto de documentos PDF para crear un índice de búsqueda inteligente:

**Pipeline: "Indexación de documentos PDF"**

```yaml
name: indexacion-pdf
steps:
  # 1. Descubrir PDFs en Blob Storage
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: documentos-legales
      file_extensions: [".pdf"]

  # 2. Recuperar contenido del blob
  - executor: azure_blob_content_retriever

  # 3. Extraer texto con Azure Document Intelligence
  - executor: azure_document_intelligence_extractor
    settings:
      model_id: prebuilt-layout

  # 4. Dividir en fragmentos manejables
  - executor: recursive_text_chunker
    settings:
      chunk_size: 1000
      chunk_overlap: 200

  # 5. Generar vectores para búsqueda semántica
  - executor: azure_openai_embeddings
    settings:
      model: text-embedding-3-small

  # 6. Indexar en Azure AI Search
  - executor: ai_search_index_output
    settings:
      index_name: documentos-legales-index
```

**Resultado**: Cada PDF se convierte en fragmentos indexados con vectores semánticos, listos para búsquedas inteligentes tipo "¿cuáles son las cláusulas de rescisión?".

---

## 9. Resumen ejecutivo

| Aspecto | Detalle |
|---------|---------|
| **Tipo de solución** | Plataforma de procesamiento de contenido empresarial |
| **Arquitectura** | Microservicios, event-driven, cloud-native |
| **Nube** | Microsoft Azure |
| **Servicios** | 3 contenedores: API, Worker, Web |
| **Motor de IA** | GPT-4.1, Document Intelligence, Embeddings |
| **Base de datos** | Cosmos DB (Serverless) |
| **Almacenamiento** | Azure Blob Storage |
| **Mensajería** | Azure Storage Queue |
| **Ejecutores disponibles** | 35+ ejecutores pre-construidos |
| **Formatos soportados** | PDF, Word, Excel, PowerPoint, CSV, HTML, web |
| **Seguridad** | Managed Identity, RBAC, sin contraseñas |
| **Despliegue** | `azd up` — un solo comando |
| **Modos** | Básico (desarrollo) o AILZ (producción empresarial) |

---

> **ContentFlow** simplifica el camino desde documentos crudos hasta datos inteligentes, combinando la potencia de Azure AI con una arquitectura escalable y una experiencia de usuario intuitiva.
