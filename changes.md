# Deployment Fixes – `azd up` Template Validation Errors

## Table of Contents

- [1. Fix: LogAnalytics CustomerId Must Be a GUID](#1-fix-loganalytics-customerid-must-be-a-guid)
- [2. Fix: Property Name Typo `privateEndpointsSubnetId`](#2-fix-property-name-typo-privateendpointssubnetid)
- [3. Fix: `UnmatchedPrincipalType` – `deployer().objectId` Hardcoded as `User`](#3-fix-unmatchedprincipaltype--deployerobjectid-hardcoded-as-user)

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
      principalType: deployer().objectType
      roleDefinitionIdOrName: 'Storage Blob Data Contributor'        
    }
    {
      principalId: deployer().objectId
      principalType: deployer().objectType
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
      principalType: deployer().objectType
      roleDefinitionIdOrName: 'App Configuration Data Owner'        
    }
  ]
```

**Explanation:**

The `deployer()` function in Bicep returns both `.objectId` and `.objectType`. Using `deployer().objectType` instead of the hardcoded `'User'` string dynamically resolves the correct principal type (`User` for interactive logins, `ServicePrincipal` for managed identities), making the template work with both deployment methods.
