# Deployment Fixes – `azd up` Template Validation Errors

## Table of Contents

- [1. Fix: LogAnalytics CustomerId Must Be a GUID](#1-fix-loganalytics-customerid-must-be-a-guid)
- [2. Fix: Property Name Typo `privateEndpointsSubnetId`](#2-fix-property-name-typo-privateendpointssubnetid)
- [3. Fix: `UnmatchedPrincipalType` – `deployer().objectId` Hardcoded as `User`](#3-fix-unmatchedprincipaltype--deployerobjectid-hardcoded-as-user)
- [4. Feature: Support Existing Container Registry from AI Landing Zone](#4-feature-support-existing-container-registry-from-ai-landing-zone)

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

## 3. Fix: `UnmatchedPrincipalType` – `deployer().objectId` Hardcoded as `User`

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
