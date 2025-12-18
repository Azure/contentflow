"""
Sample script to demonstrate the ContentFlow worker workflow.

This script shows how to:
1. Send a content processing task manually
2. Check queue status

Note: Source workers automatically poll Cosmos DB for pipelines with vaults,
so InputSourceTask messages are no longer needed.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from models import ContentProcessingTask, TaskPriority
from queue_client import TaskQueueClient
from settings import get_settings
from utils import create_task_id, create_execution_id


async def send_processing_task():
    """Send a sample content processing task"""
    settings = get_settings()
    
    # Initialize queue client
    queue_client = TaskQueueClient(
        queue_url=settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
        queue_name=settings.STORAGE_WORKER_QUEUE_NAME
    )
    
    # Create sample task
    task = ContentProcessingTask(
        task_id=create_task_id(),
        pipeline_id="sample_pipeline_123",
        pipeline_name="Sample Document Processing",
        execution_id=create_execution_id(),
        content_id="content_456",
        content_data={
            "text": "This is sample content to process",
            "metadata": {
                "source": "sample_script",
                "type": "text"
            }
        },
        priority=TaskPriority.NORMAL,
        inputs={
            "language": "en"
        },
        executed_input_executor="blob_input",  # Mark input executor as already executed
        max_retries=3
    )
    
    # Send to queue
    message_id = queue_client.send_content_processing_task(task)
    
    print(f"✅ Sent content processing task:")
    print(f"   Task ID: {task.task_id}")
    print(f"   Pipeline: {task.pipeline_name}")
    print(f"   Message ID: {message_id}")
    print(f"   Priority: {task.priority}")
    print(f"   Input Executor: {task.executed_input_executor} (already executed)")


async def check_queue_status():
    """Check queue status"""
    settings = get_settings()
    
    # Initialize queue client
    queue_client = TaskQueueClient(
        queue_url=settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
        queue_name=settings.STORAGE_WORKER_QUEUE_NAME
    )
    
    # Get queue length
    length = queue_client.get_queue_length()
    
    print(f"\n📊 Queue Status:")
    print(f"   Queue Name: {settings.STORAGE_WORKER_QUEUE_NAME}")
    print(f"   Messages: {length}")


async def main():
    """Main function"""
    print("=" * 60)
    print("ContentFlow Worker - Sample Task Sender")
    print("=" * 60)
    
    try:
        # Check queue status
        await check_queue_status()
        
        print("\nSending content processing task...")
        await send_processing_task()
        
        print("\nNote: Source workers automatically poll Cosmos DB")
        print("for enabled pipelines with vaults. No manual source")
        print("tasks need to be sent.")
        
        # Check queue status again
        await check_queue_status()
        
        print("\n✅ Done! Task sent successfully.")
        print("Workers should pick it up from the queue.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
