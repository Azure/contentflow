# Guía de Despliegue: ContentFlow en Modo AI Landing Zone Integrated

> **Documento técnico operativo** - Instrucciones paso a paso para desplegar ContentFlow con conectividad privada usando una AI Landing Zone mínima en un ambiente de demo con suscripción única.

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [¿Qué es el Modo AILZ-Integrated?](#2-qué-es-el-modo-ailz-integrated)
3. [Arquitectura de Red: Basic vs AILZ](#3-arquitectura-de-red-basic-vs-ailz)
4. [Prerrequisitos Generales](#4-prerrequisitos-generales)
5. [El Problema: Demo con Suscripción Única](#5-el-problema-demo-con-suscripción-única)
6. [Solución: AI Landing Zone Mínima ("Mini-AILZ")](#6-solución-ai-landing-zone-mínima-mini-ailz)
7. [Paso a Paso: Crear la Mini-AILZ](#7-paso-a-paso-crear-la-mini-ailz)
8. [Paso a Paso: Desplegar ContentFlow en Modo AILZ](#8-paso-a-paso-desplegar-contentflow-en-modo-ailz)
9. [Acceso y Pruebas de Conectividad Privada](#9-acceso-y-pruebas-de-conectividad-privada)
10. [Mapa Completo de Parámetros](#10-mapa-completo-de-parámetros)
11. [Cambios por Recurso en Modo AILZ](#11-cambios-por-recurso-en-modo-ailz)
12. [Troubleshooting](#12-troubleshooting)
13. [Costos Estimados de la Mini-AILZ](#13-costos-estimados-de-la-mini-ailz)
14. [Limpieza de Recursos](#14-limpieza-de-recursos)

---

## 1. Resumen Ejecutivo

ContentFlow soporta dos modos de despliegue:

| Aspecto | `basic` | `ailz-integrated` |
|---|---|---|
| Endpoints | Públicos (internet) | Privados (VNet) |
| Red | Sin VNet | VNet + Private Endpoints |
| DNS | Resolución pública | Private DNS Zones |
| ACR SKU | Standard | **Premium** (requerido para PE) |
| Firewall de recursos | `Allow` (todo abierto) | `Deny` (solo PE) |
| Ingress de Container Apps | Externo (público) | **Interno** (solo VNet) |
| Acceso a la UI Web | Navegador directo | Requiere VPN/JumpBox |

**Escenario de este documento:** Tienes **una sola suscripción de Azure** para demos y quieres probar el modo `ailz-integrated` completo. Normalmente, la AI Landing Zone ya existe como infraestructura compartida enterprise. Aquí crearemos una **versión mínima ("Mini-AILZ")** en la misma suscripción para simular ese escenario.

---

## 2. ¿Qué es el Modo AILZ-Integrated?

En un entorno enterprise real, el **AI Landing Zone** es una infraestructura de red pre-provisionada por el equipo de plataforma que incluye:

- **Virtual Network (VNet)** con subredes dedicadas
- **Private DNS Zones** para resolución de nombres internos
- **Network Security Groups (NSGs)** y políticas de seguridad
- **JumpBox VM** para acceso administrativo
- **Shared Log Analytics** y **Application Insights** centralizados
- **Azure Firewall** o NVA para control de tráfico (enterprise completo)

ContentFlow en modo `ailz-integrated` **no crea red propia**. En su lugar:

1. **Reutiliza** la VNet y subredes existentes del AILZ
2. **Crea Private Endpoints** en la subred dedicada (`pe-subnet`)
3. **Registra registros DNS** en las Private DNS Zones existentes
4. **Configura todos los recursos** con `publicNetworkAccess: Disabled`
5. **Integra Container Apps Environment** con la VNet (modo interno)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI Landing Zone (VNet)                            │
│                                                                     │
│  ┌──────────────────────┐    ┌────────────────────────────────────┐ │
│  │   pe-subnet (/27+)   │    │   aca-env-subnet (/23)             │ │
│  │                      │    │                                    │ │
│  │  ● Storage PE (blob) │    │  ┌──────────────────────────────┐  │ │
│  │  ● Storage PE (queue)│    │  │  Container Apps Environment  │  │ │
│  │  ● Cosmos DB PE      │    │  │  (Internal Load Balancer)    │  │ │
│  │  ● App Config PE     │    │  │                              │  │ │
│  │  ● ACR PE (Premium)  │    │  │  ┌─────┐ ┌──────┐ ┌─────┐  │  │ │
│  │  ● AI Foundry PE     │    │  │  │ API │ │Worker│ │ Web │  │  │ │
│  │                      │    │  │  └─────┘ └──────┘ └─────┘  │  │ │
│  └──────────────────────┘    │  └──────────────────────────────┘  │ │
│                              └────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────┐ ┌──────────────────────────────────────────────┐  │
│  │  jumpbox-vm  │ │  Private DNS Zones (6 requeridas)            │  │
│  │  (acceso)    │ │  ● privatelink.blob.core.windows.net         │  │
│  └──────────────┘ │  ● privatelink.documents.azure.com           │  │
│                   │  ● privatelink.azconfig.io                   │  │
│                   │  ● privatelink.azurecr.io                    │  │
│                   │  ● privatelink.cognitiveservices.azure.com   │  │
│                   │  ● privatelink.azurecontainerapps.io         │  │
│                   └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Arquitectura de Red: Basic vs AILZ

### Modo Basic (Público)

```
Internet ──→ Container Apps (API/Web) ──→ Storage Account (público)
                                     ──→ Cosmos DB (público)
                                     ──→ App Config (público)
                                     ──→ ACR Standard (público)
                                     ──→ AI Foundry (público)
```

- Todos los recursos tienen endpoints públicos
- Accesibles desde cualquier IP
- Network ACLs: `defaultAction: Allow`

### Modo AILZ-Integrated (Privado)

```
JumpBox/VPN ──→ VNet ──→ Container Apps (interno) ──→ Storage PE (privado)
                                                  ──→ Cosmos PE (privado)
                                                  ──→ App Config PE (privado)
                                                  ──→ ACR PE Premium (privado)
                                                  ──→ AI Foundry PE (privado)
```

- Todos los recursos: `publicNetworkAccess: Disabled`
- Network ACLs: `defaultAction: Deny`, `bypass: AzureServices`
- Acceso solo vía Private Endpoints dentro de la VNet
- Container Apps: `internal: true`, solo accesible desde VNet

---

## 4. Prerrequisitos Generales

### Herramientas Requeridas

```bash
# Verificar instalación
az --version          # Azure CLI 2.60+
azd version           # Azure Developer CLI 1.5+
docker --version      # Docker Desktop (para build de containers)
```

### Permisos Azure Requeridos

| Permiso | Escenario | Razón |
|---|---|---|
| `Contributor` | Resource Group de ContentFlow | Crear todos los recursos |
| `Network Contributor` | Resource Group de la VNet | Crear Private Endpoints en subredes |
| `Private DNS Zone Contributor` | Resource Group de DNS Zones | Crear registros A para PEs |
| `User Access Administrator` | Resource Group | Asignar RBAC a Managed Identity |

> **Nota:** En el escenario Mini-AILZ (suscripción única), si usas un Resource Group separado para la red, necesitas permisos en ambos RGs.

### Registro de Providers

```bash
# Asegurar que estos providers estén registrados
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.DocumentDB
az provider register --namespace Microsoft.Network
az provider register --namespace Microsoft.CognitiveServices
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.AppConfiguration
```

---

## 5. El Problema: Demo con Suscripción Única

En un entorno enterprise real:

```
┌──────────────────────────────┐  ┌──────────────────────────────┐
│  Suscripción: Platform       │  │  Suscripción: Workloads      │
│                              │  │                              │
│  RG: rg-ailz-network        │  │  RG: rg-contentflow          │
│  ├── VNet                   │  │  ├── Storage + PE            │
│  ├── Private DNS Zones      │  │  ├── Cosmos DB + PE          │
│  ├── NSGs                   │  │  ├── Container Apps (int)    │
│  ├── Azure Firewall         │  │  ├── ACR Premium + PE        │
│  └── JumpBox VM             │  │  ├── App Config + PE         │
│                              │  │  └── AI Foundry + PE         │
│  (Manejado por Platform Team)│  │  (Manejado por App Team)     │
└──────────────────────────────┘  └──────────────────────────────┘
```

**Tu situación:** Solo tienes **una suscripción**. No existe un AILZ pre-provisionado. Necesitas:

1. **Simular** la infraestructura de red que normalmente provee el Platform Team
2. **Desplegar** ContentFlow en modo `ailz-integrated` apuntando a esa red
3. **Acceder** a los servicios internos para validar la demo

---

## 6. Solución: AI Landing Zone Mínima ("Mini-AILZ")

Crearemos la infraestructura mínima necesaria en un **Resource Group separado** dentro de la misma suscripción:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Suscripción Única de Demo                                          │
│                                                                     │
│  ┌──────────────────────────────┐  ┌─────────────────────────────┐ │
│  │ RG: rg-mini-ailz             │  │ RG: rg-contentflow-ailz     │ │
│  │                              │  │                             │ │
│  │ ● VNet (10.0.0.0/16)        │  │ ● Storage + PE              │ │
│  │   ├── pe-subnet /27         │  │ ● Cosmos DB + PE            │ │
│  │   ├── aca-env-subnet /23    │  │ ● ACR Premium + PE          │ │
│  │   └── jumpbox-subnet /27    │  │ ● App Config + PE           │ │
│  │                              │  │ ● Container Apps Env (int)  │ │
│  │ ● 6 Private DNS Zones       │  │ ● Container Apps (API/      │ │
│  │   (vinculadas a la VNet)     │  │   Worker/Web)               │ │
│  │                              │  │ ● AI Foundry + PE           │ │
│  │ ● JumpBox VM (B2s)          │  │ ● App Insights (nuevo)      │ │
│  │   (con Bastion o IP pública │  │ ● Log Analytics (nuevo)     │ │
│  │    temporal para demo)       │  │ ● User Assigned Identity    │ │
│  │                              │  │                             │ │
│  │ ● Log Analytics (opcional)   │  │                             │ │
│  │ ● App Insights (opcional)    │  │                             │ │
│  └──────────────────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### ¿Por qué un RG separado?

- **Simula el escenario real**: Red y aplicación en RGs diferentes
- **Limpieza fácil**: Puedes borrar `rg-contentflow-ailz` sin afectar la red
- **Permisos realistas**: Puedes validar que los permisos cross-RG funcionan
- **Reutilizable**: La Mini-AILZ puede servir para otras demos de servicios con Private Endpoints

---

## 7. Paso a Paso: Crear la Mini-AILZ

### 7.1 Definir Variables

```bash
# === CONFIGURACIÓN ===
# Ajusta estos valores a tu ambiente
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
LOCATION="eastus2"                          # Tu región preferida
AILZ_RG="rg-mini-ailz"                      # RG para la infraestructura de red
CF_RG="rg-contentflow-ailz"                 # RG para ContentFlow (lo crea azd)
VNET_NAME="vnet-ailz-demo"
VNET_PREFIX="10.0.0.0/16"

# Subredes
PE_SUBNET_NAME="pe-subnet"                  # Nombre esperado por ContentFlow
PE_SUBNET_PREFIX="10.0.1.0/27"              # /27 = 32 IPs (suficiente para ~25 PEs)
ACA_SUBNET_NAME="aca-env-subnet"            # Nombre esperado por ContentFlow
ACA_SUBNET_PREFIX="10.0.16.0/23"            # /23 = 512 IPs (requerido por Container Apps)
JUMPBOX_SUBNET_NAME="jumpbox-subnet"
JUMPBOX_SUBNET_PREFIX="10.0.2.0/27"         # /27 = 32 IPs
```

### 7.2 Crear Resource Group de Red

```bash
az group create \
  --name $AILZ_RG \
  --location $LOCATION \
  --tags purpose=mini-ailz owner=demo
```

### 7.3 Crear Virtual Network con Subredes

```bash
# Crear VNet
az network vnet create \
  --resource-group $AILZ_RG \
  --name $VNET_NAME \
  --address-prefix $VNET_PREFIX \
  --location $LOCATION \
  --tags purpose=mini-ailz

# Subred para Private Endpoints
az network vnet subnet create \
  --resource-group $AILZ_RG \
  --vnet-name $VNET_NAME \
  --name $PE_SUBNET_NAME \
  --address-prefix $PE_SUBNET_PREFIX

# Subred para Container Apps Environment
# IMPORTANTE: Container Apps necesita /23 mínimo y la subred debe estar delegada
az network vnet subnet create \
  --resource-group $AILZ_RG \
  --vnet-name $VNET_NAME \
  --name $ACA_SUBNET_NAME \
  --address-prefix $ACA_SUBNET_PREFIX

# Subred para JumpBox
az network vnet subnet create \
  --resource-group $AILZ_RG \
  --vnet-name $VNET_NAME \
  --name $JUMPBOX_SUBNET_NAME \
  --address-prefix $JUMPBOX_SUBNET_PREFIX
```

> **Nota sobre el tamaño de subred para Container Apps:** Container Apps Environment en modo VNet-integrated requiere una subred de al menos `/23` (512 direcciones). Esto es un requisito de la plataforma para manejar la infraestructura interna del entorno.

### 7.4 Crear las 6 Private DNS Zones Requeridas

Cada zona debe vincularse (link) a la VNet para que la resolución DNS funcione:

```bash
# Lista de zonas requeridas por ContentFlow
DNS_ZONES=(
  "privatelink.blob.core.windows.net"
  "privatelink.documents.azure.com"
  "privatelink.azconfig.io"
  "privatelink.azurecr.io"
  "privatelink.cognitiveservices.azure.com"
  "privatelink.azurecontainerapps.io"
)

# Crear cada zona y vincularla a la VNet
for ZONE in "${DNS_ZONES[@]}"; do
  echo "Creando DNS Zone: $ZONE"
  
  # Crear la zona
  az network private-dns zone create \
    --resource-group $AILZ_RG \
    --name "$ZONE" \
    --tags purpose=mini-ailz

  # Vincular la zona a la VNet (CRÍTICO - sin esto la resolución DNS no funciona)
  LINK_NAME=$(echo "$ZONE" | sed 's/\./-/g')-link
  az network private-dns link vnet create \
    --resource-group $AILZ_RG \
    --zone-name "$ZONE" \
    --name "$LINK_NAME" \
    --virtual-network "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$AILZ_RG/providers/Microsoft.Network/virtualNetworks/$VNET_NAME" \
    --registration-enabled false
done

echo "✓ 6 Private DNS Zones creadas y vinculadas a la VNet"
```

### 7.5 (Opcional) Crear Private DNS Zone para Key Vault

```bash
# Solo si planeas usar Key Vault con Private Endpoint
az network private-dns zone create \
  --resource-group $AILZ_RG \
  --name "privatelink.vaultcore.azure.net" \
  --tags purpose=mini-ailz

az network private-dns link vnet create \
  --resource-group $AILZ_RG \
  --zone-name "privatelink.vaultcore.azure.net" \
  --name "privatelink-vaultcore-azure-net-link" \
  --virtual-network "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$AILZ_RG/providers/Microsoft.Network/virtualNetworks/$VNET_NAME" \
  --registration-enabled false
```

### 7.6 Crear JumpBox VM

La JumpBox es necesaria para acceder a los servicios internos después del despliegue. Tienes **tres opciones**:

#### Opción A: JumpBox con Azure Bastion (Recomendada para Demo)

Azure Bastion provee acceso seguro RDP/SSH sin exponer IP pública en la VM.

```bash
# Crear subred para Azure Bastion (REQUIERE nombre exacto y mínimo /26)
az network vnet subnet create \
  --resource-group $AILZ_RG \
  --vnet-name $VNET_NAME \
  --name "AzureBastionSubnet" \
  --address-prefix "10.0.3.0/26"

# Crear IP pública para Bastion
az network public-ip create \
  --resource-group $AILZ_RG \
  --name "pip-bastion-demo" \
  --sku Standard \
  --allocation-method Static \
  --location $LOCATION

# Crear Azure Bastion (Developer SKU - más económico)
az network bastion create \
  --resource-group $AILZ_RG \
  --name "bastion-demo" \
  --public-ip-address "pip-bastion-demo" \
  --vnet-name $VNET_NAME \
  --sku Developer \
  --location $LOCATION

# Crear la JumpBox VM (sin IP pública - Bastion proporciona acceso)
az vm create \
  --resource-group $AILZ_RG \
  --name "jmp-ailz-demo" \
  --image "MicrosoftWindowsDesktop:windows-11:win11-24h2-pro:latest" \
  --size "Standard_B2ms" \
  --vnet-name $VNET_NAME \
  --subnet $JUMPBOX_SUBNET_NAME \
  --public-ip-address "" \
  --admin-username "azureuser" \
  --admin-password "$(openssl rand -base64 16)A1!" \
  --tags role=jumpbox purpose=mini-ailz \
  --location $LOCATION
```

> **Importante:** Anota la contraseña generada. También puedes usar `--admin-password` con un valor específico que controles.

#### Opción B: JumpBox con IP Pública Temporal (Más Simple)

```bash
# JumpBox con IP pública (solo para demo, desactivar después)
az vm create \
  --resource-group $AILZ_RG \
  --name "jmp-ailz-demo" \
  --image "MicrosoftWindowsDesktop:windows-11:win11-24h2-pro:latest" \
  --size "Standard_B2ms" \
  --vnet-name $VNET_NAME \
  --subnet $JUMPBOX_SUBNET_NAME \
  --admin-username "azureuser" \
  --admin-password "TuPasswordSeguro123!" \
  --tags role=jumpbox purpose=mini-ailz \
  --nsg-rule RDP \
  --location $LOCATION
```

> **Seguridad:** Restringe RDP solo a tu IP:
> ```bash
> MY_IP=$(curl -s https://api.ipify.org)
> az network nsg rule update \
>   --resource-group $AILZ_RG \
>   --nsg-name "jmp-ailz-demoNSG" \
>   --name "rdp" \
>   --source-address-prefixes "$MY_IP/32"
> ```

#### Opción C: JumpBox Linux (Más Económica)

```bash
az vm create \
  --resource-group $AILZ_RG \
  --name "jmp-ailz-demo" \
  --image "Ubuntu2404" \
  --size "Standard_B2s" \
  --vnet-name $VNET_NAME \
  --subnet $JUMPBOX_SUBNET_NAME \
  --admin-username "azureuser" \
  --generate-ssh-keys \
  --tags role=jumpbox purpose=mini-ailz \
  --public-ip-address "" \
  --location $LOCATION
```

### 7.7 (Opcional) Crear Observabilidad Compartida

Si quieres simular el escenario enterprise donde Log Analytics y App Insights son compartidos:

```bash
# Log Analytics Workspace compartido
az monitor log-analytics workspace create \
  --resource-group $AILZ_RG \
  --workspace-name "log-ailz-shared" \
  --sku PerGB2018 \
  --location $LOCATION \
  --tags purpose=mini-ailz

# Application Insights compartido
LOG_WS_ID=$(az monitor log-analytics workspace show \
  --resource-group $AILZ_RG \
  --workspace-name "log-ailz-shared" \
  --query id -o tsv)

az monitor app-insights component create \
  --resource-group $AILZ_RG \
  --app "appi-ailz-shared" \
  --location $LOCATION \
  --workspace "$LOG_WS_ID" \
  --tags purpose=mini-ailz
```

> **Nota:** Si no creas estos recursos, ContentFlow en modo `ailz-integrated` **creará sus propios** Log Analytics y App Insights (el código Bicep lo contempla). Solo necesitas crearlos si quieres probar el escenario de observabilidad compartida.

### 7.8 Verificar la Mini-AILZ

```bash
echo "=== Verificación de Mini-AILZ ==="

echo "VNet:"
az network vnet show -g $AILZ_RG -n $VNET_NAME --query "{name:name, address:addressSpace.addressPrefixes[0]}" -o table

echo ""
echo "Subredes:"
az network vnet subnet list -g $AILZ_RG --vnet-name $VNET_NAME --query "[].{name:name, prefix:addressPrefix}" -o table

echo ""
echo "Private DNS Zones:"
az network private-dns zone list -g $AILZ_RG --query "[].{name:name, links:numberOfVirtualNetworkLinks}" -o table

echo ""
echo "JumpBox VM:"
az vm list -g $AILZ_RG --query "[].{name:name, size:hardwareProfile.vmSize, tags:tags.role}" -o table
```

Salida esperada:
```
=== Verificación de Mini-AILZ ===
VNet:
Name             Address
-----------      ----------
vnet-ailz-demo   10.0.0.0/16

Subredes:
Name              Prefix
-----------       ----------
pe-subnet         10.0.1.0/27
aca-env-subnet    10.0.16.0/23
jumpbox-subnet    10.0.2.0/27

Private DNS Zones:
Name                                           Links
---------------------------------------------  -----
privatelink.blob.core.windows.net              1
privatelink.documents.azure.com                1
privatelink.azconfig.io                        1
privatelink.azurecr.io                         1
privatelink.cognitiveservices.azure.com        1
privatelink.azurecontainerapps.io              1

JumpBox VM:
Name            Size           Tags
-----------     -----------   --------
jmp-ailz-demo   Standard_B2ms jumpbox
```

---

## 8. Paso a Paso: Desplegar ContentFlow en Modo AILZ

### 8.1 Obtener IDs de Recursos de la Mini-AILZ

Usa el script incluido en ContentFlow o hazlo manualmente:

#### Opción A: Script Automático (Recomendada)

```bash
cd infra/scripts

# Ejecutar con auto-set (configura variables de azd automáticamente)
./get-ailz-resources.sh --auto-set
# Cuando pregunte por el RG, ingresa: rg-mini-ailz
```

El script busca automáticamente:
- VNet y subredes (`pe-subnet`, `aca-env-subnet`)
- Las 6 Private DNS Zones requeridas
- JumpBox VM (busca tag `role=jumpbox` o nombre con `jmp`)
- Log Analytics y App Insights (opcionales)

Genera un archivo `ailz-resources.env` y con `--auto-set` configura las variables en azd directamente.

#### Opción B: Recopilación Manual

```bash
# Obtener VNet Resource ID
VNET_ID=$(az network vnet show -g $AILZ_RG -n $VNET_NAME --query id -o tsv)
echo "VNET_ID: $VNET_ID"

# Obtener IDs de Private DNS Zones
BLOB_DNS_ID=$(az network private-dns zone show -g $AILZ_RG -n "privatelink.blob.core.windows.net" --query id -o tsv)
COSMOS_DNS_ID=$(az network private-dns zone show -g $AILZ_RG -n "privatelink.documents.azure.com" --query id -o tsv)
APPCONFIG_DNS_ID=$(az network private-dns zone show -g $AILZ_RG -n "privatelink.azconfig.io" --query id -o tsv)
ACR_DNS_ID=$(az network private-dns zone show -g $AILZ_RG -n "privatelink.azurecr.io" --query id -o tsv)
COGNITIVE_DNS_ID=$(az network private-dns zone show -g $AILZ_RG -n "privatelink.cognitiveservices.azure.com" --query id -o tsv)
ACA_DNS_ID=$(az network private-dns zone show -g $AILZ_RG -n "privatelink.azurecontainerapps.io" --query id -o tsv)

# Opcionales
LOG_WS_ID=$(az monitor log-analytics workspace show -g $AILZ_RG -n "log-ailz-shared" --query id -o tsv 2>/dev/null || echo "")
APPI_ID=$(az monitor app-insights component show -g $AILZ_RG --app "appi-ailz-shared" --query id -o tsv 2>/dev/null || echo "")
```

### 8.2 Inicializar Entorno de azd

```bash
# Ir al raíz del repositorio
cd /ruta/a/contentflow

# Inicializar nuevo entorno azd
azd init -e contentflow-ailz-demo

# Configurar ubicación y suscripción
azd env set AZURE_LOCATION "$LOCATION"
azd env set AZURE_AI_FOUNDRY_LOCATION "$LOCATION"
```

### 8.3 Configurar Variables de Modo AILZ

```bash
# === MODO DE DESPLIEGUE ===
azd env set DEPLOYMENT_MODE "ailz-integrated"

# === RED ===
azd env set EXISTING_VNET_RESOURCE_ID "$VNET_ID"
azd env set PRIVATE_ENDPOINT_SUBNET_NAME "pe-subnet"
azd env set CONTAINER_APPS_SUBNET_NAME "aca-env-subnet"

# === PRIVATE DNS ZONES (6 requeridas) ===
azd env set EXISTING_BLOB_PRIVATE_DNS_ZONE_ID "$BLOB_DNS_ID"
azd env set EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID "$COSMOS_DNS_ID"
azd env set EXISTING_APP_CONFIG_PRIVATE_DNS_ZONE_ID "$APPCONFIG_DNS_ID"
azd env set EXISTING_ACR_PRIVATE_DNS_ZONE_ID "$ACR_DNS_ID"
azd env set EXISTING_COGNITIVE_SERVICES_PRIVATE_DNS_ZONE_ID "$COGNITIVE_DNS_ID"
azd env set EXISTING_CONTAINER_APPS_ENV_PRIVATE_DNS_ZONE_ID "$ACA_DNS_ID"

# === OPCIONALES: OBSERVABILIDAD COMPARTIDA ===
# Solo si creaste Log Analytics y App Insights compartidos en el paso 7.7
if [ ! -z "$LOG_WS_ID" ]; then
  azd env set EXISTING_LOG_ANALYTICS_WORKSPACE_ID "$LOG_WS_ID"
fi
if [ ! -z "$APPI_ID" ]; then
  azd env set EXISTING_APP_INSIGHTS_ID "$APPI_ID"
fi

# === Principal ID (tu usuario para RBAC) ===
PRINCIPAL_ID=$(az ad signed-in-user show --query id -o tsv)
azd env set AZURE_PRINCIPAL_ID "$PRINCIPAL_ID"
```

### 8.4 Verificar Configuración

```bash
# Listar todas las variables del entorno azd
azd env get-values | grep -E "DEPLOYMENT_MODE|EXISTING_|PRIVATE_|CONTAINER_APPS_SUBNET|AZURE_LOCATION"
```

Salida esperada:
```
DEPLOYMENT_MODE="ailz-integrated"
EXISTING_VNET_RESOURCE_ID="/subscriptions/.../virtualNetworks/vnet-ailz-demo"
PRIVATE_ENDPOINT_SUBNET_NAME="pe-subnet"
CONTAINER_APPS_SUBNET_NAME="aca-env-subnet"
EXISTING_BLOB_PRIVATE_DNS_ZONE_ID="/subscriptions/.../privateDnsZones/privatelink.blob.core.windows.net"
EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID="/subscriptions/.../privateDnsZones/privatelink.documents.azure.com"
EXISTING_APP_CONFIG_PRIVATE_DNS_ZONE_ID="/subscriptions/.../privateDnsZones/privatelink.azconfig.io"
EXISTING_ACR_PRIVATE_DNS_ZONE_ID="/subscriptions/.../privateDnsZones/privatelink.azurecr.io"
EXISTING_COGNITIVE_SERVICES_PRIVATE_DNS_ZONE_ID="/subscriptions/.../privateDnsZones/privatelink.cognitiveservices.azure.com"
EXISTING_CONTAINER_APPS_ENV_PRIVATE_DNS_ZONE_ID="/subscriptions/.../privateDnsZones/privatelink.azurecontainerapps.io"
AZURE_LOCATION="eastus2"
```

### 8.5 Desplegar

```bash
# Despliegue completo (provision + build + deploy)
azd up
```

**¿Qué sucede durante `azd up`?**

1. **Pre-provision hook**: Valida que Azure CLI, azd y Docker estén instalados
2. **Bicep Provisioning**:
   - Valida parámetros AILZ (all 6 DNS zones + VNet + subredes)
   - Crea User Assigned Identity
   - Crea Storage Account con PE en `pe-subnet` → registra en `privatelink.blob.core.windows.net`
   - Crea Cosmos DB con PE en `pe-subnet` → registra en `privatelink.documents.azure.com`
   - Crea App Configuration con PE en `pe-subnet` → registra en `privatelink.azconfig.io`
   - Crea Container Registry **Premium** con PE en `pe-subnet` → registra en `privatelink.azurecr.io`
   - Crea Container Apps Environment **interno** en `aca-env-subnet`
   - Crea Container Apps (API, Worker, Web) con ingress **interno**
   - Crea AI Foundry Hub & Project
   - Si no proporcionaste Log Analytics/App Insights existentes: crea nuevos
   - Configura RBAC para la Managed Identity
3. **Container Build**: Construye imágenes Docker para API, Worker, Web
4. **Push to ACR**: Sube imágenes a Container Registry (vía PE si estás en la VNet, o vía Azure CLI si públicamente)
5. **Deploy to Container Apps**: Despliega las apps (internamente accesibles)
6. **Post-deploy hook**: Muestra endpoints (internos)

> **⚠️ IMPORTANTE sobre el push a ACR:** En modo AILZ, el ACR tiene `publicNetworkAccess: Disabled`. Si ejecutas `azd up` desde tu máquina local (fuera de la VNet), el push de imágenes **podría fallar**. Ver sección de Troubleshooting para soluciones.

### 8.6 Verificar Despliegue

```bash
# Verificar que los Private Endpoints se crearon correctamente
az network private-endpoint list \
  --resource-group $(azd env get-value AZURE_RESOURCE_GROUP) \
  --query "[].{name:name, status:privateLinkServiceConnections[0].privateLinkServiceConnectionState.status}" \
  -o table
```

Salida esperada:
```
Name                      Status
-----------------------   ---------
stXXXXX-blob-pe           Approved
stXXXXX-queue-pe          Approved
cosmos-XXXXX-pe           Approved
appcs-XXXXX-pe            Approved
crXXXXX-pe                Approved
```

---

## 9. Acceso y Pruebas de Conectividad Privada

### 9.1 Acceder vía JumpBox

Dado que todos los servicios son internos, necesitas estar dentro de la VNet:

```bash
# Conectar a la JumpBox vía Bastion (Portal Azure)
# O vía Azure CLI:
az network bastion ssh \
  --resource-group $AILZ_RG \
  --name "bastion-demo" \
  --target-resource-id $(az vm show -g $AILZ_RG -n "jmp-ailz-demo" --query id -o tsv) \
  --auth-type password \
  --username azureuser
```

### 9.2 Conseguir URLs Internas

Las URLs de Container Apps en modo interno tienen el formato:
```
https://<app-name>.<unique-id>.<region>.azurecontainerapps.io
```

Pero solo son resolvibles dentro de la VNet (gracias a la Private DNS Zone `privatelink.azurecontainerapps.io`).

```bash
# Obtener URLs internas desde azd
azd env get-values | grep "SERVICE_.*_URI"

# O directamente:
API_URL=$(az containerapp show -g $(azd env get-value AZURE_RESOURCE_GROUP) -n $(azd env get-value API_CONTAINER_APP_NAME) --query "properties.configuration.ingress.fqdn" -o tsv)
WEB_URL=$(az containerapp show -g $(azd env get-value AZURE_RESOURCE_GROUP) -n $(azd env get-value WEB_CONTAINER_APP_NAME) --query "properties.configuration.ingress.fqdn" -o tsv)

echo "API: https://$API_URL"
echo "Web: https://$WEB_URL"
```

### 9.3 Probar desde la JumpBox

Desde la JumpBox (Windows):
```powershell
# Verificar resolución DNS (debe resolver a IP privada 10.x.x.x)
nslookup <api-fqdn>

# Probar API health check
Invoke-WebRequest -Uri "https://<api-fqdn>/health" -UseBasicParsing

# Abrir navegador para la Web UI
Start-Process "https://<web-fqdn>"
```

Desde la JumpBox (Linux):
```bash
# Verificar resolución DNS
nslookup <api-fqdn>
# Debe retornar IP privada (10.x.x.x), NO una IP pública

# Probar API
curl -k https://<api-fqdn>/health

# Probar que los Private Endpoints resuelven correctamente
nslookup <storage-account>.blob.core.windows.net
# Debe retornar privatelink.blob.core.windows.net → 10.x.x.x

nslookup <cosmos-account>.documents.azure.com
# Debe retornar privatelink.documents.azure.com → 10.x.x.x
```

### 9.4 Probar Resolución DNS de Cada Servicio

```bash
# Desde la JumpBox, verificar que todos los PEs resuelven a IPs privadas
SERVICES=(
  "<storage-account>.blob.core.windows.net"
  "<storage-account>.queue.core.windows.net"
  "<cosmos-account>.documents.azure.com"
  "<appconfig-name>.azconfig.io"
  "<acr-name>.azurecr.io"
)

for SVC in "${SERVICES[@]}"; do
  echo "=== $SVC ==="
  nslookup $SVC
  echo ""
done
```

---

## 10. Mapa Completo de Parámetros

### Variables de Entorno azd → Parámetros Bicep

| Variable azd | Parámetro Bicep | Requerido en AILZ | Default | Descripción |
|---|---|---|---|---|
| `DEPLOYMENT_MODE` | `deploymentMode` | ✅ | — | Debe ser `ailz-integrated` |
| `AZURE_ENV_NAME` | `environmentName` | ✅ | — | Nombre del entorno |
| `AZURE_LOCATION` | `location` | ✅ | — | Región Azure |
| `AZURE_AI_FOUNDRY_LOCATION` | `foundryLocation` | ✅ | — | Región para AI Foundry |
| `AZURE_PRINCIPAL_ID` | `principalId` | ⬜ | `""` | Tu Object ID para RBAC |
| `EXISTING_VNET_RESOURCE_ID` | `existingVnetResourceId` | ✅ | `""` | Resource ID completo de la VNet |
| `PRIVATE_ENDPOINT_SUBNET_NAME` | `privateEndpointSubnetName` | ✅ | `pe-subnet` | Nombre de la subred para PEs |
| `CONTAINER_APPS_SUBNET_NAME` | `containerAppsSubnetName` | ✅ | `aca-env-subnet` | Nombre de la subred para CAE |
| `EXISTING_COGNITIVE_SERVICES_PRIVATE_DNS_ZONE_ID` | `existingCognitiveServicesPrivateDnsZoneId` | ✅ | `""` | DNS Zone para AI Services |
| `EXISTING_BLOB_PRIVATE_DNS_ZONE_ID` | `existingBlobPrivateDnsZoneId` | ✅ | `""` | DNS Zone para Blob Storage |
| `EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID` | `existingCosmosPrivateDnsZoneId` | ✅ | `""` | DNS Zone para Cosmos DB |
| `EXISTING_APP_CONFIG_PRIVATE_DNS_ZONE_ID` | `existingAppConfigPrivateDnsZoneId` | ✅ | `""` | DNS Zone para App Config |
| `EXISTING_ACR_PRIVATE_DNS_ZONE_ID` | `existingAcrPrivateDnsZoneId` | ✅ | `""` | DNS Zone para Container Registry |
| `EXISTING_CONTAINER_APPS_ENV_PRIVATE_DNS_ZONE_ID` | `existingContainerAppsEnvPrivateDnsZoneId` | ✅ | `""` | DNS Zone para Container Apps |
| `EXISTING_KEY_VAULT_PRIVATE_DNS_ZONE_ID` | `existingKeyVaultPrivateDnsZoneId` | ⬜ | `""` | DNS Zone para Key Vault |
| `EXISTING_LOG_ANALYTICS_WORKSPACE_ID` | `existingLogAnalyticsWorkspaceId` | ⬜ | `""` | Log Analytics compartido |
| `EXISTING_APP_INSIGHTS_ID` | `existingAppInsightsId` | ⬜ | `""` | App Insights compartido |

### Formato de Resource IDs

```
VNet:       /subscriptions/{subId}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks/{name}
DNS Zone:   /subscriptions/{subId}/resourceGroups/{rg}/providers/Microsoft.Network/privateDnsZones/{zone-name}
Log Analyt: /subscriptions/{subId}/resourceGroups/{rg}/providers/Microsoft.OperationalInsights/workspaces/{name}
App Insigh: /subscriptions/{subId}/resourceGroups/{rg}/providers/Microsoft.Insights/components/{name}
```

---

## 11. Cambios por Recurso en Modo AILZ

### Comparativa Detallada

| Recurso | Basic | AILZ-Integrated |
|---|---|---|
| **Storage Account** | SKU: Standard_LRS, Public | SKU: Standard_LRS, **PE (blob+queue)**, `Deny` ACL |
| **Cosmos DB** | Serverless, Public | Serverless, **PE**, `Disabled` public access |
| **App Configuration** | Standard, Public | Standard, **PE**, `Disabled` public access |
| **Container Registry** | **Standard** | **Premium** (requerido para PE), **PE** |
| **Container Apps Env** | Public, External LB | **VNet-integrated**, **Internal LB**, `aca-env-subnet` |
| **Container Apps (API)** | `externalIngress: true` | `externalIngress: false` (solo VNet) |
| **Container Apps (Worker)** | `externalIngress: true` | `externalIngress: false` (solo VNet) |
| **Container Apps (Web)** | `externalIngress: true` | `externalIngress: false` (solo VNet) |
| **AI Foundry** | Public | **PE** para Cognitive Services |
| **Log Analytics** | Creado nuevo (basic) | Usa existente O crea nuevo |
| **App Insights** | Creado nuevo (basic) | Usa existente O crea nuevo |
| **Managed Identity** | Sin cambios | Sin cambios |

### Nomenclatura de Private Endpoints

ContentFlow usa una convención consistente:

```
{resourceName}-{service}-pe        → Nombre del Private Endpoint
{resourceName}-{service}-plsc      → Private Link Service Connection
{service}-dns-zone-group           → DNS Zone Group
{service}-config                   → DNS Zone Group Config
```

Ejemplos:
- `st4a7b2c-blob-pe` / `st4a7b2c-blob-plsc`
- `st4a7b2c-queue-pe` / `st4a7b2c-queue-plsc`
- `cosmos-4a7b2c-pe` / `cosmos-4a7b2c-cosmos-plsc`
- `appcs-4a7b2c-pe` / `appcs-4a7b2c-app-config-plsc`
- `cr4a7b2c-pe` / `cr4a7b2c-acr-plsc`

---

## 12. Troubleshooting

### Problema 1: Error "ACR push failed" durante `azd up`

**Causa:** ACR tiene `publicNetworkAccess: Disabled`. Tu máquina local no puede hacer push de imágenes.

**Soluciones:**

**Solución A - Temporalmente habilitar acceso público al ACR:**
```bash
# Antes de azd deploy
ACR_NAME=$(azd env get-value AZURE_CONTAINER_REGISTRY_NAME)
CF_RG=$(azd env get-value AZURE_RESOURCE_GROUP)

# Habilitar temporalmente
az acr update -n $ACR_NAME -g $CF_RG --public-network-enabled true

# Hacer el deploy
azd deploy

# Volver a deshabilitar
az acr update -n $ACR_NAME -g $CF_RG --public-network-enabled false
```

**Solución B - Build y push desde la JumpBox:**
```bash
# Ejecutar azd up desde la JumpBox (dentro de la VNet)
# Requiere instalar azd, az cli, docker en la JumpBox
```

**Solución C - Usar ACR Tasks (build en la nube):**
```bash
# ACR Tasks puede hacer build sin necesidad de Docker local
az acr build --registry $ACR_NAME -t contentflow-api:latest ./contentflow-api/
az acr build --registry $ACR_NAME -t contentflow-worker:latest ./contentflow-worker/
az acr build --registry $ACR_NAME -t contentflow-web:latest ./contentflow-web/
```

### Problema 2: Error "VNet subnet not found"

**Causa:** Los nombres de subred no coinciden con los esperados.

**Solución:**
```bash
# Verificar nombres exactos
az network vnet subnet list -g $AILZ_RG --vnet-name $VNET_NAME --query "[].name" -o tsv

# Si los nombres son diferentes, ajustar:
azd env set PRIVATE_ENDPOINT_SUBNET_NAME "tu-nombre-de-pe-subnet"
azd env set CONTAINER_APPS_SUBNET_NAME "tu-nombre-de-aca-subnet"
```

### Problema 3: Error de validación "fail('existingXXX is required')"

**Causa:** Falta algún parámetro requerido para modo `ailz-integrated`.

**Solución:** Ejecutar el script de verificación:
```bash
# Verificar todas las variables están configuradas
REQUIRED_VARS=(
  "DEPLOYMENT_MODE"
  "EXISTING_VNET_RESOURCE_ID"
  "EXISTING_BLOB_PRIVATE_DNS_ZONE_ID"
  "EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID"
  "EXISTING_APP_CONFIG_PRIVATE_DNS_ZONE_ID"
  "EXISTING_ACR_PRIVATE_DNS_ZONE_ID"
  "EXISTING_COGNITIVE_SERVICES_PRIVATE_DNS_ZONE_ID"
  "EXISTING_CONTAINER_APPS_ENV_PRIVATE_DNS_ZONE_ID"
)

for VAR in "${REQUIRED_VARS[@]}"; do
  VALUE=$(azd env get-value $VAR 2>/dev/null)
  if [ -z "$VALUE" ]; then
    echo "❌ FALTA: $VAR"
  else
    echo "✓ $VAR configurada"
  fi
done
```

### Problema 4: DNS no resuelve a IP privada desde JumpBox

**Causa:** La Private DNS Zone no está vinculada a la VNet, o el DNS Zone Group no se creó.

**Solución:**
```bash
# Verificar que cada zona tiene un VNet link
for ZONE in "privatelink.blob.core.windows.net" "privatelink.documents.azure.com" "privatelink.azconfig.io" "privatelink.azurecr.io" "privatelink.cognitiveservices.azure.com" "privatelink.azurecontainerapps.io"; do
  echo "=== $ZONE ==="
  az network private-dns link vnet list --zone-name $ZONE -g $AILZ_RG --query "[].{name:name, state:virtualNetworkLinkState}" -o table
done

# Si falta un link:
az network private-dns link vnet create \
  --resource-group $AILZ_RG \
  --zone-name "privatelink.blob.core.windows.net" \
  --name "blob-vnet-link" \
  --virtual-network "$VNET_ID" \
  --registration-enabled false
```

### Problema 5: Container Apps no inician (health check failed)

**Causa:** Las Container Apps no pueden alcanzar los servicios backend (Storage, Cosmos) porque los PEs no están configurados correctamente o los DNS Zone Groups no registraron los records A.

**Solución:**
```bash
# Verificar logs de Container Apps
az containerapp logs show \
  -n $(azd env get-value API_CONTAINER_APP_NAME) \
  -g $(azd env get-value AZURE_RESOURCE_GROUP) \
  --type system

# Verificar que los A records existen en las DNS zones
az network private-dns record-set a list -g $AILZ_RG -z "privatelink.blob.core.windows.net" -o table
az network private-dns record-set a list -g $AILZ_RG -z "privatelink.documents.azure.com" -o table
```

### Problema 6: Permisos insuficientes para crear PE en subnet de otro RG

**Causa:** Tu usuario no tiene `Network Contributor` en el RG de la VNet.

**Solución:**
```bash
# Asignar permisos en el RG de red
USER_OBJ_ID=$(az ad signed-in-user show --query id -o tsv)

az role assignment create \
  --assignee $USER_OBJ_ID \
  --role "Network Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$AILZ_RG"

az role assignment create \
  --assignee $USER_OBJ_ID \
  --role "Private DNS Zone Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$AILZ_RG"
```

### Problema 7: Error "Container Apps Environment subnet too small"

**Causa:** La subred `aca-env-subnet` es menor a `/23`.

**Solución:** Recrear la subred con el tamaño correcto (requiere borrar la existente primero si no tiene recursos):
```bash
az network vnet subnet delete -g $AILZ_RG --vnet-name $VNET_NAME -n $ACA_SUBNET_NAME
az network vnet subnet create \
  --resource-group $AILZ_RG \
  --vnet-name $VNET_NAME \
  --name $ACA_SUBNET_NAME \
  --address-prefix "10.0.16.0/23"
```

---

## 13. Costos Estimados de la Mini-AILZ

### Recursos de Red (RG: rg-mini-ailz)

| Recurso | SKU/Tier | Costo Estimado (USD/mes) |
|---|---|---|
| VNet + Subredes | Gratuito | $0 |
| Private DNS Zones (6) | $0.50/zona | ~$3 |
| Azure Bastion | Developer SKU | ~$5.50 |
| JumpBox VM (B2ms, Windows) | Standard_B2ms | ~$60 (24/7) |
| JumpBox VM (B2s, Linux) | Standard_B2s | ~$15 (24/7) |

**Tip para reducir costos de demo:**
```bash
# Apagar la JumpBox cuando no la uses
az vm deallocate -g $AILZ_RG -n "jmp-ailz-demo"

# Encenderla cuando la necesites
az vm start -g $AILZ_RG -n "jmp-ailz-demo"
```

### Recursos ContentFlow Adicionales en AILZ vs Basic

| Recurso | Cambio en AILZ | Impacto en Costo |
|---|---|---|
| Container Registry | Standard → **Premium** | +~$45/mes |
| Private Endpoints (5-6) | Cada PE tiene costo | +~$5/mes total |
| Procesamiento de PE (datos) | Por GB procesado | Mínimo en demo |

### Costo Total Estimado de Demo (Mini-AILZ + ContentFlow)

| Componente | Costo Estimado |
|---|---|
| Mini-AILZ (red + JumpBox Linux + Bastion) | ~$24/mes |
| ContentFlow AILZ (Premium ACR, PEs) delta vs Basic | ~$50/mes |
| ContentFlow base (Storage, Cosmos, Container Apps, AI) | ~$30-80/mes |
| **Total estimado** | **~$100-150/mes** |

> **Nota:** Los costos de AI Foundry (GPT-4.1) son por uso (tokens). El estimado base asume uso mínimo. Apaga la JumpBox cuando no la uses para reducir costos.

---

## 14. Limpieza de Recursos

### Eliminar ContentFlow

```bash
# Eliminar todos los recursos de ContentFlow
azd down --force --purge
```

> `--purge` elimina los recursos en soft-delete (Cosmos DB, Key Vault, AI Services).

### Eliminar la Mini-AILZ

```bash
# Eliminar todo el Resource Group de red
az group delete --name $AILZ_RG --yes --no-wait
```

### Limpieza Selectiva (Mantener la Red)

Si quieres mantener la Mini-AILZ para futuras demos:
```bash
# Solo eliminar ContentFlow
azd down --force --purge

# Apagar JumpBox para ahorrar
az vm deallocate -g $AILZ_RG -n "jmp-ailz-demo"
```

---

## Apéndice A: Script Completo de Creación de Mini-AILZ

Para conveniencia, aquí está el script completo que crea toda la Mini-AILZ de un solo paso:

```bash
#!/bin/bash
# create-mini-ailz.sh - Crea una AI Landing Zone mínima para demo de ContentFlow
set -e

# === CONFIGURACIÓN (AJUSTAR SEGÚN TU AMBIENTE) ===
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
LOCATION="eastus2"
AILZ_RG="rg-mini-ailz"
VNET_NAME="vnet-ailz-demo"
VNET_PREFIX="10.0.0.0/16"
PE_SUBNET_PREFIX="10.0.1.0/27"
ACA_SUBNET_PREFIX="10.0.16.0/23"
JUMPBOX_SUBNET_PREFIX="10.0.2.0/27"
BASTION_SUBNET_PREFIX="10.0.3.0/26"

echo "=== Creando Mini-AILZ para ContentFlow Demo ==="
echo "Suscripción: $SUBSCRIPTION_ID"
echo "Ubicación: $LOCATION"
echo "Resource Group: $AILZ_RG"
echo ""

# 1. Resource Group
echo "[1/6] Creando Resource Group..."
az group create -n $AILZ_RG -l $LOCATION --tags purpose=mini-ailz -o none

# 2. VNet + Subredes
echo "[2/6] Creando VNet y subredes..."
az network vnet create -g $AILZ_RG -n $VNET_NAME --address-prefix $VNET_PREFIX -l $LOCATION -o none
az network vnet subnet create -g $AILZ_RG --vnet-name $VNET_NAME -n "pe-subnet" --address-prefix $PE_SUBNET_PREFIX -o none
az network vnet subnet create -g $AILZ_RG --vnet-name $VNET_NAME -n "aca-env-subnet" --address-prefix $ACA_SUBNET_PREFIX -o none
az network vnet subnet create -g $AILZ_RG --vnet-name $VNET_NAME -n "jumpbox-subnet" --address-prefix $JUMPBOX_SUBNET_PREFIX -o none
az network vnet subnet create -g $AILZ_RG --vnet-name $VNET_NAME -n "AzureBastionSubnet" --address-prefix $BASTION_SUBNET_PREFIX -o none
echo "  ✓ VNet con 4 subredes creada"

# 3. Private DNS Zones
echo "[3/6] Creando Private DNS Zones..."
VNET_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$AILZ_RG/providers/Microsoft.Network/virtualNetworks/$VNET_NAME"
DNS_ZONES=(
  "privatelink.blob.core.windows.net"
  "privatelink.documents.azure.com"
  "privatelink.azconfig.io"
  "privatelink.azurecr.io"
  "privatelink.cognitiveservices.azure.com"
  "privatelink.azurecontainerapps.io"
)
for ZONE in "${DNS_ZONES[@]}"; do
  az network private-dns zone create -g $AILZ_RG -n "$ZONE" -o none
  LINK_NAME=$(echo "$ZONE" | sed 's/\./-/g')-link
  az network private-dns link vnet create -g $AILZ_RG -z "$ZONE" -n "$LINK_NAME" -v "$VNET_ID" -e false -o none
done
echo "  ✓ 6 Private DNS Zones creadas y vinculadas"

# 4. Azure Bastion
echo "[4/6] Creando Azure Bastion..."
az network public-ip create -g $AILZ_RG -n "pip-bastion-demo" --sku Standard --allocation-method Static -l $LOCATION -o none
az network bastion create -g $AILZ_RG -n "bastion-demo" --public-ip-address "pip-bastion-demo" --vnet-name $VNET_NAME --sku Developer -l $LOCATION -o none
echo "  ✓ Azure Bastion (Developer SKU) creado"

# 5. JumpBox VM (Linux para costo mínimo)
echo "[5/6] Creando JumpBox VM..."
az vm create -g $AILZ_RG -n "jmp-ailz-demo" \
  --image "Ubuntu2404" --size "Standard_B2s" \
  --vnet-name $VNET_NAME --subnet "jumpbox-subnet" \
  --admin-username "azureuser" --generate-ssh-keys \
  --tags role=jumpbox purpose=mini-ailz \
  --public-ip-address "" -l $LOCATION -o none
echo "  ✓ JumpBox Linux creada"

# 6. Resumen
echo ""
echo "[6/6] Verificación..."
echo ""
echo "=== Mini-AILZ Creada Exitosamente ==="
echo ""
echo "Resource Group: $AILZ_RG"
echo "VNet: $VNET_NAME ($VNET_PREFIX)"
echo "Subredes:"
echo "  - pe-subnet:          $PE_SUBNET_PREFIX"
echo "  - aca-env-subnet:     $ACA_SUBNET_PREFIX"
echo "  - jumpbox-subnet:     $JUMPBOX_SUBNET_PREFIX"
echo "  - AzureBastionSubnet: $BASTION_SUBNET_PREFIX"
echo ""
echo "Private DNS Zones: 6 zonas creadas y vinculadas"
echo "JumpBox: jmp-ailz-demo (acceso vía Bastion)"
echo ""
echo "=== Siguiente paso ==="
echo "Ejecuta el script de descubrimiento de ContentFlow:"
echo "  cd infra/scripts && ./get-ailz-resources.sh --auto-set"
echo "Luego despliega:"
echo "  azd env set DEPLOYMENT_MODE ailz-integrated"
echo "  azd up"
```

---

## Apéndice B: Diagrama de Flujo de Despliegue

```
┌────────────────────────┐
│   1. Preparar Mini-AILZ │
│   (create-mini-ailz.sh) │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│   2. Obtener IDs        │
│   (get-ailz-resources   │
│    --auto-set)          │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│   3. Configurar azd     │
│   DEPLOYMENT_MODE=      │
│   ailz-integrated       │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│   4. azd up             │
│   (provision + deploy)  │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐     ┌──────────────────────┐
│   5. Conectar a         │────▶│  6. Probar servicios  │
│   JumpBox vía Bastion   │     │  internos (API, Web)  │
└────────────────────────┘     └──────────────────────┘
```

---

> **Última actualización:** Febrero 2026  
> **Aplica a:** ContentFlow con plantillas Bicep para despliegue `basic` y `ailz-integrated`
