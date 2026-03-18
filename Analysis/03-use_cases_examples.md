# ContentFlow — Casos de Uso y Ejemplos

> **Catálogo de escenarios implementables con el acelerador ContentFlow**, organizados por industria y función, con los ejecutores recomendados para cada caso.

---

## Índice

- [1. Procesamiento de facturas y recibos](#1-procesamiento-de-facturas-y-recibos)
- [2. Indexación inteligente de contenido](#2-indexación-inteligente-de-contenido)
- [3. Análisis de contratos](#3-análisis-de-contratos)
- [4. Grafos de conocimiento evolutivos](#4-grafos-de-conocimiento-evolutivos)
- [5. Procesamiento de formularios](#5-procesamiento-de-formularios)
- [6. Cumplimiento normativo y gestión de riesgos](#6-cumplimiento-normativo-y-gestión-de-riesgos)
- [7. Procesamiento de contenido web](#7-procesamiento-de-contenido-web)
- [8. Análisis de imagen y contenido visual](#8-análisis-de-imagen-y-contenido-visual)
- [9. Procesamiento de adjuntos de correo electrónico](#9-procesamiento-de-adjuntos-de-correo-electrónico)
- [10. Ingestión de contenido para GPT-RAG](#10-ingestión-de-contenido-para-gpt-rag)
- [11. Resumen de artículos y reportes](#11-resumen-de-artículos-y-reportes)
- [12. Traducción de contenido multilingüe](#12-traducción-de-contenido-multilingüe)
- [13. Resumen de ejecutores por caso de uso](#13-resumen-de-ejecutores-por-caso-de-uso)
- [14. Pipelines de ejemplo incluidos en el repositorio](#14-pipelines-de-ejemplo-incluidos-en-el-repositorio)

---

## 1. Procesamiento de facturas y recibos

Automatiza la extracción de datos estructurados de facturas, recibos y órdenes de compra usando Azure Content Understanding.

**Capacidades**:
- Extraer datos estructurados de facturas usando Azure Content Understanding
- Clasificar documentos por tipo (factura, recibo, orden de compra)
- Validar campos extraídos y señalar anomalías
- Exportar a sistemas ERP o bases de datos

**Pipeline sugerido**:

```yaml
name: procesamiento-facturas
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: facturas-entrantes
      file_extensions: [".pdf", ".png", ".jpg"]

  - executor: azure_blob_content_retriever

  - executor: azure_content_understanding_extractor
    settings:
      model_id: prebuilt-invoice

  - executor: content_classifier
    settings:
      categories: ["factura", "recibo", "orden_de_compra"]

  - executor: field_mapper
    settings:
      mappings:
        vendor_name: "proveedor"
        total_amount: "monto_total"
        invoice_date: "fecha_factura"

  - executor: azure_blob_output
    settings:
      blob_container_name: facturas-procesadas
```

**Ejecutores clave**: `azure_content_understanding_extractor`, `content_classifier`, `field_mapper`, `azure_blob_output`

---

## 2. Indexación inteligente de contenido

Procesa documentos, imágenes, audio y video para generar embeddings vectoriales e indexar en Azure AI Search, habilitando búsqueda semántica empresarial.

**Capacidades**:
- Procesar documentos en múltiples formatos (PDF, Word, Excel, PowerPoint)
- Generar vectores de embedding para búsqueda semántica
- Indexar contenido en Azure AI Search
- Habilitar búsqueda semántica en todo el contenido empresarial

**Pipeline sugerido**:

```yaml
name: indexacion-inteligente
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: documentos-empresa

  - executor: azure_blob_content_retriever

  - executor: azure_document_intelligence_extractor
    settings:
      model_id: prebuilt-layout

  - executor: recursive_text_chunker
    settings:
      chunk_size: 1000
      chunk_overlap: 200

  - executor: azure_openai_embeddings
    settings:
      model: text-embedding-3-small

  - executor: ai_search_index_output
    settings:
      index_name: contenido-empresarial
```

**Ejecutores clave**: `azure_document_intelligence_extractor`, `recursive_text_chunker`, `azure_openai_embeddings`, `ai_search_index_output`

---

## 3. Análisis de contratos

Extrae cláusulas clave, identifica partes involucradas, fechas, montos, y genera resúmenes automáticos para revisión legal.

**Capacidades**:
- Extraer cláusulas clave y obligaciones contractuales
- Identificar partes, fechas y valores monetarios
- Señalar términos riesgosos usando análisis de IA
- Generar resúmenes para revisión legal

**Pipeline sugerido**:

```yaml
name: analisis-contratos
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: contratos

  - executor: azure_blob_content_retriever

  - executor: pdf_extractor

  - executor: entity_extractor
    settings:
      entity_types: ["persona", "organizacion", "fecha", "monto"]

  - executor: azure_openai_agent
    settings:
      model: gpt-4.1
      prompt: |
        Analiza este contrato y extrae:
        1. Cláusulas clave y obligaciones
        2. Términos riesgosos o inusuales
        3. Fechas límite y vencimientos
        4. Valores monetarios y condiciones de pago

  - executor: text_summarizer
    settings:
      max_length: 500
      style: "resumen ejecutivo legal"

  - executor: azure_blob_output
    settings:
      blob_container_name: contratos-analizados
```

**Ejecutores clave**: `pdf_extractor`, `entity_extractor`, `azure_openai_agent`, `text_summarizer`

---

## 4. Grafos de conocimiento evolutivos

Construye grafos de conocimiento que mapean entidades, relaciones y estructuras organizativas a partir de documentos corporativos.

**Capacidades**:
- Extraer entidades (personas, organizaciones, productos, ubicaciones)
- Identificar relaciones (trabaja_en, gestiona, ubicado_en)
- Mapear estructuras organizativas
- Descubrir conexiones ocultas entre documentos

**Pipeline sugerido**:

```yaml
name: grafo-conocimiento
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: documentos-corporativos

  - executor: azure_blob_content_retriever

  - executor: azure_document_intelligence_extractor

  - executor: recursive_text_chunker
    settings:
      chunk_size: 2000

  - executor: entity_extractor
    settings:
      entity_types: ["persona", "organizacion", "producto", "ubicacion"]

  - executor: azure_openai_agent
    settings:
      model: gpt-4.1
      prompt: |
        A partir de las entidades extraídas, identifica relaciones como:
        - trabaja_en, gestiona, reporta_a
        - ubicado_en, opera_en
        - provee, compra_a, compite_con
        Devuelve las relaciones en formato estructurado.

  - executor: azure_blob_output
    settings:
      blob_container_name: grafos-conocimiento
```

**Ejecutores clave**: `entity_extractor`, `azure_openai_agent`, `document_set_initializer`, `cross_document_comparison`

---

## 5. Procesamiento de formularios

Automatiza la captura y validación de datos de formularios, solicitudes, reclamaciones y aplicaciones.

**Capacidades**:
- Procesar solicitudes, reclamaciones y formularios
- Extraer campos estructurados con ejecutores de IA
- Validar completitud y precisión de los datos
- Enrutar al sistema de línea de negocio (LoB) apropiado

**Pipeline sugerido**:

```yaml
name: procesamiento-formularios
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: formularios-entrantes

  - executor: azure_blob_content_retriever

  - executor: azure_content_understanding_extractor
    settings:
      model_id: prebuilt-document

  - executor: field_selector
    settings:
      fields: ["nombre", "fecha", "tipo_solicitud", "monto", "descripcion"]

  - executor: azure_openai_agent
    settings:
      model: gpt-4.1-mini
      prompt: |
        Valida los campos extraídos:
        - ¿Están todos los campos obligatorios presentes?
        - ¿Los formatos son correctos (fechas, montos)?
        - Señala campos faltantes o inconsistentes.

  - executor: content_classifier
    settings:
      categories: ["solicitud_credito", "reclamacion_seguro", "solicitud_empleo"]

  - executor: azure_blob_output
    settings:
      blob_container_name: formularios-procesados
```

**Ejecutores clave**: `azure_content_understanding_extractor`, `field_selector`, `content_classifier`, `azure_openai_agent`

---

## 6. Cumplimiento normativo y gestión de riesgos

Detecta información personal identificable (PII), clasifica documentos por sensibilidad y señala problemas de cumplimiento.

**Capacidades**:
- Detectar PII (Información Personalmente Identificable)
- Clasificar documentos por nivel de sensibilidad
- Señalar problemas de cumplimiento normativo
- Extraer entidades clave y temas sensibles

**Pipeline sugerido**:

```yaml
name: cumplimiento-riesgos
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: documentos-revision

  - executor: azure_blob_content_retriever

  - executor: pdf_extractor

  - executor: pii_detector
    settings:
      pii_types: ["nombre", "email", "telefono", "numero_seguro_social",
                   "tarjeta_credito", "direccion", "fecha_nacimiento"]

  - executor: content_classifier
    settings:
      categories: ["publico", "interno", "confidencial", "restringido"]

  - executor: azure_openai_agent
    settings:
      model: gpt-4.1
      prompt: |
        Analiza el documento para cumplimiento normativo:
        - ¿Contiene información regulada (GDPR, HIPAA, PCI-DSS)?
        - ¿Se manejan datos sensibles correctamente?
        - Identifica riesgos potenciales de cumplimiento.
        Genera un reporte con nivel de riesgo: bajo, medio, alto, crítico.

  - executor: azure_blob_output
    settings:
      blob_container_name: reportes-cumplimiento
```

**Ejecutores clave**: `pii_detector`, `content_classifier`, `entity_extractor`, `azure_openai_agent`

---

## 7. Procesamiento de contenido web

Extrae, traduce y corrige contenido de sitios web para alimentar soluciones de chat basadas en RAG o sitios multilingües.

**Capacidades**:
- Extraer contenido de sitios web para soluciones de chat basadas en RAG
- Traducir contenido web para experiencias multilingües
- Identificar y corregir errores ortográficos y de contenido

**Pipeline sugerido**:

```yaml
name: procesamiento-web
steps:
  - executor: web_scraper
    settings:
      urls:
        - "https://docs.empresa.com"
        - "https://soporte.empresa.com"
      max_depth: 3
      selectors: ["article", "main", ".content"]

  - executor: recursive_text_chunker
    settings:
      chunk_size: 1500

  - executor: language_detector

  - executor: content_translator
    settings:
      target_language: "es"

  - executor: azure_openai_embeddings
    settings:
      model: text-embedding-3-small

  - executor: ai_search_index_output
    settings:
      index_name: contenido-web-rag
```

**Ejecutores clave**: `web_scraper`, `language_detector`, `content_translator`, `azure_openai_embeddings`

---

## 8. Análisis de imagen y contenido visual

Digitaliza notas clínicas manuscritas, extrae texto de reportes visuales y analiza imágenes de daños para procesamiento automatizado de reclamaciones.

**Capacidades**:

| Industria | Aplicación |
|-----------|-----------|
| **Salud** | Digitalizar notas clínicas manuscritas, extraer texto de reportes, generar descripciones de imágenes médicas para registros electrónicos de salud y cumplimiento de accesibilidad |
| **Seguros** | Procesar formularios manuscritos de reclamaciones, extraer datos de fotos de accidentes, analizar imágenes de evaluación de daños para procesamiento automatizado |

**Pipeline sugerido**:

```yaml
name: analisis-visual-seguros
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: reclamaciones-fotos
      file_extensions: [".jpg", ".png", ".pdf"]

  - executor: azure_blob_content_retriever

  - executor: azure_content_understanding_extractor
    settings:
      model_id: prebuilt-document

  - executor: azure_openai_agent
    settings:
      model: gpt-4.1
      prompt: |
        Analiza esta imagen/documento de reclamación de seguro:
        - Identifica el tipo de daño visible
        - Estima la severidad (leve, moderado, severo)
        - Extrae información del formulario de reclamación
        - Señala cualquier inconsistencia

  - executor: content_classifier
    settings:
      categories: ["vehicular", "propiedad", "salud", "vida"]

  - executor: azure_blob_output
    settings:
      blob_container_name: reclamaciones-procesadas
```

**Ejecutores clave**: `azure_content_understanding_extractor`, `azure_openai_agent`, `content_classifier`

---

## 9. Procesamiento de adjuntos de correo electrónico

Analiza hilos de correo para extraer tareas, detectar sentimiento y enrutar automáticamente a los equipos adecuados.

**Capacidades**:

| Industria | Aplicación |
|-----------|-----------|
| **Servicio al cliente** | Analizar hilos de soporte para extraer acciones pendientes, detectar sentimiento del cliente, y enrutar automáticamente problemas urgentes a los equipos apropiados |
| **Legal** | Categorizar automáticamente correspondencia legal, identificar puntos de negociación, extraer fechas límite y obligaciones de hilos de correo |

**Pipeline sugerido**:

```yaml
name: procesamiento-correos
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: correos-entrantes

  - executor: azure_blob_content_retriever

  - executor: pdf_extractor

  - executor: sentiment_analyser
    settings:
      granularity: "documento"

  - executor: entity_extractor
    settings:
      entity_types: ["persona", "fecha", "organizacion", "accion"]

  - executor: azure_openai_agent
    settings:
      model: gpt-4.1-mini
      prompt: |
        Del correo electrónico, extrae:
        1. Acciones pendientes y responsables
        2. Fechas límite mencionadas
        3. Nivel de urgencia (bajo, medio, alto, crítico)
        4. Tema principal y categoría

  - executor: content_classifier
    settings:
      categories: ["soporte_tecnico", "facturacion", "queja",
                   "solicitud_informacion", "legal"]

  - executor: azure_blob_output
    settings:
      blob_container_name: correos-procesados
```

**Ejecutores clave**: `sentiment_analyser`, `entity_extractor`, `azure_openai_agent`, `content_classifier`

---

## 10. Ingestión de contenido para GPT-RAG

Construye bases de conocimiento buscables a partir de documentos empresariales, procesando múltiples formatos y creando embeddings para búsqueda semántica en soluciones de chat con IA.

**Capacidades**:
- Construir bases de conocimiento buscables desde documentos empresariales
- Procesar contenido en múltiples formatos para chat impulsado por IA
- Crear embeddings para búsqueda semántica

**Pipeline sugerido**:

```yaml
name: ingestion-gpt-rag
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: base-conocimiento

  - executor: azure_blob_content_retriever

  - executor: azure_document_intelligence_extractor
    settings:
      model_id: prebuilt-layout

  - executor: recursive_text_chunker
    settings:
      chunk_size: 800
      chunk_overlap: 150

  - executor: azure_openai_embeddings
    settings:
      model: text-embedding-3-small

  - executor: gptrag_search_index_document_generator
    settings:
      index_name: rag-knowledge-base

  - executor: ai_search_index_output
    settings:
      index_name: rag-knowledge-base
```

**Ejecutores clave**: `azure_document_intelligence_extractor`, `recursive_text_chunker`, `azure_openai_embeddings`, `gptrag_search_index_document_generator`

---

## 11. Resumen de artículos y reportes

Genera resúmenes concisos de artículos de noticias, reportes ejecutivos y snippets para redes sociales.

**Capacidades**:
- Resumir artículos de noticias para boletines internos
- Crear resúmenes ejecutivos de reportes extensos
- Generar snippets para publicaciones en redes sociales

**Pipeline sugerido**:

```yaml
name: resumen-articulos
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: articulos-reportes

  - executor: azure_blob_content_retriever

  - executor: pdf_extractor

  - executor: language_detector

  - executor: keyword_extractor
    settings:
      max_keywords: 10

  - executor: text_summarizer
    settings:
      max_length: 300
      style: "resumen ejecutivo"

  - executor: azure_openai_agent
    settings:
      model: gpt-4.1-mini
      prompt: |
        A partir del resumen generado, crea:
        1. Un titular de una línea
        2. Un resumen de 3 oraciones para boletín
        3. Un snippet para redes sociales (max 280 caracteres)

  - executor: azure_blob_output
    settings:
      blob_container_name: resumenes-generados
```

**Ejecutores clave**: `keyword_extractor`, `text_summarizer`, `language_detector`, `azure_openai_agent`

---

## 12. Traducción de contenido multilingüe

Traduce documentación de productos, marketing y bases de conocimiento para alcanzar audiencias globales.

**Capacidades**:
- Traducir documentación de productos a múltiples idiomas
- Localizar contenido de marketing para diferentes regiones
- Crear bases de conocimiento multilingües

**Pipeline sugerido**:

```yaml
name: traduccion-multilingue
steps:
  - executor: azure_blob_input_discovery
    settings:
      blob_container_name: contenido-original

  - executor: azure_blob_content_retriever

  - executor: pdf_extractor

  - executor: language_detector

  - executor: recursive_text_chunker
    settings:
      chunk_size: 2000

  - executor: content_translator
    settings:
      target_languages: ["es", "fr", "de", "pt", "ja"]

  - executor: azure_openai_embeddings
    settings:
      model: text-embedding-3-small

  - executor: ai_search_index_output
    settings:
      index_name: contenido-multilingue
```

**Ejecutores clave**: `language_detector`, `content_translator`, `azure_openai_embeddings`, `ai_search_index_output`

---

## 13. Resumen de ejecutores por caso de uso

| Caso de uso | Ejecutores principales |
|---|---|
| **Facturas y recibos** | `azure_content_understanding_extractor`, `content_classifier`, `field_mapper` |
| **Indexación inteligente** | `azure_document_intelligence_extractor`, `recursive_text_chunker`, `azure_openai_embeddings`, `ai_search_index_output` |
| **Análisis de contratos** | `pdf_extractor`, `entity_extractor`, `azure_openai_agent`, `text_summarizer` |
| **Grafos de conocimiento** | `entity_extractor`, `azure_openai_agent`, `cross_document_comparison` |
| **Formularios** | `azure_content_understanding_extractor`, `field_selector`, `content_classifier` |
| **Cumplimiento y riesgos** | `pii_detector`, `content_classifier`, `azure_openai_agent` |
| **Contenido web** | `web_scraper`, `content_translator`, `azure_openai_embeddings` |
| **Análisis visual** | `azure_content_understanding_extractor`, `azure_openai_agent` |
| **Correo electrónico** | `sentiment_analyser`, `entity_extractor`, `content_classifier` |
| **GPT-RAG** | `azure_document_intelligence_extractor`, `recursive_text_chunker`, `gptrag_search_index_document_generator` |
| **Resúmenes** | `keyword_extractor`, `text_summarizer`, `azure_openai_agent` |
| **Traducción** | `language_detector`, `content_translator`, `azure_openai_embeddings` |

---

## 14. Pipelines de ejemplo incluidos en el repositorio

El repositorio incluye más de **20 pipelines de ejemplo** listos para ejecutar en la carpeta `contentflow-lib/samples/`:

| Carpeta | Nombre | Descripción |
|---------|--------|-------------|
| `01-simple/` | Pipeline simple | Pipeline básico de extracción de texto |
| `02-batch-processing/` | Procesamiento por lotes | Procesamiento de múltiples documentos |
| `03-pdf-extractor_chunker/` | PDF + Chunking | Extracción de PDF y división en fragmentos |
| `04-word-extractor/` | Extractor Word | Procesamiento de documentos .docx |
| `05-powerpoint-extractor/` | Extractor PowerPoint | Procesamiento de presentaciones .pptx |
| `06-ai-analysis/` | Análisis con IA | Análisis inteligente con GPT |
| `07-embeddings/` | Embeddings | Generación de vectores de embedding |
| `08-content-understanding/` | Content Understanding | Azure Content Understanding |
| `09-blob-input/` | Entrada desde Blob | Descubrimiento de contenido en Blob Storage |
| `10-table-row-splitter/` | Divisor de filas | Procesamiento fila por fila de tablas |
| `11-excel-extractor/` | Extractor Excel | Procesamiento de hojas de cálculo |
| `12-field-transformation/` | Transformación de campos | Mapeo y transformación de datos |
| `13-blob-output-sample/` | Salida a Blob | Escritura de resultados a Blob Storage |
| `14-gpt-rag-ingestion/` | Ingestión GPT-RAG | Pipeline completo para RAG |
| `15-document-analysis/` | Análisis de documentos | Análisis completo con Document Intelligence |
| `16-spreadsheet-pipeline/` | Pipeline de hojas de cálculo | Procesamiento de Excel end-to-end |
| `17-knowledge-graph/` | Grafo de conocimiento | Extracción de entidades y relaciones |
| `18-web-scraping/` | Web scraping | Extracción de contenido web |
| `19-sub-pipelines/` | Sub-pipelines | Pipelines anidados |
| `20-document-set-static/` | Conjunto estático | Procesamiento de conjuntos de documentos |
| `21-document-set-comparison/` | Comparación de documentos | Comparación cruzada de documentos |
| `22-document-set-dynamic/` | Conjunto dinámico | Conjuntos de documentos dinámicos |
| `23-inline-document-set/` | Conjunto inline | Conjuntos definidos en línea |
| `27-subpipeline-processing/` | Sub-pipeline avanzado | Procesamiento con sub-pipelines |
| `28-advanced-batch/` | Lotes avanzado | Procesamiento por lotes avanzado |
| `32-parallel-processing/` | Procesamiento paralelo | Flujos de trabajo en paralelo |
| `44-conditional-routing/` | Enrutamiento condicional | Lógica condicional en pipelines |

---

> Cada caso de uso se puede implementar combinando los **35+ ejecutores** disponibles en ContentFlow. Los pipelines YAML son completamente configurables y se pueden diseñar visualmente desde la interfaz web o editarse directamente en el editor YAML integrado.
