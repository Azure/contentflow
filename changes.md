# Deployment Fixes – `azd up` Template Validation Errors

## Table of Contents

- [1. Fix: LogAnalytics CustomerId Must Be a GUID](#1-fix-loganalytics-customerid-must-be-a-guid)
- [2. Fix: Property Name Typo `privateEndpointsSubnetId`](#2-fix-property-name-typo-privateendpointssubnetid)
- [3. Fix: `UnmatchedPrincipalType` - `deployer().objectId` Hardcoded as `User`](#3-fix-unmatchedprincipaltype---deployerobjectid-hardcoded-as-user)
- [4. Cleanup: ACR Configuration Simplification](#4-cleanup-acr-configuration-simplification)
- [5. Fix: Container Apps Timeout - DNS Zone Group Creation Workaround](#5-fix-container-apps-timeout---dns-zone-group-creation-workaround)
- [6. Fix: App Configuration Keys Failure - Private Network Access Limitation](#6-fix-app-configuration-keys-failure---private-network-access-limitation)
- [7. Fix: Storage Account Name Output Returns Module Name Instead of Resource Name](#7-fix-storage-account-name-output-returns-module-name-instead-of-resource-name)
- [8. Fix: Queue Storage Private DNS Zone Missing in AILZ Resource Group](#8-fix-queue-storage-private-dns-zone-missing-in-ailz-resource-group)
- [Solution Dependencies](#solution-dependencies)

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

## 4. Cleanup: ACR Configuration Simplification

**Changes Made:**

Simplified ACR deployment configuration to align with Zero Trust and workload isolation principles:

### `infra/bicep/main.bicep`

- **Removed** `existingContainerRegistryResourceId` parameter — now always creates a new ACR per workload
- **Removed** conditional ACR creation logic (was overly complex)
- **Removed** private endpoint + RBAC configuration for existing ACR references
- **Added** `networkRuleBypassOptions: 'AzureServices'` parameter to `containerRegistry` module call
- **Simplified** container app module calls — removed conditional `placeholderImage` logic
- **Simplified** outputs — use direct `containerRegistry.outputs.*` references

### `infra/bicep/main.parameters.json`

- **Removed** `existingContainerRegistryResourceId` parameter mapping

### `infra/bicep/modules/container-registry.bicep`

- **Added** `networkRuleBypassOptions` parameter (default: `'AzureServices'`)
- Pass-through to AVM module for trusted Azure services support

### `infra/bicep/modules/acr-role-assignment.bicep`

- **DELETED** — no longer needed (no cross-resource-group ACR RBAC)

### `infra/bicep/modules/container-app.bicep`

- No changes — already has correct default `placeholderImage: 'mcr.microsoft.com/k8se/quickstart:latest'`

**Rationale:**

✅ **Zero Trust compliance** — each workload has its own ACR, no shared central registry  
✅ **Simplified codebase** — removed conditional logic and cross-RG complexity  
✅ **Trusted services bypass** — `networkRuleBypassOptions: 'AzureServices'` enables Azure services (like Azure Pipelines, GitHub Actions) to access the ACR even with `publicNetworkAccess: Disabled`  
✅ **Best practices** — aligns with Azure Landing Zone workload isolation principles

**Note:** This item documents architectural simplification. The Container Apps timeout issue (initially thought to be related to ACR image access) was actually caused by missing DNS zone groups for private endpoints. See **Item 5** below for the actual solution to the timeout problem

---

## 5. Fix: Private Endpoint DNS Zone Groups Not Created - AVM Module Limitation

**Error:**

```
Container Apps deployment timing out after 20 minutes during AILZ-integrated deployments
Storage Queue: The request may be blocked by network rules
App Configuration: Failed to resolve 'appcs-*.azconfig.io' [Errno -2] Name or service not known
```

**Symptoms:**

- Container Apps (API, Worker, Web) fail to provision and timeout after exactly 20 minutes
- Private endpoints exist and show correct IP addresses
- Private DNS Zones are linked to VNet
- **BUT**: Private DNS Zones have NO A records for any resource
- DNS zone groups do NOT exist (query returns `[]` for all resources)
- Without DNS resolution, services cannot resolve private FQDNs
- Requests fall back to public DNS but resources have `publicNetworkAccess: Disabled` → connection refused → timeout or failures

**Affected Resources:**
- ❌ Container Registry (ACR)
- ❌ Storage Account (blob + queue endpoints)
- ❌ Cosmos DB
- ❌ App Configuration

**Root Cause:**

Multiple Azure Verified Modules (AVMs) do not properly handle the `privateDnsZoneGroups` parameter when passed conditionally through wrapper modules:

- `avm/res/container-registry/registry:0.9.3`
- `avm/res/storage/storage-account:0.27.1`
- `avm/res/document-db/database-account:0.13.1`
- `avm/res/app-configuration/configuration-store:0.9.2`

Even with proper conditional logic in the configuration:

```bicep
privateDnsZoneGroups: !empty(privateDnsZoneId) ? [{...}] : []
```

The AVM modules fail to create the DNS zone group child resources, resulting in NO A record registration in the Private DNS Zones.

**Investigation via Azure CLI:**

```bash
# All returned [] (empty) - confirming no DNS zone groups created
az network private-endpoint dns-zone-group list --endpoint-name cra5s63braj5xj2-pe
az network private-endpoint dns-zone-group list --endpoint-name sta5s63braj5xj2-blob-pe
az network private-endpoint dns-zone-group list --endpoint-name sta5s63braj5xj2-queue-pe
az network private-endpoint dns-zone-group list --endpoint-name cosmos-a5s63braj5xj2-pe
az network private-endpoint dns-zone-group list --endpoint-name appcs-a5s63braj5xj2-pe

# All returned empty tables - confirming no A records registered
az network private-dns record-set a list --zone-name privatelink.azurecr.io
az network private-dns record-set a list --zone-name privatelink.blob.core.windows.net
az network private-dns record-set a list --zone-name privatelink.queue.core.windows.net
az network private-dns record-set a list --zone-name privatelink.documents.azure.com
az network private-dns record-set a list --zone-name privatelink.azconfig.io
```

**Why This Only Affects AILZ Mode:**

In **basic mode**, private endpoints are NOT created (`enablePrivateEndpoint = false`), so:
- Resources use public endpoints
- DNS resolves via Azure's public DNS
- No Private DNS Zones needed
- ✅ Works without issues

In **AILZ mode**, private endpoints ARE created (`enablePrivateEndpoint = true`), so:
- Resources have `publicNetworkAccess: 'Disabled'`
- Must resolve FQDNs via Private DNS Zones
- Requires DNS zone groups to register A records
- ❌ Fails when DNS zone groups missing

---

**Solution: Explicit DNS Zone Group Modules**

Instead of relying on the AVM modules to create DNS zone groups, we now create them explicitly using separate Bicep modules that run **after** the private endpoints are provisioned.

### Files Changed

#### **New File: `infra/bicep/modules/private-endpoint-dns-zone-group.bicep`**

Created a reusable module that creates a DNS zone group for any existing private endpoint:

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

#### **Modified: Resource Wrapper Modules**

Removed `privateDnsZoneGroups` configuration from all affected modules:

- `infra/bicep/modules/container-registry.bicep`
- `infra/bicep/modules/storage.bicep` (not removed, but will be ignored by AVM)
- `infra/bicep/modules/cosmos.bicep` (not removed, but will be ignored by AVM)
- `infra/bicep/modules/app-config-store.bicep` (not removed, but will be ignored by AVM)

**Note:** We kept the `privateDnsZoneGroups` configurations in place for documentation purposes, but they are effectively ignored as the explicit modules take precedence.

#### **Modified: `infra/bicep/main.bicep`**

Added explicit DNS zone group modules **after** each resource module:

**1. Container Registry:**
```bicep
module acrDnsZoneGroup 'modules/private-endpoint-dns-zone-group.bicep' = if (isAILZIntegrated) {
  name: 'acr-dns-zone-group-${resourceToken}'
  params: {
    privateEndpointName: '${containerRegistryName}-pe'
    privateDnsZoneId: networkConfig.privateDnsZoneIds.acr
    location: location
  }
  dependsOn: [containerRegistry]
}
```

**2. Storage Account (Blob):**
```bicep
module storageBlobDnsZoneGroup 'modules/private-endpoint-dns-zone-group.bicep' = if (isAILZIntegrated) {
  name: 'storage-blob-dns-zone-group-${resourceToken}'
  params: {
    privateEndpointName: '${storageAccountName}-blob-pe'
    privateDnsZoneId: networkConfig.privateDnsZoneIds.blob
    location: location
  }
  dependsOn: [storage]
}
```

**3. Storage Account (Queue):**
```bicep
module storageQueueDnsZoneGroup 'modules/private-endpoint-dns-zone-group.bicep' = if (isAILZIntegrated) {
  name: 'storage-queue-dns-zone-group-${resourceToken}'
  params: {
    privateEndpointName: '${storageAccountName}-queue-pe'
    privateDnsZoneId: networkConfig.privateDnsZoneIds.queue
    location: location
  }
  dependsOn: [storage]
}
```

**4. Cosmos DB:**
```bicep
module cosmosDnsZoneGroup 'modules/private-endpoint-dns-zone-group.bicep' = if (isAILZIntegrated) {
  name: 'cosmos-dns-zone-group-${resourceToken}'
  params: {
    privateEndpointName: '${cosmosAccountName}-pe'
    privateDnsZoneId: networkConfig.privateDnsZoneIds.cosmos
    location: location
  }
  dependsOn: [cosmos]
}
```

**5. App Configuration:**
```bicep
module appConfigDnsZoneGroup 'modules/private-endpoint-dns-zone-group.bicep' = if (isAILZIntegrated) {
  name: 'appconfig-dns-zone-group-${resourceToken}'
  params: {
    privateEndpointName: '${appConfigStoreName}-pe'
    privateDnsZoneId: networkConfig.privateDnsZoneIds.appConfig
    location: location
  }
  dependsOn: [appConfigStore]
}
```

**Summary of DNS Zone Groups Created:**
- 1× ACR (login server + data endpoint via single zone group)
- 2× Storage Account (blob + queue endpoints - separate zone groups)
- 1× Cosmos DB
- 1× App Configuration
- **Total: 5 DNS zone group modules**

**How It Works:**

1. **Resource Module** creates the resource with private endpoint (but DNS zone group fails silently)
2. **Explicit DNS Zone Group Module** (conditional on AILZ mode) creates the DNS zone group
3. Azure automatically registers A records in the Private DNS Zone
4. **Dependent Services** can now resolve private FQDNs correctly
5. All network connections work via private endpoints

**Expected Results After Fix:**

✅ All Private DNS Zones automatically get A records for resource FQDNs pointing to private IPs (10.0.0.x)  
✅ DNS zone groups exist for all 5 private endpoints  
✅ DNS resolution works correctly within the VNet for all resources  
✅ Container Apps deploy successfully without 20-minute timeout  
✅ Postprovision hook can access Storage Account and App Configuration  
✅ No manual DNS record creation needed  
✅ Deployment completes in 15-20 minutes total (vs 20-minute timeout)

**Verification Commands:**

```bash
# 1. Verify all DNS zone groups exist
az network private-endpoint dns-zone-group list --resource-group <workload-rg> --endpoint-name <acr-name>-pe
az network private-endpoint dns-zone-group list --resource-group <workload-rg> --endpoint-name <storage-name>-blob-pe
az network private-endpoint dns-zone-group list --resource-group <workload-rg> --endpoint-name <storage-name>-queue-pe
az network private-endpoint dns-zone-group list --resource-group <workload-rg> --endpoint-name <cosmos-name>-pe
az network private-endpoint dns-zone-group list --resource-group <workload-rg> --endpoint-name <appconfig-name>-pe

# 2. Verify A records registered in Private DNS Zones
az network private-dns record-set a list --resource-group <ailz-rg> --zone-name privatelink.azurecr.io
az network private-dns record-set a list --resource-group <ailz-rg> --zone-name privatelink.blob.core.windows.net
az network private-dns record-set a list --resource-group <ailz-rg> --zone-name privatelink.queue.core.windows.net
az network private-dns record-set a list --resource-group <ailz-rg> --zone-name privatelink.documents.azure.com
az network private-dns record-set a list --resource-group <ailz-rg> --zone-name privatelink.azconfig.io

# 3. Test DNS resolution from within VNet (e.g., from jumpbox)
nslookup <acr-name>.azurecr.io
nslookup <storage-name>.blob.core.windows.net
nslookup <storage-name>.queue.core.windows.net
nslookup <cosmos-name>.documents.azure.com
nslookup <appconfig-name>.azconfig.io
# All should resolve to 10.0.0.x private IPs
```

---

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

---

## 7. Fix: Storage Account Name Output Returns Module Name Instead of Resource Name

**Error:**

```
ERROR: HTTPSConnection(host='storage-a5s63braj5xj2.storageaccount.queue.core.windows.net', port=443):
Failed to resolve 'storage-a5s63braj5xj2.storageaccount.queue.core.windows.net'
[Errno -2] Name or service not known
```

**Symptoms:**

- Postprovision hook fails when trying to create App Configuration keys
- DNS resolution errors for Storage Account queue endpoint
- `azd env get-value STORAGE_ACCOUNT_NAME` returns incorrect value: `storage-a5s63braj5xj2.storageAccount`
- Expected value should be: `sta5s63braj5xj2`
- The `.storageAccount` suffix is the **module deployment name**, not the actual storage account name

---

**Root Cause:**

In `infra/bicep/modules/storage.bicep`, the storage account is deployed using the Azure Verified Module (AVM):

```bicep
module storageAccount 'br/public:avm/res/storage/storage-account:0.27.1' = {
  name: '${deployment().name}.storageAccount'  // Deployment name: "storage-xyz.storageAccount"
  params: {
    name: storageAccountName                    // Actual resource name: "sta5s63braj5xj2"
  }
}
```

The bug was in the module's output:

```bicep
output name string = storageAccount.name  // ❌ Returns deployment name
```

Bicep's `module.name` property returns the **deployment name** (the `name:` parameter of the module declaration), NOT the name of the resource created by that module. To get the actual resource name, you must access the module's outputs.

---

**Impact:**

1. **`main.bicep` output is incorrect:**
   ```bicep
   output STORAGE_ACCOUNT_NAME string = storage.outputs.name  // Gets wrong value
   ```
   - This output feeds `azd` environment variables
   - Results in: `STORAGE_ACCOUNT_NAME=storage-a5s63braj5xj2.storageAccount`

2. **Postprovision script fails (AILZ mode):**
   ```bash
   STORAGE_ACCOUNT=$(azd env get-value STORAGE_ACCOUNT_NAME)
   # STORAGE_ACCOUNT="storage-a5s63braj5xj2.storageAccount"  ❌
   
   az appconfig kv set --name "$APP_CONFIG_NAME" \
     --key "contentflow.common.BLOB_STORAGE_ACCOUNT_NAME" \
     --value "$STORAGE_ACCOUNT"  # Wrong value inserted! ❌
   ```

3. **DNS resolution fails:**
   - Code constructs: `${STORAGE_ACCOUNT}.queue.core.windows.net`
   - Results in: `storage-a5s63braj5xj2.storageaccount.queue.core.windows.net` ❌
   - Correct would be: `sta5s63braj5xj2.queue.core.windows.net` ✅

4. **Container Apps cannot access storage:**
   - Apps read storage account name from App Configuration
   - Receive incorrect value with `.storageAccount` suffix
   - Cannot connect to blob storage or queues

---

**Solution:**

### File Changed: `infra/bicep/modules/storage.bicep`

**Line 184 - Before:**
```bicep
output name string = storageAccount.name
```

**Line 184 - After:**
```bicep
output name string = storageAccount.outputs.name
```

**Explanation:**

- `storageAccount.name` → Returns the **module deployment name** (`storage-xyz.storageAccount`)
- `storageAccount.outputs.name` → Returns the actual **storage account resource name** from the AVM module (`sta5s63braj5xj2`)

The AVM module exposes the actual resource name via its output properties. By accessing `outputs.name`, we get the correct value that was passed in the `params.name` and used to create the actual Azure Storage Account resource.

---

**Verification:**

To verify the fix works correctly:

```bash
# 1. Check azd environment has correct storage account name
azd env get-value STORAGE_ACCOUNT_NAME
# Expected: sta5s63braj5xj2 (no .storageAccount suffix)

# 2. Verify DNS resolution works from jumpbox
nslookup sta5s63braj5xj2.queue.core.windows.net
# Should resolve to private IP (10.0.0.x) in AILZ mode

# 3. Check App Configuration keys have correct value
az appconfig kv show \
  --name appcs-<resource-token> \
  --key "contentflow.common.BLOB_STORAGE_ACCOUNT_NAME" \
  --auth-mode login \
  --query "value" -o tsv
# Expected: sta5s63braj5xj2

# 4. Test storage queue creation from postprovision hook
az storage queue create \
  --name test-queue \
  --account-name sta5s63braj5xj2 \
  --auth-mode login
# Should succeed without DNS errors
```

---

**Related Modules (No Issues Found):**

Audited all other modules that use the same pattern. All others correctly use `module.outputs.name`:

✅ `log-analytics-ws.bicep`: `output name string = logAnalytics.outputs.name`  
✅ `container-apps-environment.bicep`: `output name string = containerAppsEnvironment.outputs.name`  
✅ `app-config-store.bicep`: `output name string = appConfigStore.outputs.name`  
✅ `container-registry.bicep`: `output name string = containerRegistry.outputs.name`  
✅ `user-assigned-identity.bicep`: `output name string = userAssignedIdentity.outputs.name`  
✅ `static-web-app.bicep`: `output name string = staticWebApp.outputs.name`

⚠️ `container-app.bicep`: Uses `output name string = containerApp.name` but this output is **never consumed** in `main.bicep` (only `.outputs.fqdn` is used), so no impact.

---

**Benefits After Fix:**

✅ **Correct storage account name** propagates to azd environment  
✅ **DNS resolution works** for blob and queue endpoints  
✅ **Postprovision hook succeeds** in AILZ mode  
✅ **App Configuration keys** contain correct storage account name  
✅ **Container Apps** can connect to storage successfully  
✅ **No breaking changes** — existing code in `main.bicep` uses variable `storageAccountName` for App Config keys (basic mode), not affected by this output

---

## 8. Fix: Queue Storage Private DNS Zone Missing in AILZ Resource Group

**Error:**

```
LinkedInvalidPropertyId: Property id '' at path 'properties.privateDnsZoneConfigs[0].properties.privateDnsZoneId' 
is invalid. Expect fully qualified resource Id that start with '/subscriptions/{subscriptionId}' 
or '/providers/{resourceProviderNamespace}/'.
```

**Symptoms:**

- Deployment fails after all resources provision successfully
- Error occurs during `storageQueueDnsZoneGroup` module creation
- `privateDnsZoneId` parameter is empty (`''`)
- Script `get-ailz-resources.sh` cannot find Queue Storage DNS Zone
- Azure Portal shows AILZ resource group (`rg-mini-ailz-jx05`) has only 6 Private DNS Zones:
  - ✅ `privatelink.azconfig.io`
  - ✅ `privatelink.azurecr.io`
  - ✅ `privatelink.azurecontainerapps.io`
  - ✅ `privatelink.blob.core.windows.net`
  - ✅ `privatelink.cognitiveservices.azure.com`
  - ✅ `privatelink.documents.azure.com`
  - ❌ `privatelink.queue.core.windows.net` **(MISSING)**

---

**Root Cause:**

Azure Storage Account creates **two separate private endpoints** when network isolation is enabled:
1. **Blob endpoint** (`privatelink.blob.core.windows.net`) — ✅ Exists in AILZ RG
2. **Queue endpoint** (`privatelink.queue.core.windows.net`) — ❌ Does NOT exist in AILZ RG

Both endpoints are created by ContentFlow deployment, but only the Blob DNS Zone was provisioned in the AILZ resource group. Without the Queue DNS Zone, the `storageQueueDnsZoneGroup` module cannot create the DNS zone group configuration, causing deployment failure.

**Why This Wasn't Caught Earlier:**

Items 1-7 focused on **existing** Private DNS Zones (ACR, Blob, Cosmos, App Config). The Queue DNS Zone requirement was assumed to exist alongside Blob, but AILZ infrastructure only provisioned Blob zone initially.

---

**Solution: Conditional DNS Zone Group Creation**

Since the Queue Storage Private DNS Zone is **infrastructure that must be created by the AILZ administrator** (not by this deployment template), we make the Queue DNS Zone Group creation **conditional** — it only executes if the DNS Zone exists.

### Files Changed

#### **Modified: `infra/bicep/main.bicep`** (line 247)

**Before:**
```bicep
module storageQueueDnsZoneGroup 'modules/private-endpoint-dns-zone-group.bicep' = if (isAILZIntegrated) {
  name: 'storage-queue-dns-zone-group-${resourceToken}'
  params: {
    privateEndpointName: '${storageAccountName}-queue-pe'
    privateDnsZoneId: networkConfig.privateDnsZoneIds.queue
    location: location
  }
  dependsOn: [storage]
}
```

**After:**
```bicep
module storageQueueDnsZoneGroup 'modules/private-endpoint-dns-zone-group.bicep' = if (isAILZIntegrated && !empty(networkConfig.privateDnsZoneIds.queue)) {
  name: 'storage-queue-dns-zone-group-${resourceToken}'
  params: {
    privateEndpointName: '${storageAccountName}-queue-pe'
    privateDnsZoneId: networkConfig.privateDnsZoneIds.queue
    location: location
  }
  dependsOn: [storage]
}
```

**Explanation:**

Added `&& !empty(networkConfig.privateDnsZoneIds.queue)` condition:
- **Before:** Module always executes in AILZ mode (even with empty DNS zone ID → deployment fails)
- **After:** Module only executes if DNS zone ID is not empty (deployment succeeds, DNS zone group skipped)

This allows deployment to proceed without error while the Queue DNS Zone is missing, but maintains the correct configuration when the zone exists.

#### **Modified: `infra/bicep/main.bicep`** (parameter added at line ~44)

**Added:**
```bicep
@description('Resource ID of existing Queue Storage Private DNS Zone (required for ailz-integrated mode)')
param existingQueuePrivateDnsZoneId string = ''
```

#### **Modified: `infra/bicep/main.bicep`** (networkConfig object at line ~136)

**Added:**
```bicep
privateDnsZoneIds: {
  cognitiveServices: existingCognitiveServicesPrivateDnsZoneId
  blob: existingBlobPrivateDnsZoneId
  queue: existingQueuePrivateDnsZoneId  // ← Added
  cosmos: existingCosmosPrivateDnsZoneId
  appConfig: existingAppConfigPrivateDnsZoneId
  acr: existingAcrPrivateDnsZoneId
  keyVault: existingKeyVaultPrivateDnsZoneId
  containerAppsEnv: existingContainerAppsEnvPrivateDnsZoneId
}
```

#### **Modified: `infra/scripts/get-ailz-resources.sh`** (line ~180)

**Added:**
```bash
get_resource_id "Queue Storage Private DNS Zone" "EXISTING_QUEUE_PRIVATE_DNS_ZONE_ID" \
    "az network private-dns zone show --name privatelink.queue.core.windows.net --resource-group $AILZ_RG --query id -o tsv"
```

---

**Impact: Deployment Will Succeed BUT Queue Access Will Fail**

With this fix:

✅ **Deployment completes successfully** (no more `LinkedInvalidPropertyId` error)  
✅ **All resources provision** (Storage Account, Container Apps, etc.)  
✅ **Blob endpoint works** (has DNS zone + DNS zone group)  
❌ **Queue endpoint DOES NOT WORK** (no DNS resolution)  
❌ **Worker service cannot access queue** (cannot process content)

**Why Queue Access Fails Without DNS Zone:**

```
Worker Container App (in VNet)
    ↓
Tries to connect: sta5s63braj5xj2.queue.core.windows.net
    ↓
DNS resolution fails (no A record in Private DNS Zone)
    ↓
Falls back to public DNS → gets public IP
    ↓
Storage Account has publicNetworkAccess: 'Disabled'
    ↓
Connection refused → HTTPSConnectionError
```

Without the DNS zone group, there's no A record registered in Private DNS Zone. DNS resolution fails, and the Worker cannot access the queue endpoint even though the private endpoint exists.

---

**Required Action: Request DNS Zone Creation from AILZ Administrator**

To fully resolve this issue, the AILZ administrator must create the missing Private DNS Zone.

### Request Context for Administrator

**What's Needed:**
- Create Private DNS Zone: `privatelink.queue.core.windows.net`
- Location: AILZ Resource Group `rg-mini-ailz-jx05`
- Link to VNet: Same VNet used for other Private DNS Zones
- Reason: Storage Account creates 2 private endpoints (blob + queue), each requires its own DNS zone

**Technical Context:**

Azure Storage Account with private endpoints enabled creates **two separate service endpoints**:
1. **Blob Service** (`*.blob.core.windows.net`) — DNS zone exists ✅
2. **Queue Service** (`*.queue.core.windows.net`) — DNS zone missing ❌

Without both DNS zones, ContentFlow Worker service cannot access Azure Storage Queue, which is required for asynchronous content processing tasks.

**Impact:**
- **Current:** Deployment succeeds but Worker service non-functional (cannot process content)
- **After DNS Zone Created:** Worker can access queue → full functionality restored

### Azure CLI Commands for Administrator

```bash
# 1. Create Queue Storage Private DNS Zone
az network private-dns zone create \
  --resource-group rg-mini-ailz-jx05 \
  --name privatelink.queue.core.windows.net

# 2. Link DNS Zone to VNet (replace with actual VNet name)
az network private-dns link vnet create \
  --resource-group rg-mini-ailz-jx05 \
  --zone-name privatelink.queue.core.windows.net \
  --name ailz-vnet-link \
  --virtual-network <ailz-vnet-name> \
  --registration-enabled false
```

**After DNS Zone Created:**

1. Development team re-runs discovery script on jumpbox:
   ```bash
   cd ~/contentflow
   ./infra/scripts/get-ailz-resources.sh
   ```

2. Verify Queue DNS Zone ID is set:
   ```bash
   azd env get-value EXISTING_QUEUE_PRIVATE_DNS_ZONE_ID
   # Should return: /subscriptions/.../privateDnsZones/privatelink.queue.core.windows.net
   ```

3. Re-deploy to create DNS zone group:
   ```bash
   azd provision --no-prompt
   ```

4. Verify DNS zone group created:
   ```bash
   az network private-endpoint dns-zone-group list \
     --resource-group rg-contentflow-test004-jx05 \
     --endpoint-name sta5s63braj5xj2-queue-pe
   ```

5. Verify A record registered:
   ```bash
   az network private-dns record-set a list \
     --resource-group rg-mini-ailz-jx05 \
     --zone-name privatelink.queue.core.windows.net
   # Should show A record for sta5s63braj5xj2 → 10.0.0.x
   ```

6. Test DNS resolution from jumpbox:
   ```bash
   nslookup sta5s63braj5xj2.queue.core.windows.net
   # Should resolve to private IP (10.0.0.x)
   ```

---

**Why Not Make Queue Storage Optional?**

The Worker service requires Azure Storage Queue for task distribution and content processing orchestration. Without queue access, the core functionality of ContentFlow does not work.

**Alternatives Considered:**
- ❌ **Enable public network access** — Violates Zero Trust / network isolation policies
- ❌ **Use only blob storage** — Requires major application architecture changes
- ❌ **Remove worker service** — ContentFlow becomes non-functional (cannot process content)
- ✅ **Request DNS Zone creation** — Minimal infrastructure change, preserves security, enables full functionality

---

**Expected Results After DNS Zone Created and Redeployed:**

✅ All 5 DNS zone groups exist (ACR, Blob, **Queue**, Cosmos, App Config)  
✅ All 5 Private DNS Zones have A records registered  
✅ Worker service can access Storage Queue via private endpoint  
✅ Content processing workflows function correctly  
✅ Complete end-to-end deployment successful

---

**Verification After Full Fix:**

```bash
# 1. Verify all 5 DNS zone groups exist
az network private-endpoint dns-zone-group list --resource-group <workload-rg> --endpoint-name <acr-name>-pe
az network private-endpoint dns-zone-group list --resource-group <workload-rg> --endpoint-name <storage-name>-blob-pe
az network private-endpoint dns-zone-group list --resource-group <workload-rg> --endpoint-name <storage-name>-queue-pe  # ← This one
az network private-endpoint dns-zone-group list --resource-group <workload-rg> --endpoint-name <cosmos-name>-pe
az network private-endpoint dns-zone-group list --resource-group <workload-rg> --endpoint-name <appconfig-name>-pe

# 2. Verify A records in all 5 Private DNS Zones
az network private-dns record-set a list --resource-group <ailz-rg> --zone-name privatelink.azurecr.io
az network private-dns record-set a list --resource-group <ailz-rg> --zone-name privatelink.blob.core.windows.net
az network private-dns record-set a list --resource-group <ailz-rg> --zone-name privatelink.queue.core.windows.net  # ← This one
az network private-dns record-set a list --resource-group <ailz-rg> --zone-name privatelink.documents.azure.com
az network private-dns record-set a list --resource-group <ailz-rg> --zone-name privatelink.azconfig.io

# 3. Test worker queue access (check Container App logs)
az containerapp logs show \
  --name worker-<resource-token> \
  --resource-group <workload-rg> \
  --follow \
  --query "[?contains(Log, 'Queue')]"
```

---

## Solution Dependencies

Some fixes depend on others to function correctly. Understanding these dependencies is important for deployment sequencing and troubleshooting.

### Dependency Graph

```
Items 1-4 (Independent)
    ↓
Item 5: DNS Zone Groups (Foundation)
    ↓
    ├──→ Item 6: App Config Keys Postprovision Hook (Requires DNS resolution)
    ├──→ Item 7: Storage Account Name Output (Independent bug, but output consumed by Item 6)
    └──→ Item 8: Queue Storage DNS Zone (Infrastructure prerequisite - BLOCKED)
```

### Dependency Details

#### **Item 5 enables Item 6** (Critical Dependency)

**Item 5** (DNS Zone Groups) is a **prerequisite** for **Item 6** (App Config Keys Postprovision Hook):

- **Without Item 5:** Postprovision hook fails with DNS resolution errors
  ```
  Failed to resolve 'sta5s63braj5xj2.queue.core.windows.net'
  Failed to resolve 'appcs-a5s63braj5xj2.azconfig.io'
  ```

- **With Item 5:** DNS zone groups register A records → jumpbox can resolve FQDNs → postprovision hook succeeds

**Why:** The postprovision hook runs from the jumpbox VM (inside VNet) and must access Storage Account and App Configuration via private endpoints. Without DNS zone groups, there are no A records in Private DNS Zones, so DNS resolution fails.

#### **Item 7 consumed by Item 6** (Data Dependency)

**Item 7** (Storage Account Name Output) is **independent** but its output is **consumed by Item 6**:

- **Without Item 7:** Wrong storage account name (`storage-xyz.storageAccount`) inserted into App Config
- **With Item 7:** Correct storage account name (`sta5s63braj5xj2`) inserted into App Config

**Why:** The postprovision hook reads `STORAGE_ACCOUNT_NAME` from azd environment (populated from Bicep output) and writes it to App Configuration keys. Container Apps read this value to connect to blob storage and queues.

#### **Item 8 blocks Worker functionality** (Infrastructure Dependency)

**Item 8** (Queue Storage DNS Zone) is **BLOCKED** by missing infrastructure in AILZ resource group:

- **Without Item 8:** Deployment succeeds but Worker service cannot access Storage Queue (no DNS resolution)
- **With Item 8:** Worker can access queue → full ContentFlow functionality

**Why:** Storage Account creates two private endpoints (blob + queue). Item 5 implemented support for both DNS zone groups, but the Queue DNS Zone itself does not exist in AILZ RG. This is an **infrastructure prerequisite** that must be created by AILZ administrator before Worker service can function.

**Current Status:** Code is ready (Items 5 + 8 completed), awaiting DNS zone creation by admin.

#### **Items 1-4 are Independent**

These fixes have no dependencies on other items:

- **Item 1** (LogAnalytics CustomerId): Standalone Bicep reference() function fix
- **Item 2** (Property Name Typo): Simple typo fix in parameter name
- **Item 3** (UnmatchedPrincipalType): Standalone deployer() principalType detection
- **Item 4** (ACR Configuration Simplification): Architectural cleanup, no dependencies

### Deployment Order (Recommended)

All items are implemented in Bicep code and deployed together via `azd provision`. The dependency resolution happens automatically:

1. **Bicep Provisioning** deploys Items 1-8 (in dependency order managed by Bicep's `dependsOn`)
2. **Item 5 modules execute** after resource modules (explicit `dependsOn: [storage]`, `dependsOn: [appConfigStore]`, etc.)
3. **Item 8 Queue DNS Zone Group** conditionally skipped (DNS zone doesn't exist yet)
4. **Postprovision Hook** (Item 6) executes after Bicep completes, relies on Item 5 DNS + Item 7 outputs

**No manual sequencing needed** — the Bicep module dependencies and azd hooks ensure correct execution order.

**Note:** Item 8 (Queue Storage DNS Zone) requires AILZ administrator action before full deployment can succeed. Current deployment completes but Worker service remains non-functional until Queue DNS Zone is created.
