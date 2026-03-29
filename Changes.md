# Deployment Fixes – `azd deploy` in `ailz-integrated` mode

## Table of Contents

- [1. Fix: `remoteBuild: true` Incompatible with Private ACR](#1-fix-remotebuild-true-incompatible-with-private-acr)
- [2. Fix: ACR Pull Fails on Fresh Environment Due to RBAC Propagation Delay](#2-fix-acr-pull-fails-on-fresh-environment-due-to-rbac-propagation-delay)
- [3. Fix: Container Apps `ingress.external: false` Blocks VNet Traffic in Internal CAE](#3-fix-container-apps-ingressexternal-false-blocks-vnet-traffic-in-internal-cae)
- [4. Fix: Queue Private Endpoint Missing DNS A Record](#4-fix-queue-private-endpoint-missing-dns-a-record)

---

## 1. Fix: `remoteBuild: true` Incompatible with Private ACR

**Error:**

```
failed to login, ran out of retries: failed to set docker credentials:
Error response from daemon: Get "https://crmpuiourm56df6.azurecr.io/v2/": denied:
client with IP '104.208.200.68' is not allowed access.
```

Followed by the local Docker fallback also failing:

```
Local fallback unavailable: the docker service is not running, please start it:
exit code: 1, stderr: permission denied while trying to connect to the Docker API
at unix:///var/run/docker.sock
```

**Root Cause:**

`remoteBuild: true` in `azure.yaml` causes `azd` to use ACR Tasks to build container images. ACR Tasks run from public Azure infrastructure IPs. In `ailz-integrated` mode the ACR is provisioned with `publicNetworkAccess: Disabled`, so those IPs are rejected at the network level. This is a hard incompatibility [documented by Microsoft](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-private-link#use-az-acr-build-with-private-endpoint-and-private-registry): *"If you disable public network access, `az acr build` commands will fail."*

When `azd` fell back to a local Docker build, a second issue blocked it: the JumpBox user `aiuser` was not a member of the `docker` group, causing `permission denied` on `/var/run/docker.sock`. The Docker daemon itself was running correctly.

**Files:** `azure.yaml`, `infra/scripts/pre-provision.sh`, `infra/README.md`

---

### `azure.yaml` — Remove `remoteBuild: true` from all services

**Before:**

```yaml
services:
  api:
    project: ./contentflow-api
    language: py
    host: containerapp
    docker:
      path: ./Dockerfile
      context: ..
      remoteBuild: true
  worker:
    project: ./contentflow-worker
    language: py
    host: containerapp
    docker:
      path: ./Dockerfile
      context: ..
      remoteBuild: true
  web:
    project: ./contentflow-web
    language: ts
    host: containerapp
    docker:
      path: ./Dockerfile
      remoteBuild: true
```

**After:**

```yaml
services:
  api:
    project: ./contentflow-api
    language: py
    host: containerapp
    docker:
      path: ./Dockerfile
      context: ..
  worker:
    project: ./contentflow-worker
    language: py
    host: containerapp
    docker:
      path: ./Dockerfile
      context: ..
  web:
    project: ./contentflow-web
    language: ts
    host: containerapp
    docker:
      path: ./Dockerfile
```

Removing `remoteBuild` makes `azd` always perform a local Docker build from the machine running the command. In `basic` mode the local machine pushes to the ACR public endpoint. In `ailz-integrated` mode the JumpBox is inside the AILZ VNet and can push via the ACR private endpoint. Both modes functionally equivalent; local build was already an implicit prerequisite since Docker is declared as a required tool.

---

### `infra/scripts/pre-provision.sh` — Validate Docker daemon access

**Before:**

```bash
echo "✓ Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    exit 1
fi
```

**After:**

```bash
echo "✓ Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    exit 1
fi

echo "✓ Checking Docker daemon..."
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running or current user cannot connect to it."
    echo "   For Linux: ensure dockerd is running and your user is in the 'docker' group."
    echo "   Run: sudo usermod -aG docker \$USER  (then log out and back in)"
    exit 1
fi
```

The previous check only verified that the Docker CLI binary was installed, not that the daemon was reachable by the current user. Since a local Docker build is now required at deploy time, this catches the missing group membership issue early with a clear, actionable message.

---

### `infra/README.md` — Update build step description

**Before:**

> Builds Docker images (remote build)  
> Pushes to ACR  
> Updates Container Apps

**After:**

> Builds Docker images locally (requires Docker daemon running on the machine executing `azd`)  
> Pushes to ACR (via public endpoint in `basic` mode, via private endpoint in `ailz-integrated` mode — must be executed from within the AI LZ VNet, e.g. from the JumpBox VM)  
> Updates Container Apps

---

## 2. Fix: ACR Pull Fails on Fresh Environment Due to RBAC Propagation Delay

**Error:**

```
Failed to provision revision for container app 'api-xmi4h2hmzcfbk'.
Error details: Invalid value: "crxmi4h2hmzcfbk.azurecr.io/contentflow/api-content_flow_sunday29:azd-deploy-1774789666":
unable to pull image using Managed identity
/subscriptions/.../providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-xmi4h2hmzcfbk
for registry crxmi4h2hmzcfbk.azurecr.io
```

**Root Cause:**

When `azd up` runs on a fresh environment, Bicep creates the Managed Identity, the ACR, and the `AcrPull` role assignment in a single ARM deployment. ARM reports success as soon as the role assignment _resource_ exists. However, Azure RBAC propagation is **eventually consistent** — the `AcrPull` permission can take up to 10 minutes to be effective across all Azure data planes.

`azd up` proceeds immediately from `provision` to `deploy`. During deploy, `azd` pushes the image to ACR (succeeds because push uses the CLI's own credentials), then updates the Container App revision. The Container App infrastructure tries to pull the image using the Managed Identity's `AcrPull` role, but the role has not yet propagated — resulting in the pull failure above.

This affects **both deployment modes** (`basic` and `ailz-integrated`) because both use Managed Identity + `AcrPull` for registry access. The failure is more frequent in `ailz-integrated` mode because the private endpoint adds additional resolution latency.

**Files:** `azure.yaml`, `infra/scripts/pre-deploy.sh`

---

### `azure.yaml` — Add global `predeploy` hook

**Before:**

```yaml
# Global hooks
hooks:
  preprovision:
    shell: sh
    run: ./infra/scripts/pre-provision.sh
    interactive: false
    continueOnError: false
  
  postprovision:
    shell: sh
    run: ./infra/scripts/post-provision.sh
    interactive: false
    continueOnError: false

  postdeploy:
    shell: sh
    run: ./infra/scripts/post-deploy.sh
    interactive: true
    continueOnError: false
```

**After:**

```yaml
# Global hooks
hooks:
  preprovision:
    shell: sh
    run: ./infra/scripts/pre-provision.sh
    interactive: false
    continueOnError: false
  
  postprovision:
    shell: sh
    run: ./infra/scripts/post-provision.sh
    interactive: false
    continueOnError: false

  # Run before deploying services - validates ACR pull readiness
  predeploy:
    shell: sh
    run: ./infra/scripts/pre-deploy.sh
    interactive: false
    continueOnError: false

  postdeploy:
    shell: sh
    run: ./infra/scripts/post-deploy.sh
    interactive: true
    continueOnError: false
```

The `predeploy` hook already existed as a script (`infra/scripts/pre-deploy.sh`) but was **not wired** into `azure.yaml`. Now it runs automatically before `azd` deploys any service — both in `azd up` and standalone `azd deploy`.

---

### `infra/scripts/pre-deploy.sh` — ACR Pull Readiness Gate

**Before:**

```bash
#!/bin/bash
# Pre-deploy hook - runs before deploying all services
set -e

# ... basic infrastructure check only ...

if ! azd env get-value AZURE_RESOURCE_GROUP &> /dev/null; then
    echo "❌ Infrastructure not provisioned. Please run 'azd provision' first."
    exit 1
fi

echo "✓ Infrastructure is ready for deployment"
```

**After:**

The script now performs a 3-phase ACR readiness validation:

**Phase 1 — AcrPull role visibility polling (both modes)**

Reads `AZURE_CONTAINER_REGISTRY_NAME` and `MANAGED_IDENTITY_PRINCIPAL_ID` from `azd env` outputs. Polls `az role assignment list` every 10 seconds until `AcrPull` appears for the principal on the ACR scope. Timeout defaults to 300 seconds. If the role is already visible (e.g. second deploy on existing environment), passes immediately with no delay.

```bash
ROLES=$(az role assignment list \
    --assignee-object-id "$IDENTITY_PRINCIPAL_ID" \
    --scope "$ACR_RESOURCE_ID" \
    --query "[?roleDefinitionName=='AcrPull'].roleDefinitionName" \
    -o tsv 2>/dev/null || echo "")
```

**Phase 2 — ACR Private Endpoint DNS verification (AILZ only)**

In `ailz-integrated` mode, verifies that the ACR login server resolves to a private IP (RFC 1918 range). If it resolves to a public IP or doesn't resolve, emits a warning. This catches misconfigured `privatelink.azurecr.io` DNS zones early.

**Phase 3 — RBAC stabilization wait (both modes)**

After `AcrPull` is visible in the control plane, waits a configurable stabilization period (default: 60 seconds) before allowing deploy. This compensates for the gap between role assignment queryability and data plane effectiveness.

**Configurability:**

| Variable | Default | Override |
|---|---|---|
| `ACR_RBAC_TIMEOUT` | 300s | `ACR_RBAC_TIMEOUT=600 azd deploy` |
| `ACR_RBAC_STABILIZATION` | 60s | `ACR_RBAC_STABILIZATION=0 azd deploy` |

On an existing environment where RBAC is already propagated, the script detects `AcrPull` immediately and only waits the stabilization period. For subsequent deploys where no RBAC change occurred, the stabilization can be set to 0.

**Failure behavior:**

If the timeout is reached without finding `AcrPull`, the script exits with code 1 and prints:
- The ACR name and principal ID that failed
- The elapsed wait time
- The retry command with instructions to increase timeout

---

## 3. Fix: Container Apps `ingress.external: false` Blocks VNet Traffic in Internal CAE

**Error:**

From JumpBox or Application Gateway attempting to reach any Container App:

```
HTTP 404 — site not found
```

The Container Apps are running and healthy, but unreachable from VNet resources outside the CAE.

**Root Cause:**

All three Container Apps (API, Worker, Web) were provisioned with `externalIngress: !isAILZIntegrated`, which evaluates to `false` in `ailz-integrated` mode. In an **internal** Container Apps Environment (`internal: true`), the `ingress.external` flag controls VNet-level visibility:

| `ingress.external` | Internal CAE behavior |
|---|---|
| `true` | Accessible from **any resource in the VNet** (App Gateway, JumpBox, other subnets) |
| `false` | Accessible **only from other Container Apps in the same CAE** |

With `external: false`, the App Gateway, JumpBox, and any other VNet-hosted client receives HTTP 404 because the CAE reverse proxy refuses to route traffic from non-CAE sources.

Critically, in an internal CAE **neither setting exposes the app to the internet** — the CAE itself has no public IP. Setting `external: true` in an internal CAE simply opens VNet-level routing, which is exactly what's needed for Application Gateway integration.

**Impact on both deployment modes:**

| Mode | Before | After | Net change |
|---|---|---|---|
| `basic` | `externalIngress: true` (public CAE, internet-facing) | `externalIngress: true` | **None** — already `true` |
| `ailz-integrated` | `externalIngress: false` (internal CAE, CAE-only) | `externalIngress: true` (internal CAE, VNet-accessible) | **VNet resources can now reach the apps** — no internet exposure |

**Files:** `infra/bicep/main.bicep`

---

### `main.bicep` — Change `externalIngress` to `true` for all three Container Apps

**Before (API, line ~578):**

```bicep
externalIngress: !isAILZIntegrated
```

**After:**

```bicep
externalIngress: true
```

The same change was applied to:
- **API** Container App (`apiContainerApp`)
- **Worker** Container App (`workerContainerApp`)
- **Web** Container App (`webContainerApp`)

All three previously had `externalIngress: !isAILZIntegrated`. Now all three have `externalIngress: true`. The `container-app.bicep` module default was already `true` — the override in `main.bicep` was forcing it to `false` in AILZ mode.

---

## 4. Fix: Queue Private Endpoint Missing DNS A Record

**Error:**

Worker container crashes on startup validation:

```
azure.core.exceptions.HttpResponseError: Unable to resolve host queue endpoint
```

Or: the queue private endpoint exists but `nslookup <storageaccount>.queue.core.windows.net` returns a public IP instead of the private endpoint IP, causing timeouts in a private-network-only environment.

**Root Cause:**

Three compounding gaps prevented the queue private DNS zone ID from reaching the storage module:

1. **`main.parameters.json`** — Missing `existingQueuePrivateDnsZoneId` mapping. The `get-ailz-resources.sh` script discovers the value and sets `EXISTING_QUEUE_PRIVATE_DNS_ZONE_ID` in the azd environment, but the parameters file never passed it to Bicep.

2. **`main.bicep` storage module call** — The `queuePrivateDnsZoneId` parameter was never passed. The `blobPrivateDnsZoneId` was correctly passed, but the queue equivalent was missing.

3. **`main.bicep` storageQueueDnsZoneGroup condition** — The condition `isAILZIntegrated && !empty(existingQueuePrivateDnsZoneId)` was too restrictive. Since the parameter was always empty (due to gaps 1 and 2), this fallback DNS zone group module never executed.

Additionally, the AILZ validation block did not validate the presence of `existingQueuePrivateDnsZoneId`, so the deployment proceeded silently without the queue DNS zone.

**Impact on both deployment modes:**

| Mode | Before | After | Net change |
|---|---|---|---|
| `basic` | No private endpoints, public access | No private endpoints, public access | **None** — queue PE not used in basic mode |
| `ailz-integrated` | Queue PE created but no DNS A record → worker crash | Queue PE created **with** DNS A record → worker resolves correctly | **Queue endpoint resolves to private IP** |

**Files:** `infra/bicep/main.bicep`, `infra/bicep/main.parameters.json`

---

### `main.parameters.json` — Add queue private DNS zone ID mapping

**Before:**

```json
"existingBlobPrivateDnsZoneId": {
  "value": "${EXISTING_BLOB_PRIVATE_DNS_ZONE_ID=}"
},
"existingCosmosPrivateDnsZoneId": {
```

**After:**

```json
"existingBlobPrivateDnsZoneId": {
  "value": "${EXISTING_BLOB_PRIVATE_DNS_ZONE_ID=}"
},
"existingQueuePrivateDnsZoneId": {
  "value": "${EXISTING_QUEUE_PRIVATE_DNS_ZONE_ID=}"
},
"existingCosmosPrivateDnsZoneId": {
```

The `=` suffix (empty default) ensures basic mode deployments pass an empty string, which is the expected no-op value.

---

### `main.bicep` — Pass `queuePrivateDnsZoneId` to storage module

**Before:**

```bicep
blobPrivateDnsZoneId: isAILZIntegrated ? networkConfig.privateDnsZoneIds.blob : ''
publicNetworkAccess: isAILZIntegrated ? 'Disabled' : 'Enabled'
```

**After:**

```bicep
blobPrivateDnsZoneId: isAILZIntegrated ? networkConfig.privateDnsZoneIds.blob : ''
queuePrivateDnsZoneId: isAILZIntegrated ? networkConfig.privateDnsZoneIds.queue : ''
publicNetworkAccess: isAILZIntegrated ? 'Disabled' : 'Enabled'
```

Uses the same pattern as `blobPrivateDnsZoneId`: pass the DNS zone ID from `networkConfig` in AILZ mode, empty string in basic mode. The `networkConfig` variable already had the `queue` key mapped to `existingQueuePrivateDnsZoneId`.

---

### `main.bicep` — Simplify `storageQueueDnsZoneGroup` condition

**Before:**

```bicep
module storageQueueDnsZoneGroup ... = if (isAILZIntegrated && !empty(existingQueuePrivateDnsZoneId)) {
```

**After:**

```bicep
module storageQueueDnsZoneGroup ... = if (isAILZIntegrated) {
```

The `!empty()` guard was redundant because the AILZ validation block now fails the deployment if the queue DNS zone ID is missing. Simplifying the condition makes it consistent with the `storageBlobDnsZoneGroup` module, which already used `if (isAILZIntegrated)`.

---

### `main.bicep` — Add queue DNS zone validation to AILZ block

**Before:**

```bicep
acrPrivateDnsZoneRequired: !empty(existingAcrPrivateDnsZoneId) ?? fail(...)
containerAppsEnvPrivateDnsZoneRequired: !empty(existingContainerAppsEnvPrivateDnsZoneId) ?? fail(...)
} : {}
```

**After:**

```bicep
acrPrivateDnsZoneRequired: !empty(existingAcrPrivateDnsZoneId) ?? fail(...)
containerAppsEnvPrivateDnsZoneRequired: !empty(existingContainerAppsEnvPrivateDnsZoneId) ?? fail(...)
queuePrivateDnsZoneRequired: !empty(existingQueuePrivateDnsZoneId) ?? fail('existingQueuePrivateDnsZoneId is required for ailz-integrated mode')
} : {}
```

This ensures AILZ deployments fail fast with a clear error message if the queue private DNS zone ID is not provided, instead of silently deploying with a broken queue endpoint.
