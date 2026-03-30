# Mini-AILZ con Terraform AVM Pattern Module para ContentFlow

> **Documento técnico operativo** — Despliegue de una AI Landing Zone mínima usando el módulo oficial Terraform AVM `Azure/avm-ptn-aiml-landing-zone`, optimizada para el costo mínimo necesario para ContentFlow en modo `ailz-integrated`.

---

## Tabla de Contenidos

1. [Objetivo y Contexto](#1-objetivo-y-contexto)
2. [¿Por qué el Pattern Module en lugar de Azure CLI Manual?](#2-por-qué-el-pattern-module-en-lugar-de-azure-cli-manual)
3. [Análisis del Módulo: Todos los Recursos vs Lo Mínimo](#3-análisis-del-módulo-todos-los-recursos-vs-lo-mínimo)
4. [Mapeo: Requisitos ContentFlow → Parámetros del Módulo](#4-mapeo-requisitos-contentflow--parámetros-del-módulo)
5. [Configuración Terraform Mínima Completa](#5-configuración-terraform-mínima-completa)
6. [Conexión de Outputs con ContentFlow azd](#6-conexión-de-outputs-con-contentflow-azd)
7. [Fix Conocido: storage_use_azuread](#7-fix-conocido-storage_use_azuread)
8. [Paso a Paso: Despliegue](#8-paso-a-paso-despliegue)
9. [Comparación de Costo: Full vs Mini](#9-comparación-de-costo-full-vs-mini)
10. [Diagrama de Arquitectura Resultante](#10-diagrama-de-arquitectura-resultante)
11. [Notas de Operación y Troubleshooting](#11-notas-de-operación-y-troubleshooting)
12. [Limpieza de Recursos](#12-limpieza-de-recursos)

---

## 1. Objetivo y Contexto

### Situación

ContentFlow soporta despliegue en modo `ailz-integrated`, el cual requiere infraestructura de red pre-existente (VNet, subredes, Private DNS Zones, Container Apps Environment). En el [documento 04](04-ai_lz_options.md) se describe cómo crear esta infraestructura con comandos Azure CLI manuales.

### Nuevo Enfoque

En lugar de scripts manuales, usaremos el **módulo oficial Terraform AVM Pattern** para AI/ML Landing Zones:

- **Módulo**: [`Azure/avm-ptn-aiml-landing-zone/azurerm`](https://github.com/Azure/terraform-azurerm-avm-ptn-aiml-landing-zone)
- **Versión**: `0.4.0`
- **Registry**: [Terraform Registry](https://registry.terraform.io/modules/Azure/avm-ptn-aiml-landing-zone/azurerm/latest)

### Principio Clave: Solo lo Mínimo Indispensable

El módulo completo despliega **más de 25 recursos** incluyendo AI Foundry, App Gateway, Firewall, APIM, Build VM, AI Search, Bing Grounding, etc. ContentFlow **no necesita la mayoría de estos**. Este documento configura **exclusivamente** lo que ContentFlow requiere para funcionar en modo privado.

---

## 2. ¿Por qué el Pattern Module en lugar de Azure CLI Manual?

| Aspecto | Azure CLI Manual (Doc 04) | Terraform AVM Module (Este Doc) |
|---|---|---|
| **Reproducibilidad** | Scripts bash con variables | Declarativo, idempotente, plan/apply |
| **Estado** | No hay tracking de estado | `terraform.tfstate` con full tracking |
| **Drift detection** | Manual (`az resource show`) | `terraform plan` detecta drift |
| **Limpieza** | `az group delete` (todo o nada) | `terraform destroy` selectivo |
| **Validación** | Post-ejecución manual | `terraform validate` + `plan` pre-apply |
| **Subredes y DNS** | Creación manual una por una | El módulo crea subredes automáticamente |
| **Private DNS Zones** | 6 comandos individuales + links | El módulo las crea y vincula |
| **Container Apps Env** | No incluido en doc 04 | Incluido con VNet integration |
| **Bastion** | Configuración manual compleja | Un flag `deploy = true` |
| **Versionamiento** | Copiar/pegar scripts | Module version pinning |
| **Soporte oficial** | Ninguno | Módulo oficial de Microsoft (AVM) |

**Ventaja principal**: El módulo maneja internamente la creación de subredes con los nombres, tamaños y delegaciones correctas. Esto elimina errores comunes como subredes con prefijos incorrectos o sin delegación para Container Apps.

---

## 3. Análisis del Módulo: Todos los Recursos vs Lo Mínimo

### Recursos que el módulo PUEDE desplegar (despliegue completo)

| Recurso | Default `deploy` | ¿ContentFlow lo necesita? | Acción Mini-AILZ |
|---|---|---|---|
| **VNet + Subredes** | Siempre (required) | **SÍ** | ✅ Mantener |
| **Private DNS Zones** | Siempre | **SÍ** | ✅ Mantener |
| **Log Analytics Workspace** | `true` | **SÍ** (compartido) | ✅ Mantener |
| **NSGs** | Siempre | **SÍ** (seguridad) | ✅ Mantener |
| **Container Apps Environment** | `true` | **SÍ** | ✅ Mantener |
| **Bastion** | `true` | **SÍ** (acceso a red privada) | ✅ Mantener |
| **GenAI Container Registry** | `true` | **Parcial** (ContentFlow crea el suyo) | ⚠️ Mantener* |
| **GenAI Key Vault** | Siempre | **Parcial** | ⚠️ Mantener* |
| **GenAI Storage Account** | `true` | **No directamente** | ⚠️ Mantener* |
| **GenAI App Configuration** | `true` | **No directamente** | ⚠️ Mantener* |
| **GenAI Cosmos DB** | `true` | **No directamente** | ⚠️ Mantener* |
| **AI Foundry Hub + BYOR** | `{}` (vacío = no crea) | **No** | ❌ Omitir |
| **AI Model Deployments** | `{}` (vacío = no crea) | **No** | ❌ Omitir |
| **AI Projects** | `{}` (vacío = no crea) | **No** | ❌ Omitir |
| **App Gateway** | `null` (no crea) | **No** | ❌ Omitir |
| **Azure Firewall** | `true` | **No** (demo) | ❌ Deshabilitar |
| **Build VM / Jump VM** | `true` | **No** (usamos Bastion) | ❌ Deshabilitar |
| **AI Search (BYOR)** | `{}` (vacío = no crea) | **No** | ❌ Omitir |
| **AI Search (KS)** | `true` | **No** | ❌ Deshabilitar |
| **Bing Grounding** | `true` | **No** | ❌ Deshabilitar |
| **APIM** | `true` | **No** | ❌ Deshabilitar |
| **WAF Policy** | Solo con App GW | **No** | ❌ Omitir |

> **\*** Los recursos GenAI (Container Registry, Key Vault, Storage, App Config, Cosmos) se crean por defecto como parte de la plataforma GenAI del módulo. ContentFlow crea sus propios recursos de datos (Cosmos, Storage, App Config) durante `azd up`, pero el módulo necesita el Container Registry y Key Vault internamente. Para minimizar costo, podemos aceptar estos con configuración por defecto ligera.

### ¿Qué NO se puede deshabilitar?

El módulo **siempre crea** estos recursos independientemente de la configuración:

1. **Resource Group** (si no existe)
2. **VNet** (required input)
3. **Subredes** (calculadas internamente según recursos habilitados)
4. **Private DNS Zones** (necesarias para private endpoints)
5. **NSGs** (asociados a subredes)
6. **Key Vault** (usado internamente por el módulo para secretos de GenAI)
7. **Role Assignments** (deployment user → Key Vault Admin)

---

## 4. Mapeo: Requisitos ContentFlow → Parámetros del Módulo

### Lo que ContentFlow Necesita del AILZ

| Requisito ContentFlow | Parámetro del Módulo | Variable de Entorno `azd` |
|---|---|---|
| VNet Resource ID | `module.ailz.virtual_network.id` | `EXISTING_VNET_RESOURCE_ID` |
| Subred `pe-subnet` | Creada automáticamente por el módulo | `PRIVATE_ENDPOINT_SUBNET_NAME` |
| Subred `aca-env-subnet` | Creada automáticamente por el módulo | `CONTAINER_APPS_SUBNET_NAME` |
| DNS: `privatelink.blob.core.windows.net` | Parte de `private_dns_zones` del módulo | `EXISTING_BLOB_PRIVATE_DNS_ZONE_ID` |
| DNS: `privatelink.documents.azure.com` | Parte de `private_dns_zones` del módulo | `EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID` |
| DNS: `privatelink.azconfig.io` | Parte de `private_dns_zones` del módulo | `EXISTING_APP_CONFIG_PRIVATE_DNS_ZONE_ID` |
| DNS: `privatelink.azurecr.io` | Parte de `private_dns_zones` del módulo | `EXISTING_ACR_PRIVATE_DNS_ZONE_ID` |
| DNS: `privatelink.cognitiveservices.azure.com` | Parte de `private_dns_zones` del módulo | `EXISTING_COGNITIVE_SERVICES_PRIVATE_DNS_ZONE_ID` |
| DNS: `privatelink.azurecontainerapps.io` | Parte de `private_dns_zones` del módulo | `EXISTING_CONTAINER_APPS_ENV_PRIVATE_DNS_ZONE_ID` |
| Log Analytics Workspace | `module.ailz.log_analytics_workspace_id` | `EXISTING_LOG_ANALYTICS_WORKSPACE_ID` |
| Container Apps Environment | Creado por el módulo (VNet-integrated, interno) | El CAE se crea aquí, ContentFlow lo usa |

### Nota Importante sobre Subredes

El módulo AVM Pattern calcula y crea las subredes internamente basándose en qué recursos están habilitados. Los nombres de subredes son determinados por el módulo. ContentFlow espera subredes llamadas `pe-subnet` y `aca-env-subnet`. Puedes usar el bloque `vnet_definition.subnets` para configurar override de nombres si es necesario.

### Nota sobre Container Apps Environment

El módulo crea un Container Apps Environment integrado con la VNet. Esto es **exactamente lo que ContentFlow necesita**. Sin embargo, ContentFlow normalmente crea su propio CAE durante `azd up`. Para el modo Mini-AILZ con Terraform, tienes dos opciones:

1. **Usar el CAE del módulo** — Más eficiente; ContentFlow debe configurarse para no crear un CAE propio
2. **Deshabilitar el CAE del módulo** — ContentFlow crea el suyo durante deploy, usando la subred apropiada

La **opción recomendada es la 1** (usar el CAE del módulo) ya que garantiza la configuración correcta de VNet integration.

---

## 5. Configuración Terraform Mínima Completa

### Estructura de Archivos

```
mini-ailz-contentflow/
├── terraform.tf          # Providers y versiones
├── variables.tf          # Variables de entrada
├── main.tf               # Data sources y helpers
├── ailz.tf               # Módulo AILZ con configuración mínima
├── outputs.tf            # Outputs para ContentFlow
└── terraform.tfvars      # Valores (opcional, gitignored)
```

### `terraform.tf` — Providers

```hcl
terraform {
  required_version = ">= 1.9, < 2.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.116, < 5.0"
    }
    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "azurerm" {
  features {
    cognitive_account {
      purge_soft_delete_on_destroy = true
    }
    key_vault {
      purge_soft_delete_on_destroy = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }

  # CRÍTICO: Sin esto, las Storage Accounts dan error 403
  # Ver sección 7 para detalles
  storage_use_azuread = true
}

provider "azapi" {}
```

### `variables.tf` — Variables de Entrada

```hcl
variable "location" {
  type        = string
  description = "Región de Azure para los recursos"
  default     = "swedencentral"
}

variable "resource_group_name" {
  type        = string
  description = "Nombre del Resource Group para la Mini-AILZ"
  default     = "rg-mini-ailz-contentflow"
}

variable "name_prefix" {
  type        = string
  description = "Prefijo para nombres de recursos (máx 10 chars, minúsculas alfanuméricas)"
  default     = "cfailz"

  validation {
    condition     = length(var.name_prefix) <= 10 && can(regex("^[a-z0-9]+$", var.name_prefix))
    error_message = "name_prefix debe tener máximo 10 caracteres alfanuméricos en minúsculas."
  }
}

variable "enable_telemetry" {
  type        = bool
  description = "Habilitar telemetría del módulo AVM"
  default     = false
}
```

### `main.tf` — Data Sources

```hcl
data "azurerm_client_config" "current" {}
```

### `ailz.tf` — Módulo AILZ Configuración Mínima

```hcl
# =============================================================================
# Mini-AILZ para ContentFlow
# =============================================================================
# Este archivo configura SOLO lo mínimo indispensable del módulo AVM Pattern
# para satisfacer los requisitos de ContentFlow en modo ailz-integrated:
#   1. VNet con subredes (pe-subnet, aca-env-subnet)
#   2. Private DNS Zones vinculadas a la VNet
#   3. Container Apps Environment (VNet-integrated, internal LB)
#   4. Bastion (acceso a la red privada)
#   5. Log Analytics Workspace (monitoreo compartido)
#   6. NSGs (seguridad de subredes)
#   7. Key Vault + Container Registry (requeridos internamente por el módulo)
#
# TODO lo demás está DESHABILITADO para minimizar costo:
#   ✗ AI Foundry, Model Deployments, AI Projects
#   ✗ App Gateway, WAF Policy
#   ✗ Azure Firewall
#   ✗ Build VM, Jump VM
#   ✗ AI Search (BYOR y KS)
#   ✗ Bing Grounding
#   ✗ APIM
# =============================================================================

module "ailz" {
  source  = "Azure/avm-ptn-aiml-landing-zone/azurerm"
  version = "0.4.0"

  # ── Ubicación y Resource Group ──────────────────────────────────────────────
  location            = var.location
  resource_group_name = var.resource_group_name

  # ── VNet (REQUIRED) ────────────────────────────────────────────────────────
  # ContentFlow necesita:
  #   - pe-subnet: para Private Endpoints (~32 IPs, /27+)
  #   - aca-env-subnet: para Container Apps Environment (~512 IPs, /23)
  #
  # NOTA: El módulo calcula y crea las subredes internamente.
  # Usamos 10.0.0.0/16 para tener espacio suficiente.
  vnet_definition = {
    address_space              = ["10.0.0.0/16"]
    enable_diagnostic_settings = false
  }

  # ── Container Apps Environment ─────────────────────────────────────────────
  # ContentFlow despliega API, Worker y Web como Container Apps.
  # Este CAE se integra con la VNet en modo interno (solo accesible desde VNet).
  container_app_environment_definition = {
    internal_load_balancer_enabled = true
    zone_redundancy_enabled        = false  # false = ahorro de costo para demo
    enable_diagnostic_settings     = false
    workload_profile = [
      {
        name                  = "Consumption"
        workload_profile_type = "Consumption"
      }
    ]
  }

  # ── Bastion ────────────────────────────────────────────────────────────────
  # Necesario para acceder a la red privada (UI de ContentFlow, debug, etc.)
  # SKU "Basic" es más barato que "Standard" (~$140/mes vs ~$350/mes)
  bastion_definition = {
    deploy = true
    sku    = "Basic"
    zones  = []  # Sin zone redundancy para demo
  }

  # ── Log Analytics Workspace ────────────────────────────────────────────────
  # Compartido con ContentFlow para monitoreo centralizado.
  law_definition = {
    deploy = true
  }

  # ── AI Foundry ─────────────────────────────────────────────────────────────
  # ContentFlow NO necesita AI Foundry del AILZ.
  # (ContentFlow crea su propio AI Foundry durante azd up)
  # Dejamos el default vacío {} = no crea hub, projects, ni BYOR resources.
  ai_foundry_definition = {
    create_byor = false     # No crear BYOR resources (AI Search, Cosmos, KV, Storage)
    ai_foundry = {
      enable_diagnostic_settings = false
    }
  }

  # ── DESHABILITADOS ─────────────────────────────────────────────────────────

  # App Gateway: ContentFlow no usa App Gateway (acceso via Bastion/VPN)
  # Default es null = no se despliega
  app_gateway_definition = null

  # Azure Firewall: No necesario para demo (ahorra ~$250/mes)
  firewall_definition = {
    deploy = false
  }

  # Build VM: No necesaria (usamos Bastion + local development)
  buildvm_definition = {
    deploy = false
  }

  # Jump VM: No necesaria si tenemos Bastion
  # (jumpvm_definition no tiene deploy flag, se controla por buildvm)

  # KS AI Search: ContentFlow no necesita AI Search federado
  ks_ai_search_definition = {
    deploy = false
  }

  # Bing Grounding: ContentFlow no usa Bing
  ks_bing_grounding_definition = {
    deploy = false
  }

  # APIM: ContentFlow no usa API Management
  apim_definition = {
    deploy          = false
    publisher_email = "noreply@example.com"
    publisher_name  = "N/A"
  }

  # ── GenAI Platform Resources ───────────────────────────────────────────────
  # Estos recursos se crean por defecto como parte de la plataforma GenAI.
  # ContentFlow crea sus propios Cosmos DB, Storage, App Config durante azd up,
  # pero el módulo internamente necesita algunos de estos.
  # Configuración mínima para reducir costo:

  genai_container_registry_definition = {
    zone_redundancy_enabled    = false       # Ahorro: sin ZRS
    enable_diagnostic_settings = false
  }

  genai_key_vault_definition = {
    # Acceso público habilitado para facilitar deploy desde local
    # En producción: false + Private Endpoint
    public_network_access_enabled = true
    network_acls = {
      bypass         = "AzureServices"
      default_action = "Deny"
    }
  }

  genai_storage_account_definition = {
    account_replication_type = "LRS"   # LRS es más barato que GRS (default)
    enable_diagnostic_settings = false
  }

  genai_app_configuration_definition = {
    purge_protection_enabled   = false  # Facilita destroy para demo
    enable_diagnostic_settings = false
  }

  genai_cosmosdb_definition = {
    analytical_storage_enabled = false   # No necesario para demo
    automatic_failover_enabled = false   # No necesario para single-region demo
    enable_diagnostic_settings = false
  }

  # ── Flags y otros ──────────────────────────────────────────────────────────
  # flag_platform_landing_zone = false → No crea route tables con Firewall
  # (Si es true, se asume que hay un Firewall y crea UDRs para enrutar tráfico)
  flag_platform_landing_zone = false

  enable_telemetry = var.enable_telemetry
  name_prefix      = var.name_prefix
}
```

### `outputs.tf` — Valores para ContentFlow

```hcl
# =============================================================================
# Outputs para configurar ContentFlow azd environment
# =============================================================================
# Estos valores se usan como variables de entorno para:
#   azd env set <NOMBRE> <VALOR>
# antes de ejecutar: azd up --deployment-mode ailz-integrated
# =============================================================================

output "vnet_resource_id" {
  description = "VNet Resource ID → EXISTING_VNET_RESOURCE_ID"
  value       = module.ailz.virtual_network.id
}

output "log_analytics_workspace_id" {
  description = "Log Analytics Workspace ID → EXISTING_LOG_ANALYTICS_WORKSPACE_ID"
  value       = module.ailz.log_analytics_workspace_id
}

output "subnets" {
  description = "Mapa de subredes creadas (para verificar nombres)"
  value       = module.ailz.subnets
}

# =============================================================================
# NOTA SOBRE PRIVATE DNS ZONES:
# =============================================================================
# El módulo crea las Private DNS Zones automáticamente, pero actualmente (v0.4.0)
# NO expone sus Resource IDs como outputs directos.
#
# Para obtener los IDs de las DNS Zones, después de `terraform apply`:
#
#   az network private-dns zone list \
#     --resource-group <rg-mini-ailz-contentflow> \
#     --query "[].{name:name, id:id}" -o table
#
# Alternativamente, puedes usar data sources de Terraform para leerlos:
# =============================================================================

# Instrucciones que se imprimen después del apply
output "contentflow_setup_instructions" {
  description = "Instrucciones para configurar ContentFlow con esta Mini-AILZ"
  value       = <<-EOT

    ╔══════════════════════════════════════════════════════════════════╗
    ║  Mini-AILZ desplegada exitosamente para ContentFlow             ║
    ╚══════════════════════════════════════════════════════════════════╝

    Próximos pasos:

    1. Obtener los Resource IDs de las Private DNS Zones:

       az network private-dns zone list \
         --resource-group ${var.resource_group_name} \
         --query "[].{name:name, id:id}" -o table

    2. Configurar el environment de ContentFlow:

       cd <directorio-contentflow>
       azd env set DEPLOYMENT_MODE ailz-integrated
       azd env set EXISTING_VNET_RESOURCE_ID ${module.ailz.virtual_network.id}
       azd env set EXISTING_LOG_ANALYTICS_WORKSPACE_ID ${module.ailz.log_analytics_workspace_id}

       # Copiar los IDs de DNS Zones del paso 1:
       azd env set EXISTING_BLOB_PRIVATE_DNS_ZONE_ID <id-blob-zone>
       azd env set EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID <id-cosmos-zone>
       azd env set EXISTING_APP_CONFIG_PRIVATE_DNS_ZONE_ID <id-appconfig-zone>
       azd env set EXISTING_ACR_PRIVATE_DNS_ZONE_ID <id-acr-zone>
       azd env set EXISTING_COGNITIVE_SERVICES_PRIVATE_DNS_ZONE_ID <id-cognitive-zone>
       azd env set EXISTING_CONTAINER_APPS_ENV_PRIVATE_DNS_ZONE_ID <id-containerapp-zone>

    3. Desplegar ContentFlow:

       azd up

  EOT
}
```

---

## 6. Conexión de Outputs con ContentFlow azd

Después de ejecutar `terraform apply`, necesitas pasar los valores de infraestructura a ContentFlow.

### Script Automatizado: `configure-contentflow.sh`

```bash
#!/bin/bash
# =============================================================================
# configure-contentflow.sh
# Configura las variables de entorno de ContentFlow azd con los outputs
# de la Mini-AILZ desplegada con Terraform.
# =============================================================================
set -euo pipefail

# Verificar que estamos en el directorio correcto de Terraform
if [[ ! -f "ailz.tf" ]]; then
  echo "ERROR: Ejecuta este script desde el directorio de Terraform Mini-AILZ"
  exit 1
fi

# Directorio de ContentFlow (ajustar según tu setup)
CONTENTFLOW_DIR="${1:-../contentflow-test-001}"

echo "Obteniendo outputs de Terraform..."
VNET_ID=$(terraform output -raw vnet_resource_id)
LAW_ID=$(terraform output -raw log_analytics_workspace_id)
RG_NAME=$(terraform output -raw 2>/dev/null | grep -oP 'resource-group \K[^ \\]+' || true)

# Obtener el nombre real del resource group del state
RG_NAME=$(terraform show -json | python3 -c "
import sys, json
state = json.load(sys.stdin)
for r in state.get('values', {}).get('root_module', {}).get('child_modules', []):
    for res in r.get('resources', []):
        if res['type'] == 'azurerm_resource_group':
            print(res['values']['name'])
            break
" 2>/dev/null || echo "rg-mini-ailz-contentflow")

echo "Resource Group: $RG_NAME"
echo "VNet ID: $VNET_ID"
echo "Log Analytics ID: $LAW_ID"

echo ""
echo "Obteniendo Private DNS Zone IDs..."

# Función helper para obtener DNS Zone ID
get_dns_zone_id() {
  local zone_name=$1
  az network private-dns zone show \
    --resource-group "$RG_NAME" \
    --name "$zone_name" \
    --query id -o tsv 2>/dev/null || echo ""
}

BLOB_DNS=$(get_dns_zone_id "privatelink.blob.core.windows.net")
COSMOS_DNS=$(get_dns_zone_id "privatelink.documents.azure.com")
APPCONFIG_DNS=$(get_dns_zone_id "privatelink.azconfig.io")
ACR_DNS=$(get_dns_zone_id "privatelink.azurecr.io")
COGNITIVE_DNS=$(get_dns_zone_id "privatelink.cognitiveservices.azure.com")
CONTAINERAPP_DNS=$(get_dns_zone_id "privatelink.azurecontainerapps.io")

# Verificar que encontramos todas las zonas
MISSING=0
for ZONE_VAR in BLOB_DNS COSMOS_DNS APPCONFIG_DNS ACR_DNS COGNITIVE_DNS CONTAINERAPP_DNS; do
  if [[ -z "${!ZONE_VAR}" ]]; then
    echo "⚠ WARNING: No se encontró DNS Zone para $ZONE_VAR"
    MISSING=1
  fi
done

if [[ $MISSING -eq 1 ]]; then
  echo ""
  echo "Algunas DNS Zones no se encontraron. Verifica con:"
  echo "  az network private-dns zone list --resource-group $RG_NAME -o table"
  echo ""
  echo "El módulo puede usar nombres diferentes. Ajusta manualmente si es necesario."
fi

echo ""
echo "Configurando azd environment en: $CONTENTFLOW_DIR"

pushd "$CONTENTFLOW_DIR" > /dev/null

azd env set DEPLOYMENT_MODE ailz-integrated
azd env set EXISTING_VNET_RESOURCE_ID "$VNET_ID"
azd env set EXISTING_LOG_ANALYTICS_WORKSPACE_ID "$LAW_ID"
[[ -n "$BLOB_DNS" ]]         && azd env set EXISTING_BLOB_PRIVATE_DNS_ZONE_ID "$BLOB_DNS"
[[ -n "$COSMOS_DNS" ]]       && azd env set EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID "$COSMOS_DNS"
[[ -n "$APPCONFIG_DNS" ]]    && azd env set EXISTING_APP_CONFIG_PRIVATE_DNS_ZONE_ID "$APPCONFIG_DNS"
[[ -n "$ACR_DNS" ]]          && azd env set EXISTING_ACR_PRIVATE_DNS_ZONE_ID "$ACR_DNS"
[[ -n "$COGNITIVE_DNS" ]]    && azd env set EXISTING_COGNITIVE_SERVICES_PRIVATE_DNS_ZONE_ID "$COGNITIVE_DNS"
[[ -n "$CONTAINERAPP_DNS" ]] && azd env set EXISTING_CONTAINER_APPS_ENV_PRIVATE_DNS_ZONE_ID "$CONTAINERAPP_DNS"

popd > /dev/null

echo ""
echo "✅ Configuración completada. Ejecuta:"
echo "   cd $CONTENTFLOW_DIR && azd up"
```

### Mapeo Completo de Outputs → Variables azd

| Output Terraform / Comando az | Variable azd ContentFlow | Descripción |
|---|---|---|
| `module.ailz.virtual_network.id` | `EXISTING_VNET_RESOURCE_ID` | Resource ID de la VNet |
| `module.ailz.log_analytics_workspace_id` | `EXISTING_LOG_ANALYTICS_WORKSPACE_ID` | LAW compartido |
| `az ... privatelink.blob.core.windows.net` | `EXISTING_BLOB_PRIVATE_DNS_ZONE_ID` | DNS Zone para Blob |
| `az ... privatelink.documents.azure.com` | `EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID` | DNS Zone para Cosmos |
| `az ... privatelink.azconfig.io` | `EXISTING_APP_CONFIG_PRIVATE_DNS_ZONE_ID` | DNS Zone para App Config |
| `az ... privatelink.azurecr.io` | `EXISTING_ACR_PRIVATE_DNS_ZONE_ID` | DNS Zone para ACR |
| `az ... privatelink.cognitiveservices.azure.com` | `EXISTING_COGNITIVE_SERVICES_PRIVATE_DNS_ZONE_ID` | DNS Zone para AI Services |
| `az ... privatelink.azurecontainerapps.io` | `EXISTING_CONTAINER_APPS_ENV_PRIVATE_DNS_ZONE_ID` | DNS Zone para Container Apps |
| (contenido en `pe-subnet`) | `PRIVATE_ENDPOINT_SUBNET_NAME` | Default: `pe-subnet` |
| (contenido en `aca-env-subnet`) | `CONTAINER_APPS_SUBNET_NAME` | Default: `aca-env-subnet` |

---

## 7. Fix Conocido: storage_use_azuread

### El Problema

El módulo crea Storage Accounts con `shared_access_key_enabled = false` (default seguro). Sin embargo, el provider `azurerm` por defecto usa **autenticación por key** para operaciones de Storage. Esto produce:

```
Error: StatusCode=403 -- Original Error: autorest/azure: Service returned an error.
Status=403 Code="AuthorizationFailure"
```

### La Solución

Agregar `storage_use_azuread = true` en el bloque del provider:

```hcl
provider "azurerm" {
  features { ... }
  storage_use_azuread = true   # ← CRÍTICO
}
```

### Prerrequisito

El usuario que ejecuta `terraform apply` debe tener el rol **Storage Blob Data Contributor** en la suscripción o en los Resource Groups correspondientes:

```bash
# Asignar rol a tu usuario (una vez)
az role assignment create \
  --assignee "$(az ad signed-in-user show --query id -o tsv)" \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/$(az account show --query id -o tsv)"
```

---

## 8. Paso a Paso: Despliegue

### 8.1 Preparar el Entorno

```bash
# Crear directorio de trabajo
mkdir mini-ailz-contentflow && cd mini-ailz-contentflow

# Crear los archivos Terraform (copiar de la sección 5)
# terraform.tf, variables.tf, main.tf, ailz.tf, outputs.tf
```

### 8.2 Inicializar Terraform

```bash
terraform init
```

Esto descarga el módulo AVM y todos sus sub-módulos (~20 módulos).

### 8.3 Validar y Planificar

```bash
# Validar sintaxis
terraform validate

# Ver plan de ejecución
terraform plan -out=tfplan
```

El plan debería mostrar aproximadamente **15-20 recursos** a crear (vs ~45+ con el módulo completo).

### 8.4 Aplicar

```bash
terraform apply tfplan
```

Tiempo estimado: **15-25 minutos** (Bastion y Container Apps Environment son los más lentos).

### 8.5 Verificar Recursos Creados

```bash
# Listar recursos en el RG
az resource list \
  --resource-group rg-mini-ailz-contentflow \
  --query "[].{name:name, type:type}" \
  -o table
```

Deberías ver:
- Virtual Network
- Subredes (varias, creadas por el módulo)
- NSGs
- Private DNS Zones (6+)
- Bastion Host + Public IP
- Container Apps Environment
- Log Analytics Workspace
- Key Vault
- Container Registry
- Storage Account
- App Configuration
- Cosmos DB Account

### 8.6 Configurar ContentFlow

```bash
# Opción A: Script automatizado
chmod +x configure-contentflow.sh
./configure-contentflow.sh /path/to/contentflow

# Opción B: Manual
cd /path/to/contentflow
azd env set DEPLOYMENT_MODE ailz-integrated
azd env set EXISTING_VNET_RESOURCE_ID "$(terraform -chdir=/path/to/mini-ailz output -raw vnet_resource_id)"
# ... (ver sección 6 para el mapeo completo)
```

### 8.7 Desplegar ContentFlow

```bash
cd /path/to/contentflow
azd up
```

---

## 9. Comparación de Costo: Full vs Mini

### Despliegue Completo del Módulo (tu test anterior en standalone-test001)

| Recurso | SKU/Tier | Costo Estimado/mes |
|---|---|---|
| AI Foundry Hub + BYOR | S0 | ~$0 (pago por uso) |
| GPT-4.1 Model | GlobalStandard x1 | ~$0-30 (por tokens) |
| AI Search | Standard, 2 replicas | **~$500** |
| App Gateway (WAF_v2) | 2 scale units | **~$350** |
| Azure Bastion | Standard, 3 AZs | **~$350** |
| Azure Firewall | Standard, 3 AZs | **~$250** |
| Build VM | Standard_B2s | **~$30** |
| APIM | Premium x3 | **~$2,100** |
| Container Apps Env | Consumption (ZR) | ~$0-20 |
| Cosmos DB (BYOR) | Serverless | ~$0-10 |
| Cosmos DB (GenAI) | Serverless | ~$0-10 |
| Key Vault x2 | Standard | ~$0-5 |
| Storage Account x2 | ZRS/GRS | ~$5-15 |
| Container Registry | Premium (ZR) | **~$60** |
| App Configuration | Standard | ~$36 |
| Log Analytics | Per-GB | ~$0-20 |
| Bing Grounding | G1 | ~$5 |
| KS AI Search | Standard | **~$250** |
| VNet + Subredes | - | ~$0 |
| Private DNS Zones | - | ~$1-5 |
| **TOTAL ESTIMADO** | | **~$3,500-4,000/mes** |

### Mini-AILZ (este documento)

| Recurso | SKU/Tier | Costo Estimado/mes |
|---|---|---|
| Azure Bastion | **Basic**, sin AZs | **~$140** |
| Container Apps Env | Consumption, sin ZR | ~$0-20 |
| Container Registry | Premium (requerido para PE) | **~$50** |
| Cosmos DB (GenAI) | Serverless | ~$0-10 |
| Key Vault | Standard | ~$0-5 |
| Storage Account | **LRS** | ~$2-5 |
| App Configuration | Standard | ~$36 |
| Log Analytics | Per-GB | ~$0-20 |
| VNet + Subredes | - | ~$0 |
| Private DNS Zones | - | ~$1-5 |
| NSGs | - | ~$0 |
| **TOTAL ESTIMADO** | | **~$230-290/mes** |

### Ahorro

| Métrica | Full | Mini | Ahorro |
|---|---|---|---|
| Costo mensual | ~$3,700 | ~$260 | **~$3,440/mes (93%)** |
| Recursos Azure | ~40+ | ~15-20 | **50% menos** |
| Tiempo deploy | ~45 min | ~20 min | **55% menos** |

> **Nota**: Los costos de ContentFlow en sí (Container Apps, Cosmos DB, Storage, etc. que crea `azd up`) son adicionales y similares en ambos escenarios (~$100-200/mes dependiendo del uso).

---

## 10. Diagrama de Arquitectura Resultante

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Resource Group: rg-mini-ailz-contentflow                               │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  VNet (10.0.0.0/16)                                               │  │
│  │                                                                   │  │
│  │  ┌─────────────────┐  ┌──────────────────────────────────────┐   │  │
│  │  │  Bastion Subnet  │  │  Container Apps Subnet (/23)         │   │  │
│  │  │  ┌────────────┐  │  │                                      │   │  │
│  │  │  │  Bastion    │  │  │  ┌──────────────────────────────┐   │   │  │
│  │  │  │  (Basic)    │  │  │  │  Container Apps Environment  │   │   │  │
│  │  │  └────────────┘  │  │  │  (Internal Load Balancer)     │   │   │  │
│  │  └─────────────────┘  │  │  │                              │   │   │  │
│  │                        │  │  │  ← ContentFlow despliega:   │   │   │  │
│  │  ┌─────────────────┐  │  │  │    API / Worker / Web       │   │   │  │
│  │  │  PE Subnet      │  │  │  └──────────────────────────────┘   │   │  │
│  │  │                 │  │  └──────────────────────────────────────┘   │  │
│  │  │  ← ContentFlow  │  │                                            │  │
│  │  │    crea PEs:    │  │  ┌──────────────────────────────────────┐  │  │
│  │  │  ● Blob Storage │  │  │  Plataforma AILZ (módulo)            │  │  │
│  │  │  ● Cosmos DB    │  │  │                                      │  │  │
│  │  │  ● App Config   │  │  │  ● Log Analytics Workspace          │  │  │
│  │  │  ● ACR          │  │  │  ● Key Vault (GenAI)                │  │  │
│  │  │  ● AI Foundry   │  │  │  ● Container Registry (GenAI)       │  │  │
│  │  └─────────────────┘  │  │  ● Storage Account (GenAI, LRS)     │  │  │
│  │                        │  │  ● App Configuration (GenAI)        │  │  │
│  └───────────────────────│  │  ● Cosmos DB (GenAI)                │  │  │
│                           │  │  ● NSGs                             │  │  │
│  ┌────────────────────┐  │  └──────────────────────────────────────┘  │  │
│  │  Private DNS Zones │  │                                            │  │
│  │  (auto-vinculadas) │  └────────────────────────────────────────────┘  │
│  │                    │                                                   │
│  │  ● privatelink.blob.core.windows.net                                  │
│  │  ● privatelink.documents.azure.com                                    │
│  │  ● privatelink.azconfig.io                                            │
│  │  ● privatelink.azurecr.io                                             │
│  │  ● privatelink.cognitiveservices.azure.com                            │
│  │  ● privatelink.azurecontainerapps.io                                  │
│  │  ● (+ otras del módulo: vault, openai, etc.)                         │
│  └────────────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Resource Group: rg-contentflow-ailz (creado por azd up)                │
│                                                                         │
│  ● Storage Account (Blob + Queue) + Private Endpoints en pe-subnet     │
│  ● Cosmos DB + Private Endpoint en pe-subnet                           │
│  ● App Configuration + Private Endpoint en pe-subnet                   │
│  ● ACR Premium + Private Endpoint en pe-subnet                         │
│  ● AI Foundry (Cognitive Services) + Private Endpoint en pe-subnet     │
│  ● Container Apps (API, Worker, Web) → Container Apps Environment      │
│  ● Application Insights → Log Analytics Workspace (compartido)         │
│  ● User Assigned Managed Identity + Role Assignments                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Notas de Operación y Troubleshooting

### 11.1 Nombres de Subredes

El módulo AVM genera nombres de subredes internamente. ContentFlow espera `pe-subnet` y `aca-env-subnet`. Si los nombres generados por el módulo no coinciden, puedes:

1. **Verificar nombres reales** después del apply:
   ```bash
   terraform output subnets
   ```

2. **Configurar en ContentFlow** los nombres reales:
   ```bash
   azd env set PRIVATE_ENDPOINT_SUBNET_NAME "<nombre-real-pe-subnet>"
   azd env set CONTAINER_APPS_SUBNET_NAME "<nombre-real-aca-subnet>"
   ```

3. **Override en vnet_definition** (si el módulo lo permite):
   ```hcl
   vnet_definition = {
     address_space = ["10.0.0.0/16"]
     subnets = {
       pe-subnet = {
         name           = "pe-subnet"
         address_prefix = "10.0.1.0/27"
       }
       aca-env-subnet = {
         name           = "aca-env-subnet"
         address_prefix = "10.0.16.0/23"
       }
     }
   }
   ```

### 11.2 Container Apps Environment Dual

Si el módulo crea un Container Apps Environment pero ContentFlow también intenta crear uno durante `azd up`, podrías terminar con dos CAEs. Para evitar esto:

- **Opción A**: Configurar ContentFlow para usar el CAE existente (pasar su ID como variable de entorno)
- **Opción B**: Deshabilitar el CAE en el módulo (`deploy = false` en `container_app_environment_definition`) y dejar que ContentFlow lo cree

### 11.3 Error: "Address space conflict"

Si ves errores sobre conflictos de rango de IP:

```
Error: creating Virtual Network: the address space "192.168.0.0/20" overlaps with...
```

Asegúrate de usar un rango que **no esté en uso** en tu suscripción. Recomendamos `10.0.0.0/16` en lugar de `192.168.0.0/x`.

### 11.4 Error: "Insufficient subnet size"

Container Apps Environment requiere una subred de al menos `/23` (512 IPs). El módulo normalmente calcula esto correctamente, pero si haces override de subredes, asegúrate de respetar este mínimo.

### 11.5 Terraform Destroy: Orden de Dependencias

Para destruir la Mini-AILZ:

```bash
# PRIMERO: Destruir ContentFlow (tiene dependencias en la red)
cd /path/to/contentflow
azd down --force --purge

# SEGUNDO: Destruir la Mini-AILZ
cd /path/to/mini-ailz
terraform destroy
```

> **Importante**: Si intentas destruir la Mini-AILZ mientras ContentFlow tiene Private Endpoints activos en las subredes, el destroy fallará. Siempre destruye ContentFlow primero.

### 11.6 Restricción de Address Space para Foundry CapabilityHost

Si alguna vez necesitas habilitar AI Foundry con agent service (`capabilityHost`), hay una restricción conocida:

> El address space de la VNet **no puede ser** `192.168.0.0/16` (pero sí puede ser ranges dentro de él como `192.168.0.0/20`). Otros rangos RFC1918 como `10.0.0.0/8` y `172.16.0.0/12` **sí funcionan correctamente**.

Nuestro rango `10.0.0.0/16` no tiene este problema.

---

## 12. Limpieza de Recursos

### Limpieza Completa (ContentFlow + Mini-AILZ)

```bash
# 1. Destruir ContentFlow primero
cd /path/to/contentflow
azd down --force --purge

# 2. Destruir Mini-AILZ
cd /path/to/mini-ailz
terraform destroy -auto-approve

# 3. Verificar que el RG fue eliminado
az group show --name rg-mini-ailz-contentflow 2>/dev/null && echo "RG aún existe" || echo "RG eliminado"
```

### Limpieza Solo ContentFlow (mantener Mini-AILZ)

```bash
# Solo destruir ContentFlow, la red permanece para reusar
cd /path/to/contentflow
azd down --force --purge
```

### Purge de Recursos con Soft-Delete

Algunos recursos Azure tienen soft-delete. Si necesitas re-crear con el mismo nombre:

```bash
# Key Vault
az keyvault purge --name <nombre-kv>

# Cognitive Services
az cognitiveservices account purge \
  --location <location> \
  --resource-group <rg> \
  --name <name>

# App Configuration
az appconfig purge --name <nombre-appconfig>
```

---

## Referencia Rápida

### Versiones Utilizadas

| Componente | Versión |
|---|---|
| Terraform | >= 1.9, < 2.0 |
| AVM Pattern Module | 0.4.0 |
| azurerm provider | >= 3.116, < 5.0 |
| azapi provider | ~> 2.0 |
| ContentFlow | Modo `ailz-integrated` |

### Documentos Relacionados

- [01-overview.md](01-overview.md) — Visión general de ContentFlow
- [02-architecture-detailed.md](02-architecture-detailed.md) — Arquitectura técnica detallada
- [03-use_cases_examples.md](03-use_cases_examples.md) — Casos de uso y ejemplos
- [04-ai_lz_options.md](04-ai_lz_options.md) — Guía de despliegue AILZ (Azure CLI manual)
- **[Módulo AVM en GitHub](https://github.com/Azure/terraform-azurerm-avm-ptn-aiml-landing-zone)** — Código fuente y documentación completa
- **[Módulo AVM en Terraform Registry](https://registry.terraform.io/modules/Azure/avm-ptn-aiml-landing-zone/azurerm/latest)** — Registry oficial

---

> **Última actualización**: Julio 2025
> **Módulo fuente**: `Azure/avm-ptn-aiml-landing-zone/azurerm` v0.4.0
> **Autor**: Análisis técnico para demos ContentFlow con suscripción única
