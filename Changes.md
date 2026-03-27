# Deployment Fixes – `azd deploy` in `ailz-integrated` mode

## Table of Contents

- [1. Fix: `remoteBuild: true` Incompatible with Private ACR](#1-fix-remotebuild-true-incompatible-with-private-acr)

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
