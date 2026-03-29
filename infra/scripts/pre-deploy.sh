#!/bin/bash
# Pre-deploy hook - runs before deploying all services
# Validates ACR pull readiness to prevent RBAC propagation failures
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

# ──────────────────────────────────────────────────────────
# ACR Pull Readiness Gate
# ──────────────────────────────────────────────────────────
# After azd provision, the AcrPull role assignment exists in ARM but Azure RBAC
# propagation is eventually consistent. Container Apps may fail to pull images
# if the role is not yet effective. This gate blocks deploy until readiness is
# confirmed, preventing the intermittent "unable to pull image using Managed
# identity" error on fresh environments.
# ──────────────────────────────────────────────────────────

ACR_NAME=$(azd env get-value AZURE_CONTAINER_REGISTRY_NAME 2>/dev/null || echo "")
IDENTITY_PRINCIPAL_ID=$(azd env get-value MANAGED_IDENTITY_PRINCIPAL_ID 2>/dev/null || echo "")
DEPLOYMENT_MODE=$(azd env get-value DEPLOYMENT_MODE 2>/dev/null || echo "basic")

# Configurable via azd env set (seconds)
ACR_RBAC_TIMEOUT=${ACR_RBAC_TIMEOUT:-300}
ACR_RBAC_STABILIZATION=${ACR_RBAC_STABILIZATION:-60}

if [ -z "$ACR_NAME" ] || [ -z "$IDENTITY_PRINCIPAL_ID" ]; then
    echo "⚠ ACR_NAME or MANAGED_IDENTITY_PRINCIPAL_ID not found in azd env."
    echo "  Skipping ACR readiness check. Deploy may fail if RBAC is not yet propagated."
else
    echo ""
    echo "── ACR Pull Readiness Check ──"
    echo "  Registry:     $ACR_NAME"
    echo "  Principal ID: $IDENTITY_PRINCIPAL_ID"
    echo "  Mode:         $DEPLOYMENT_MODE"
    echo "  Timeout:      ${ACR_RBAC_TIMEOUT}s"
    echo "  Stabilization: ${ACR_RBAC_STABILIZATION}s"
    echo ""

    # Get ACR resource ID for scoped role query
    ACR_RESOURCE_ID=$(az acr show -n "$ACR_NAME" --query id -o tsv 2>/dev/null || echo "")

    if [ -z "$ACR_RESOURCE_ID" ]; then
        echo "⚠ Could not resolve ACR resource ID for '$ACR_NAME'. Skipping readiness check."
    else
        # ── Phase 1: Wait for AcrPull role to be visible ──
        echo "  Checking AcrPull role assignment..."
        ELAPSED=0
        POLL_INTERVAL=10
        ACR_PULL_FOUND=false

        while [ "$ELAPSED" -lt "$ACR_RBAC_TIMEOUT" ]; do
            ROLES=$(az role assignment list \
                --assignee-object-id "$IDENTITY_PRINCIPAL_ID" \
                --scope "$ACR_RESOURCE_ID" \
                --query "[?roleDefinitionName=='AcrPull'].roleDefinitionName" \
                -o tsv 2>/dev/null || echo "")

            if echo "$ROLES" | grep -q "AcrPull"; then
                ACR_PULL_FOUND=true
                break
            fi

            echo "  ⏳ AcrPull not yet visible (${ELAPSED}s elapsed). Retrying in ${POLL_INTERVAL}s..."
            sleep "$POLL_INTERVAL"
            ELAPSED=$((ELAPSED + POLL_INTERVAL))
        done

        if [ "$ACR_PULL_FOUND" = false ]; then
            echo ""
            echo "❌ ACR readiness check FAILED after ${ACR_RBAC_TIMEOUT}s."
            echo "   AcrPull role not visible for principal $IDENTITY_PRINCIPAL_ID on $ACR_NAME."
            echo ""
            echo "   To retry: azd deploy --no-prompt"
            echo "   To increase timeout: ACR_RBAC_TIMEOUT=600 azd deploy --no-prompt"
            exit 1
        fi

        echo "  ✓ AcrPull role is visible"

        # ── Phase 2: AILZ-only DNS verification ──
        if [ "$DEPLOYMENT_MODE" = "ailz-integrated" ]; then
            echo ""
            echo "  Verifying ACR private endpoint DNS resolution (AILZ mode)..."
            ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
            RESOLVED_IP=$(nslookup "$ACR_LOGIN_SERVER" 2>/dev/null | grep -A1 "privatelink.azurecr.io" | grep "Address:" | awk '{print $2}' || echo "")

            if [ -z "$RESOLVED_IP" ]; then
                # Fallback: just check if it resolves to any IP
                RESOLVED_IP=$(nslookup "$ACR_LOGIN_SERVER" 2>/dev/null | tail -2 | grep "Address:" | awk '{print $2}' || echo "")
            fi

            if [ -z "$RESOLVED_IP" ]; then
                echo "  ⚠ Could not resolve $ACR_LOGIN_SERVER. ACR private endpoint DNS may not be configured."
                echo "    Deploy may fail if Container Apps cannot reach the registry."
            elif echo "$RESOLVED_IP" | grep -qE "^10\.|^172\.(1[6-9]|2[0-9]|3[01])\.|^192\.168\."; then
                echo "  ✓ ACR resolves to private IP: $RESOLVED_IP"
            else
                echo "  ⚠ ACR resolves to public IP: $RESOLVED_IP"
                echo "    In AILZ mode, ACR should resolve to a private endpoint IP."
                echo "    Verify privatelink.azurecr.io DNS zone is configured correctly."
            fi
        fi

        # ── Phase 3: Stabilization wait ──
        # RBAC can be queryable before ACA can effectively use it.
        # A short stabilization wait reduces the chance of a race condition.
        if [ "$ACR_RBAC_STABILIZATION" -gt 0 ]; then
            echo ""
            echo "  ⏳ Waiting ${ACR_RBAC_STABILIZATION}s for RBAC stabilization..."
            sleep "$ACR_RBAC_STABILIZATION"
            echo "  ✓ Stabilization complete"
        fi

        echo ""
        echo "  ✓ ACR pull readiness confirmed"
    fi
fi

echo ""
echo "=================================================="
echo "✓ Pre-deploy checks completed successfully"
echo "=================================================="
