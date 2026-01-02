#!/bin/bash

# ContentFlow AILZ Integration Helper Script
# This script helps you gather AILZ resource IDs and deploy ContentFlow in integrated mode
# 
# Usage: ./get-ailz-resources.sh [OPTIONS]
# Options:
#   --auto-set    Automatically set azd environment variables for retrieved resources

set -e

# Parse command line arguments
AUTO_SET_ENV=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-set)
            AUTO_SET_ENV=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./get-ailz-resources.sh [--auto-set]"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "ContentFlow AILZ Integration Helper"
echo "=========================================="
echo ""

# Function to check if Azure CLI is installed
check_az_cli() {
    if ! command -v az &> /dev/null; then
        echo "ERROR: Azure CLI is not installed."
        echo "Please install it from: https://docs.microsoft.com/cli/azure/install-azure-cli"
        exit 1
    fi
    echo "✓ Azure CLI found"
}

# Function to check if logged in
check_az_login() {
    if ! az account show &> /dev/null; then
        echo "ERROR: Not logged in to Azure CLI"
        echo "Please run: az login"
        exit 1
    fi
    echo "✓ Logged in to Azure"
}

# Function to check if azd is installed (needed for auto-set mode)
check_azd_cli() {
    if [ "$AUTO_SET_ENV" = true ]; then
        if ! command -v azd &> /dev/null; then
            echo "ERROR: Azure Developer CLI (azd) is not installed."
            echo "Please install it from: https://aka.ms/azd/install"
            exit 1
        fi
        echo "✓ Azure Developer CLI (azd) found"
    fi
}

# Main script
check_az_cli
check_az_login
check_azd_cli

# Get current subscription
CURRENT_SUB=$(az account show --query name -o tsv)
CURRENT_SUB_ID=$(az account show --query id -o tsv)
echo ""
echo "Current Subscription: $CURRENT_SUB"
echo "Subscription ID: $CURRENT_SUB_ID"
echo ""

# Ask for AILZ resource group
read -p "Enter your AI Landing Zone resource group name: " AILZ_RG

# Verify resource group exists
if ! az group show --name "$AILZ_RG" &> /dev/null; then
    echo "ERROR: Resource group '$AILZ_RG' not found"
    exit 1
fi

echo ""
echo "=========================================="
echo "Gathering AILZ Resource IDs..."
echo "=========================================="
echo ""

# Initialize output file
OUTPUT_FILE="ailz-resources.env"
> $OUTPUT_FILE

echo "# AILZ Resource IDs for ContentFlow Deployment" >> $OUTPUT_FILE
echo "# Generated on $(date)" >> $OUTPUT_FILE
echo "# AILZ Resource Group: $AILZ_RG" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# Function to get resource ID
get_resource_id() {
    local resource_type=$1
    local output_var=$2
    local query_command=$3
    
    echo -n "Searching for $resource_type..."
    
    local resource_id=$(eval "$query_command" 2>/dev/null || echo "")
    
    if [ -z "$resource_id" ]; then
        echo " NOT FOUND"
        echo "# $output_var not found" >> $OUTPUT_FILE
    else
        echo " FOUND ✓"
        echo "$output_var=\"$resource_id\"" >> $OUTPUT_FILE
        
        if [ "$AUTO_SET_ENV" = true ]; then
            azd env set "$output_var" "$resource_id" > /dev/null 2>&1
            echo "  └─ Set azd env: $output_var"
        fi
    fi
}

# Virtual Network
get_resource_id "Virtual Network" "EXISTING_VNET_RESOURCE_ID" \
    "az network vnet list --resource-group $AILZ_RG --query '[0].id' -o tsv"

# Subnet Names
echo ""
echo "Retrieving Subnet Names..."
echo ""

# Get VNet name to query subnets
VNET_NAME=$(az network vnet list --resource-group $AILZ_RG --query '[0].name' -o tsv)

if [ ! -z "$VNET_NAME" ]; then
    echo -n "Searching for Private Endpoint Subnet..."
    PE_SUBNET=$(az network vnet subnet list --resource-group $AILZ_RG --vnet-name "$VNET_NAME" --query "[?name=='pe-subnet'].name" -o tsv)
    if [ ! -z "$PE_SUBNET" ]; then
        echo " FOUND ✓"
        echo "PRIVATE_ENDPOINT_SUBNET_NAME=\"$PE_SUBNET\"" >> $OUTPUT_FILE
        if [ "$AUTO_SET_ENV" = true ]; then
            azd env set "PRIVATE_ENDPOINT_SUBNET_NAME" "$PE_SUBNET" > /dev/null 2>&1
            echo "  └─ Set azd env: PRIVATE_ENDPOINT_SUBNET_NAME"
        fi
    else
        echo " NOT FOUND"
        echo "# PRIVATE_ENDPOINT_SUBNET_NAME not found" >> $OUTPUT_FILE
    fi

    echo -n "Searching for Container Apps Environment Subnet..."
    ACA_SUBNET=$(az network vnet subnet list --resource-group $AILZ_RG --vnet-name "$VNET_NAME" --query "[?name=='aca-env-subnet'].name" -o tsv)
    if [ ! -z "$ACA_SUBNET" ]; then
        echo " FOUND ✓"
        echo "CONTAINER_APPS_SUBNET_NAME=\"$ACA_SUBNET\"" >> $OUTPUT_FILE
        if [ "$AUTO_SET_ENV" = true ]; then
            azd env set "CONTAINER_APPS_SUBNET_NAME" "$ACA_SUBNET" > /dev/null 2>&1
            echo "  └─ Set azd env: CONTAINER_APPS_SUBNET_NAME"
        fi
    else
        echo " NOT FOUND"
        echo "# CONTAINER_APPS_SUBNET_NAME not found" >> $OUTPUT_FILE
    fi
fi

echo ""

# Private DNS Zones
echo "Retrieving Required Private DNS Zones..."
echo ""

get_resource_id "Cognitive Services Private DNS Zone" "EXISTING_COGNITIVE_SERVICES_PRIVATE_DNS_ZONE_ID" \
    "az network private-dns zone show --name privatelink.cognitiveservices.azure.com --resource-group $AILZ_RG --query id -o tsv"

get_resource_id "Blob Storage Private DNS Zone" "EXISTING_BLOB_PRIVATE_DNS_ZONE_ID" \
    "az network private-dns zone show --name privatelink.blob.core.windows.net --resource-group $AILZ_RG --query id -o tsv"

get_resource_id "Cosmos DB Private DNS Zone" "EXISTING_COSMOS_PRIVATE_DNS_ZONE_ID" \
    "az network private-dns zone show --name privatelink.documents.azure.com --resource-group $AILZ_RG --query id -o tsv"

get_resource_id "App Config Private DNS Zone" "EXISTING_APP_CONFIG_PRIVATE_DNS_ZONE_ID" \
    "az network private-dns zone show --name privatelink.azconfig.io --resource-group $AILZ_RG --query id -o tsv"

get_resource_id "Container Registry Private DNS Zone" "EXISTING_ACR_PRIVATE_DNS_ZONE_ID" \
    "az network private-dns zone show --name privatelink.azurecr.io --resource-group $AILZ_RG --query id -o tsv"

get_resource_id "Container Apps Environment Private DNS Zone" "EXISTING_CONTAINER_APPS_ENV_PRIVATE_DNS_ZONE_ID" \
    "az network private-dns zone list --resource-group $AILZ_RG --query \"[?contains(name, 'containerappsenvironment')].id\" -o tsv | head -n1"

# JumpBox VM
echo ""
echo "Retrieving JumpBox VM Information..."
echo ""

echo -n "Searching for JumpBox VM..."
JUMPBOX_VM=$(az vm list --resource-group $AILZ_RG --query "[?tags.role=='jumpbox' || name | contains(@, 'jmp')].{id:id, name:name, rg:resourceGroup}" -o tsv | head -n1)
if [ ! -z "$JUMPBOX_VM" ]; then
    JUMPBOX_ID=$(echo "$JUMPBOX_VM" | awk '{print $1}')
    JUMPBOX_NAME=$(echo "$JUMPBOX_VM" | awk '{print $2}')
    echo " FOUND ✓"
    echo "JUMPBOX_VM_RESOURCE_ID=\"$JUMPBOX_ID\"" >> $OUTPUT_FILE
    echo "JUMPBOX_VM_NAME=\"$JUMPBOX_NAME\"" >> $OUTPUT_FILE
    if [ "$AUTO_SET_ENV" = true ]; then
        azd env set "JUMPBOX_VM_RESOURCE_ID" "$JUMPBOX_ID" > /dev/null 2>&1
        azd env set "JUMPBOX_VM_NAME" "$JUMPBOX_NAME" > /dev/null 2>&1
        echo "  └─ Set azd env: JUMPBOX_VM_RESOURCE_ID"
        echo "  └─ Set azd env: JUMPBOX_VM_NAME"
    fi
else
    echo " NOT FOUND"
    echo "# JUMPBOX_VM_RESOURCE_ID not found - no JumpBox VM deployed" >> $OUTPUT_FILE
    echo "# JUMPBOX_VM_NAME not found - no JumpBox VM deployed" >> $OUTPUT_FILE
fi

# Optional resources
echo ""
echo "=========================================="
echo "Retrieving Optional AILZ Resources..."
echo "=========================================="
echo ""

get_resource_id "Key Vault Private DNS Zone" "EXISTING_KEY_VAULT_PRIVATE_DNS_ZONE_ID" \
    "az network private-dns zone show --name privatelink.vaultcore.azure.net --resource-group $AILZ_RG --query id -o tsv"

get_resource_id "Log Analytics Workspace" "EXISTING_LOG_ANALYTICS_WORKSPACE_ID" \
    "az monitor log-analytics workspace list --resource-group $AILZ_RG --query '[0].id' -o tsv"

get_resource_id "Application Insights" "EXISTING_APP_INSIGHTS_ID" \
    "az monitor app-insights component list --resource-group $AILZ_RG --query '[0].id' -o tsv"

echo ""
echo "=========================================="
echo "Resource IDs saved to: $OUTPUT_FILE"
echo "=========================================="
echo ""

if [ "$AUTO_SET_ENV" = true ]; then
    echo "✓ All resource IDs have been automatically set in azd environment"
    echo ""
    echo "You can now deploy ContentFlow directly:"
    echo ""
    echo "azd deploy"
else
    echo "You can now use these resource IDs to deploy ContentFlow:"
    echo ""
    echo "Option 1: Manually set each variable:"
    echo "  source $OUTPUT_FILE"
    echo "  azd env set EXISTING_VNET_RESOURCE_ID \"\$EXISTING_VNET_RESOURCE_ID\""
    echo "  azd env set EXISTING_BLOB_PRIVATE_DNS_ZONE_ID \"\$EXISTING_BLOB_PRIVATE_DNS_ZONE_ID\""
    echo "  # ... (set all required variables)"
    echo ""
    echo "Option 2: Re-run with --auto-set flag:"
    echo "  ./get-ailz-resources.sh --auto-set"
    echo ""
    echo "Then deploy with:"
    echo "  azd deploy"
fi

echo ""
