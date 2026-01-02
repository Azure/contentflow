#!/bin/bash

# Knowledge Graph Sample - Environment Setup Script

echo "=========================================="
echo "Knowledge Graph Sample - Environment Setup"
echo "=========================================="
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | xargs)
else
    echo "No .env file found. Creating template..."
    cat > .env << EOF
# Azure Cosmos DB Gremlin API Configuration
COSMOS_GREMLIN_ENDPOINT="wss://your-account.gremlin.cosmos.azure.com:443/"
COSMOS_GREMLIN_DATABASE="knowledge"
COSMOS_GREMLIN_COLLECTION="entities"
COSMOS_GREMLIN_KEY="your-primary-key-here"

# Azure AI Configuration
AI_ENDPOINT="https://your-ai-endpoint.azure.com/"
AI_API_KEY="your-api-key-here"
AI_MODEL_NAME="gpt-4"
EOF
    echo "Created .env template. Please edit it with your credentials."
    echo ""
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your Azure credentials"
echo "  2. Run: python build_knowledge_graph.py"
echo "  3. Run: python enrich_knowledge_graph.py"
echo "  4. Run: python query_knowledge_graph.py"
echo ""
