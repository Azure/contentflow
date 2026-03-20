#!/bin/bash
# Post-provision hook - runs after infrastructure is provisioned
set -e

echo "=================================================="
echo "ContentFlow - Post-Provision Hook"
echo "=================================================="

echo "✓ Infrastructure provisioned successfully!"

# Get the outputs from azd
RESOURCE_GROUP=$(azd env get-value AZURE_RESOURCE_GROUP)
STORAGE_ACCOUNT=$(azd env get-value STORAGE_ACCOUNT_NAME)
COSMOS_ENDPOINT=$(azd env get-value COSMOS_DB_ENDPOINT)
DEPLOYMENT_MODE=$(azd env get-value DEPLOYMENT_MODE)
ACR_NAME=$(azd env get-value AZURE_CONTAINER_REGISTRY_NAME)

echo "Resource Group: $RESOURCE_GROUP"
echo "Storage Account: $STORAGE_ACCOUNT"
echo "Cosmos DB Endpoint: $COSMOS_ENDPOINT"
echo "Deployment Mode: $DEPLOYMENT_MODE"
echo "Container Registry: $ACR_NAME"

echo "✓ Creating storage queue (if not exists)..."
QUEUE_NAME="contentflow-execution-requests"
az storage queue create \
  --name "$QUEUE_NAME" \
  --account-name "$STORAGE_ACCOUNT" \
  --auth-mode login \
  --only-show-errors || echo "Queue already exists or error creating queue"

# Create App Configuration keys in AILZ mode
# Why: ARM deployment service cannot access App Config with publicNetworkAccess: 'Disabled'
# Solution: Jumpbox (inside VNet) has access via private endpoint
if [ "$DEPLOYMENT_MODE" = "ailz-integrated" ]; then
  echo ""
  echo "✓ Creating App Configuration keys (AILZ mode - via jumpbox with VNet access)..."
  
  APP_CONFIG_NAME=$(azd env get-value APP_CONFIG_NAME)
  COSMOS_DB_NAME=$(azd env get-value COSMOS_DB_NAME)
  STORAGE_CONTAINER_NAME="docs"
  WORKER_FQDN=$(azd env get-value WORKER_ENDPOINT | sed 's|https://||')
  QUEUE_URL=$(azd env get-value STORAGE_QUEUE_URL)
  QUEUE_NAME=$(azd env get-value STORAGE_QUEUE_NAME)
  
  echo "  App Config Store: $APP_CONFIG_NAME"
  echo "  Creating 30 keys..."
  
  # Create keys using Azure CLI (accesses via private endpoint)
  # Common keys
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.common.COSMOS_DB_ENDPOINT" --value "$COSMOS_ENDPOINT" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.common.COSMOS_DB_NAME" --value "$COSMOS_DB_NAME" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.common.BLOB_STORAGE_ACCOUNT_NAME" --value "$STORAGE_ACCOUNT" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.common.BLOB_STORAGE_CONTAINER_NAME" --value "$STORAGE_CONTAINER_NAME" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.common.STORAGE_ACCOUNT_WORKER_QUEUE_URL" --value "$QUEUE_URL" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.common.STORAGE_WORKER_QUEUE_NAME" --value "$QUEUE_NAME" --auth-mode login --yes --only-show-errors
  
  # API keys
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.api.API_ENABLED" --value "True" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.api.DEBUG" --value "False" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.api.LOG_LEVEL" --value "DEBUG" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.api.API_SERVER_HOST" --value "0.0.0.0" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.api.API_SERVER_PORT" --value "8090" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.api.API_SERVER_WORKERS" --value "1" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.api.CORS_ALLOW_CREDENTIALS" --value "true" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.api.CORS_ALLOW_ORIGINS" --value "*" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.api.WORKER_ENGINE_API_ENDPOINT" --value "https://$WORKER_FQDN" --auth-mode login --yes --only-show-errors
  
  # Worker keys
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.NUM_PROCESSING_WORKERS" --value "4" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.NUM_SOURCE_WORKERS" --value "2" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.LOG_LEVEL" --value "INFO" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.DEBUG" --value "false" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.API_ENABLED" --value "true" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.API_HOST" --value "0.0.0.0" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.API_PORT" --value "8099" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.QUEUE_POLL_INTERVAL_SECONDS" --value "5" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.QUEUE_VISIBILITY_TIMEOUT_SECONDS" --value "300" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.QUEUE_MAX_MESSAGES" --value "32" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.MAX_TASK_RETRIES" --value "3" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.TASK_TIMEOUT_SECONDS" --value "600" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.DEFAULT_POLLING_INTERVAL_SECONDS" --value "60" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.SCHEDULER_SLEEP_INTERVAL_SECONDS" --value "5" --auth-mode login --yes --only-show-errors
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "contentflow.worker.LOCK_TTL_SECONDS" --value "300" --auth-mode login --yes --only-show-errors
  
  # Sentinel key (marks completion)
  az appconfig kv set --name "$APP_CONFIG_NAME" --key "sentinel" --value "1" --auth-mode login --yes --only-show-errors
  
  echo "  ✓ Successfully created all 30 App Configuration keys"
  
  # Verify keys were created
  KEY_COUNT=$(az appconfig kv list --name "$APP_CONFIG_NAME" --auth-mode login --query "length([])" -o tsv 2>/dev/null || echo "0")
  echo "  ✓ Verification: $KEY_COUNT keys found in App Config Store"
  
  if [ "$KEY_COUNT" -lt "30" ]; then
    echo "  ⚠ Warning: Expected 30 keys, found $KEY_COUNT"
    echo "  Some keys may not have been created successfully. Check Azure Portal."
  fi
else
  echo ""
  echo "⊘ Skipping App Config keys creation (basic mode - keys created via Bicep)"
fi

echo ""
echo "=================================================="
echo "✓ Post-provision completed successfully"
echo "=================================================="
