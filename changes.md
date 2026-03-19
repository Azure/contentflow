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

## 4. Feature: Support Existing Container Registry from AI Landing Zone

**Problem:**

In AILZ-integrated deployments without internet egress (no NAT Gateway), the Container Apps provisioning fails with a **20-minute timeout** because it cannot pull the hardcoded placeholder image `mcr.microsoft.com/azuredocs/containerapps-helloworld:latest` from the public Microsoft Container Registry (MCR). The private VNet has no outbound internet connectivity, making any MCR pull impossible.

**Solution:**

Added support for referencing an existing Azure Container Registry from the AI Landing Zone, following the same conditional pattern used for Log Analytics and App Insights. When an existing ACR is provided, the template:

1. **Skips creating** a new Container Registry
2. **References the existing ACR** using the Bicep `existing` keyword
3. **Creates a private endpoint** for the existing ACR in the app's PE subnet (enables cross-VNet connectivity)
4. **Assigns RBAC** (AcrPull + AcrPush) to the managed identity on the existing ACR
5. **Uses a conditioned placeholder image** — MCR for basic mode (has internet), `${acr}/placeholder:latest` for AILZ (no internet)

**Prerequisites for AILZ mode:**

Before running `azd provision`, import a placeholder image into the existing ACR:
```bash
az acr import --name <existing-acr> --source mcr.microsoft.com/k8se/quickstart:latest --image placeholder:latest
```

Then set the environment variable (use the full resource ID):
```bash
azd env set EXISTING_CONTAINER_REGISTRY_RESOURCE_ID "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.ContainerRegistry/registries/<acr-name>"
```

**Affected Files:**

### `infra/bicep/main.bicep`

- Added `existingContainerRegistryResourceId` parameter (string, default empty)
- Added `shouldCreateContainerRegistry` conditional variable
- Added `existingAcrName` and `existingAcrResourceGroup` derived from resource ID
- Wrapped existing `containerRegistry` module with `if (shouldCreateContainerRegistry)`
- Added `containerRegistryLoginServer` (deterministic `<name>.azurecr.io`) and `containerRegistryNameResolved` variables
- Added private endpoint + DNS zone group for existing ACR (conditioned on AILZ mode), using the resource ID in `privateLinkServiceId`
- Added cross-resource-group RBAC module (`modules/acr-role-assignment.bicep`) with `scope: resourceGroup(existingAcrResourceGroup)` for AcrPull + AcrPush
- Updated all 3 container app module calls to use `containerRegistryLoginServer` instead of `containerRegistry!.outputs.loginServer`
- Added `placeholderImage` parameter to all 3 container app module calls
- Updated outputs to use resolved variables

### `infra/bicep/modules/acr-role-assignment.bicep` (new file)

New module for cross-resource-group RBAC assignment on an existing ACR. Deployed with `scope: resourceGroup(existingAcrResourceGroup)` so it can reference the ACR in its own resource group. Assigns AcrPull and AcrPush to the managed identity.

### `infra/bicep/main.parameters.json`

Added parameter mapping:
```json
"existingContainerRegistryResourceId": {
  "value": "${EXISTING_CONTAINER_REGISTRY_RESOURCE_ID=}"
}
```

### `infra/bicep/modules/container-app.bicep`

- Added `placeholderImage` parameter (string, default `mcr.microsoft.com/k8se/quickstart:latest`)
- Replaced hardcoded MCR image with `placeholderImage` parameter

**Scenario Matrix:**

| Mode | `EXISTING_CONTAINER_REGISTRY_RESOURCE_ID` | ACR Created | Placeholder Image | PE Created |
|------|-------------------------------------|-------------|-------------------|------------|
| basic | empty (default) | Yes (new) | `mcr.microsoft.com/k8se/quickstart:latest` | No |
| ailz-integrated | empty | Yes (new) | `mcr.microsoft.com/k8se/quickstart:latest` | Yes (new ACR) |
| ailz-integrated | `/subscriptions/.../registries/<acr>` | No (existing) | `<acr>/placeholder:latest` | Yes (existing ACR) |
