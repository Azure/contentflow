#!/usr/bin/env python3
"""
Knowledge Graph Prerequisites Checker

This script verifies that all prerequisites are met for running
the knowledge graph samples.
"""

import os
import sys
import importlib.util


def check_env_var(var_name, description):
    """Check if environment variable is set."""
    value = os.getenv(var_name)
    if value and value != "your-key-here" and not value.startswith("your-"):
        print(f"✓ {var_name}: {description}")
        return True
    else:
        print(f"✗ {var_name}: {description} - NOT SET")
        return False


def check_package(package_name, import_name=None):
    """Check if Python package is installed."""
    if import_name is None:
        import_name = package_name
    
    spec = importlib.util.find_spec(import_name)
    if spec is not None:
        print(f"✓ {package_name}: Installed")
        return True
    else:
        print(f"✗ {package_name}: NOT INSTALLED")
        return False


def main():
    """Run all prerequisite checks."""
    print("=" * 70)
    print("Knowledge Graph Prerequisites Checker")
    print("=" * 70)
    print()
    
    all_ok = True
    
    # Check environment variables
    print("Checking Environment Variables:")
    print("-" * 70)
    
    env_checks = [
        ("COSMOS_GREMLIN_ENDPOINT", "Cosmos DB Gremlin endpoint"),
        ("COSMOS_GREMLIN_DATABASE", "Database name"),
        ("COSMOS_GREMLIN_COLLECTION", "Graph collection name"),
        ("COSMOS_GREMLIN_KEY", "Primary key"),
        ("AI_ENDPOINT", "Azure AI endpoint"),
        ("AI_MODEL_NAME", "AI model name"),
    ]
    
    for var, desc in env_checks:
        if not check_env_var(var, desc):
            all_ok = False
    
    print()
    
    # Optional env vars
    print("Optional Environment Variables:")
    print("-" * 70)
    check_env_var("AI_API_KEY", "AI API key (optional if using Managed Identity)")
    print()
    
    # Check Python packages
    print("Checking Python Packages:")
    print("-" * 70)
    
    packages = [
        ("gremlinpython", "gremlin_python"),
        ("azure-identity", "azure.identity"),
        ("azure-ai-inference", "azure.ai.inference"),
    ]
    
    for pkg_name, import_name in packages:
        if not check_package(pkg_name, import_name):
            all_ok = False
    
    print()
    
    # Check ContentFlow packages
    print("Checking ContentFlow Packages:")
    print("-" * 70)
    
    contentflow_packages = [
        ("agent_framework", None),
        ("packages.models", None),
        ("packages.executors", None),
        ("packages.connectors", None),
    ]
    
    for pkg_name, _ in contentflow_packages:
        if not check_package(pkg_name):
            all_ok = False
    
    print()
    
    # Check specific executors
    print("Checking Knowledge Graph Executors:")
    print("-" * 70)
    
    try:
        from packages.executors import (
            KnowledgeGraphEntityExtractorExecutor,
            KnowledgeGraphWriterExecutor,
            KnowledgeGraphQueryExecutor,
            KnowledgeGraphEnrichmentExecutor
        )
        print("✓ All knowledge graph executors available")
    except ImportError as e:
        print(f"✗ Knowledge graph executors: {e}")
        all_ok = False
    
    print()
    
    # Check specific connector
    print("Checking Cosmos Gremlin Connector:")
    print("-" * 70)
    
    try:
        from packages.connectors import CosmosGremlinConnector
        print("✓ CosmosGremlinConnector available")
    except ImportError as e:
        print(f"✗ CosmosGremlinConnector: {e}")
        all_ok = False
    
    print()
    
    # Final summary
    print("=" * 70)
    if all_ok:
        print("✓ All prerequisites met! You're ready to run the samples.")
        print()
        print("Next steps:")
        print("  1. python build_knowledge_graph.py")
        print("  2. python enrich_knowledge_graph.py")
        print("  3. python query_knowledge_graph.py")
        return 0
    else:
        print("✗ Some prerequisites are missing.")
        print()
        print("To fix:")
        print("  1. Set missing environment variables in .env file")
        print("  2. Install missing packages: pip install -r requirements.txt")
        print("  3. Run this checker again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
