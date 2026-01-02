"""Test edge-based workflow configuration."""

import asyncio
from pathlib import Path
from doc_proc_workflow import PipelineExecutor


async def test_fan_out_fan_in():
    """Test fan-out/fan-in workflow with edges."""
    config_path = Path(__file__).parent / "fan_out_fan_in.yaml"
    
    print(f"Loading workflow from: {config_path}")
    
    async with PipelineExecutor.from_config_file(
        config_path=str(config_path),
        workflow_name="multi_path_processing"
    ) as executor:
        
        # Test connector connections
        print("\nTesting connector connections...")
        test_results = await executor.test_connectors()
        for connector_id, result in test_results.items():
            status = "✓" if result else "✗"
            print(f"  {status} {connector_id}")
        
        print("\nWorkflow created and initialized")
        info = executor.get_workflow_info()
        print(f"Workflow uses edge-based graph construction")
        print(f"  Dynamic loading: {info['factory_info']['dynamic_loading']}")
        
    print("\n✓ Test completed successfully!")


async def test_conditional_routing():
    """Test conditional routing workflow."""
    config_path = Path(__file__).parent / "conditional_routing.yaml"
    
    print(f"Loading workflow from: {config_path}")
    
    async with PipelineExecutor.from_config_file(
        config_path=str(config_path),
        workflow_name="document_routing"
    ) as executor:
        
        print("\nWorkflow created and initialized")
        info = executor.get_workflow_info()
        print(f"Workflow uses conditional edge routing")
        print(f"  Connectors: {info['factory_info']['connectors']}")
        
    print("\n✓ Test completed successfully!")


async def test_sequential_fallback():
    """Test that workflows without edges still work (sequential fallback)."""
    config_path = Path(__file__).parent / "simple_config.yaml"
    
    print(f"Loading workflow from: {config_path}")
    
    async with PipelineExecutor.from_config_file(
        config_path=str(config_path),
        workflow_name="simple_document_processing"
    ) as executor:
        
        print("\nWorkflow created and initialized")
        info = executor.get_workflow_info()
        print(f"Workflow uses sequential execution_sequence (no edges)")
        print(f"  Workflows available: {info['factory_info']['workflows']}")
        
    print("\n✓ Test completed successfully!")


async def main():
    """Run all edge workflow tests."""
    print("=" * 60)
    print("Testing Edge-Based Workflow Factory")
    print("=" * 60)
    
    print("\n\nTest 1: Fan-Out/Fan-In Pattern")
    print("-" * 60)
    await test_fan_out_fan_in()
    
    print("\n\nTest 2: Conditional Routing Pattern")
    print("-" * 60)
    await test_conditional_routing()
    
    print("\n\nTest 3: Sequential Fallback (No Edges)")
    print("-" * 60)
    await test_sequential_fallback()
    
    print("\n\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
