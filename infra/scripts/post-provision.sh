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
echo "Deployer Role - Cognitive Services Contributor & Azure AI Developer"
echo "=================================================="

AI_SERVICES_NAME=$(azd env get-value AI_SERVICES_NAME 2>/dev/null || echo "")
DEPLOYER_OID=$(az ad signed-in-user show --query id -o tsv 2>/dev/null || echo "")

if [ -n "$DEPLOYER_OID" ] && [ -n "$AI_SERVICES_NAME" ]; then
    AI_SERVICES_SCOPE="/subscriptions/$(az account show --query id -o tsv)/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${AI_SERVICES_NAME}"

    echo "Ensuring deployer ($DEPLOYER_OID) has Cognitive Services Contributor on $AI_SERVICES_NAME..."
    ROLE_OUT=$(az role assignment create \
        --assignee-object-id "$DEPLOYER_OID" \
        --assignee-principal-type User \
        --role "Cognitive Services Contributor" \
        --scope "$AI_SERVICES_SCOPE" \
        --only-show-errors 2>&1) && \
        echo "  ✅ Deployer has Cognitive Services Contributor" || \
        { echo "$ROLE_OUT" | grep -qi "RoleAssignmentExists" && \
            echo "  ✅ Deployer already has Cognitive Services Contributor" || \
            echo "  ⚠️  Could not assign Cognitive Services Contributor (may need Owner/UAA permissions on the scope)"; }

    # Azure AI Developer is the DATA-PLANE write role required for:
    #   - Setting CU defaults (PATCH /contentunderstanding/defaults)
    #   - Creating/updating analyzers (PUT /contentunderstanding/analyzers/{id})
    #   - Accessing CU Studio (superset of Azure AI User — covers read access too)
    # Azure AI User (read-only) is NOT sufficient; it causes 401 on any write operation.
    echo "Ensuring deployer ($DEPLOYER_OID) has Azure AI Developer on $AI_SERVICES_NAME..."
    ROLE_OUT=$(az role assignment create \
        --assignee-object-id "$DEPLOYER_OID" \
        --assignee-principal-type User \
        --role "Azure AI Developer" \
        --scope "$AI_SERVICES_SCOPE" \
        --only-show-errors 2>&1) && \
        echo "  ✅ Deployer has Azure AI Developer (data-plane read+write — required for CU setup & Studio)" || \
        { echo "$ROLE_OUT" | grep -qi "RoleAssignmentExists" && \
            echo "  ✅ Deployer already has Azure AI Developer" || \
            echo "  ⚠️  Could not assign Azure AI Developer (may need Owner/UAA permissions on the scope)"; }
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

    # --- Helper: acquire a bearer token for Cognitive Services scope ---
    acquire_token() {
        az account get-access-token \
            --resource "https://cognitiveservices.azure.com" \
            --query accessToken -o tsv 2>/dev/null || echo ""
    }

    # --- RBAC Readiness Probe ---
    # Instead of a fixed sleep, poll the CU data-plane until RBAC propagates.
    # Retries every 30s for up to 30 minutes (60 attempts).
    echo "Probing CU data-plane for RBAC readiness (up to 30 minutes)..."
    RBAC_MAX_ATTEMPTS=60
    RBAC_WAIT_SECONDS=30
    RBAC_READY=false
    ACCESS_TOKEN=""

    for RBAC_ATTEMPT in $(seq 1 $RBAC_MAX_ATTEMPTS); do
        ACCESS_TOKEN=$(acquire_token)
        if [ -z "$ACCESS_TOKEN" ]; then
            echo "  [attempt $RBAC_ATTEMPT/$RBAC_MAX_ATTEMPTS] Failed to acquire token — retrying in ${RBAC_WAIT_SECONDS}s..."
            sleep "$RBAC_WAIT_SECONDS"
            continue
        fi

        PROBE_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            "${CU_ENDPOINT}/contentunderstanding/analyzers?api-version=${CU_API_VERSION}" \
            -H "Authorization: Bearer ${ACCESS_TOKEN}" 2>/dev/null)

        if [ "$PROBE_HTTP_CODE" -ge 200 ] 2>/dev/null && [ "$PROBE_HTTP_CODE" -lt 300 ] 2>/dev/null; then
            echo "  ✅ RBAC is active (HTTP $PROBE_HTTP_CODE on attempt $RBAC_ATTEMPT)"
            RBAC_READY=true
            break
        else
            echo "  [attempt $RBAC_ATTEMPT/$RBAC_MAX_ATTEMPTS] RBAC not ready (HTTP $PROBE_HTTP_CODE) — retrying in ${RBAC_WAIT_SECONDS}s..."
            sleep "$RBAC_WAIT_SECONDS"
        fi
    done

    if [ "$RBAC_READY" != "true" ]; then
        echo "❌ RBAC did not propagate within $((RBAC_MAX_ATTEMPTS * RBAC_WAIT_SECONDS)) seconds."
        echo "   Re-run 'azd up' or 'azd hooks run postprovision' after a few minutes."
        exit 1
    else
        # --- Step 1: Set default model deployments (with retry) ---
        echo ""
        echo "[CU-1] Setting default model deployments..."
        DEFAULTS_MAX_RETRIES=5
        DEFAULTS_BACKOFF=15
        DEFAULTS_OK=false

        for DEFAULTS_ATTEMPT in $(seq 1 $DEFAULTS_MAX_RETRIES); do
            # Refresh token before each attempt (handles expiry edge case)
            if [ "$DEFAULTS_ATTEMPT" -gt 1 ]; then
                ACCESS_TOKEN=$(acquire_token)
            fi

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
                echo "  ✅ Default model deployments configured successfully (attempt $DEFAULTS_ATTEMPT)"
                DEFAULTS_OK=true
                break
            fi

            # Retry on transient errors (401, 403, 429, 5xx)
            case "$CU_DEFAULTS_HTTP_CODE" in
                401|403|429|500|502|503|504)
                    echo "  [attempt $DEFAULTS_ATTEMPT/$DEFAULTS_MAX_RETRIES] CU defaults failed (HTTP $CU_DEFAULTS_HTTP_CODE) — retrying in ${DEFAULTS_BACKOFF}s..."
                    sleep "$DEFAULTS_BACKOFF"
                    DEFAULTS_BACKOFF=$((DEFAULTS_BACKOFF * 2))
                    [ "$DEFAULTS_BACKOFF" -gt 120 ] && DEFAULTS_BACKOFF=120
                    ;;
                *)
                    echo "  ⚠️  CU defaults failed with non-retryable error (HTTP $CU_DEFAULTS_HTTP_CODE)"
                    echo "     Response: $CU_DEFAULTS_BODY"
                    break
                    ;;
            esac
        done

        if [ "$DEFAULTS_OK" != "true" ]; then
            echo "  ⚠️  Failed to set CU defaults after $DEFAULTS_MAX_RETRIES attempts."
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

                # PUT is create-or-replace (idempotent) — retry with exponential backoff
                PUT_MAX_RETRIES=5
                PUT_BACKOFF=15
                PUT_OK=false

                for PUT_ATTEMPT in $(seq 1 $PUT_MAX_RETRIES); do
                    # Refresh token before each retry (handles expiry edge case)
                    if [ "$PUT_ATTEMPT" -gt 1 ]; then
                        ACCESS_TOKEN=$(acquire_token)
                    fi

                    ANALYZER_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT \
                        "${CU_ENDPOINT}/contentunderstanding/analyzers/${ANALYZER_ID}?api-version=${CU_API_VERSION}" \
                        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
                        -H "Content-Type: application/json" \
                        -d @"$ANALYZER_FILE" 2>/dev/null)

                    ANALYZER_HTTP_CODE=$(echo "$ANALYZER_RESPONSE" | tail -1)
                    ANALYZER_BODY=$(echo "$ANALYZER_RESPONSE" | sed '$d')

                    if [ "$ANALYZER_HTTP_CODE" -ge 200 ] 2>/dev/null && [ "$ANALYZER_HTTP_CODE" -lt 300 ] 2>/dev/null; then
                        echo "    ✅ $ANALYZER_ID — created/updated (HTTP $ANALYZER_HTTP_CODE, attempt $PUT_ATTEMPT)"
                        PUT_OK=true
                        break
                    fi

                    # Retry on transient errors (401, 403, 429, 5xx)
                    case "$ANALYZER_HTTP_CODE" in
                        401|403|429|500|502|503|504)
                            echo "    [attempt $PUT_ATTEMPT/$PUT_MAX_RETRIES] $ANALYZER_ID failed (HTTP $ANALYZER_HTTP_CODE) — retrying in ${PUT_BACKOFF}s..."
                            sleep "$PUT_BACKOFF"
                            PUT_BACKOFF=$((PUT_BACKOFF * 2))
                            [ "$PUT_BACKOFF" -gt 120 ] && PUT_BACKOFF=120
                            ;;
                        *)
                            echo "    ❌ $ANALYZER_ID — non-retryable error (HTTP $ANALYZER_HTTP_CODE)"
                            echo "       Response: $ANALYZER_BODY"
                            break
                            ;;
                    esac
                done

                if [ "$PUT_OK" = "true" ]; then
                    ANALYZER_SUCCESS=$((ANALYZER_SUCCESS + 1))
                else
                    echo "    ❌ $ANALYZER_ID — failed after $PUT_MAX_RETRIES attempts"
                    ANALYZER_FAILED=$((ANALYZER_FAILED + 1))
                fi
            done

            if [ "$ANALYZER_COUNT" -eq 0 ]; then
                echo "  ℹ️  No analyzer JSON files found in seed/analyzers/"
            else
                echo ""
                echo "  Analyzers processed: $ANALYZER_COUNT (✅ $ANALYZER_SUCCESS succeeded, ❌ $ANALYZER_FAILED failed)"

                # Fail deployment if ALL analyzers failed — partial success is allowed
                if [ "$ANALYZER_FAILED" -gt 0 ] && [ "$ANALYZER_SUCCESS" -eq 0 ]; then
                    echo ""
                    echo "❌ All analyzer creations failed. Deployment cannot proceed."
                    echo "   Re-run 'azd up' or 'azd hooks run postprovision' after verifying roles."
                    exit 1
                fi
            fi
        fi
    fi
fi

echo ""
echo "=================================================="
echo "✓ Post-provision completed successfully"
echo "=================================================="
