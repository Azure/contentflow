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

## 6. Fix: App Configuration Keys Failure - ARM Private Link Delegation

**Error:**

```
appConfigKeys-a5s63braj5xj2 → Failed
Error: Forbidden - Access to the requested resource is forbidden
```

**Root Cause:**

In AILZ-integrated deployments with private endpoints, the App Configuration Store is configured with:
- `publicNetworkAccess: 'Disabled'` — no public internet access
- Private endpoint in the VNet — accessible only through private network
- `dataPlaneProxy.privateLinkDelegation: 'Disabled'` — **THIS IS THE PROBLEM**

When the `appConfigStoreKeys` Bicep module tries to create key-value pairs using the ARM deployment service, **ARM cannot access the App Configuration data plane** because:

1. ARM deployment service operates **outside the customer's VNet**
2. App Configuration has public access disabled (correct for AILZ)
3. ARM has no private endpoint connection to the customer's VNet
4. **Azure Resource Manager requires explicit private link delegation** to access resources through private endpoints during deployments

The `dataPlaneProxy.privateLinkDelegation` property controls whether ARM can access the App Configuration data plane through its own private link connection when the resource has private endpoints and public access disabled.

**This is NOT an RBAC issue** — the deployer MI has correct permissions (Owner on RG + App Configuration Data Owner). The error is a **network connectivity issue**.

---

**Microsoft Documentation:**

From [Azure App Configuration REST API - Data Plane Proxy](https://learn.microsoft.com/en-us/rest/api/appconfiguration/data-plane-proxy):

> **privateLinkDelegation**: When set to `'Enabled'`, Azure Resource Manager (ARM) can access the data plane through its private link even when public network access is disabled. This is required for ARM template deployments that create key-values in App Configuration stores with private endpoints.

**API Version:** Requires `2025-02-01-preview` or later

---

**Verification via Azure CLI:**

Confirmed current App Configuration data plane proxy configuration:

```bash
az rest --method GET \
  --url "https://management.azure.com/subscriptions/<subscription-id>/resourceGroups/<rg-name>/providers/Microsoft.AppConfiguration/configurationStores/<app-config-name>?api-version=2025-02-01-preview" \
  --query "properties.dataPlaneProxy"
```

**Current Output:**
```json
{
  "authenticationMode": "Pass-through",
  "privateLinkDelegation": "Disabled"  // ← Problem
}
```

**Required Configuration:**
```json
{
  "authenticationMode": "Pass-through",
  "privateLinkDelegation": "Enabled"  // ← Fix
}
```

---

**Solution: Conditional Private Link Delegation**

The `privateLinkDelegation` setting should be conditional based on deployment mode:

- **Basic Mode** (public deployment): Set to `'Disabled'` — ARM accesses via public endpoint, no delegation needed
- **AILZ Mode** (private endpoints): Set to `'Enabled'` — ARM needs delegation to access through private link

### File Changed: `infra/bicep/modules/app-config-store.bicep`

**Before:**

```bicep
dataPlaneProxy: {
  authenticationMode: 'Pass-through'
  privateLinkDelegation: 'Disabled'  // Hardcoded
}
```

**After:**

```bicep
dataPlaneProxy: {
  authenticationMode: 'Pass-through'
  privateLinkDelegation: enablePrivateEndpoint ? 'Enabled' : 'Disabled'  // Conditional
}
```

**How It Works:**

| Deployment Mode | `enablePrivateEndpoint` | `privateLinkDelegation` | ARM Access Method |
|-----------------|------------------------|------------------------|-------------------|
| **Basic** | `false` | `'Disabled'` | Public endpoint (internet) |
| **AILZ** | `true` | `'Enabled'` | Private link delegation |

The module already receives the `enablePrivateEndpoint` parameter from `main.bicep` (set to `isAILZIntegrated`), so no changes to the main template are required.

---

**Why Not Use Trusted Services Bypass?**

Unlike Azure Container Registry (which has `networkRuleBypassOptions: 'AzureServices'`), **Azure App Configuration does not support a trusted services bypass**. The only way for ARM to access the data plane through private endpoints is via private link delegation.

This design choice follows the principle of **explicit authorization** rather than implicit trust.

---

**Expected Results After Fix:**

✅ App Configuration Store provisions successfully  
✅ Private endpoint created in AILZ mode  
✅ `privateLinkDelegation` set to `'Enabled'` in AILZ mode  
✅ ARM deployment can access data plane through private link  
✅ `appConfigStoreKeys` module creates key-values successfully  
✅ No 403 Forbidden errors  
✅ Single `azd provision` command completes end-to-end  
✅ Basic mode continues to work with public access (delegation disabled)

---

**Verification After Deployment:**

```bash
# Verify private link delegation is enabled (AILZ mode)
az rest --method GET \
  --url "https://management.azure.com/subscriptions/<subscription-id>/resourceGroups/<rg-name>/providers/Microsoft.AppConfiguration/configurationStores/<app-config-name>?api-version=2025-02-01-preview" \
  --query "properties.dataPlaneProxy.privateLinkDelegation"

# Expected output: "Enabled"

# Verify key-values were created successfully
az appconfig kv list \
  --name <app-config-name> \
  --auth-mode login

# Should show all expected keys without errors
```

---

**Impact on Deployment Modes:**

- **Basic Mode**: No change in behavior — public access enabled, delegation disabled (least privilege)
- **AILZ Mode**: Enables ARM to deploy key-values through private network (required for functionality)

This fix maintains security best practices by only enabling private link delegation when private endpoints are actually configured.
