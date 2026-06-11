#!/bin/bash
# Pre-provision hook - runs before infrastructure is provisioned
set -e

echo "=================================================="
echo "ContentFlow - Pre-Provision Hook"
echo "=================================================="

echo "✓ Checking Azure CLI installation..."
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

echo "✓ Checking azd installation..."
if ! command -v azd &> /dev/null; then
    echo "❌ Azure Developer CLI (azd) is not installed. Please install it first."
    exit 1
fi

echo "✓ Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install it first."
    exit 1
fi

echo "✓ Verifying Azure CLI login..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure CLI. Please run 'az login' first."
    exit 1
fi

# Note: ACR placeholder image import is NOT done here.
# In AILZ mode, ACR is fully private (publicNetworkAccess=Disabled).
# Use 'az acr build' (ACR Tasks) during 'azd deploy' to build and push images
# inside the ACR without requiring public access.
echo "✓ ACR image build will be handled by ACR Tasks during deployment phase."

echo "=================================================="
echo "✓ Pre-provision checks completed successfully"
echo "=================================================="
