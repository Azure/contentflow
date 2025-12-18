"""
Queue client for managing task messages in Azure Storage Queue.

This module provides a wrapper around Azure Storage Queue for sending
and receiving processing tasks.
"""
import json
import logging
from typing import Optional, List
from azure.storage.queue import QueueClient, QueueMessage
from azure.identity import ChainedTokenCredential
from azure.core.exceptions import ResourceNotFoundError

from contentflow.utils import get_azure_credential

from app.models import TaskMessage, ContentProcessingTask, InputSourceTask, TaskType

logger = logging.getLogger("contentflow.worker.queue_client")


class TaskQueueClient:
    """
    Client for managing task messages in Azure Storage Queue.
    
    This client provides methods to:
    - Send tasks to the queue
    - Receive tasks from the queue
    - Delete processed messages
    - Update message visibility
    """
    
    def __init__(
        self,
        queue_url: str,
        queue_name: str,
        credential: Optional[ChainedTokenCredential] = None
    ):
        """
        Initialize the task queue client.
        
        Args:
            queue_url: Azure Storage account queue URL
            queue_name: Name of the queue
            credential: Azure credential (uses DefaultAzureCredential if not provided)
        """
        self.queue_url = queue_url
        self.queue_name = queue_name
        self.credential = credential or get_azure_credential()
        
        # Create queue client
        full_queue_url = f"{queue_url}/{queue_name}"
        self.client = QueueClient.from_queue_url(
            queue_url=full_queue_url,
            credential=self.credential
        )
        
        logger.info(f"Initialized TaskQueueClient for queue: {queue_name}")
    
    async def ensure_queue_exists(self):
        """Ensure the queue exists, create if it doesn't"""
        try:
            # Check if queue exists
            properties = self.client.get_queue_properties()
            logger.info(f"Queue '{self.queue_name}' exists with {properties.approximate_message_count} messages")
        except ResourceNotFoundError:
            # Create queue if it doesn't exist
            logger.info(f"Creating queue: {self.queue_name}")
            self.client.create_queue()
    
    def send_content_processing_task(
        self,
        task: ContentProcessingTask,
        visibility_timeout: Optional[int] = None
    ) -> str:
        """
        Send a content processing task to the queue.
        
        Args:
            task: ContentProcessingTask to send
            visibility_timeout: Optional visibility timeout in seconds
            
        Returns:
            Message ID
        """
        message = TaskMessage(
            task_type=TaskType.CONTENT_PROCESSING,
            payload=task.model_dump()
        )
        return self._send_message(message, visibility_timeout)
    
    def send_input_source_task(
        self,
        task: InputSourceTask,
        visibility_timeout: Optional[int] = None
    ) -> str:
        """
        Send an input source loading task to the queue.
        
        Args:
            task: InputSourceTask to send
            visibility_timeout: Optional visibility timeout in seconds
            
        Returns:
            Message ID
        """
        message = TaskMessage(
            task_type=TaskType.INPUT_SOURCE_LOADING,
            payload=task.model_dump()
        )
        return self._send_message(message, visibility_timeout)
    
    def _send_message(
        self,
        message: TaskMessage,
        visibility_timeout: Optional[int] = None
    ) -> str:
        """
        Send a message to the queue.
        
        Args:
            message: TaskMessage to send
            visibility_timeout: Optional visibility timeout in seconds
            
        Returns:
            Message ID
        """
        message_text = json.dumps(message.model_dump())
        
        result = self.client.send_message(
            content=message_text,
            visibility_timeout=visibility_timeout
        )
        
        logger.debug(f"Sent message to queue: {result.id}")
        return result.id
    
    def receive_messages(
        self,
        max_messages: int = 1,
        visibility_timeout: int = 300
    ) -> List[QueueMessage]:
        """
        Receive messages from the queue.
        
        Args:
            max_messages: Maximum number of messages to receive
            visibility_timeout: Visibility timeout in seconds
            
        Returns:
            List of QueueMessage objects
        """
        messages = self.client.receive_messages(
            messages_per_page=max_messages,
            visibility_timeout=visibility_timeout
        )
        
        return list(messages)
    
    def parse_message(self, message: QueueMessage) -> tuple[TaskType, dict]:
        """
        Parse a queue message into a task.
        
        Args:
            message: QueueMessage from the queue
            
        Returns:
            Tuple of (TaskType, task_payload_dict)
        """
        try:
            # Parse message content
            message_data = json.loads(message.content)
            
            # Extract task type and payload
            task_type = TaskType(message_data["task_type"])
            payload = message_data["payload"]
            
            return task_type, payload
            
        except Exception as e:
            logger.error(f"Failed to parse message {message.id}: {e}")
            raise
    
    def delete_message(self, message: QueueMessage):
        """
        Delete a message from the queue after successful processing.
        
        Args:
            message: QueueMessage to delete
        """
        try:
            self.client.delete_message(message.id, message.pop_receipt)
            logger.debug(f"Deleted message: {message.id}")
        except Exception as e:
            logger.error(f"Failed to delete message {message.id}: {e}")
            raise
    
    def update_message_visibility(
        self,
        message: QueueMessage,
        visibility_timeout: int
    ) -> QueueMessage:
        """
        Update message visibility timeout (e.g., to extend processing time).
        
        Args:
            message: QueueMessage to update
            visibility_timeout: New visibility timeout in seconds
            
        Returns:
            Updated QueueMessage
        """
        try:
            updated = self.client.update_message(
                message.id,
                message.pop_receipt,
                visibility_timeout=visibility_timeout
            )
            logger.debug(f"Updated message visibility: {message.id}")
            return updated
        except Exception as e:
            logger.error(f"Failed to update message visibility {message.id}: {e}")
            raise
    
    def get_queue_length(self) -> int:
        """
        Get approximate number of messages in the queue.
        
        Returns:
            Approximate message count
        """
        try:
            properties = self.client.get_queue_properties()
            return properties.approximate_message_count
        except Exception as e:
            logger.error(f"Failed to get queue properties: {e}")
            return 0
