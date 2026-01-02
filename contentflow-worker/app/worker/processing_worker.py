"""
Content processing worker for executing pipeline tasks.

This module implements the ContentProcessingWorker that:
- Listens to the task queue for content processing tasks
- Executes pipelines on content
- Reports execution status back to Cosmos DB
"""

import asyncio
import logging
import multiprocessing as mp
import signal
import sys
import time
import traceback
from pathlib import Path
from typing import List, Optional

from azure.identity import ChainedTokenCredential
from azure.cosmos import CosmosClient
from azure.cosmos import exceptions as cosmos_exceptions

from contentflow.pipeline import PipelineExecutor
from contentflow.models import Content, ContentIdentifier
from contentflow.pipeline import PipelineResult
from contentflow.utils import get_azure_credential, make_safe_json

from app.models import ContentProcessingTask
from app.queue_client import TaskQueueClient
from app.settings import WorkerSettings

logger = logging.getLogger("contentflow.worker.processing_worker")


class ContentProcessingWorker:
    """
    Worker process for executing content processing tasks.
    
    This worker:
    1. Polls the task queue for ContentProcessingTask messages
    2. Loads pipeline configuration from Cosmos DB
    3. Executes the pipeline on the content
    4. Updates execution status in Cosmos DB
    5. Deletes the message from queue on success
    """
    
    def __init__(
        self,
        worker_id: int,
        settings: WorkerSettings,
        stop_event
    ):
        """
        Initialize the content processing worker.
        
        Args:
            worker_id: Unique worker identifier
            settings: Worker configuration settings
            stop_event: Multiprocessing event for graceful shutdown
        """
        self.worker_id = worker_id
        self.settings = settings
        self.stop_event = stop_event
        self.name = f"ContentProcessingWorker-{worker_id}"
        
        # Azure clients (initialized in run)
        self.credential: Optional[ChainedTokenCredential] = None
        self.queue_client: Optional[TaskQueueClient] = None
        self.cosmos_client: Optional[CosmosClient] = None
        
        logger.info(f"Initialized {self.name}")
    
    def run(self):
        """Main worker loop"""
        logger.info(f"{self.name} starting...")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Initialize Azure clients
            self._initialize_clients()
            
            # Main processing loop
            logger.info(f"{self.name} entering main processing loop")
            
            while not self.stop_event.is_set():
                try:
                    self._process_batch()
                    
                    # Sleep between polls
                    if not self.stop_event.is_set():
                        time.sleep(self.settings.QUEUE_POLL_INTERVAL_SECONDS)
                        
                except Exception as e:
                    logger.error(f"{self.name} error in processing loop: {e}")
                    logger.error(traceback.format_exc())
                    time.sleep(5)  # Back off on error
                    
        except KeyboardInterrupt:
            logger.info(f"{self.name} received interrupt signal")
        except Exception as e:
            logger.error(f"{self.name} fatal error: {e}")
            logger.error(traceback.format_exc())
        finally:
            logger.info(f"{self.name} shutting down...")
    
    def _initialize_clients(self):
        """Initialize Azure clients"""
        logger.info(f"{self.name} initializing Azure clients...")
        
        # Initialize credential
        self.credential = get_azure_credential()
        
        # Initialize queue client
        self.queue_client = TaskQueueClient(
            queue_url=self.settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
            queue_name=self.settings.STORAGE_WORKER_QUEUE_NAME,
            credential=self.credential
        )
        
        # Initialize Cosmos DB client
        self.cosmos_client = CosmosClient(
            url=self.settings.COSMOS_DB_ENDPOINT,
            credential=self.credential
        )
        
        logger.info(f"{self.name} clients initialized")
    
    def _process_batch(self):
        """Process a batch of messages from the queue"""
        try:
            # Receive messages
            messages = self.queue_client.receive_messages(
                max_messages=self.settings.QUEUE_MAX_MESSAGES,
                visibility_timeout=self.settings.QUEUE_VISIBILITY_TIMEOUT_SECONDS
            )
            
            if not messages:
                logger.debug(f"{self.name} no messages in queue")
                return
            
            logger.debug(f"{self.name} received {len(messages)} messages")
            
            # Process each message
            for message in messages:
                if self.stop_event.is_set():
                    break
                    
                try:
                    self._process_message(message)
                except Exception as e:
                    logger.error(f"{self.name} failed to process message {message.id}: {e}")
                    logger.error(traceback.format_exc())
                    # Message will become visible again after timeout
                    
        except Exception as e:
            logger.error(f"{self.name} error receiving messages: {e}")
            logger.error(traceback.format_exc())
    
    def _process_message(self, message):
        """Process a single message"""
        logger.debug(f"{self.name} processing message {message.id}")
        
        try:
            # Parse message
            task_type, payload = self.queue_client.parse_message(message)
            logger.debug(f"{self.name} parsed message {message.id} with task type {task_type}")
            
            # Only process content processing tasks
            if task_type.value != "content_processing":
                logger.warning(f"{self.name} received non-processing task: {task_type}")
                # self.queue_client.delete_message(message)
                return
            
            # Create task object
            task = ContentProcessingTask(**payload)
            
            # Check retry count
            if task.retry_count >= task.max_retries:
                logger.error(f"{self.name} task {task.task_id} exceeded max retries")
                self._update_execution_status(task.execution_id, "failed", error="Max retries exceeded")
                self.queue_client.delete_message(message)
                return
            
            # Execute task
            success = self._execute_task(task)
            
            # Delete message on success
            if success:
                self.queue_client.delete_message(message)
                logger.debug(f"{self.name} completed message {message.id}")
            else:
                logger.warning(f"{self.name} task failed, will retry")
                # Message will become visible again after timeout
                
        except Exception as e:
            logger.error(f"{self.name} error processing message {message.id}: {e}")
            logger.exception(e)
            raise
    
    def _execute_task(self, task: ContentProcessingTask) -> bool:
        """
        Execute a content processing task.
        
        Args:
            task: ContentProcessingTask to execute
            
        Returns:
            True if successful, False otherwise
        """
        logger.debug(f"{self.name} executing task {task.task_id} for pipeline {task.pipeline_name}")
        
        try:
            # Update execution status to running
            self._update_execution_status(task.execution_id, "running")
            
            # Get pipeline from Cosmos DB
            pipeline_config = self._get_pipeline(task.pipeline_id)
            if not pipeline_config:
                logger.error(f"{self.name} pipeline not found: {task.pipeline_id}")
                self._update_execution_status(task.execution_id, "failed", error="Pipeline not found")
                return False
            
            # verify input content
            content = task.content
            if not content or len(content) == 0:
                logger.error(f"{self.name} no input content for task {task.task_id}")
                self._update_execution_status(task.execution_id, "failed", error="No input content")
                return False
            
            # Execute pipeline synchronously (using asyncio.run)
            result = self._run_pipeline(pipeline_config, content, task)
            
            if result and result.status == "completed":
                self._update_execution_status(task.execution_id, "completed")
                
                try:
                    self._save_execution_output(task.execution_id, result)
                except cosmos_exceptions.CosmosHttpResponseError as ce:
                    # check if it's due to request entity too large
                    if ce.status_code == 413:
                        
                        logger.warning(f"Result too large to store for execution {task.execution_id}, skipping event data storage.")
                        
                        # update the data field in each content item to indicate data too large
                        if isinstance(result.content, list):
                            for c in result.content:
                                c.data = {"data": "Output data too large to store in Cosmos DB. View output saved by output executor(s)."}
                            self._save_execution_output(task.execution_id, result)
                        else:
                            result.content.data = {"data": "Output data too large to store in Cosmos DB. View output saved by output executor(s)."}
                            self._save_execution_output(task.execution_id, result)
                    
                    else:
                        logger.error(f"Failed to add save result to execution {task.execution_id}: {ce}", exc_info=True)
                        raise ce
                
                logger.debug(f"{self.name} task {task.task_id} completed successfully")
                return True
            else:
                self._update_execution_status(task.execution_id, "failed", error="Pipeline execution failed")
                return False
                
        except Exception as e:
            logger.error(f"{self.name} error executing task {task.task_id}: {e}")
            logger.exception(e)
            self._update_execution_status(task.execution_id, "failed", error=str(e))
            return False
    
    def _run_pipeline(self, pipeline_config: dict, content: List[Content], task: ContentProcessingTask) -> PipelineResult:
        """Run pipeline execution"""
        try:
            # Load pipeline executor
            import yaml
            
            # Parse the YAML
            _parsed_pipeline_config = yaml.safe_load(pipeline_config["yaml"])
            
            # If an input executor was already executed, remove it from the pipeline
            if task.executed_input_executor:
                logger.debug(f"{self.name} excluding already-executed input executor: {task.executed_input_executor}")
                _parsed_pipeline_config = self._exclude_executor(_parsed_pipeline_config, task.executed_input_executor)
            
            
            pipeline_definition = _parsed_pipeline_config.get('pipeline', _parsed_pipeline_config)
            
            # Create pipeline executor
            async def execute():
                async with PipelineExecutor.from_pipeline_definition_dict(
                    pipeline_definition=pipeline_definition
                ) as pipeline_executor:
                    
                    # Execute
                    return await pipeline_executor.execute(content)
            
            # Run async pipeline
            result = asyncio.run(execute())
            
            logger.debug(f"{self.name} pipeline execution result: {result.status}")
            return result
                
        except Exception as e:
            logger.error(f"{self.name} pipeline execution error: {e}")
            logger.exception(e)
            raise e
    
    def _exclude_executor(self, config: dict, executor_id: str) -> dict:
        """
        Exclude a specific executor from the pipeline configuration.
        
        Args:
            config: Pipeline configuration
            executor_id: ID of executor to exclude
            
        Returns:
            Modified configuration with executor removed
        """
        try:
            # Get pipeline definition
            pipeline_def = config.get('pipeline', config)
            
            # Remove executor from executors list
            if 'executors' in pipeline_def:
                executors = pipeline_def['executors']
                pipeline_def['executors'] = [
                    ex for ex in executors 
                    if ex.get('id') != executor_id
                ]
                logger.info(f"{self.name} removed executor {executor_id} from pipeline")
            
            # Remove executor from execution_sequence if present
            if 'execution_sequence' in pipeline_def:
                sequence = pipeline_def['execution_sequence']
                if executor_id in sequence:
                    pipeline_def['execution_sequence'] = [
                        ex_id for ex_id in sequence 
                        if ex_id != executor_id
                    ]
                    logger.info(f"{self.name} removed {executor_id} from execution_sequence")
            
            # Remove executor from edges if present
            if 'edges' in pipeline_def:
                edges = pipeline_def['edges']
                pipeline_def['edges'] = [
                    edge for edge in edges
                    if edge.get('from') != executor_id and edge.get('to') != executor_id
                ]
                logger.info(f"{self.name} removed edges involving {executor_id}")
            
            return config
            
        except Exception as e:
            logger.error(f"{self.name} error excluding executor: {e}")
            return config
    
    def _get_pipeline(self, pipeline_id: str) -> Optional[dict]:
        """Get pipeline configuration from Cosmos DB"""
        try:
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_PIPELINES)
            
            pipeline = container.read_item(item=pipeline_id, partition_key=pipeline_id)
            return pipeline
            
        except Exception as e:
            logger.error(f"{self.name} error reading pipeline {pipeline_id}: {e}")
            return None
    
    def _update_execution_status(self, execution_id: str, status: str, error: Optional[str] = None):
        """Update execution status in Cosmos DB"""
        try:
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_VAULT_EXECUTIONS)
            
            # Read current execution
            execution = container.read_item(item=execution_id, partition_key=execution_id)
            
            # Update status
            execution["status"] = status
            if error:
                execution["error"] = error
            
            # Update in Cosmos DB
            container.upsert_item(execution)
            
            logger.debug(f"{self.name} updated execution {execution_id} status to {status}")
            
        except Exception as e:
            logger.error(f"{self.name} error updating execution status: {e}")
    
    def _save_execution_output(self, execution_id: str, result: PipelineResult):
        """Save execution output to Cosmos DB"""
        try:
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_VAULT_EXECUTIONS)
            
            # Read current execution
            execution = container.read_item(item=execution_id, partition_key=execution_id)
            
            # Save output
            if result.content is not None:
                if isinstance(result.content, list):
                    execution["content"] = [make_safe_json(c) for c in result.content]
                else:
                    execution["content"] = make_safe_json(result.content)
            
            # Update in Cosmos DB
            container.upsert_item(execution)
            
            logger.debug(f"{self.name} saved output for execution {execution_id}")
        
        except Exception as e:
            logger.error(f"{self.name} error saving execution output: {e}")
            raise e
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"{self.name} received signal {signum}")
        self.stop_event.set()
