"""
Example demonstrating dynamic executor loading from catalog.

This example shows how to use the executor catalog for dynamic
executor loading instead of hardcoded executor types.
"""

import asyncio
from pathlib import Path
from doc_proc_workflow.factory.pipeline_factory import PipelineFactory


async def main():
    """Demonstrate dynamic executor loading."""
    
    # Get paths
    examples_dir = Path(__file__).parent
    catalog_path = examples_dir.parent / "executor_catalog.yaml"
    config_path = examples_dir / "simple_config.yaml"
    
    print("=" * 70)
    print("Dynamic Executor Loading Example")
    print("=" * 70)
    
    # Create factory with executor catalog (enables dynamic loading)
    print(f"\nLoading factory with executor catalog: {catalog_path}")
    factory = PipelineFactory.from_config_file(
        config_path=str(config_path),
        executor_catalog_path=str(catalog_path)
    )
    
    print(f"✓ Factory created with dynamic loading enabled")
    
    # Show executor catalog
    print("\n" + "-" * 70)
    print("Executor Catalog:")
    print("-" * 70)
    catalog = factory.get_executor_catalog()
    for executor in catalog:
        print(f"\n{executor['id']}:")
        print(f"  Name: {executor['name']}")
        print(f"  Category: {executor['category']}")
        print(f"  Tags: {', '.join(executor['tags'])}")
        print(f"  Required Connectors: {', '.join(executor['required_connectors'])}")
        print(f"  Settings: {len(executor['settings_schema'])} settings")
    
    # Validate workflow
    print("\n" + "-" * 70)
    print("Workflow Validation:")
    print("-" * 70)
    workflow_name = "simple_document_processing"
    validation = factory.validate_pipeline_executors(workflow_name)
    
    print(f"\nWorkflow: {workflow_name}")
    print(f"Valid: {validation['valid']}")
    
    if validation['errors']:
        print("\nErrors:")
        for error in validation['errors']:
            print(f"  ✗ {error}")
    else:
        print("  ✓ No errors")
    
    if validation['warnings']:
        print("\nWarnings:")
        for warning in validation['warnings']:
            print(f"  ⚠ {warning}")
    else:
        print("  ✓ No warnings")
    
    # Initialize connectors
    print("\n" + "-" * 70)
    print("Initializing Connectors:")
    print("-" * 70)
    await factory.initialize_connectors()
    
    # Test connections
    print("\nTesting connector connections...")
    test_results = await factory.test_connectors()
    for connector_id, result in test_results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {connector_id}")
    
    # Create workflow with dynamic executor loading
    print("\n" + "-" * 70)
    print("Creating Workflow:")
    print("-" * 70)
    print(f"\nWorkflow: {workflow_name}")
    workflow = factory.create_workflow(workflow_name)
    print(f"✓ Workflow created with dynamically loaded executors")
    print(f"  Workflow: {workflow}")
    
    # Get executor information
    print("\n" + "-" * 70)
    print("Executor Registry Information:")
    print("-" * 70)
    print(f"Registered executors: {len(factory.executor_registry)}")
    print(f"Executor IDs: {', '.join(factory.executor_registry.list_executor_ids())}")
    
    # Show executors by category
    print("\nExecutors by category:")
    categories = set(e['category'] for e in catalog)
    for category in sorted(categories):
        executors_in_cat = [
            e['id'] for e in catalog if e['category'] == category
        ]
        print(f"  {category}: {', '.join(executors_in_cat)}")
    
    # Cleanup
    print("\n" + "-" * 70)
    print("Cleanup:")
    print("-" * 70)
    await factory.cleanup_connectors()
    print("✓ Connectors cleaned up")
    
    print("\n" + "=" * 70)
    print("Dynamic Loading Example Complete!")
    print("=" * 70)
    
    # Show benefits
    print("\nBenefits of Dynamic Loading:")
    print("  ✓ No need to modify PipelineFactory for new executors")
    print("  ✓ Executor metadata available for UI generation")
    print("  ✓ Settings validation using schema")
    print("  ✓ Easy to add custom executors via catalog")
    print("  ✓ Backward compatible with legacy executor types")


async def compare_loading_modes():
    """Compare legacy vs dynamic loading."""
    
    examples_dir = Path(__file__).parent
    catalog_path = examples_dir.parent / "executor_catalog.yaml"
    config_path = examples_dir / "simple_config.yaml"
    
    print("\n" + "=" * 70)
    print("Comparing Loading Modes")
    print("=" * 70)
    
    # Legacy loading (no catalog)
    print("\n1. Legacy Loading (no catalog):")
    print("-" * 70)
    factory_legacy = PipelineFactory.from_config_file(str(config_path))
    print(f"Dynamic loading: {factory_legacy.use_dynamic_loading}")
    print(f"Executor catalog size: {len(factory_legacy.executor_registry)}")
    legacy_catalog = factory_legacy.get_executor_catalog()
    print(f"Available executors: {len(legacy_catalog)}")
    for exec_info in legacy_catalog:
        print(f"  - {exec_info['id']} ({exec_info['class']})")
    
    # Dynamic loading (with catalog)
    print("\n2. Dynamic Loading (with catalog):")
    print("-" * 70)
    factory_dynamic = PipelineFactory.from_config_file(
        config_path=str(config_path),
        executor_catalog_path=str(catalog_path)
    )
    print(f"Dynamic loading: {factory_dynamic.use_dynamic_loading}")
    print(f"Executor catalog size: {len(factory_dynamic.executor_registry)}")
    dynamic_catalog = factory_dynamic.get_executor_catalog()
    print(f"Available executors: {len(dynamic_catalog)}")
    for exec_info in dynamic_catalog:
        print(f"  - {exec_info['id']} ({exec_info['name']})")
    
    print("\n" + "=" * 70)
    print("Key Difference:")
    print("  Legacy: Uses hardcoded EXECUTOR_TYPES dict")
    print("  Dynamic: Uses executor_catalog.yaml for configuration")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(compare_loading_modes())
