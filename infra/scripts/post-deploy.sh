#!/bin/bash
# Post-deploy hook - runs after all services are deployed
# Displays endpoints and locks down resources opened during provisioning
set -e

echo "=================================================="
echo "ContentFlow - Post-Deploy Hook"
echo "=================================================="

# Get deployment outputs
API_ENDPOINT=$(azd env get-value API_ENDPOINT 2>/dev/null || echo "Not available")
WEB_ENDPOINT=$(azd env get-value WEB_ENDPOINT 2>/dev/null || echo "Not available")
# WORKER DISABLED: WORKER_ENDPOINT=$(azd env get-value WORKER_ENDPOINT 2>/dev/null || echo "Not available")

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║     ContentFlow Deployment Complete! 🚀        ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "Service Endpoints:"
echo "  API:    $API_ENDPOINT"
echo "  Web:    $WEB_ENDPOINT"
# WORKER DISABLED: echo "  Worker: $WORKER_ENDPOINT"
echo ""

# ========== SECURITY HARDENING (AILZ mode only) ==========
DEPLOYMENT_MODE=$(azd env get-value DEPLOYMENT_MODE 2>/dev/null || echo "basic")
RESOURCE_GROUP=$(azd env get-value AZURE_RESOURCE_GROUP 2>/dev/null || echo "")
ACR_NAME=$(azd env get-value AZURE_CONTAINER_REGISTRY_NAME 2>/dev/null || echo "")

if [ "$DEPLOYMENT_MODE" = "ailz-integrated" ]; then
    echo "=================================================="
    echo "Security Hardening (AILZ mode)"
    echo "=================================================="

    if [ -z "$RESOURCE_GROUP" ]; then
        RESOURCE_GROUP=$(az group list --query "[?tags.\"azd-env-name\"=='$(azd env get-value AZURE_ENV_NAME 2>/dev/null)'].name | [0]" -o tsv 2>/dev/null || echo "")
    fi

    # --- P-1: Disable App Config public access ---
    echo ""
    echo "[P-1] Disabling App Config public network access..."
    APPCONFIG_NAME=$(az resource list --resource-group "$RESOURCE_GROUP" \
        --resource-type "Microsoft.AppConfiguration/configurationStores" \
        --query "[?tags.application=='contentflow'].name | [0]" -o tsv 2>/dev/null || echo "")
    if [ -n "$APPCONFIG_NAME" ]; then
        az appconfig update --name "$APPCONFIG_NAME" --resource-group "$RESOURCE_GROUP" \
            --enable-public-network false --only-show-errors 2>/dev/null \
            && echo "  ✅ App Config '$APPCONFIG_NAME' — public access disabled" \
            || echo "  ⚠️  Could not disable App Config public access"
    else
        echo "  ⚠️  App Config not found — skipping"
    fi

    # --- P-2: ACR stays private (no action needed) ---
    echo "[P-2] ACR public access — already Disabled at provisioning (ZTA compliant, no action needed)"

    # --- P-3: Verify private DNS A records ---
    echo "[P-3] Verifying private DNS zone A records..."
    for ZONE in "privatelink.azurecr.io" "privatelink.blob.core.windows.net" "privatelink.documents.azure.com" "privatelink.azconfig.io"; do
        COUNT=$(az network private-dns record-set a list --zone-name "$ZONE" \
            --resource-group "$RESOURCE_GROUP" --query "length([])" -o tsv 2>/dev/null || echo "0")
        if [ "$COUNT" -gt 0 ] 2>/dev/null; then
            echo "  ✅ $ZONE — $COUNT A record(s)"
        else
            echo "  ⚠️  $ZONE — no A records (check PE DNS zone groups)"
        fi
    done

    # --- P-4: Queue DNS zone ---
    echo "[P-4] Checking Queue DNS zone..."
    az network private-dns zone show --name "privatelink.queue.core.windows.net" \
        --resource-group "$RESOURCE_GROUP" -o none 2>/dev/null \
        && echo "  ✅ Queue DNS zone exists" \
        || echo "  ℹ️  No queue DNS zone — queue PE uses public resolution"

    echo ""
    echo "=================================================="
    echo "Hardening complete. Remaining manual actions:"
    echo "  P-5:  Restrict CORS origins to: $WEB_ENDPOINT"
    echo "  P-6:  Add API authentication (OAuth/JWT middleware)"
    echo "  P-7:  Disable App Config local auth"
    echo "  P-8:  Remove storage account Contributor role"
    echo "  P-9:  Add diagnostic settings to all resources"
    echo "=================================================="
fi

echo ""
echo "Next Steps:"
echo "  1. Access the web UI at: $WEB_ENDPOINT"
echo "  2. View API docs at: $API_ENDPOINT/docs"
echo "  3. Check logs: azd monitor --logs"
echo ""
echo "=================================================="
