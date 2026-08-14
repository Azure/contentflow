# SARSP Frontend-Only Deployment

Use this path when you do not want to run `azd up` or change the existing ContentFlow API, worker, storage, queue, or Cosmos resources.

## What This Deploys

Only the SARSP Case Assistant web frontend.

It must call an existing ContentFlow API endpoint that already exposes the SARSP routes:

- `POST /api/sarsp/cases/{case_id}/validate`
- `GET /api/sarsp/cases/{case_id}/executions/{execution_id}`

## Required Value

Get the existing API base URL from the current ContentFlow deployment owner:

```text
https://<existing-api-fqdn>/api/
```

## Build Static Files

From `contentflow-web`:

```powershell
$env:VITE_API_BASE_URL="https://<existing-api-fqdn>/api/"
npm run build
```

The deployable static files are in:

```text
contentflow-web/dist
```

## Runtime API URL Override

The app also reads `/env-config.js` at runtime. After build, update this file in the deployed static site if the API URL changes:

```javascript
window.__CONTENTFLOW_CONFIG__ = {
  apiBaseUrl: "https://<existing-api-fqdn>/api/"
};
```

This lets you retarget the frontend without rebuilding the JavaScript bundle.

## Static Hosting Options

Preferred low-risk options:

1. Azure Static Web Apps
2. Azure App Service static content
3. Storage static website behind approved customer networking
4. A new frontend-only Container App

Do not run `azd up` for this option.

## Frontend-Only Container App Option

If someone with Azure permissions provides an existing ACR and Container Apps Environment, build and deploy only the web image.

Build image from repo root:

```powershell
docker build -f contentflow-web/Dockerfile -t <acr-login-server>/sarsp-case-assistant-web:latest .
docker push <acr-login-server>/sarsp-case-assistant-web:latest
```

Create a new Container App named something like `sarsp-case-assistant-web` and set:

```text
VITE_API_BASE_URL=https://<existing-api-fqdn>/api/
```

This creates a new frontend app only and does not update the existing ContentFlow API or worker.

## Smoke Test

1. Open deployed frontend URL.
2. Submit Case ID `100395`.
3. Confirm the browser calls the existing API URL.
4. Confirm status progresses and `results.json` is available after completion.

## Required API CORS

The existing API must allow the new frontend origin in CORS. If CORS blocks the browser call, ask the API owner to add the frontend URL to allowed origins.
