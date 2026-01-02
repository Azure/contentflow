#!/bin/bash
# Post-deploy hook - runs after all services are deployed
set -e

echo "=================================================="
echo "ContentFlow - Post-Deploy Hook"
echo "=================================================="

# Get deployment outputs
API_ENDPOINT=$(azd env get-value API_ENDPOINT 2>/dev/null || echo "Not available")
WEB_ENDPOINT=$(azd env get-value WEB_ENDPOINT 2>/dev/null || echo "Not available")
WORKER_ENDPOINT=$(azd env get-value WORKER_ENDPOINT 2>/dev/null || echo "Not available")

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║     ContentFlow Deployment Complete! 🚀        ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "Service Endpoints:"
echo "  API:    $API_ENDPOINT"
echo "  Web:    $WEB_ENDPOINT"
echo "  Worker: $WORKER_ENDPOINT"
echo ""
echo "Next Steps:"
echo "  1. Access the web UI at: $WEB_ENDPOINT"
echo "  2. View API docs at: $API_ENDPOINT/docs"
echo "  3. Check logs: azd monitor --logs"
echo ""
echo "=================================================="
