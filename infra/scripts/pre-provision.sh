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

echo "✓ Checking Docker daemon..."
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running or current user cannot connect to it."
    echo "   For Linux: ensure dockerd is running and your user is in the 'docker' group."
    echo "   Run: sudo usermod -aG docker \$USER  (then log out and back in)"
    exit 1
fi

echo "✓ Verifying Azure CLI login..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure CLI. Please run 'az login' first."
    exit 1
fi

echo "=================================================="
echo "✓ Pre-provision checks completed successfully"
echo "=================================================="
