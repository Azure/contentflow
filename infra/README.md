# ContentFlow Infrastructure

This directory contains all infrastructure as code (IaC) and deployment scripts for ContentFlow on Azure.

## 🚀 Deployment Modes

ContentFlow supports **two deployment configurations** based on your infrastructure requirements:

1. [Basic deployment mode](#1️⃣-basic-mode-default---recommended-for-quick-setup-and-testing)
2. [Azure AI Landing Zone integrated deployment mode](#2️⃣-ai-landing-zone-integrated-mode-enterprise---private)

## Deployment Modes Comparison

| Feature | Basic Mode | AILZ-Integrated Mode |
|---------|-----------|---------------------|
| **Network Access** | 🌐 Public Endpoints | 🔒 Private Endpoints |
| **Internet Exposure** | Direct access | No public internet access |
| **Network Setup** | Does not use VNETs | Uses existing AI LZ VNet |
| **DNS Resolution** | Public DNS | Private DNS Zones |
| **Compliance Ready** |  N/A | ✅ Yes |
| **Enterprise Use** | Development | Production |
| **Cost** | Lower | Slightly higher (Network infra costs added) |
| **Prerequisites** | Azure subscription | Azure subscription + AI LZ |

---

## Prerequisites

Before deploying, ensure you have:

✅ **Azure Subscription** - Active Azure account with sufficient permissions  
✅ **Azure CLI** - `az` command-line tool  
✅ **Azure Developer CLI** - `azd` command-line tool  
✅ **PowerShell>=7.5 or Bash Shell** - `pwsh or bash` command-line tool  
✅ **Git** - For cloning the repository

**For AILZ-Integrated Mode:**
- Access to existing AI Landing Zone infrastructure
- Documentation of VNet and DNS zone resource IDs
- Appropriate permissions in the AI LZ resource group

**Verify tools are installed:**
```shell
az --version
azd --version
```

---

### 1️⃣ Basic Mode (Default - Recommended for quick setup and testing)

**What it does**: Deploys ContentFlow services with public endpoints using Azure Container Apps.

#### Deployment Steps

Minimal setup required:

```bash
# Step 1: Clone repository
git clone https://github.com/Azure/contentflow
cd contentflow

# Step 2: Authenticate
az login
azd auth login

# Step 3: Deploy - Select basic deployment mode when prompted
azd up

```

**That's it!** The deployment will create everything needed.

**Architecture:**
- ✅ Public endpoints for all services
- ✅ No VNet infrastructure created (uses Azure-managed networking)
- ✅ Self-contained environment
- ✅ No external dependencies
- ✅ Simplest setup process

**Best for:**
- Quick proof-of-concepts
- Development and quick testing
- Standalone environments

**What Gets Deployed:**
- Container Apps (API, Worker, Web) with public endpoints
- Public Container Registry
- Storage Account (public access)
- Cosmos DB (public access)
- App Configuration (public)
- Log Analytics & Application Insights
- Managed Identity for service authentication
- No VNet or private networking infrastructure

**Duration:** 10-15 minutes

---

### 2️⃣ AI Landing Zone Integrated Mode (Enterprise - Private)

**What it does**: Deploys ContentFlow services with private endpoints, fully integrated with existing Azure AI Landing Zone infrastructure

#### Deployment Steps

For enterprise AI Landing Zone integration, ContentFlow provides a helper script to automatically gather all required resource IDs.

##### Step 1: Setup Your AI Landing Zone

If you don't already have an AI Landing Zone, set it up using the official Azure AI Landing Zones template:

- **Repository**: [Azure AI Landing Zone on GitHub](https://github.com/Azure/AI-Landing-Zones)
- **Documentation**: Follow the setup instructions in the repository's README
- **Key resources created**:
  - Virtual Network with private subnets
  - Private DNS Zones for all services
  - Jump VM for deploying services from within the VNET
  - Log Analytics & Application Insights (optional to reuse)

##### Step 2: Gather AI LZ Resource IDs

Use the provided helper script to automatically collect all required resource IDs and automatically set azd environment variables:

**If using bash (Recommended - with auto-set):**
```bash
# Navigate to ContentFlow repository
cd contentflow/infra/scripts

# Run the helper script with --auto-set flag to automatically configure azd
./get-ailz-resources.sh --auto-set
```

**If using bash (without auto-set):**
```bash
# Navigate to ContentFlow repository
cd contentflow/infra/scripts

# Run the helper script
./get-ailz-resources.sh

# Then manually configure from the generated file
cd ../.. # Back to contentflow root
source infra/scripts/ailz-resources.env
```

**If using PowerShell:**
```pwsh
# Navigate to ContentFlow repository
cd contentflow\infra\scripts

# Run the helper script
pwsh .\get-ailz-resources.ps
```

**What the script does:**
1. ✅ Checks Azure CLI authentication
2. ✅ Asks for your AI Landing Zone resource group name
3. ✅ Discovers all required resources automatically:
   - Virtual Network ID and Subnet Names
   - Private DNS Zone IDs (blob, cosmos, acr, app config, cognitive services, key vault, container apps environment)
   - JumpBox VM information (if available)
   - Log Analytics Workspace ID (optional)
   - Application Insights ID (optional)
4. ✅ Creates `ailz-resources.env` file with all resource IDs
5. ✅ If using `--auto-set`: Automatically sets all azd environment variables
6. ✅ Shows next deployment steps

**Output:**
The script generates an `ailz-resources.env` file with all resource IDs:

```shell
# Example ailz-resources.env
EXISTING_VNET_RESOURCE_ID="/subscriptions/.../virtualNetworks/my-vnet"
PRIVATE_ENDPOINT_SUBNET_NAME="pe-subnet"
CONTAINER_APPS_SUBNET_NAME="aca-env-subnet"
EXISTING_BLOB_PRIVATE_DNS_ZONE_ID="/subscriptions/.../privateDnsZones/privatelink.blob.core.windows.net"
EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID="/subscriptions/.../privateDnsZones/privatelink.documents.azure.com"
JUMPBOX_VM_RESOURCE_ID="/subscriptions/.../resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/jumpbox"
JUMPBOX_VM_NAME="jumpbox"
# ... etc
```

#### Step 3: Configure ContentFlow for AILZ Integration

**If you used `--auto-set` flag:**
Your environment variables are already configured! Skip to Step 4.

**If you used the script without `--auto-set`:**
Manually load the resource IDs:

```shell
# Navigate back to project root
cd contentflow

# Authenticate with Azure
azd auth login

# Create new environment
azd env new
# Enter environment name: (e.g., 'prod-ailz')

# Set deployment mode
azd env set DEPLOYMENT_MODE ailz-integrated

# Load and set all resource IDs from the helper script output
source infra/scripts/ailz-resources.env

# Set all required variables (the script output will contain these values)
azd env set EXISTING_VNET_RESOURCE_ID "$EXISTING_VNET_RESOURCE_ID"
azd env set PRIVATE_ENDPOINT_SUBNET_NAME "$PRIVATE_ENDPOINT_SUBNET_NAME"
azd env set CONTAINER_APPS_SUBNET_NAME "$CONTAINER_APPS_SUBNET_NAME"
azd env set EXISTING_BLOB_PRIVATE_DNS_ZONE_ID "$EXISTING_BLOB_PRIVATE_DNS_ZONE_ID"
azd env set EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID "$EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID"
azd env set EXISTING_ACR_PRIVATE_DNS_ZONE_ID "$EXISTING_ACR_PRIVATE_DNS_ZONE_ID"
azd env set EXISTING_APP_CONFIG_PRIVATE_DNS_ZONE_ID "$EXISTING_APP_CONFIG_PRIVATE_DNS_ZONE_ID"
azd env set EXISTING_COGNITIVE_SERVICES_PRIVATE_DNS_ZONE_ID "$EXISTING_COGNITIVE_SERVICES_PRIVATE_DNS_ZONE_ID"
azd env set EXISTING_CONTAINER_APPS_ENV_PRIVATE_DNS_ZONE_ID "$EXISTING_CONTAINER_APPS_ENV_PRIVATE_DNS_ZONE_ID"

# Optional: Set existing Log Analytics and Application Insights IDs
# (ContentFlow will create new ones if not provided)
# azd env set EXISTING_LOG_ANALYTICS_WORKSPACE_ID "$EXISTING_LOG_ANALYTICS_WORKSPACE_ID"
# azd env set EXISTING_APP_INSIGHTS_ID "$EXISTING_APP_INSIGHTS_ID"
```

#### Step 4: Deploy ContentFlow

After configuration, deploy with a single command:

```bash
azd up
```

This will:
1. ✅ Validate all AI LZ parameters
2. ✅ Deploy ContentFlow services with private endpoints
3. ✅ Connect to existing AI LZ VNet
4. ✅ Register private DNS records in existing Private DNS Zones
5. ✅ Create managed identities and role assignments
6. ✅ Output service endpoints (accessible only from within AI LZ VNet)

**Deployment from Local Machine vs JumpBox VM:**
- **Local machine**: Use `azd up` if you have VPN or network access to the AI LZ VNet
- **JumpBox VM**: For secure deployments, use the Jump VM from within the AI LZ (see "Deploying from JumpBox VM" below)


**Architecture:**
- ✅ Private endpoints for all services (no public internet exposure)
- ✅ Integrates with existing AI Landing Zone VNet
- ✅ Uses existing DNS zones for private resolution
- ✅ Centralized logging and monitoring
- ✅ Enterprise security compliance
- ✅ Multi-layer network isolation

**Best for:**
- Enterprise environments with strict security policies
- Compliance-required deployments (HIPAA, SOC 2, etc.)
- Organizations with existing Azure and AI Landing Zone infrastructure
- High-security, air-gapped or restricted networks

**What Gets Deployed:**
- Container Apps with private endpoints
- Private Container Registry
- Storage Account with private endpoints
- Cosmos DB with private endpoints
- App Configuration with private endpoints
- Log Analytics & Application Insights
- Managed Identity for service authentication

**What Gets Integrated With (from AI LZ):**
- Existing Virtual Network
- Private subnets for endpoints (`pe-subnet`)
- Private subnets for container apps (`aca-env-subnet`)
- Existing Private DNS Zones:
  - Cognitive Services
  - Blob Storage
  - Cosmos DB
  - App Configuration
  - Container Registry
  - Container Apps Environment
  - Key Vault (optional)
- Existing Log Analytics Workspace (optional)
- Existing Application Insights (optional)

**Duration:** 10-15 minutes (depends on existing AI LZ setup)

---

#### Step 5: Deploy from JumpBox VM (Recommended for Secure Environments)

For enterprise environments, it's recommended to deploy ContentFlow from within the AI LZ VNet using the JumpBox VM:

**Prerequisites:**
- JumpBox VM retrieved by the helper script (check `ailz-resources.env` for `JUMPBOX_VM_NAME`)
- SSH/RDP access to the JumpBox VM
- Git, Azure CLI, Azure Developer CLI, and required runtime tools installed on JumpBox

**Option A: Deploy from JumpBox via SSH**

```bash
# 1. Connect to JumpBox VM
ssh azureuser@<jumpbox-ip>

# 2. Clone ContentFlow repository
git clone https://github.com/Azure/contentflow.git
cd contentflow

# 3. Authenticate with Azure
az login
azd auth login

# 4. Create azd environment (same as Step 3)
azd env new
azd env set DEPLOYMENT_MODE ailz-integrated

# 5. Set all resource IDs (or load from file if available)
azd env set EXISTING_VNET_RESOURCE_ID "<your-vnet-id>"
# ... (set all required variables)

# 6. Deploy ContentFlow
azd up
```

**Option B: Deploy from JumpBox using Environment File**

If you want to pre-stage the configuration:

```bash
# 1. On your local machine, generate the resource IDs:
cd contentflow/infra/scripts
./get-ailz-resources.sh

# 2. Copy ailz-resources.env to JumpBox:
scp infra/scripts/ailz-resources.env azureuser@<jumpbox-ip>:~/ 

# 3. On JumpBox, clone and configure:
ssh azureuser@<jumpbox-ip>
git clone https://github.com/Azure/contentflow.git
cd contentflow

az login
azd auth login

# Create environment and load resource IDs
azd env new
azd env set DEPLOYMENT_MODE ailz-integrated

source ~/ailz-resources.env
azd env set EXISTING_VNET_RESOURCE_ID "$EXISTING_VNET_RESOURCE_ID"
azd env set PRIVATE_ENDPOINT_SUBNET_NAME "$PRIVATE_ENDPOINT_SUBNET_NAME"
# ... (load all other variables)

# 4. Deploy
azd up
```

**Benefits of JumpBox Deployment:**
- ✅ Deployment originates from within the VNet (no need for public network access)
- ✅ All Container Apps are provisioned with proper VNet integration
- ✅ Better security compliance for restricted networks
- ✅ Reduced exposure of deployment credentials
- ✅ Ideal for air-gapped or highly restricted environments

---


### AILZ-Integrated Mode - Manual Configuration (Alternative)

If you prefer not to use the helper script, you can manually set each parameter:

For enterprise AI Landing Zone integration:

```bash
# Step 1: Gather AI Landing Zone Information
# You'll need the following from your existing AI LZ:
# - Virtual Network Resource ID
# - Private subnet names (pe-subnet, aca-env-subnet)
# - Private DNS Zone Resource IDs for each service

# Step 2: Clone and authenticate
git clone <repo-url>
cd contentflow
azd auth login

# Step 3: Create environment
azd env new
# Enter environment name: (e.g., 'prod-ailz')

# Step 4: Set deployment mode
azd env set DEPLOYMENT_MODE ailz-integrated

# Step 5: Configure AI LZ integration parameters
azd env set EXISTING_VNET_RESOURCE_ID /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet-name>

azd env set PRIVATE_ENDPOINT_SUBNET_NAME pe-subnet
azd env set CONTAINER_APPS_SUBNET_NAME aca-env-subnet

# Step 6: Set all required Private DNS Zone IDs
azd env set EXISTING_COGNITIVE_SERVICES_PRIVATE_DNS_ZONE_ID /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Network/privateDnsZones/privatelink.cognitiveservices.azure.com

azd env set EXISTING_BLOB_PRIVATE_DNS_ZONE_ID /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Network/privateDnsZones/privatelink.blob.core.windows.net

azd env set EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Network/privateDnsZones/privatelink.documents.azure.com

azd env set EXISTING_APP_CONFIG_PRIVATE_DNS_ZONE_ID /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Network/privateDnsZones/privatelink.azconfig.io

azd env set EXISTING_ACR_PRIVATE_DNS_ZONE_ID /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Network/privateDnsZones/privatelink.azurecr.io

azd env set EXISTING_CONTAINER_APPS_ENV_PRIVATE_DNS_ZONE_ID /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Network/privateDnsZones/privatelink.azurecontainerapps.io

# Optional: Use existing Log Analytics and Application Insights
azd env set EXISTING_LOG_ANALYTICS_WORKSPACE_ID /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.OperationalInsights/workspaces/<la-name>

azd env set EXISTING_APP_INSIGHTS_ID /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Insights/components/<ai-name>

# Step 7: Deploy
azd up
```

**Finding Your AI Landing Zone Resources:**

```bash
# List your AI LZ Virtual Network
az network vnet list --query "[?tags.environment=='ailz']" --output table

# Get resource IDs
az network vnet show --name <vnet-name> --resource-group <rg> --query id
az network private-dns-zone list --resource-group <rg> --output table
```

---

## Structure

```
infra/
├── bicep/                     # Bicep infrastructure templates
│   ├── main.bicep             # Main template (subscription-scoped)
│   ├── main.parameters.json   # Parameters file
│   ├── abbreviations.json     # Resource naming conventions
│   └── modules/               # Reusable Bicep modules
│       ├── container-app.bicep
│       ├── app-config-store.bicep
│       ├── app-insights.bicep
│       ├── container-apps-environment.bicep
│       ├── container-registry.bicep
│       ├── cosmos-db.bicep
│       ├── log-analytics-ws.bicep
│       ├── storage.bicep
│       ├── user-assigned-identity.bicep
│       └── ai-foundry.bicep
└── scripts/                   # Deployment automation scripts
    ├── pre-provision.sh       # Pre-provisioning checks
    ├── post-provision.sh      # Post-provisioning setup
    ├── pre-deploy.sh          # Pre-deployment validation
    ├── post-deploy.sh         # Post-deployment summary
    ├── post-deploy-api.sh     # API-specific post-deploy
    └── post-deploy-worker.sh  # Worker-specific post-deploy
```

## Bicep Templates

### main.bicep
Main infrastructure template that provisions:
- Resource Group (if not already existing)
- Managed Identity (for Container Apps)
- Container Registry
- Container Apps Environment
- Storage Account (blob + queue)
- Cosmos DB with all required containers
- App Configuration Store
- AI Foundry Hub & Project
- Log Analytics & Application Insights
- Container Apps (api, worker, web)
- All necessary role assignments

**Scope**: Resource Group-level deployment  
**Compatible**: Azure Developer CLI (azd)

### Modules

Each module is a reusable component:
- **app-config-store.bicep**: App Configuration with key-values
- **app-insights.bicep**: Application Insights for monitoring
- **container-app.bicep**: Creates a Container App with configurable settings
- **container-apps-environment.bicep**: Container Apps Environment
- **container-registry.bicep**: Azure Container Registry
- **cosmos-db.bicep**: Cosmos DB account with containers
- **log-analytics-ws.bicep**: Log Analytics Workspace
- **storage.bicep**: Storage Account with blob container and queue
- **user-assigned-identity.bicep**: Managed Identity
- **ai-foundry.bicep**: AI Foundry Hub and Project

## Scripts

All scripts are bash scripts designed to run as azd hooks.

### Hook Execution Order

1. **pre-provision.sh** - Before infrastructure provisioning
   - Checks for required tools (az, azd)
   - Verifies Azure authentication

2. **Infrastructure Provisioning** (azd provision)
   - Deploys Bicep templates
   - Creates all Azure resources

3. **post-provision.sh** - After infrastructure provisioning
   - Creates storage queue
   - Displays resource information

4. **pre-deploy.sh** - Before service deployment
   - Validates infrastructure exists

5. **Service Deployment** (azd deploy)
   - Builds Docker images (remote build)
   - Pushes to ACR
   - Updates Container Apps

6. **post-deploy-{service}.sh** - After each service deployment
   - Service-specific post-deployment tasks

7. **post-deploy.sh** - After all services deployed
   - Displays endpoints and next steps

## Detailed AZD Usage

### Full Deployment (Mode 1 - Recommended)

Deploy everything with a single command:

```bash
azd up
```

**What happens:**
1. ✅ Checks for required tools and Azure authentication
2. ✅ Provisions all Azure infrastructure (Container Apps, Storage, Cosmos DB, etc.)
3. ✅ Builds Docker images for all services
4. ✅ Pushes images to Azure Container Registry
5. ✅ Deploys services to Container Apps
6. ✅ Configures application settings
7. ✅ Displays deployment summary with URLs

**Timeline:**
- First deployment: 10-15 minutes
- Subsequent deployments: 5-10 minutes

**Output:** Service URLs and connection information

---

### Infrastructure Only (Mode 2a)

Provision Azure resources without deploying services:

```bash
azd provision
```

**What happens:**
1. ✅ Creates Resource Group
2. ✅ Deploys Bicep templates
3. ✅ Provisions all Azure services:
   - Container Apps Environment
   - Container Registry
   - Storage Account
   - Cosmos DB
   - App Configuration
   - Application Insights
   - Log Analytics

**When to use:**
- Setting up infrastructure for team review
- Separating infrastructure and application deployment
- Iterating on infrastructure changes

**Next step:** Run `azd deploy` when ready to deploy services

---

### Deploy Services Only (Mode 2b)

Deploy/update services to existing infrastructure:

```bash
azd deploy
```

**Prerequisites:** Infrastructure must already exist (from `azd provision`)

**What happens:**
1. ✅ Builds Docker images
2. ✅ Pushes to Container Registry
3. ✅ Updates Container Apps with new images
4. ✅ Restarts services with new configuration

**When to use:**
- Updating application code
- Changing service configuration
- Testing new builds without recreating infrastructure

---

### Update Infrastructure Only

Modify infrastructure without redeploying services:

```bash
# Edit infrastructure files
# Then redeploy infrastructure
azd provision

# Services will continue running with existing deployment
```

---

### View Deployed Resources

```bash
# Get resource group name
azd env get-value AZURE_RESOURCE_GROUP

# List all resources
az resource list \
  --resource-group <resource-group-name> \
  --output table

# Get service URLs
azd env get-values
```

---

## Environment Variables

The infrastructure sets these key outputs:

- `AZURE_LOCATION` - Azure region
- `AZURE_RESOURCE_GROUP` - Resource group name
- `AZURE_CONTAINER_REGISTRY_ENDPOINT` - ACR login server
- `COSMOS_DB_ENDPOINT` - Cosmos DB endpoint
- `STORAGE_ACCOUNT_NAME` - Storage account name
- `APP_CONFIG_ENDPOINT` - App Configuration endpoint
- `API_ENDPOINT` - API service URL
- `WORKER_ENDPOINT` - Worker service URL
- `WEB_ENDPOINT` - Web application URL

## Best Practices

1. **Naming**: Resources use uniqueString() for unique names
2. **Security**: All services use managed identities
3. **Monitoring**: Log Analytics and Application Insights enabled
4. **Scaling**: Container Apps auto-scale based on HTTP traffic
5. **Configuration**: Centralized in App Configuration
6. **Secrets**: Use Azure Key Vault (optional, configured)

## Troubleshooting

### Common Issues and Solutions

#### 1. **Authentication Failed**
```
Error: Not authenticated. Use `azd auth login`
```

**Solution:**
```bash
azd auth login
# Or if you have multiple subscriptions
azd env select
```

---

#### 2. **Insufficient Permissions**
```
Error: The user does not have the required permissions
```

**Solution:** Ensure your Azure account has these roles:
- `Owner` or `Contributor` and `User Access Administrator` on the resource group
- Contact your Azure administrator if needed

---

#### 3. **Deployment Timeout**
```
Error: Deployment failed after 30 minutes
```

**Solution:**
- Check Azure service limits for your region
- Try deploying to a different region:
  ```bash
  azd env set AZURE_LOCATION eastus
  azd provision
  ```

---

#### 4. **Container Registry Issues**
```
Error: Failed to push image to registry
```

**Solution:**
```bash
# Verify authentication
az acr login --name <registry-name>

# Rebuild images
docker system prune -a
azd deploy
```

---

#### 5. **Resource Group Already Exists**
```
Error: Resource group '<name>' already exists
```

**Solution:**
```bash
# Use an existing environment
azd env select

# Or create a new environment
azd env new <new-env-name>
```

---

### Checking Deployment Status

```bash
# Get all resource information
azd env get-values

# Check Container Apps status
az containerapp list --resource-group <resource-group-name> --output table

# View Container App logs
az containerapp logs show \
  --name <app-name> \
  --resource-group <resource-group-name>

# Check Application Insights
az monitor app-insights show \
  --resource-group <resource-group-name> \
  --name <app-insights-name>
```

---

### Debug Mode Deployment

For detailed deployment logs:

```bash
# Verbose provisioning
azd provision --debug

# Verbose deployment
azd deploy --debug
```

---

### View Deployment Logs

```bash
# Last deployment operation logs
az deployment sub show \
  --name <deployment-name> \
  --resource-group <resource-group-name>

# Activity log for resource group
az monitor activity-log list \
  --resource-group <resource-group-name> \
  --max-events 20
```

---

### Validate Bicep Templates

Before deploying, validate infrastructure templates:

```bash
cd infra/bicep
az bicep build --file main.bicep
```

---

## View Deployed Resources

```bash
# Get resource group name
azd env get-value AZURE_RESOURCE_GROUP

# List all resources
az resource list \
  --resource-group <resource-group-name> \
  --output table

# Get service URLs
azd env get-values
```

---

## References

- [Azure AI Landing Zones](https://github.com/Azure/AI-Landing-Zones)
- [Azure Developer CLI Documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
