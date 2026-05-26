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

echo "Resource Group: $RESOURCE_GROUP"
echo "Storage Account: $STORAGE_ACCOUNT"
echo "Cosmos DB Endpoint: $COSMOS_ENDPOINT"

# --- WORKER DISABLED: uncomment to re-enable queue creation ---
# echo "✓ Creating storage queue (if not exists)..."
# QUEUE_NAME="contentflow-execution-requests"
# az storage queue create \
#   --name "$QUEUE_NAME" \
#   --account-name "$STORAGE_ACCOUNT" \
#   --auth-mode login \
#   --only-show-errors || echo "Queue already exists or error creating queue"
# --- END WORKER DISABLED ---

# ========== DEPLOYER ROLE ASSIGNMENT ==========
echo ""
echo "=================================================="
echo "Deployer Role - Cognitive Services Contributor"
echo "=================================================="

AI_SERVICES_NAME=$(azd env get-value AI_SERVICES_NAME 2>/dev/null || echo "")
DEPLOYER_OID=$(az ad signed-in-user show --query id -o tsv 2>/dev/null || echo "")

if [ -n "$DEPLOYER_OID" ] && [ -n "$AI_SERVICES_NAME" ]; then
    echo "Ensuring deployer ($DEPLOYER_OID) has Cognitive Services Contributor on $AI_SERVICES_NAME..."
    az role assignment create \
        --assignee "$DEPLOYER_OID" \
        --role "Cognitive Services Contributor" \
        --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${AI_SERVICES_NAME}" \
        --only-show-errors 2>/dev/null \
        && echo "  ✅ Deployer has Cognitive Services Contributor" \
        || echo "  ⚠️  Could not assign role (may need Owner/UAA permissions on the scope)"
else
    echo "⚠️  Could not determine deployer identity or AI Services name. Skipping role assignment."
fi

# ========== CONTENT UNDERSTANDING SETUP ==========
echo ""
echo "=================================================="
echo "Content Understanding - Model Defaults & Analyzers"
echo "=================================================="

# AI_SERVICES_NAME already resolved above

if [ -z "$AI_SERVICES_NAME" ]; then
    echo "⚠️  AI_SERVICES_NAME not found in azd env. Skipping CU setup."
    echo "   Set AI_SERVICES_NAME manually and re-run if needed."
else
    # Construct CU endpoint from AI Services account name
    CU_ENDPOINT="https://${AI_SERVICES_NAME}.services.ai.azure.com"
    CU_API_VERSION="2025-11-01"
    echo "CU Endpoint: $CU_ENDPOINT"

    # Obtain a bearer token for Cognitive Services scope
    echo "Acquiring access token..."
    ACCESS_TOKEN=$(az account get-access-token \
        --resource "https://cognitiveservices.azure.com" \
        --query accessToken -o tsv 2>/dev/null || echo "")

    if [ -z "$ACCESS_TOKEN" ]; then
        echo "⚠️  Failed to acquire access token. Skipping CU setup."
        echo "   Ensure the deployer identity has 'Cognitive Services User' role."
    else
        # --- Step 1: Set default model deployments ---
        echo ""
        echo "[CU-1] Setting default model deployments..."
        CU_DEFAULTS_RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH \
            "${CU_ENDPOINT}/contentunderstanding/defaults?api-version=${CU_API_VERSION}" \
            -H "Authorization: Bearer ${ACCESS_TOKEN}" \
            -H "Content-Type: application/merge-patch+json" \
            -d '{
                "modelDeployments": {
                    "gpt-4.1": "gpt-4.1",
                    "gpt-4.1-mini": "gpt-4.1-mini",
                    "text-embedding-3-large": "text-embedding-3-large"
                }
            }' 2>/dev/null)

        CU_DEFAULTS_HTTP_CODE=$(echo "$CU_DEFAULTS_RESPONSE" | tail -1)
        CU_DEFAULTS_BODY=$(echo "$CU_DEFAULTS_RESPONSE" | sed '$d')

        if [ "$CU_DEFAULTS_HTTP_CODE" -ge 200 ] 2>/dev/null && [ "$CU_DEFAULTS_HTTP_CODE" -lt 300 ] 2>/dev/null; then
            echo "  ✅ Default model deployments configured successfully"
        else
            echo "  ⚠️  Failed to set CU defaults (HTTP $CU_DEFAULTS_HTTP_CODE)"
            echo "     Response: $CU_DEFAULTS_BODY"
            echo "     Model deployments may not be available yet. Run post-provision again after models are ready."
        fi

        # --- Step 2: Create/update custom analyzers from seed folder ---
        echo ""
        echo "[CU-2] Creating custom analyzers from seed definitions..."

        SEED_DIR="$(cd "$(dirname "$0")/../.." && pwd)/contentflow-api/seed/analyzers"

        if [ ! -d "$SEED_DIR" ]; then
            echo "  ℹ️  No seed/analyzers folder found at: $SEED_DIR"
            echo "     Skipping custom analyzer creation."
        else
            ANALYZER_COUNT=0
            ANALYZER_SUCCESS=0
            ANALYZER_FAILED=0

            for ANALYZER_FILE in "$SEED_DIR"/*.json; do
                # Skip if no JSON files exist (glob returns literal pattern)
                [ -e "$ANALYZER_FILE" ] || continue

                ANALYZER_COUNT=$((ANALYZER_COUNT + 1))
                # Derive analyzer ID from filename (e.g., details_extractor_documents_new1.json -> details_extractor_documents_new1)
                ANALYZER_ID=$(basename "$ANALYZER_FILE" .json)

                echo "  Creating analyzer: $ANALYZER_ID ..."

                # PUT is create-or-replace (idempotent)
                ANALYZER_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT \
                    "${CU_ENDPOINT}/contentunderstanding/analyzers/${ANALYZER_ID}?api-version=${CU_API_VERSION}" \
                    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
                    -H "Content-Type: application/json" \
                    -d @"$ANALYZER_FILE" 2>/dev/null)

                ANALYZER_HTTP_CODE=$(echo "$ANALYZER_RESPONSE" | tail -1)
                ANALYZER_BODY=$(echo "$ANALYZER_RESPONSE" | sed '$d')

                if [ "$ANALYZER_HTTP_CODE" -ge 200 ] 2>/dev/null && [ "$ANALYZER_HTTP_CODE" -lt 300 ] 2>/dev/null; then
                    echo "    ✅ $ANALYZER_ID — created/updated (HTTP $ANALYZER_HTTP_CODE)"
                    ANALYZER_SUCCESS=$((ANALYZER_SUCCESS + 1))
                else
                    echo "    ❌ $ANALYZER_ID — failed (HTTP $ANALYZER_HTTP_CODE)"
                    echo "       Response: $ANALYZER_BODY"
                    ANALYZER_FAILED=$((ANALYZER_FAILED + 1))
                fi
            done

            if [ "$ANALYZER_COUNT" -eq 0 ]; then
                echo "  ℹ️  No analyzer JSON files found in seed/analyzers/"
            else
                echo ""
                echo "  Analyzers processed: $ANALYZER_COUNT (✅ $ANALYZER_SUCCESS succeeded, ❌ $ANALYZER_FAILED failed)"
            fi
        fi
    fi
fi

echo ""
echo "=================================================="
echo "✓ Post-provision completed successfully"
echo "=================================================="
