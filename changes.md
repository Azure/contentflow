# Deployment Fixes – `azd up` Template Validation Errors

## Table of Contents

- [1. Fix: LogAnalytics CustomerId Must Be a GUID](#1-fix-loganalytics-customerid-must-be-a-guid)
- [2. Fix: Property Name Typo `privateEndpointsSubnetId`](#2-fix-property-name-typo-privateendpointssubnetid)
- [3. Fix: `UnmatchedPrincipalType` - `deployer().objectId` Hardcoded as `User`](#3-fix-unmatchedprincipaltype---deployerobjectid-hardcoded-as-user)
- [4. Feature: Automated ACR Placeholder Import for AILZ Deployments](#4-feature-automated-acr-placeholder-import-for-ailz-deployments)
- [5. Fix: Container Apps Timeout - DNS Zone Group Creation Workaround](#5-fix-container-apps-timeout---dns-zone-group-creation-workaround)
- [6. Fix: App Configuration Keys Failure - ARM Private Link Delegation](#6-fix-app-configuration-keys-failure---arm-private-link-delegation)

---

## 1. Fix: LogAnalytics CustomerId Must Be a GUID

**Error:**

```
InvalidRequestParameterWithDetails: LogAnalyticsConfiguration.CustomerId is invalid.
CustomerId must be a GUID without additional whiteSpace.
```

**Root Cause:**

In `infra/bicep/main.bicep`, the `containerAppsEnvironment` module was receiving the full ARM **resource ID** of the existing Log Analytics workspace (e.g., `/subscriptions/.../providers/Microsoft.OperationalInsights/workspaces/ailz-law`) as the `logAnalyticsWorkspaceId` parameter. However, the Container Apps Environment module uses this value as the `customerId` in `logAnalyticsConfiguration`, which requires the **Workspace GUID** — not the ARM resource path.

This only affects AILZ-integrated deployments that reference a pre-existing Log Analytics workspace via the `EXISTING_LOG_ANALYTICS_WORKSPACE_ID` environment variable.

**File:** `infra/bicep/main.bicep` (containerAppsEnvironment module call)

**Before:**

```bicep
logAnalyticsWorkspaceId: !empty(existingLogAnalyticsWorkspaceId)
  ? existingLogAnalyticsWorkspaceId
  : logAnalytics!.outputs.logAnalyticsWorkspaceId
```

**After:**

```bicep
logAnalyticsWorkspaceId: !empty(existingLogAnalyticsWorkspaceId)
  ? reference(existingLogAnalyticsWorkspaceId, '2021-12-01-preview').customerId
  : logAnalytics!.outputs.logAnalyticsWorkspaceId
```

The `reference()` function retrieves the workspace properties at deploy time and extracts the `customerId` (GUID), which is the format the Container Apps Environment requires.

---

## 2. Fix: Property Name Typo `privateEndpointsSubnetId`

**Error:**

```
InvalidTemplate: The language expression property 'privateEndpointsSubnetId' doesn't exist,
available properties are 'enablePrivateEndpoints, publicNetworkAccess, vnetResourceId,
privateEndpointSubnetId, containerAppsSubnetId, privateDnsZoneIds'.
```

**Root Cause:**

In `infra/bicep/main.bicep`, the `containerRegistry` module call referenced `networkConfig.privateEndpointsSubnetId` (plural, with an extra **s**), but the `networkConfig` variable defines the property as `privateEndpointSubnetId` (singular).

**File:** `infra/bicep/main.bicep` (containerRegistry module call)

**Before:**

```bicep
privateEndpointSubnetId: isAILZIntegrated ? networkConfig.privateEndpointsSubnetId : ''
```

**After:**

```bicep
privateEndpointSubnetId: isAILZIntegrated ? networkConfig.privateEndpointSubnetId : ''
```

Simple typo fix — `privateEndpointsSubnetId` → `privateEndpointSubnetId`.

---

## 3. Fix: `UnmatchedPrincipalType` - `deployer().objectId` Hardcoded as `User`

**Error:**

```
UnmatchedPrincipalType: The PrincipalId '634c8d99dc1442e18389ece9c4fe7e8a' has type
'ServicePrincipal', which is different from specified PrincipalType 'User'.
```

**Root Cause:**

The modules `storage.bicep` and `app-config-store.bicep` use the Bicep `deployer().objectId` function to assign RBAC roles to the identity running the deployment. The `principalType` is hardcoded as `'User'`, which fails when the deployment is executed via a **managed identity** (which is of type `ServicePrincipal`).

This affects AILZ-integrated deployments where `azd provision` is run from a jumpbox VM using `azd auth login --managed-identity`.

**Affected Files:**

### `infra/bicep/modules/storage.bicep` (lines ~72-80)

**Before:**

```bicep
var deployerRoleAssignments = [
    {
      principalId: deployer().objectId
      principalType: 'User'
      roleDefinitionIdOrName: 'Storage Blob Data Contributor'        
    }
    {
      principalId: deployer().objectId
      principalType: 'User'
      roleDefinitionIdOrName: 'Storage Queue Data Contributor'        
    }
  ]
```

**After:**

```bicep
var deployerRoleAssignments = [
    {
      principalId: deployer().objectId
      principalType: empty(deployer().?userPrincipalName ?? '') ? 'ServicePrincipal' : 'User'
      roleDefinitionIdOrName: 'Storage Blob Data Contributor'        
    }
    {
      principalId: deployer().objectId
      principalType: empty(deployer().?userPrincipalName ?? '') ? 'ServicePrincipal' : 'User'
      roleDefinitionIdOrName: 'Storage Queue Data Contributor'        
    }
  ]
```

### `infra/bicep/modules/app-config-store.bicep` (lines ~36-41)

**Before:**

```bicep
var deployerRoleAssignments = [
    {
      principalId: deployer().objectId
      principalType: 'User'
      roleDefinitionIdOrName: 'App Configuration Data Owner'        
    }
  ]
```

**After:**

```bicep
var deployerRoleAssignments = [
    {
      principalId: deployer().objectId
      principalType: empty(deployer().?userPrincipalName ?? '') ? 'ServicePrincipal' : 'User'
      roleDefinitionIdOrName: 'App Configuration Data Owner'        
    }
  ]
```

**Explanation:**

The `deployer()` function returns `objectId` and `tenantId` for all principal types, but `userPrincipalName` is only included when the deployer is a user — it is **omitted entirely** (not just empty) for service principals and managed identities. Using `deployer().userPrincipalName` directly throws a runtime error because the property doesn't exist in the ARM response object.

The fix uses the Bicep **safe-access operator** (`?.`) combined with the **null-coalescing operator** (`??`):
- `deployer().?userPrincipalName` → returns the value if it exists, or `null` if the property is absent
- `?? ''` → converts `null` to an empty string
- `empty(...)` → evaluates to `true` for managed identity/SP (no UPN), `false` for users (UPN present)

This works correctly for both interactive user logins and managed identity deployments without requiring any additional parameters.

---

## 4. Feature: Automated ACR Placeholder Import for AILZ Deployments

**Problem:**

In AILZ-integrated deployments without internet egress (no NAT Gateway), Container Apps provisioning previously failed with a **20-minute timeout** because it couldn't pull placeholder images from the public Microsoft Container Registry (MCR). The private VNet has no outbound internet connectivity.

**Solution:**

Implemented an automated approach that maintains **Zero Trust / workload isolation** principles:

1. **Always create a new ACR per workload** — never share a central ACR across workloads (violates isolation)
2. **Enable trusted Azure services** — set `networkRuleBypassOptions: 'AzureServices'` on the new ACR, allowing server-side operations like `az acr import` even when the ACR has private endpoints and `publicNetworkAccess: Disabled`
3. **Automated postprovision hook** — after Bicep provisions infrastructure, automatically import the placeholder image: `mcr.microsoft.com/k8se/quickstart:latest` → `${acr}/placeholder:latest`
4. **Non-blocking design** — Container Apps use the ACA platform-cached image `mcr.microsoft.com/k8se/quickstart:latest` during provisioning. The import is defensive, ensuring subsequent operations can resolve the image from ACR.

**How It Works:**

The `postprovision` hook in [azure.yaml](azure.yaml) runs [post-provision.sh](infra/scripts/post-provision.sh) after Bicep completes:

```bash
# Conditional import (only in AILZ mode)
if [ "$DEPLOYMENT_MODE" = "ailz-integrated" ]; then
  az acr import \
    --name "$ACR_NAME" \
    --source mcr.microsoft.com/k8se/quickstart:latest \
    --image placeholder:latest
fi
```

- **Basic mode**: Skip import (ACR is public, MCR reachable)
- **AILZ mode**: Import runs server-side via trusted services bypass (no client-side Docker or internet needed)

**Affected Files:**

### `infra/bicep/main.bicep`

- **Removed** `existingContainerRegistryResourceId` parameter (and all related variables/logic)
- **Removed** conditional ACR creation — now always creates new ACR
- **Removed** private endpoint + RBAC for existing ACR
- **Added** `networkRuleBypassOptions: 'AzureServices'` parameter to `containerRegistry` module call
- **Simplified** container app module calls — removed conditional `placeholderImage` (use default `k8se/quickstart`)
- **Simplified** outputs — use direct `containerRegistry.outputs.*`

### `infra/bicep/main.parameters.json`

- **Removed** `existingContainerRegistryResourceId` parameter mapping

### `infra/bicep/modules/container-registry.bicep`

- **Added** `networkRuleBypassOptions` parameter (default: `'AzureServices'`)
- **Pass through** to AVM module for trusted services support

### `infra/bicep/modules/container-app.bicep`

- **No changes** — already has correct default `placeholderImage: 'mcr.microsoft.com/k8se/quickstart:latest'`

### `infra/bicep/modules/acr-role-assignment.bicep`

- **DELETED** — no longer needed (no cross-RG ACR RBAC)

### `azure.yaml`

- **Uncommented** `postprovision` hook to enable automated import

### `infra/scripts/post-provision.sh`

- **Added** conditional ACR import logic for AILZ mode
- **Added** error handling with fallback instructions

**Benefits:**

✅ **Zero Trust compliance** — each workload has its own ACR, no shared central registry  
✅ **`azd up` remains one command** — fully automated, no manual steps  
✅ **Works from jumpbox without Docker** — `az acr import` is server-side  
✅ **Non-blocking** — ACA platform caches `k8se/quickstart`, provisioning succeeds even if import fails  
✅ **CI/CD ready** — no human intervention required

---

## 5. Fix: Container Apps Timeout - DNS Zone Group Creation Workaround

**Error:**

```
Container Apps deployment timing out after 20 minutes during AILZ-integrated deployments
```

**Symptoms:**

- Container Apps (API, Worker, Web) fail to provision and timeout after exactly 20 minutes
- ACR private endpoint exists and shows correct IP addresses (10.0.0.16 for login server, 10.0.0.15 for data endpoint)
- Private DNS Zone `privatelink.azurecr.io` is linked to VNet
- **BUT**: Private DNS Zone has NO A records for the ACR
- DNS zone group does NOT exist (query returns `[]`)
- Without DNS resolution, Container Apps cannot resolve the private ACR FQDN
- Requests fall back to public DNS but ACR has `publicNetworkAccess: Disabled` → connection refused → timeout

**Root Cause:**

The Azure Verified Module (AVM) `containerregistry/registry:0.9.3` does not properly handle the `privateDnsZoneGroups` parameter when passed conditionally through our wrapper module. Even with the corrected conditional logic:

```bicep
privateDnsZoneGroups: !empty(acrPrivateDnsZoneId) ? [{...}] : []
```

The AVM module fails to create the DNS zone group, resulting in NO A record registration in the Private DNS Zone. Investigation via Azure CLI confirmed:
- `az network private-endpoint dns-zone-group list` returned `[]` (no zone groups)
- `az network private-dns record-set a list` returned empty table (no A records)
- ACR deployment succeeded, private endpoint succeeded, but DNS registration failed

**Solution: Explicit DNS Zone Group Module**

Instead of relying on the AVM module to create the DNS zone group, we now create it explicitly using a separate Bicep module that runs **after** the ACR and private endpoint are provisioned.

### Files Changed

#### **New File: `infra/bicep/modules/private-endpoint-dns-zone-group.bicep`**

Created a dedicated module that explicitly creates a DNS zone group for an existing private endpoint:

```bicep
@description('Name of the private endpoint')
param privateEndpointName string

@description('Resource ID of the private DNS zone')
param privateDnsZoneId string

@description('Location for the deployment metadata')
param location string = resourceGroup().location

// Reference existing private endpoint
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' existing = {
  name: privateEndpointName
}

// Create DNS zone group for the private endpoint
resource dnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-azurecr-io'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

output dnsZoneGroupName string = dnsZoneGroup.name
output dnsZoneGroupId string = dnsZoneGroup.id
```

#### **Modified: `infra/bicep/modules/container-registry.bicep`**

Removed `privateDnsZoneGroups` from the `privateEndpoints` array passed to the AVM module:

**Before:**
```bicep
privateDnsZoneGroups: !empty(acrPrivateDnsZoneId) ? [
  {
    name: 'acr-dns-zone-group'
    privateDnsZoneGroupConfigs: [
      {
        name: 'acr-config'
        privateDnsZoneResourceId: acrPrivateDnsZoneId
      }
    ]
  }
] : []
```

**After:**
```bicep
// privateDnsZoneGroups removed - AVM module 0.9.3 does not handle conditional correctly
// DNS zone group will be created explicitly in main.bicep using separate module
```

#### **Modified: `infra/bicep/main.bicep`**

Added explicit DNS zone group module **after** the ACR module:

```bicep
// ========== CONTAINER REGISTRY WITH PRIVATE ENDPOINT SUPPORT ==========
module containerRegistry 'modules/container-registry.bicep' = {
  name: 'acr-${resourceToken}'
  params: {
    containerRegistryName: containerRegistryName
    location: location
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    enablePrivateEndpoint: isAILZIntegrated
    privateEndpointSubnetId: isAILZIntegrated ? networkConfig.privateEndpointSubnetId : ''
    acrPrivateDnsZoneId: isAILZIntegrated ? networkConfig.privateDnsZoneIds.acr : ''
    publicNetworkAccess: isAILZIntegrated ? 'Disabled' : 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    tags: tags
  }
}

// ========== ACR DNS ZONE GROUP (EXPLICIT CREATION) ==========
// Create DNS zone group explicitly to ensure A records are registered in private DNS zone
// Workaround: AVM containerregistry module 0.9.3 does not properly handle privateDnsZoneGroups conditional
// This separate module creates the DNS zone group after the private endpoint exists
module acrDnsZoneGroup 'modules/private-endpoint-dns-zone-group.bicep' = if (isAILZIntegrated) {
  name: 'acr-dns-zone-group-${resourceToken}'
  params: {
    privateEndpointName: '${containerRegistryName}-pe'
    privateDnsZoneId: networkConfig.privateDnsZoneIds.acr
    location: location
  }
  dependsOn: [
    containerRegistry
  ]
}
```

Also retained the `dependsOn: [containerRegistry]` on all three Container Apps modules (API, Worker, Web) to ensure they wait for both ACR and DNS zone group to complete.

**How It Works:**

1. **ACR Module** creates the Container Registry with private endpoint (but no DNS zone group)
2. **DNS Zone Group Module** (conditional on AILZ mode) creates the DNS zone group explicitly
3. Azure automatically registers A records in the Private DNS Zone when the zone group is properly configured
4. **Container Apps** wait for the entire ACR deployment (including DNS) via explicit `dependsOn`
5. DNS resolution works correctly, Container Apps pull images successfully

**Expected Results After Fix:**

✅ Private DNS Zone automatically gets A records for ACR FQDN pointing to private IPs (10.0.0.x)  
✅ DNS zone group exists and has proper configuration (not empty `{}` or missing `[]`)  
✅ DNS resolution works correctly within the VNet  
✅ Container Apps deploy successfully without 20-minute timeout  
✅ No manual DNS record creation needed  
✅ Deployment completes in 15-20 minutes total

**Verification Commands:**

```bash
# Verify DNS zone group exists
az network private-endpoint dns-zone-group list \
  --resource-group <workload-rg> \
  --endpoint-name <acr-name>-pe

# Verify A records registered
az network private-dns record-set a list \
  --resource-group <ailz-rg> \
  --zone-name privatelink.azurecr.io \
  --query "[].{Name:name, IP:aRecords[0].ipv4Address}"
```

---

**Fix Verification Results (Deployment: content_flow_Friday20-02)**

**Tested**: March 20, 2026  
**Environment**: AILZ-integrated mode with jumpbox deployment

✅ **DNS Zone Group Created Successfully**
```json
{
  "name": "default",
  "privateDnsZoneConfigs": [
    {
      "name": "privatelink-azurecr-io",
      "privateDnsZoneId": "/subscriptions/.../privateDnsZones/privatelink.azurecr.io",
      "recordSets": [
        {
          "fqdn": "cra5s63braj5xj2.eastus2.data.privatelink.azurecr.io",
          "ipAddresses": ["10.0.0.15"],
          "provisioningState": "Succeeded",
          "recordType": "A"
        },
        {
          "fqdn": "cra5s63braj5xj2.privatelink.azurecr.io",
          "ipAddresses": ["10.0.0.16"],
          "provisioningState": "Succeeded",
          "recordType": "A"
        }
      ]
    }
  ],
  "provisioningState": "Succeeded"
}
```

✅ **A Records Registered in Private DNS Zone**
```
Name             IP
---------------  ---------
cra5s63braj5xj2  10.0.0.16
```

✅ **Container Apps Deployed Successfully**
- Worker: 16.4 seconds (previously: 20-minute timeout)
- API: 49.4 seconds (previously: 20-minute timeout)
- Web: 18.5 seconds (previously: 20-minute timeout)

**Result**: The workaround with explicit DNS zone group module completely resolved the Container Apps timeout issue. DNS records are now automatically registered, and Container Apps can successfully pull images from the private ACR.

---

## 6. Fix: App Configuration Keys Failure - Private Network Access Limitation

**Error:**

```
appConfigKeys-a5s63braj5xj2 → Failed
Error: Forbidden - Access to the requested resource is forbidden
```

**Symptoms:**

- App Configuration Store provisions successfully in AILZ mode
- Private endpoint created and functional
- Container Apps can access App Config via private endpoint
- **BUT**: Bicep module `appConfigStoreKeys` fails with 403 Forbidden when attempting to create key-value pairs
- Error persists even after RBAC role assignments have propagated (2+ hours)
- Error appears for **every key** being created (30+ Forbidden errors)

---

**Root Cause:**

This is **NOT an RBAC issue** — it's a **network connectivity limitation** with Azure Resource Manager (ARM) deployment service accessing App Configuration through private endpoints.

In AILZ-integrated deployments, the App Configuration Store is configured with:
- `publicNetworkAccess: 'Disabled'` — no public internet access ✅ (correct for AILZ)
- Private endpoint in the VNet — accessible only through private network ✅
- `dataPlaneProxy.authenticationMode: 'Pass-through'` — uses deployer MI for auth ✅
- `dataPlaneProxy.privateLinkDelegation: 'Enabled'` — enables ARM private network access ✅

**The problem:** When Bicep creates `Microsoft.AppConfiguration/configurationStores/keyValues` resources, the **ARM deployment service** (which runs in Microsoft's network, **outside the customer's VNet**) attempts to write the key-values to the App Configuration data plane. However:

1. ARM deployment service has no direct access to the customer's private VNet
2. App Configuration has `publicNetworkAccess: 'Disabled'` (no internet route)
3. ARM cannot connect → 403 Forbidden

---

**Microsoft Official Documentation:**

From [Azure App Configuration - Deployment Overview](https://learn.microsoft.com/en-us/azure/azure-app-configuration/quickstart-deployment-overview?tabs=portal#private-network-access):

> **"Private network access"**
> 
> When you restrict an App Configuration resource to private network access, deployments that access App Configuration data through public networks are blocked. For deployments to succeed when access to an App Configuration resource is restricted to private networks, you must take the following actions:
> 
> 1. **Set up an Azure Resource Management private link**
> 2. In your App Configuration resource, set the Azure Resource Manager authentication mode to **Pass-through**
> 3. In your App Configuration resource, **enable Azure Resource Manager private network access** (this is `privateLinkDelegation: 'Enabled'`)
> 4. **Run deployments accessing App Configuration data through the configured Azure Resource Manager private link**

---

**Why `privateLinkDelegation: 'Enabled'` Alone Is Not Sufficient:**

The `dataPlaneProxy.privateLinkDelegation` property (API version `2025-02-01-preview` or later) **enables** App Configuration to accept ARM connections via private link, but **does not establish the private link**. It's a prerequisite, not a complete solution.

To **actually use** this feature, you need an **Azure Resource Manager Private Link** (requirement #1 and #4 above), which is:

- **An enterprise infrastructure** configured at the **root management group** level (applies to the entire tenant)
- **Out of scope** for application-level templates like ContentFlow
- Requires **Global Administrator** or **Owner permissions at the root management group**
- See: [Create Azure Resource Manager Private Link](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/create-private-link-access-portal)

**Without ARM Private Link configured at the tenant level**, even with `privateLinkDelegation: 'Enabled'`, ARM deployment service still attempts to access App Configuration over the public internet, which fails when `publicNetworkAccess: 'Disabled'`.

---

**Solution Architecture: Two-Phase Approach**

Since ARM Private Link is an enterprise-level prerequisite beyond the scope of this template, we implement a **two-phase solution** based on deployment mode:

### **Basic Mode** (Public Deployment)
- App Configuration: `publicNetworkAccess: 'Enabled'` (no private endpoints)
- **Keys created via Bicep**: ARM can access over the internet → Success ✅
- No postprovision hook needed

### **AILZ Mode** (Private Deployment)
- App Configuration: `publicNetworkAccess: 'Disabled'` + Private Endpoint
- **Keys created via postprovision hook**: Script runs on jumpbox VM (inside VNet) → Has private endpoint access → Success ✅
- Bicep module skipped (conditional: `if (!isAILZIntegrated)`)

**Why the Hook Works:**

```
┌─────────────────────────────────────────────────────────┐
│  Azure Resource Manager (ARM) Deployment Service        │
│  (Runs in Microsoft's network, NOT in customer VNet)   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ Bicep tries: keyValues resource
                   │ Result: 403 Forbidden ❌
                   │ (no ARM Private Link configured)
                   ▼
       ┌───────────────────────────┐
       │  App Configuration Store  │
       │  • publicNetworkAccess:   │
       │    'Disabled'            │
       │  • privateLinkDelegation: │
       │    'Enabled'             │
       └───────────────────────────┘
                   ▲
                   │
                   │ postprovision hook: az appconfig kv set
                   │ Result: Success ✅
                   │ (jumpbox has VNet access)
                   │
       ┌───────────────────────────┐
       │  Jumpbox VM (in VNet)     │
       │  • Private endpoint       │
       │  • Runs post-provision.sh │
       └───────────────────────────┘
```

The postprovision hook executes **after Bicep provisioning completes**, from the jumpbox VM which:
- Is located inside the customer's VNet
- Has network access via the App Configuration private endpoint
- Uses Azure CLI with `--auth-mode login` (managed identity authentication)
- Creates all 30 key-value pairs successfully

---

**Implementation Details:**

### File Changes

#### **1. Modified: `infra/bicep/main.bicep`** (line 267)

**Before:**
```bicep
module appConfigStoreKeys 'modules/app-config-store-keys.bicep' = {
  name: 'appConfigKeys-${resourceToken}'
  params: {
    appConfigStoreName: appConfigStoreName
    configurationKeyValues: [...]
  }
}
```

**After:**
```bicep
// Basic mode: Create keys via Bicep (public access enabled, ARM can access)
// AILZ mode: Skip Bicep creation, keys created via postprovision hook
module appConfigStoreKeys 'modules/app-config-store-keys.bicep' = if (!isAILZIntegrated) {
  name: 'appConfigKeys-${resourceToken}'
  params: {
    appConfigStoreName: appConfigStoreName
    configurationKeyValues: [...]
  }
}
```

**Result:** Module only runs in basic mode. In AILZ mode, Bicep skips this module entirely → no 403 Forbidden errors.

#### **2. Modified: `infra/bicep/modules/app-config-store.bicep`**

**Kept conditional `privateLinkDelegation`** (implemented in previous fix):
```bicep
dataPlaneProxy: {
  authenticationMode: 'Pass-through'
  privateLinkDelegation: enablePrivateEndpoint ? 'Enabled' : 'Disabled'  // Conditional
}
```

**Why keep it?** Even though it doesn't solve the **key creation** problem (requires ARM Private Link at tenant level), it:
- Follows Microsoft's documented best practice for AILZ deployments
- Prepares the App Configuration Store for enterprise environments that **do** have ARM Private Link configured
- Is a prerequisite (#3 in Microsoft's documentation)
- Does not cause harm when ARM Private Link is absent

#### **3. Extended: `infra/scripts/post-provision.sh`**

**Added new section** (after ACR import, lines ~55+):

```bash
# Create App Configuration keys in AILZ mode
if [ "$DEPLOYMENT_MODE" = "ailz-integrated" ]; then
  echo "✓ Creating App Configuration keys (AILZ mode - via jumpbox with VNet access)..."
  
  APP_CONFIG_NAME=$(azd env get-value APP_CONFIG_NAME)
  COSMOS_DB_NAME=$(azd env get-value COSMOS_DB_NAME)
  # ... get other values from azd env
  
  # Create all 30 keys using az appconfig kv set
  az appconfig kv set --name "$APP_CONFIG_NAME" \
    --key "contentflow.common.COSMOS_DB_ENDPOINT" \
    --value "$COSMOS_ENDPOINT" \
    --auth-mode login --yes --only-show-errors
  
  # ... (30 total keys)
  
  # Verify creation
  KEY_COUNT=$(az appconfig kv list --name "$APP_CONFIG_NAME" \
    --auth-mode login --query "length([])" -o tsv)
  echo "  ✓ Verification: $KEY_COUNT keys found"
fi
```

**Key Features:**
- Uses `--auth-mode login`: Authenticates with deployer managed identity
- Uses `--only-show-errors`: Suppresses verbose output
- Validates key count after creation
- Provides clear error messages if creation fails

#### **4. Modified: `infra/bicep/main.bicep`** (outputs section)

**Added output:**
```bicep
output APP_CONFIG_NAME string = appConfigStoreName
```

Required for the postprovision script to identify the correct App Configuration Store.

---

**How It Works (AILZ Mode):**

1. **Bicep Provisioning (`azd provision`)**:
   - Creates App Configuration Store with private endpoint and `privateLinkDelegation: 'Enabled'`
   - **Skips** `appConfigStoreKeys` module (conditional: `if (!isAILZIntegrated)`)
   - No 403 Forbidden errors during Bicep deployment
   - Completes successfully, outputs App Config name to azd environment

2. **Postprovision Hook (`post-provision.sh`)**:
   - Detects `DEPLOYMENT_MODE=ailz-integrated`
   - Retrieves App Config name and all required values from azd environment
   - Executes `az appconfig kv set` 30 times (one per key)
   - Azure CLI accesses App Config **via private endpoint** (jumpbox is in VNet)
   - All keys created successfully
   - Verifies key count matches expected (30)

3. **Container Apps Startup**:
   - Apps read `AZURE_APP_CONFIG_ENDPOINT` from environment variables
   - Connect to App Config via private endpoint
   - Load all 30 keys successfully
   - Applications start without configuration errors

---

**Expected Results After Fix:**

✅ **Basic mode** (public deployment):
- Bicep creates all 30 keys during `azd provision`
- No postprovision hook execution needed
- Single `azd up` command completes end-to-end

✅ **AILZ mode** (private deployment):
- Bicep **skips** key creation (module not executed)
- No 403 Forbidden errors during Bicep phase
- Postprovision hook creates all 30 keys from jumpbox
- Container Apps read keys successfully via private endpoint
- Single `azd up` command completes end-to-end (hook is automatic)

✅ **Security maintained**:
- App Configuration remains fully private (`publicNetworkAccess: 'Disabled'`)
- No temporary public access required
- Zero Trust principles preserved

---

**Verification After Deployment (AILZ Mode):**

```bash
# 1. Verify privateLinkDelegation is enabled (best practice)
az rest --method GET \
  --url "https://management.azure.com/subscriptions/<subscription-id>/resourceGroups/<rg-name>/providers/Microsoft.AppConfiguration/configurationStores/<app-config-name>?api-version=2025-02-01-preview" \
  --query "properties.dataPlaneProxy.privateLinkDelegation"
# Expected: "Enabled"

# 2. Verify all 30 keys were created
az appconfig kv list \
  --name <app-config-name> \
  --auth-mode login \
  --query "length([])"
# Expected: 30

# 3. Check specific keys
az appconfig kv list \
  --name <app-config-name> \
  --auth-mode login \
  --query "[].{Key:key, Value:value}" \
  --output table

# 4. Verify Container Apps can access config
az containerapp logs show \
  --name api-<resource-token> \
  --resource-group <rg-name> \
  --query "[?contains(Log, 'Configuration loaded')]"
```

---

**Why Not Enable ARM Private Link?**

Azure Resource Manager Private Link is an **enterprise infrastructure prerequisite** that:

- **Scope:** Configured at the **root management group** level (entire tenant)
- **Impact:** Applies to **all** Azure Resource Manager deployments across the tenant
- **Permissions Required:**
  - Global Administrator for Microsoft Entra ID
  - Owner or Contributor at the root management group
  - Ability to elevate access and grant permissions across all subscriptions
- **Complexity:** Multi-step setup with private endpoints, private DNS zones, and link associations
- **Purpose:** Designed for enterprises with strict network isolation requirements across all Azure operations
- **Documentation:** [Use portal to create private link for managing Azure resources](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/create-private-link-access-portal)

**For ContentFlow deployments:**
- This template targets **application-level** deployments, not tenant-wide infrastructure
- Most customers do **not** have ARM Private Link configured (it's optional and complex)
- The postprovision hook provides a **portable solution** that works regardless of ARM Private Link presence
- If customers **do** have ARM Private Link configured, `privateLinkDelegation: 'Enabled'` ensures compatibility

---

### ✅ Chosen Solution: Postprovision Hook
**Why it's optimal:**
- ✅ Runs on existing jumpbox (no additional resources/cost)
- ✅ Has VNet access via private endpoint (already configured)
- ✅ Uses managed identity authentication (deployer MI, already assigned)
- ✅ Simple bash script with Azure CLI (standard tooling)
- ✅ Executes automatically as part of `azd up` (no manual steps)
- ✅ Maintains Zero Trust security (no public access)
- ✅ Portable across environments (doesn't require ARM Private Link)

---

**Impact on Deployment Modes:**

| Deployment Mode | Public Network Access | Keys Creation Method | ARM Private Link Required? |
|-----------------|----------------------|---------------------|---------------------------|
| **Basic** | `'Enabled'` | Bicep module | No |
| **AILZ** | `'Disabled'` | Postprovision hook | No (would enable it if present) |

---

**References:**

- [Azure App Configuration - Deployment Overview](https://learn.microsoft.com/en-us/azure/azure-app-configuration/quickstart-deployment-overview)
- [Private network access for App Configuration](https://learn.microsoft.com/en-us/azure/azure-app-configuration/quickstart-deployment-overview?tabs=portal#private-network-access)
- [Create Azure Resource Manager Private Link](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/create-private-link-access-portal)
- [Use private endpoints for Azure App Configuration](https://learn.microsoft.com/en-us/azure/azure-app-configuration/concept-private-endpoint)

---

**Troubleshooting:**

If App Configuration keys are not created in AILZ mode:

```bash
# 1. Check postprovision hook execution
# Look for: "Creating App Configuration keys (AILZ mode...)"
azd provision --no-prompt 2>&1 | grep -A 10 "Creating App Configuration"

# 2. Manually run key creation from jumpbox
APP_CONFIG_NAME="appcs-<resource-token>"
az appconfig kv set --name "$APP_CONFIG_NAME" \
  --key "contentflow.common.COSMOS_DB_ENDPOINT" \
  --value "<cosmos-endpoint>" \
  --auth-mode login --yes

# 3. Verify managed identity has correct role
az role assignment list \
  --scope "/subscriptions/<sub-id>/resourceGroups/<rg-name>/providers/Microsoft.AppConfiguration/configurationStores/$APP_CONFIG_NAME" \
  --query "[?roleDefinitionName=='App Configuration Data Owner'].principalId"

# 4. Check private endpoint connectivity from jumpbox
nslookup <app-config-name>.azconfig.io
# Should resolve to 10.0.0.x (private IP)
```

---

This solution provides a production-ready, secure, and automated approach for managing App Configuration keys in both basic and AILZ deployment modes without requiring enterprise-level ARM Private Link infrastructure.
