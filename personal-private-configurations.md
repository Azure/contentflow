# Personal Private Configurations

> **WARNING**: This file contains environment-specific configurations. Do NOT commit to a shared/public repository.

---

## Variables

Update these values to reuse all scripts below in any environment.

```bash
# ── Environment ──
RESOURCE_GROUP="rg-contentflow-test-001"
SUBSCRIPTION_ID="d12d19a9-0636-4951-90a4-339158fd57d8"

# ── Container App names ──
APP_API="api-vtkhgrhgdl4w2"
APP_WEB="web-vtkhgrhgdl4w2"
APP_WORKER="worker-vtkhgrhgdl4w2"
APPS=("$APP_API" "$APP_WEB" "$APP_WORKER")

# ── Networking ──
MY_IP=$(curl -s ifconfig.me)
RULE_NAME="allow-my-ip"

# ── Endpoints ──
API_URL="https://api-vtkhgrhgdl4w2.politeflower-3403e279.eastus2.azurecontainerapps.io"
WEB_URL="https://web-vtkhgrhgdl4w2.politeflower-3403e279.eastus2.azurecontainerapps.io"
WORKER_URL="https://worker-vtkhgrhgdl4w2.politeflower-3403e279.eastus2.azurecontainerapps.io"
```

---

## IP Access Restrictions on Azure Container Apps

**Date Applied**: March 16, 2026  
**Resource Group**: `rg-contentflow-test-001`  
**Subscription**: `ME-MngEnvMCAP887462-gereyeso-1` (`d12d19a9-0636-4951-90a4-339158fd57d8`)  
**Region**: East US 2

### What was configured

All three Container Apps were restricted to accept external ingress traffic **only** from a single IP address. Any request from a different IP receives a `403 Forbidden` response.

| Container App | Allowed IP | Rule Name |
|---------------|-----------|-----------|
| `api-vtkhgrhgdl4w2` | `57.135.198.22/32` | `allow-my-ip` |
| `web-vtkhgrhgdl4w2` | `57.135.198.22/32` | `allow-my-ip` |
| `worker-vtkhgrhgdl4w2` | `57.135.198.22/32` | `allow-my-ip` |

### Service Endpoints (restricted)

| Service | URL |
|---------|-----|
| Web UI | `$WEB_URL` |
| API | `$API_URL` |
| API Docs | `$API_URL/docs` |
| Worker | `$WORKER_URL` |

### Why this is safe for internal communication

Container Apps within the **same Container Apps Environment** communicate through the internal network. IP access restrictions apply only to **external** ingress traffic (from the internet). The service-to-service flow remains unaffected:

```
Browser (your IP) → Web UI → (browser fetches from) → API → (internal) → Worker
```

- **Web → API**: The React SPA runs in your browser, so API calls originate from your IP.
- **API → Worker**: Both are in the same Container Apps Environment; internal traffic bypasses IP restrictions.

---

### Apply IP restriction to all apps

```bash
for app in "${APPS[@]}"; do
  echo "Restricting $app to $MY_IP ..."
  az containerapp ingress access-restriction set \
    -n "$app" \
    -g "$RESOURCE_GROUP" \
    --rule-name "$RULE_NAME" \
    --ip-address "$MY_IP/32" \
    --action Allow \
    --description "Allow only my IP"
done
```

### Update IP on all apps (when your IP changes)

```bash
MY_IP=$(curl -s ifconfig.me)
echo "New IP: $MY_IP"

for app in "${APPS[@]}"; do
  echo "Updating $app ..."
  az containerapp ingress access-restriction remove \
    -n "$app" \
    -g "$RESOURCE_GROUP" \
    --rule-name "$RULE_NAME"

  az containerapp ingress access-restriction set \
    -n "$app" \
    -g "$RESOURCE_GROUP" \
    --rule-name "$RULE_NAME" \
    --ip-address "$MY_IP/32" \
    --action Allow \
    --description "Allow only my IP"
done
```

### Remove all restrictions (make public again)

```bash
for app in "${APPS[@]}"; do
  echo "Removing restriction from $app ..."
  az containerapp ingress access-restriction remove \
    -n "$app" \
    -g "$RESOURCE_GROUP" \
    --rule-name "$RULE_NAME"
done
```

### Verify current restrictions

```bash
for app in "${APPS[@]}"; do
  echo "=== $app ==="
  az containerapp ingress access-restriction list \
    -n "$app" \
    -g "$RESOURCE_GROUP" \
    --output table
done
```

### Quick health check

```bash
for url in "$API_URL/health" "$WEB_URL" "$WORKER_URL"; do
  echo "$url → $(curl -s -o /dev/null -w '%{http_code}' "$url")"
done
```
