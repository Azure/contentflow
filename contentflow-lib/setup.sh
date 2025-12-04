#!/bin/bash

# Setup script for doc-proc-lib-workflows
# This script installs the necessary dependencies and sets up the development environment

set -e  # Exit on error

echo "=================================="
echo "Doc-Proc-Lib-Workflows Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

required_version="3.10"
if [[ $(echo -e "$required_version\n$python_version" | sort -V | head -n1) != "$required_version" ]]; then
    echo "ERROR: Python 3.10 or higher is required"
    exit 1
fi
echo "✓ Python version OK"
echo ""

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "WARNING: Not running in a virtual environment"
    echo "It's recommended to use a virtual environment"
    echo ""
    read -p "Do you want to create a virtual environment? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        echo "✓ Virtual environment created and activated"
    fi
    echo ""
fi

# Install Microsoft Agent Framework
echo "Installing Microsoft Agent Framework (preview)..."
pip install agent-framework-azure-ai --pre
echo "✓ Agent Framework installed"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Install in development mode
echo "Installing doc-proc-lib-workflows in development mode..."
pip install -e .
echo "✓ Package installed in development mode"
echo ""

# Install development dependencies
echo "Installing development dependencies..."
pip install -e ".[dev]"
echo "✓ Development dependencies installed"
echo ""

# Verify installation
echo "Verifying installation..."
python3 -c "
try:
    import agent_framework
    print('✓ agent_framework imported successfully')
except ImportError as e:
    print(f'✗ Failed to import agent_framework: {e}')
    exit(1)

try:
    from doc_proc_workflow import WorkflowFactory
    print('✓ doc_proc_workflow imported successfully')
except ImportError as e:
    print(f'✗ Failed to import doc_proc_workflow: {e}')
    exit(1)

print('✓ All imports successful')
"
echo ""

# Check if doc-proc-lib is available
echo "Checking for doc-proc-lib..."
if [ -d "../doc-proc-lib" ]; then
    echo "✓ Found doc-proc-lib in parent directory"
    
    # Add to PYTHONPATH
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/../doc-proc-lib"
    echo "  Added to PYTHONPATH: $(pwd)/../doc-proc-lib"
    
    # Try to import doc.proc
    python3 -c "
import sys
sys.path.insert(0, '../doc-proc-lib')
try:
    from doc.proc.models import Document
    print('✓ doc-proc-lib models imported successfully')
except ImportError as e:
    print(f'⚠ Could not import doc-proc-lib: {e}')
    print('  Examples may not work without doc-proc-lib')
"
else
    echo "⚠ doc-proc-lib not found in parent directory"
    echo "  Some examples may not work without doc-proc-lib"
    echo "  Clone doc-proc-lib or install it separately"
fi
echo ""

echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Explore the examples:"
echo "     cd examples"
echo "     python simple_sequential.py"
echo ""
echo "  2. Read the documentation:"
echo "     - README.md - Overview and quick start"
echo "     - MIGRATION.md - Migration guide from pipelines"
echo "     - examples/README.md - Example documentation"
echo ""
echo "  3. Review the code:"
echo "     - doc_proc_workflow/executors/ - Executor implementations"
echo "     - doc_proc_workflow/factory/ - Workflow factory"
echo "     - doc_proc_workflow/models/ - Data models"
echo ""
echo "For more information, visit:"
echo "  https://github.com/microsoft/agent-framework"
echo ""
