"""
Workflow factory for creating workflows from pipeline configurations.

This module provides the WorkflowFactory class that can create Agent Framework
workflows from existing doc-proc-lib pipeline configurations, enabling a smooth
migration path from pipeline-based to workflow-based orchestration.
"""

import logging
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from agent_framework import Workflow, WorkflowBuilder

# Import from doc-proc-lib
try:
    import sys
    import os
    doc_proc_lib_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib")
    if os.path.exists(doc_proc_lib_path):
        sys.path.insert(0, doc_proc_lib_path)
    
    from doc.proc.step.step_registry import StepRegistry
    from doc.proc.step.step_config import StepConfig, StepInstanceConfig
    from doc.proc.service.service_registry import ServiceRegistry
    from doc.proc.service.service_config import ServiceConfig, ServiceInstanceConfig
    from doc.proc.source.source_registry import SourceRegistry
    from doc.proc.source.source_config import SourceConfig
    from doc.proc.source.source_instance_config import SourceInstanceConfig
    from doc.proc.pipeline.pipeline_config import PipelineConfig
    from doc.proc.step.step_instance_loader import create_step_instance
    from doc.proc.service.service_instance_loader import create_service_instance
    from doc.proc.source.source_instance_loader import create_source_instance
except ImportError as e:
    raise ImportError(
        f"Failed to import doc-proc-lib modules. Ensure doc-proc-lib is installed: {e}"
    )

from doc_proc_workflow.executors.step_adapter import StepExecutorAdapter

logger = logging.getLogger("doc_proc_workflow.factory")


class WorkflowFactory:
    """
    Factory for creating Agent Framework workflows from pipeline configurations.
    
    This factory provides methods to:
    - Load pipeline configurations from YAML files
    - Create workflows from pipeline definitions
    - Manage step, service, and source registries
    - Convert pipeline execution sequences to workflow graphs
    
    Example:
        ```python
        # Create factory from configuration files
        factory = WorkflowFactory.from_config_files(
            step_catalog_path="step_catalog.yaml",
            service_catalog_path="service_catalog.yaml",
            pipeline_config_path="pipeline_config.yaml"
        )
        
        # Create workflow from pipeline name
        workflow = await factory.create_workflow("my_pipeline")
        
        # Execute workflow
        result = await workflow.run(input_data)
        ```
    """
    
    def __init__(
        self,
        step_registry: Optional[StepRegistry] = None,
        service_registry: Optional[ServiceRegistry] = None,
        source_registry: Optional[SourceRegistry] = None
    ):
        """
        Initialize the workflow factory.
        
        Args:
            step_registry: Registry of available step definitions
            service_registry: Registry of available service definitions
            source_registry: Registry of available source definitions
        """
        self.step_registry = step_registry or StepRegistry()
        self.service_registry = service_registry or ServiceRegistry()
        self.source_registry = source_registry or SourceRegistry()
        
        # Cache for loaded configurations
        self._pipeline_configs: Dict[str, PipelineConfig] = {}
        self._service_instances: Dict[str, Any] = {}
        self._source_instances: Dict[str, Any] = {}
        
        logger.info("WorkflowFactory initialized")
    
    @classmethod
    def from_config_files(
        cls,
        step_catalog_path: Union[str, Path],
        service_catalog_path: Union[str, Path],
        pipeline_config_path: Optional[Union[str, Path]] = None,
        source_catalog_path: Optional[Union[str, Path]] = None
    ) -> "WorkflowFactory":
        """
        Create a WorkflowFactory from configuration files.
        
        Args:
            step_catalog_path: Path to step catalog YAML file
            service_catalog_path: Path to service catalog YAML file
            pipeline_config_path: Optional path to pipeline config YAML file
            source_catalog_path: Optional path to source catalog YAML file
            
        Returns:
            Configured WorkflowFactory instance
        """
        logger.info("Creating WorkflowFactory from configuration files")
        
        # Load step catalog
        step_registry = StepRegistry()
        with open(step_catalog_path, 'r') as f:
            step_catalog_data = yaml.safe_load(f)
            if 'step_catalog' in step_catalog_data:
                for step_def in step_catalog_data['step_catalog']:
                    step_config = StepConfig(**step_def)
                    step_registry.register(step_config)
        
        logger.info(f"Loaded {len(step_registry)} step definitions")
        
        # Load service catalog
        service_registry = ServiceRegistry()
        with open(service_catalog_path, 'r') as f:
            service_catalog_data = yaml.safe_load(f)
            if 'service_catalog' in service_catalog_data:
                for service_def in service_catalog_data['service_catalog']:
                    service_config = ServiceConfig(**service_def)
                    service_registry.register(service_config)
        
        logger.info(f"Loaded {len(service_registry)} service definitions")
        
        # Load source catalog if provided
        source_registry = SourceRegistry()
        if source_catalog_path:
            with open(source_catalog_path, 'r') as f:
                source_catalog_data = yaml.safe_load(f)
                if 'source_catalog' in source_catalog_data:
                    for source_def in source_catalog_data['source_catalog']:
                        source_config = SourceConfig(**source_def)
                        source_registry.register(source_config)
            
            logger.info(f"Loaded {len(source_registry)} source definitions")
        
        factory = cls(
            step_registry=step_registry,
            service_registry=service_registry,
            source_registry=source_registry
        )
        
        # Load pipeline configurations if provided
        if pipeline_config_path:
            factory._load_pipeline_configs(pipeline_config_path)
        
        return factory
    
    def _load_pipeline_configs(self, config_path: Union[str, Path]) -> None:
        """Load pipeline configurations from YAML file."""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Load service instances
        if 'service_instances' in config_data:
            for svc_instance in config_data['service_instances']:
                instance_config = ServiceInstanceConfig(**svc_instance)
                service_config = self.service_registry.get(instance_config.service_catalog_id)
                if service_config:
                    instance = create_service_instance(service_config, instance_config)
                    self._service_instances[instance_config.name] = instance
        
        logger.info(f"Loaded {len(self._service_instances)} service instances")
        
        # Load source instances
        if 'source_instances' in config_data:
            for src_instance in config_data['source_instances']:
                instance_config = SourceInstanceConfig(**src_instance)
                source_config = self.source_registry.get(instance_config.source_catalog_id)
                if source_config:
                    instance = create_source_instance(source_config, instance_config)
                    self._source_instances[instance_config.name] = instance
        
        logger.info(f"Loaded {len(self._source_instances)} source instances")
        
        # Load pipelines
        if 'pipelines' in config_data:
            for pipeline_def in config_data['pipelines']:
                pipeline_config = PipelineConfig(**pipeline_def)
                self._pipeline_configs[pipeline_config.name] = pipeline_config
        
        logger.info(f"Loaded {len(self._pipeline_configs)} pipeline configurations")
    
    async def create_workflow(
        self,
        pipeline_name: str,
        max_iterations: int = 100
    ) -> Workflow:
        """
        Create a workflow from a pipeline configuration.
        
        Args:
            pipeline_name: Name of the pipeline to convert
            max_iterations: Maximum workflow iterations
            
        Returns:
            Configured Agent Framework Workflow
            
        Raises:
            ValueError: If pipeline not found or configuration is invalid
        """
        if pipeline_name not in self._pipeline_configs:
            raise ValueError(f"Pipeline '{pipeline_name}' not found in configurations")
        
        pipeline_config = self._pipeline_configs[pipeline_name]
        
        logger.info(f"Creating workflow for pipeline '{pipeline_name}'")
        
        # Create step executor adapters
        executors = await self._create_executors(pipeline_config)
        
        # Build workflow graph from execution sequence
        workflow = self._build_workflow_graph(
            executors=executors,
            execution_sequence=pipeline_config.execution_sequence,
            max_iterations=max_iterations
        )
        
        logger.info(
            f"Created workflow '{pipeline_name}' with {len(executors)} executors"
        )
        
        return workflow
    
    async def _create_executors(
        self,
        pipeline_config: PipelineConfig
    ) -> Dict[str, StepExecutorAdapter]:
        """
        Create executor adapters from pipeline step instances.
        
        Args:
            pipeline_config: Pipeline configuration
            
        Returns:
            Dictionary mapping step instance names to executor adapters
        """
        executors = {}
        
        for step_instance_config in pipeline_config.step_instances:
            # Get step catalog definition
            step_config = self.step_registry.get(step_instance_config.step_catalog_id)
            if not step_config:
                logger.warning(
                    f"Step catalog '{step_instance_config.step_catalog_id}' not found, "
                    f"skipping step instance '{step_instance_config.name}'"
                )
                continue
            
            # Create step instance
            step_instance = create_step_instance(step_config, step_instance_config)
            
            # Wrap in executor adapter
            executor = StepExecutorAdapter(
                step_instance=step_instance,
                executor_id=step_instance_config.name,
                services=self._service_instances,
                sources=self._source_instances
            )
            
            executors[step_instance_config.name] = executor
            
            logger.debug(
                f"Created executor '{step_instance_config.name}' "
                f"for step '{step_config.id}'"
            )
        
        return executors
    
    def _build_workflow_graph(
        self,
        executors: Dict[str, StepExecutorAdapter],
        execution_sequence: List[str],
        max_iterations: int = 100
    ) -> Workflow:
        """
        Build a workflow graph from execution sequence.
        
        This creates a sequential workflow following the execution order
        defined in the pipeline configuration.
        
        Args:
            executors: Dictionary of executor adapters
            execution_sequence: Ordered list of step instance names
            max_iterations: Maximum workflow iterations
            
        Returns:
            Configured Workflow
        """
        if not execution_sequence:
            raise ValueError("Execution sequence cannot be empty")
        
        builder = WorkflowBuilder(max_iterations=max_iterations)
        
        # Set the first executor as start
        first_executor_name = execution_sequence[0]
        if first_executor_name not in executors:
            raise ValueError(f"Executor '{first_executor_name}' not found")
        
        first_executor = executors[first_executor_name]
        builder.set_start_executor(first_executor)
        
        # Add sequential edges
        for i in range(len(execution_sequence) - 1):
            current_name = execution_sequence[i]
            next_name = execution_sequence[i + 1]
            
            if current_name not in executors or next_name not in executors:
                logger.warning(
                    f"Skipping edge {current_name} -> {next_name}, "
                    f"executor not found"
                )
                continue
            
            current_executor = executors[current_name]
            next_executor = executors[next_name]
            
            builder.add_edge(current_executor, next_executor)
            
            logger.debug(f"Added edge: {current_name} -> {next_name}")
        
        # Build and return workflow
        workflow = builder.build()
        return workflow
    
    def get_pipeline_names(self) -> List[str]:
        """Get list of available pipeline names."""
        return list(self._pipeline_configs.keys())
    
    def get_service_names(self) -> List[str]:
        """Get list of loaded service instance names."""
        return list(self._service_instances.keys())
    
    def get_source_names(self) -> List[str]:
        """Get list of loaded source instance names."""
        return list(self._source_instances.keys())
