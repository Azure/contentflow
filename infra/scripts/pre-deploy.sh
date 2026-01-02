#!/bin/bash
# Pre-deploy hook - runs before deploying all services
set -e

echo "=================================================="
echo "ContentFlow - Pre-Deploy Hook"
echo "=================================================="

echo "✓ Pre-deployment checks..."

# Verify that infrastructure has been provisioned
if ! azd env get-value AZURE_RESOURCE_GROUP &> /dev/null; then
    echo "❌ Infrastructure not provisioned. Please run 'azd provision' first."
    exit 1
fi

echo "✓ Infrastructure is ready for deployment"

echo "=================================================="
echo "✓ Pre-deploy checks completed successfully"
echo "=================================================="
