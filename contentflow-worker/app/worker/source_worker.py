"""
Input source worker for loading and discovering content.

This module implements the InputSourceWorker that:
- Continuously runs with per-executor polling intervals
- Polls Cosmos DB for pipelines associated with vaults
- Uses distributed locking to prevent concurrent execution by multiple workers
- Identifies and executes input executors from enabled pipelines
- Creates content processing tasks for discovered content
- Sends tasks to the processing queue
"""
import asyncio
import logging
import multiprocessing as mp
import signal
import sys
import time
import traceback
import uuid
import yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import AsyncGenerator, Optional, List, Dict, Any

# # Add contentflow-lib to path
# lib_path = Path(__file__).parent.parent / "contentflow-lib"
# if lib_path.exists():
#     sys.path.insert(0, str(lib_path))

from azure.identity import ChainedTokenCredential
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosResourceExistsError

from contentflow.executors import BaseExecutor, InputExecutor
from contentflow.executors.executor_config import ExecutorInstanceConfig
from contentflow.models import Content
from contentflow.executors import ExecutorRegistry
from contentflow.utils import get_azure_credential, make_safe_json

from app.models import ContentProcessingTask, TaskPriority
from app.queue_client import TaskQueueClient
from app.settings import WorkerSettings

logger = logging.getLogger("contentflow.worker.source_worker")

class InputSourceWorker:
    """
    Worker process for loading content from input sources.
    
    This worker:
    1. Continuously runs with a scheduler that tracks next execution time per pipeline
    2. Uses per-executor polling intervals from executor settings
    3. Implements distributed locking via Cosmos DB to prevent concurrent execution
    4. Polls Cosmos DB for pipelines associated with vaults (enabled pipelines)
    5. Parses pipeline configuration to find input executors
    6. Executes input executors to discover content
    7. Creates ContentProcessingTask for each discovered content item
    8. Sends processing tasks to the queue
    """
    
    def __init__(
        self,
        worker_id: int,
        settings: WorkerSettings,
        stop_event
    ):
        """
        Initialize the input source worker.
        
        Args:
            worker_id: Unique worker identifier
            settings: Worker configuration settings
            stop_event: Multiprocessing event for graceful shutdown
        """
        self.worker_id = worker_id
        self.settings = settings
        self.stop_event = stop_event
        self.name = f"InputSourceWorker-{worker_id}"
        
        # Azure clients (initialized in run)
        self.credential: Optional[ChainedTokenCredential] = None
        self.queue_client: Optional[TaskQueueClient] = None
        self.cosmos_client: Optional[CosmosClient] = None
        self.executor_registry: Optional[ExecutorRegistry] = None
        
        # Scheduling: Track next execution time for each pipeline
        # Key: pipeline_id, Value: next_execution_time (datetime)
        self.pipeline_schedule: Dict[str, datetime] = {}
        
        # Map of pipeline to vault
        # Key: pipeline_id, Value: vault_id
        self.pipeline_vaults: Dict[str, str] = {}
        
        # Track polling intervals per pipeline
        # Key: pipeline_id, Value: polling_interval_seconds
        self.pipeline_intervals: Dict[str, int] = {}
        
        logger.info(f"Initialized {self.name}")
    
    def run(self):
        """Main worker loop with continuous scheduling"""
        logger.info(f"{self.name} starting...")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Initialize Azure clients
            self._initialize_clients()
            
            # Main continuous scheduling loop
            while not self.stop_event.is_set():
                try:
                    # Refresh pipeline list and schedule
                    self._refresh_pipeline_schedule()
                    
                    # Process pipelines that are ready for execution
                    asyncio.run(self._process_ready_pipelines())
                    
                    # Sleep briefly between schedule checks
                    if not self.stop_event.is_set():
                        time.sleep(self.settings.SCHEDULER_SLEEP_INTERVAL_SECONDS)
                        
                except Exception as e:
                    logger.error(f"{self.name} error in scheduling loop: {e}")
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
        
        self.executor_registry = ExecutorRegistry.load_default_catalog()  # Load default executors
        
        logger.info(f"{self.name} clients initialized")
    
    def _refresh_pipeline_schedule(self):
        """Refresh the list of pipelines and their schedules"""
        try:
            # Get pipelines with vaults
            vault_pipelines = self._get_pipelines_with_vaults()
            
            current_time = datetime.now(timezone.utc)
            
            # Update schedule for new or modified pipelines
            for vault_id, pipeline_id in vault_pipelines:
                
                # If pipeline is new to schedule, add it
                if pipeline_id not in self.pipeline_schedule:
                    # Get polling interval from executor settings
                    interval = self._get_pipeline_polling_interval(pipeline_id)
                    self.pipeline_intervals[pipeline_id] = interval
                    
                    # Schedule for immediate execution (first run)
                    self.pipeline_schedule[pipeline_id] = current_time
                    self.pipeline_vaults[pipeline_id] = vault_id
                    
                    logger.info(
                        f"{self.name} added pipeline {pipeline_id} "
                        f"with {interval}s polling interval"
                    )
            
            # Remove pipelines that are no longer active
            active_pipeline_ids = set([pipeline_id for _, pipeline_id in vault_pipelines])
            inactive_pipeline_ids = set(self.pipeline_schedule.keys()) - active_pipeline_ids
            
            for inactive_id in inactive_pipeline_ids:
                del self.pipeline_schedule[inactive_id]
                del self.pipeline_intervals[inactive_id]
                del self.pipeline_vaults[inactive_id]
                logger.info(f"{self.name} removed inactive pipeline {inactive_id}")
                
        except Exception as e:
            logger.error(f"{self.name} error refreshing pipeline schedule: {e}")
            logger.error(traceback.format_exc())
    
    def _get_pipeline_polling_interval(self, pipeline_id: str) -> int:
        """Extract polling interval from pipeline's input executor settings"""
        try:
            pipeline = self._get_pipeline_by_id(pipeline_id)
            
            # Find input executor
            input_executor_config = self._find_input_executor(pipeline)
            
            if not input_executor_config:
                return self.settings.DEFAULT_POLLING_INTERVAL_SECONDS
            
            # Check for polling_interval_seconds in executor settings
            settings = input_executor_config.get('settings', {})
            interval = settings.get('polling_interval_seconds')
            
            if interval and isinstance(interval, (int, float)) and interval > 0:
                return int(interval)
            
            # Default fallback
            return self.settings.DEFAULT_POLLING_INTERVAL_SECONDS
            
        except Exception as e:
            logger.error(f"{self.name} error getting polling interval: {e}")
            return self.settings.DEFAULT_POLLING_INTERVAL_SECONDS
    
    async def _process_ready_pipelines(self):
        """Process pipelines that are ready for execution"""
        current_time = datetime.now(timezone.utc)
        
        for pipeline_id, next_execution_time in list(self.pipeline_schedule.items()):
            if self.stop_event.is_set():
                break
            
            # Check if pipeline is ready to execute
            if current_time >= next_execution_time:
                try:
                    # Try to acquire lock for this pipeline
                    if self._acquire_lock(pipeline_id):
                        try:
                            # Get pipeline details
                            pipeline = self._get_pipeline_by_id(pipeline_id)
                            
                            if pipeline:
                                # Process the pipeline
                                await self._process_pipeline(pipeline)
                                
                                # Update next execution time
                                interval = self.pipeline_intervals.get(
                                    pipeline_id,
                                    self.settings.DEFAULT_POLLING_INTERVAL_SECONDS
                                )
                                next_time = current_time + timedelta(seconds=interval)
                                self.pipeline_schedule[pipeline_id] = next_time
                                
                                logger.debug(
                                    f"{self.name} scheduled next execution for "
                                    f"{pipeline.get('name')} at {next_time.isoformat()}"
                                )
                        finally:
                            # Always release lock
                            self._release_lock(pipeline_id)
                    else:
                        logger.debug(
                            f"{self.name} could not acquire lock for pipeline {pipeline_id}, "
                            "another worker is processing it"
                        )
                        
                except Exception as e:
                    logger.error(f"{self.name} error processing pipeline {pipeline_id}: {e}")
                    logger.error(traceback.format_exc())
    
    def _acquire_lock(self, pipeline_id: str) -> bool:
        """
        Attempt to acquire a distributed lock for a pipeline.
        
        Uses Cosmos DB for distributed locking with TTL for auto-cleanup.
        
        Args:
            pipeline_id: Pipeline identifier
            
        Returns:
            True if lock acquired, False otherwise
        """
        try:
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_VAULT_EXECUTION_LOCKS)
            
            lock_id = f"pipeline_{pipeline_id}_lock"
            current_time = datetime.now(timezone.utc)
            value_id = self.pipeline_vaults.get(pipeline_id, None)
            
            lock_doc = {
                "id": lock_id,
                "pipeline_id": pipeline_id,
                "vault_id": value_id,
                "worker_id": self.name,
                "locked_at": current_time.isoformat(),
                "ttl": self.settings.LOCK_TTL_SECONDS  # Auto-expire after TTL
            }
            
            try:
                # Try to create lock document (will fail if already exists)
                container.create_item(lock_doc)
                logger.debug(f"{self.name} acquired lock for pipeline {pipeline_id}")
                return True
                
            except CosmosResourceExistsError:
                # Lock already exists, check if it's stale
                try:
                    existing_lock = container.read_item(
                        item=lock_id,
                        partition_key=lock_id
                    )
                    
                    locked_at = datetime.fromisoformat(existing_lock['locked_at'])
                    age_seconds = (current_time - locked_at).total_seconds()
                    
                    # If lock is older than TTL, it should have been cleaned up
                    # but in case TTL cleanup is delayed, we can force delete
                    if age_seconds > self.settings.LOCK_TTL_SECONDS:
                        logger.warning(
                            f"{self.name} found stale lock for pipeline {pipeline_id}, "
                            f"age: {age_seconds}s"
                        )
                        container.delete_item(item=lock_id, partition_key=lock_id)
                        # Try to acquire again
                        return self._acquire_lock(pipeline_id)
                    
                    logger.debug(
                        f"{self.name} pipeline {pipeline_id} locked by "
                        f"{existing_lock.get('worker_id')}"
                    )
                    return False
                    
                except CosmosResourceNotFoundError:
                    # Lock was deleted between our attempts, try again
                    return self._acquire_lock(pipeline_id)
                    
        except Exception as e:
            logger.error(f"{self.name} error acquiring lock: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _release_lock(self, pipeline_id: str):
        """
        Release a distributed lock for a pipeline.
        
        Args:
            pipeline_id: Pipeline identifier
        """
        try:
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_VAULT_EXECUTION_LOCKS)
            
            lock_id = f"pipeline_{pipeline_id}_lock"
            
            try:
                # Verify we own the lock before deleting
                existing_lock = container.read_item(
                    item=lock_id,
                    partition_key=lock_id
                )
                
                if existing_lock.get('worker_id') == self.name:
                    container.delete_item(item=lock_id, partition_key=lock_id)
                    logger.debug(f"{self.name} released lock for pipeline {pipeline_id}")
                else:
                    logger.warning(
                        f"{self.name} attempted to release lock owned by "
                        f"{existing_lock.get('worker_id')}"
                    )
                    
            except CosmosResourceNotFoundError:
                # Lock already released or expired
                logger.debug(f"{self.name} lock for pipeline {pipeline_id} already released")
                
        except Exception as e:
            logger.error(f"{self.name} error releasing lock: {e}")
            logger.error(traceback.format_exc())
    
    def _get_pipeline_by_id(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline by ID from Cosmos DB"""
        try:
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_PIPELINES)
            
            pipeline = container.read_item(
                item=pipeline_id,
                partition_key=pipeline_id
            )
            
            return pipeline
            
        except CosmosResourceNotFoundError:
            logger.warning(f"{self.name} pipeline {pipeline_id} not found")
            return None
        except Exception as e:
            logger.error(f"{self.name} error getting pipeline: {e}")
            return None
    
    def _get_pipelines_with_vaults(self) -> List[tuple[str,str]]:
        """Get enabled pipelines that have associated vaults"""
        try:
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            
            # Query vaults container for enabled vaults
            vaults_container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_VAULTS)
            vault_pipelines = list(vaults_container.query_items(
                query="SELECT DISTINCT c.id, c.pipeline_id FROM c WHERE c.enabled = true",
                enable_cross_partition_query=True
            ))
            return [(vp["id"], vp["pipeline_id"]) for vp in vault_pipelines]
            
        except Exception as e:
            logger.error(f"{self.name} error querying pipelines: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def _process_pipeline(self, pipeline: Dict[str, Any]):
        """Process a single pipeline"""
        pipeline_id = pipeline.get('id')
        pipeline_name = pipeline.get('name')
        
        logger.info(f"{self.name}: processing pipeline '{pipeline_name}'")
        
        try:
            # Parse pipeline YAML to find input executor
            input_executor_config = self._find_input_executor(pipeline)
            
            if not input_executor_config:
                logger.warning(f"{self.name}: no input executor found in pipeline {pipeline_name}")
                return
            
            executor_id = input_executor_config.get('id')
            logger.debug(f"{self.name}: found input executor: {executor_id}")
            
            # Retrieve checkpoint before execution
            checkpoint_timestamp = self._get_checkpoint(pipeline_id, executor_id)
            if checkpoint_timestamp:
                logger.debug(f"{self.name}: resuming from checkpoint {checkpoint_timestamp.isoformat()}")
            else:
                logger.debug(f"{self.name}: no checkpoint found, starting fresh")
            
            # Track the latest timestamp for checkpoint
            latest_timestamp = checkpoint_timestamp
            execution_start_time = datetime.now(timezone.utc)
            tasks_created = 0
            
            # Execute input executor to discover content
            async for content_items in self._execute_input_executor(pipeline_id=pipeline_id, 
                                                                    pipeline_name=pipeline_name, 
                                                                    executor_config=input_executor_config, 
                                                                    checkpoint_timestamp=checkpoint_timestamp):
                if content_items is None:
                    logger.debug(f"{self.name}: no content discovered from pipeline {pipeline_name}")
                    self._create_no_content_discovered_execution_record(pipeline_id, pipeline_name)
                    break
            
                logger.debug(f"{self.name}: discovered {len(content_items)} content items")
                
                # Skip if no content, this might be the case if content is retrieved from the source but filtered out by the input executor
                if len(content_items) == 0:
                    continue
                
                # Create processing tasks for each content item
                try:
                    self._create_processing_task(pipeline, content_items, executor_id)
                    logger.debug(f"{self.name}: queued processing task for content with {len(content_items)} items")
                    
                    tasks_created += 1
                except Exception as e:
                    logger.error(f"{self.name}: failed to create processing task: {e}")
                    logger.exception(e)
                    
                if self.stop_event.is_set():
                    break
            
            logger.info(f"{self.name}: created {tasks_created} processing tasks for pipeline {pipeline_name}")
            
            # Save checkpoint after successful execution
            # Use start time as the checkpoint for next execution
            latest_timestamp = execution_start_time
            self._save_checkpoint(pipeline_id, executor_id, latest_timestamp)
            
        except Exception as e:
            logger.error(f"{self.name}: error processing pipeline {pipeline_name}: {e}")
            logger.exception(e)
    
    def _find_input_executor(self, pipeline: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the input executor in the pipeline configuration"""
        try:
            yaml_content = pipeline.get('yaml')
            if not yaml_content:
                return None
            
            # Parse YAML
            config = yaml.safe_load(yaml_content)
            if not config:
                return None
            
            # Get pipeline definition
            pipeline_def = config.get('pipeline', config)
            executors = pipeline_def.get('executors', [])
            
            # find the executor with input type by cross checking the executor-registry
            for executor in executors:
                executor_type = executor.get('type', '').lower()
                executor_info = self.executor_registry.get_executor_info(executor_type)
                if not executor_info:
                    continue
                
                if executor_info.category == 'input':
                    # Will always return the first input executor found
                    logger.debug(f"{self.name} found input executor: {executor.get('id')}")
                    return executor
            
            return None
            
        except Exception as e:
            logger.error(f"{self.name} error parsing pipeline YAML: {e}")
            return None
    
    async def _execute_input_executor(self, 
                                      pipeline_id: str, 
                                      pipeline_name:str, 
                                      executor_config: Dict[str, Any], 
                                      checkpoint_timestamp: Optional[datetime] = None
                                      ) -> AsyncGenerator[List[Content], None]:
        
        """Execute an input executor to discover content"""
        executor_type = executor_config.get('type')
        executor_id = executor_config.get('id')
        settings = executor_config.get('settings', {})
        
        logger.debug(f"{self.name}: executing input executor {executor_id} (type: {executor_type}) with checkpoint {checkpoint_timestamp}")
        
        try:
            # Create executor instance
            executor = self._create_executor(executor_type, executor_id, settings)
            
            if not executor or not isinstance(executor, InputExecutor):
                logger.error(f"{self.name}: failed to create executor of type {executor_type}. Returned {executor} which is not an InputExecutor.")
                # create an execution record with failed status
                self._create_failed_execution_record(pipeline_id=pipeline_id, 
                                                     pipeline_name=pipeline_name, 
                                                     error_message=f"{self.name}: failed to create executor of type {executor_type}, got {executor} which is not an InputExecutor.")
                return
            
            # Execute to discover content
            async for batch, has_more in executor.crawl(checkpoint_timestamp=checkpoint_timestamp):
                # Ensure we have a list
                if batch is not None:
                    yield batch
                
                if batch is None and has_more is False:
                    # No more items
                    yield None
        
        except Exception as e:
            logger.error(f"{self.name}: error executing input executor: {e}")
            logger.exception(e)
            # Don't save checkpoint on error - will retry from last successful checkpoint
            # create an execution record with failed status
            self._create_failed_execution_record(pipeline_id=pipeline_id, 
                                                 pipeline_name=pipeline_name, 
                                                 error_message=f"{self.name}: {str(e)}. {traceback.format_exc()}")
            raise
    
    def _create_executor(self, executor_type: str, executor_id: str, settings: Dict[str, Any]) -> BaseExecutor:
        """Create an executor instance"""
        try:
            # Create instance config
            instance_config = ExecutorInstanceConfig(
                id=executor_id,
                type=executor_type,
                settings=settings
            )
            
            # Create executor using registry (dynamic loading)
            executor = self.executor_registry.create_executor_instance(
                executor_id=executor_type,
                instance_config=instance_config
            )
            
            return executor
            
        except Exception as e:
            logger.error(f"{self.name} error creating executor: {e}")
            logger.exception(e)
            raise
    
    def _create_execution_id(self) -> str:
        """Generate a unique execution ID"""
        return f"exec_{uuid.uuid4().hex[:12]}"
    
    def _create_processing_task(
        self,
        pipeline: Dict[str, Any],
        content: List[Content],
        executed_input_executor: str
    ):
        """Create and queue a content processing task"""
        # Create execution record in Cosmos DB
        execution_id = self._create_execution_id()
        vault_id = self.pipeline_vaults.get(pipeline['id'], None)
        
        # Create processing task
        processing_task = ContentProcessingTask(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            priority=TaskPriority.NORMAL,
            pipeline_id=pipeline['id'],
            pipeline_name=pipeline['name'],
            vault_id=vault_id,
            execution_id=execution_id,
            content=content,
            executed_input_executor=executed_input_executor,  # Mark which executor was already run
            max_retries=self.settings.MAX_TASK_RETRIES
        )
        
        try:
            # Create execution record
            self._create_execution_record(execution_id, processing_task)
            
            try:
                # Send to queue
                self.queue_client.send_content_processing_task(processing_task)
            except Exception as e:
                logger.error(f"{self.name} error sending processing task to queue: {e}")
                # Mark execution as failed in Cosmos DB
                self._mark_execution_failed(execution_id, str(e))
                raise
            
            logger.debug(f"{self.name} created processing task for {len(content)} content items")
        except Exception as e:
            logger.error(f"{self.name} error execution record or queue creating processing task: {e}")
            raise
        
    def _create_execution_record(
        self,
        execution_id: str,
        task: ContentProcessingTask
    ):
        """Create execution record in Cosmos DB"""
        try:
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_VAULT_EXECUTIONS)
            
            vault_id = self.pipeline_vaults.get(task.pipeline_id, None)
            
            execution = {
                "id": execution_id,
                "pipeline_id": task.pipeline_id,
                "pipeline_name": task.pipeline_name,
                "vault_id": vault_id,
                "status": "pending",
                "status_message": "Task queued for processing with input content of size " + str(len(task.content)),
                "task_id": task.task_id,
                "source_worker_id": self.name,
                "content": [make_safe_json(c) for c in task.content],
                "number_of_items": len(task.content) if task.content else 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": self.name,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "started_at": None,
                "completed_at": None,
                "error": None,
                "executor_outputs": {},
                "events": []
            }
            
            container.create_item(execution)
            logger.debug(f"{self.name} created execution record {execution_id}")
        except Exception as e:
            logger.error(f"{self.name} error creating execution record: {e}")
            raise
    
    def _create_no_content_discovered_execution_record(self, pipeline_id: str, pipeline_name: str):
        """Create an execution record for no content discovered"""
        try:
            execution_id = self._create_execution_id()
            
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_VAULT_EXECUTIONS)
            
            vault_id = self.pipeline_vaults.get(pipeline_id, None)
            
            execution = {
                "id": execution_id,
                "pipeline_id": pipeline_id,
                "pipeline_name": pipeline_name,
                "vault_id": vault_id,
                "status": "completed",
                "status_message": "No content discovered during execution",
                "task_id": None,
                "source_worker_id": self.name,
                "error": None,
                "content": None,
                "number_of_items": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": self.name,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "started_at": None,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "executor_outputs": {},
                "events": []
            }
            
            container.create_item(execution)
            logger.debug(f"{self.name} created no-content-discovered execution record {execution_id}")
        except Exception as e:
            logger.error(f"{self.name} error creating no-content-discovered execution record: {e}")
            raise
    
    def _create_failed_execution_record(self, pipeline_id: str, pipeline_name: str, error_message: str):
        """Create a failed execution record in Cosmos DB"""
        try:
            execution_id = self._create_execution_id()
            
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_VAULT_EXECUTIONS)
            
            vault_id = self.pipeline_vaults.get(pipeline_id, None)
            
            execution = {
                "id": execution_id,
                "pipeline_id": pipeline_id,
                "pipeline_name": pipeline_name,
                "vault_id": vault_id,
                "status": "failed",
                "status_message": "Execution failed. View error for details.",
                "task_id": None,
                "source_worker_id": self.name,
                "content": None,
                "number_of_items": None,
                "error": error_message,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": self.name,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "started_at": None,
                "completed_at": None,
                "executor_outputs": {},
                "events": []
            }
            
            container.create_item(execution)
            logger.debug(f"{self.name} created failed execution record {execution_id}")
        except Exception as e:
            logger.error(f"{self.name} error creating failed execution record: {e}")
            raise
        
    def _mark_execution_failed(self, execution_id: str, error_message: str):
        """Mark an execution as failed in Cosmos DB"""
        try:
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_VAULT_EXECUTIONS)
            
            # Read existing execution
            execution = container.read_item(
                item=execution_id,
                partition_key=execution_id
            )
            
            # Update status and error message
            execution['status'] = 'failed'
            execution['status_message'] = "Execution failed. View error for details."
            execution['error'] = error_message
            execution['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            container.upsert_item(body=execution)
            logger.debug(f"{self.name} marked execution {execution_id} as failed")
            
        except Exception as e:
            logger.error(f"{self.name} error marking execution as failed: {e}")
    
    def _get_checkpoint(self, pipeline_id: str, executor_id: str) -> Optional[datetime]:
        """
        Retrieve the last checkpoint timestamp for a pipeline's input executor.
        
        Args:
            pipeline_id: Pipeline identifier
            executor_id: Executor identifier
            
        Returns:
            Last checkpoint timestamp, or None if no checkpoint exists
        """
        try:
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_CRAWL_CHECKPOINTS)
            
            checkpoint_id = f"{pipeline_id}_{executor_id}"
            
            try:
                checkpoint_doc = container.read_item(
                    item=checkpoint_id,
                    partition_key=checkpoint_id
                )
                
                timestamp_str = checkpoint_doc.get('checkpoint_timestamp')
                if timestamp_str:
                    return datetime.fromisoformat(timestamp_str)
                
                return None
                
            except CosmosResourceNotFoundError:
                # No checkpoint exists yet
                logger.debug(f"{self.name} no checkpoint found for {pipeline_id}/{executor_id}")
                return None
                
        except Exception as e:
            logger.error(f"{self.name} error retrieving checkpoint: {e}")
            logger.error(traceback.format_exc())
            # Return None to start fresh on error
            return None
    
    def _save_checkpoint(self, pipeline_id: str, executor_id: str, checkpoint_timestamp: datetime):
        """
        Save a checkpoint timestamp for a pipeline's input executor.
        
        Args:
            pipeline_id: Pipeline identifier
            executor_id: Executor identifier
            checkpoint_timestamp: Timestamp to save as checkpoint
        """
        try:
            database = self.cosmos_client.get_database_client(self.settings.COSMOS_DB_NAME)
            container = database.get_container_client(self.settings.COSMOS_DB_CONTAINER_CRAWL_CHECKPOINTS)
            
            vault_id = self.pipeline_vaults.get(pipeline_id, None)
            checkpoint_id = f"{pipeline_id}_{executor_id}"
            
            checkpoint_doc = {
                "id": checkpoint_id,
                "pipeline_id": pipeline_id,
                "vault_id": vault_id,
                "executor_id": executor_id,
                "checkpoint_timestamp": checkpoint_timestamp.isoformat(),
                "worker_id": self.name
            }
            
            # Upsert the checkpoint (create or update)
            container.upsert_item(checkpoint_doc)
            logger.debug(f"{self.name} saved checkpoint for {pipeline_id}/{executor_id}")
            
        except Exception as e:
            logger.error(f"{self.name} error saving checkpoint: {e}")
            logger.error(traceback.format_exc())
            # Log error but don't fail the execution
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"{self.name} received signal {signum}")
        self.stop_event.set()
