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

# Import placeholder image to ACR in AILZ mode (enables Container Apps provisioning without internet egress)
if [ "$DEPLOYMENT_MODE" = "ailz-integrated" ]; then
  echo "✓ Importing placeholder image to ACR (AILZ mode - no internet egress)..."
  echo "  Source: mcr.microsoft.com/k8se/quickstart:latest"
  echo "  Target: $ACR_NAME/placeholder:latest"
  
  az acr import \
    --name "$ACR_NAME" \
    --source mcr.microsoft.com/k8se/quickstart:latest \
    --image placeholder:latest \
    --only-show-errors || {
      echo "⚠ Warning: Failed to import placeholder image to ACR."
      echo "  This is not critical if the image is cached by Container Apps platform."
      echo "  If Container Apps fail to provision, you can manually import:"
      echo "  az acr import --name $ACR_NAME --source mcr.microsoft.com/k8se/quickstart:latest --image placeholder:latest"
    }
  
  echo "✓ Placeholder image imported successfully"
else
  echo "⊘ Skipping ACR import (basic mode - internet egress available)"
fi

echo "=================================================="
echo "✓ Post-provision completed successfully"
echo "=================================================="
