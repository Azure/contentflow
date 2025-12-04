"""
Pipeline factory for creating pipelines from configurations.

This module provides the PipelineFactory class that creates Agent Framework
pipelines with connector-based architecture, replacing the old service-based approach.

Supports both:
1. Legacy: Hardcoded executor types (EXECUTOR_TYPES dict)
2. Dynamic: Executor catalog with dynamic class loading (ExecutorRegistry)
"""

import logging
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from agent_framework import Workflow, WorkflowBuilder

from ..executors import (
    ExecutorRegistry,
    ExecutorInstanceConfig,
    ContentRetrieverExecutor,
    # CustomAIPromptExecutor,
    # AISearchIndexWriterExecutor,
    PassThroughExecutor,
    AzureDocumentIntelligenceExtractorExecutor,
)

logger = logging.getLogger("doc_proc_workflow.factory")


# Legacy executor type registry (for backward compatibility)
EXECUTOR_TYPES = {
    "content_retriever": ContentRetrieverExecutor,
    # "custom_ai_prompt": CustomAIPromptExecutor,
    # "ai_search_index_writer": AISearchIndexWriterExecutor,
    "pass_through_executor": PassThroughExecutor,
    "azure_document_intelligence_extractor": AzureDocumentIntelligenceExtractorExecutor,
}

class PipelineFactory:
    """
    Factory for creating Agent Framework pipelines with connectors.
    
    This factory provides methods to:
    - Load connector and pipeline configurations from YAML
    - Create pipelines from configurations
    - Manage connector registry
    - Build pipeline graphs from executor sequences or edges
    - Support both legacy (hardcoded) and dynamic (catalog) executor loading
    
    Example (Legacy - hardcoded executors):
        ```python
        # Create factory from configuration
        factory = PipelineFactory.from_config_file("pipeline_config.yaml")
        
        # Create pipeline
        pipeline = await factory.create_pipeline("document_processing")
        ```
    
    Example (Dynamic - executor catalog):
        ```python
        # Create factory with executor catalog
        factory = PipelineFactory.from_config_file(
            "pipeline_config.yaml",
            executor_catalog_path="executor_catalog.yaml"
        )
        
        # Create pipeline (executors loaded dynamically)
        pipeline = await factory.create_pipeline("document_processing")
        ```
    """
    
    def __init__(
        self,
        executor_registry: Optional[ExecutorRegistry] = None,
        use_dynamic_loading: bool = False
    ):
        """
        Initialize the workflow factory.
        
        Args:
            executor_registry: Registry of executor configurations (for dynamic loading)
            use_dynamic_loading: If True, use executor registry for dynamic loading.
                                If False, use legacy EXECUTOR_TYPES dict.
        """
        self.executor_registry = executor_registry or ExecutorRegistry()
        self.use_dynamic_loading = use_dynamic_loading
        
        # Cache for loaded configurations
        self._pipeline_configs: Dict[str, Dict[str, Any]] = {}
        
        logger.info(
            f"PipelineFactory initialized "
            f"(dynamic_loading={'enabled' if use_dynamic_loading else 'disabled'})"
        )
    
    @classmethod
    def from_config_file(
        cls,
        config_path: Union[str, Path],
        executor_catalog_path: Optional[Union[str, Path]] = None
    ) -> "PipelineFactory":
        """
        Create a PipelineFactory from a YAML configuration file.
        
        Configuration file format:
        ```yaml
        pipelines:
          - name: document_processing
            executors:
              - id: retrieve_content
                type: content_retriever
                settings:
                  container_name: documents
              
              - id: extract_content
                type: azure_document_intelligence_extractor
            
            execution_sequence: [retrieve_content, extract_content]
        ```
        
        Args:
            config_path: Path to YAML configuration file
            executor_catalog_path: Optional path to executor catalog YAML.
                                   If provided, enables dynamic executor loading.
            
        Returns:
            Configured PipelineFactory instance
        """
        logger.info(f"Creating PipelineFactory from config: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Determine if using dynamic loading
        use_dynamic = executor_catalog_path is not None
        
        # Create executor registry if catalog provided
        executor_registry = None
        if executor_catalog_path:
            executor_registry = ExecutorRegistry()
            executor_registry.load_from_yaml(str(executor_catalog_path))
            logger.info(
                f"Loaded executor catalog: {len(executor_registry)} executors"
            )
        
        factory = cls(
            executor_registry=executor_registry,
            use_dynamic_loading=use_dynamic
        )
        
        # Load pipeline workflow configurations
        if 'pipelines' in config_data:
            for pipeline_def in config_data['pipelines']:
                pipeline_name = pipeline_def['name']
                factory._pipeline_configs[pipeline_name] = pipeline_def
            
            logger.info(
                f"Loaded {len(factory._pipeline_configs)} pipeline configurations"
            )
        
        return factory
    
    async def create_pipeline(
        self,
        pipeline_name: str,
        max_iterations: int = 100
    ) -> Workflow:
        """
        Create a pipeline from configuration.
        
        Note: Returns an agent_framework.Workflow instance (implementation detail).
        The Workflow class from agent_framework is used internally to implement pipelines.
        
        Args:
            pipeline_name: Name of the pipeline to create
            max_iterations: Maximum pipeline iterations
            
        Returns:
            Configured Agent Framework Workflow (internal implementation)
            
        Raises:
            ValueError: If pipeline not found or configuration is invalid
        """
        if pipeline_name not in self._pipeline_configs:
            raise ValueError(
                f"Pipeline '{pipeline_name}' not found in configurations. "
                f"Available: {list(self._pipeline_configs.keys())}"
            )
        
        pipeline_config = self._pipeline_configs[pipeline_name]
        
        logger.info(f"Creating pipeline: {pipeline_name}")
        
        # Create executors
        executors = self._create_executors(pipeline_config)
        
        # Build pipeline graph using edges if provided, otherwise use execution_sequence
        if 'edges' in pipeline_config:
            pipeline = self._build_pipeline_from_edges(
                executors=executors,
                edges=pipeline_config['edges'],
                execution_sequence=pipeline_config.get('execution_sequence'),
                max_iterations=max_iterations
            )
        else:
            pipeline = self._build_pipeline_graph(
                executors=executors,
                execution_sequence=pipeline_config.get('execution_sequence', []),
                max_iterations=max_iterations
            )
        
        logger.info(
            f"Created pipeline '{pipeline_name}' with {len(executors)} executors"
        )
        
        return pipeline
    
    def _create_executors(
        self,
        pipeline_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create executor instances from workflow configuration.
        
        Supports both legacy (EXECUTOR_TYPES) and dynamic (ExecutorRegistry) loading.
        
        Args:
            pipeline_config: Workflow configuration dict
            
        Returns:
            Dict mapping executor IDs to executor instances
        """
        executors = {}
        
        for exec_def in pipeline_config.get('executors', []):
            executor_id = exec_def['id']
            executor_type = exec_def['type']
            
            # Use dynamic loading if enabled and executor registry has the type
            if self.use_dynamic_loading and executor_type in self.executor_registry:
                try:
                    # Create instance config
                    instance_config = ExecutorInstanceConfig(
                        id=executor_id,
                        type=executor_type,
                        settings=exec_def.get('settings', {}),
                        enabled=exec_def.get('enabled', True),
                        fail_on_error=exec_def.get('fail_on_error', False),
                        debug_mode=exec_def.get('debug_mode', False)
                    )
                    
                    # Create executor using registry (dynamic loading)
                    executor = self.executor_registry.create_executor_instance(
                        executor_id=executor_type,
                        instance_config=instance_config
                    )
                    
                    executors[executor_id] = executor
                    
                    logger.debug(
                        f"Created executor '{executor_id}' via dynamic loading "
                        f"(type: {executor_type})"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Failed to create executor '{executor_id}' "
                        f"via dynamic loading: {e}"
                    )
                    raise
            
            # Fall back to legacy EXECUTOR_TYPES
            elif executor_type in EXECUTOR_TYPES:
                try:
                    executor_class = EXECUTOR_TYPES[executor_type]
                    executor = executor_class(
                        id=executor_id,
                        settings=exec_def.get('settings', {}),
                        enabled=exec_def.get('enabled', True),
                        fail_on_error=exec_def.get('fail_on_error', False),
                        debug_mode=exec_def.get('debug_mode', False)
                    )

                    executors[executor_id] = executor
                    
                    logger.debug(
                        f"Created executor '{executor_id}' via legacy loading "
                        f"(type: {executor_type})"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Failed to create executor '{executor_id}' "
                        f"via legacy loading: {e}"
                    )
                    raise
            
            else:
                logger.warning(
                    f"Unknown executor type '{executor_type}' for '{executor_id}'. "
                    f"Available in registry: {list(self.executor_registry.list_executor_ids())}. "
                    f"Available in legacy: {list(EXECUTOR_TYPES.keys())}. "
                    f"Skipping executor."
                )
                continue
        
        return executors
    
    def _build_pipeline_graph(
        self,
        executors: Dict[str, Any],
        execution_sequence: List[str],
        max_iterations: int = 100
    ) -> Workflow:
        """
        Build a workflow graph from execution sequence.
        
        Args:
            executors: Dict of executor instances
            execution_sequence: Ordered list of executor IDs
            max_iterations: Maximum pipeline iterations
            
        Returns:
            Configured Pipeline (Workflow)
        """
        if not execution_sequence:
            raise ValueError("Execution sequence cannot be empty")
        
        builder = WorkflowBuilder(max_iterations=max_iterations)
        
        # Set the first executor as start
        first_executor_id = execution_sequence[0]
        if first_executor_id not in executors:
            raise ValueError(f"Executor '{first_executor_id}' not found")
        
        first_executor = executors[first_executor_id]
        builder.set_start_executor(first_executor)
        
        # Add sequential edges
        for i in range(len(execution_sequence) - 1):
            current_id = execution_sequence[i]
            next_id = execution_sequence[i + 1]
            
            if current_id not in executors or next_id not in executors:
                logger.warning(
                    f"Skipping edge {current_id} -> {next_id}, executor not found"
                )
                continue
            
            current_executor = executors[current_id]
            next_executor = executors[next_id]
            
            builder.add_edge(current_executor, next_executor)
            
            logger.debug(f"Added edge: {current_id} -> {next_id}")
        
        # Build and return pipeline
        pipeline = builder.build()
        return pipeline
    
    def _build_pipeline_from_edges(
        self,
        executors: Dict[str, Any],
        edges: List[Dict[str, Any]],
        execution_sequence: Optional[List[str]] = None,
        max_iterations: int = 100
    ) -> Workflow:
        """
        Build a workflow graph from edge configuration.
        
        Supports advanced patterns:
        - Sequential edges: from: step1, to: step2
        - Parallel fan-out: from: step1, to: [step2, step3, step4]
        - Join fan-in: from: [step1, step2], to: step3
        - Conditional routing: from: step1, to: [{target: step2, condition: "..."}]
        
        Args:
            executors: Dict of executor instances
            edges: List of edge definitions
            execution_sequence: Optional fallback sequence for start executor
            max_iterations: Maximum pipeline iterations
            
        Returns:
            Configured Pipeline (Workflow)
        """
        builder = WorkflowBuilder(max_iterations=max_iterations)
        
        # Determine start executor
        start_executor = self._determine_start_executor(executors, edges, execution_sequence)
        builder.set_start_executor(start_executor)
        
        logger.debug(f"Start executor: {start_executor}")
        
        # Process each edge
        for edge_def in edges:
            edge_type = edge_def.get('type', 'sequential')
            
            if edge_type == 'sequential':
                self._add_sequential_edge(builder, executors, edge_def)
            elif edge_type == 'parallel':
                self._add_parallel_edges(builder, executors, edge_def)
            elif edge_type == 'join':
                self._add_join_edges(builder, executors, edge_def)
            elif edge_type == 'conditional':
                self._add_conditional_edges(builder, executors, edge_def)
            else:
                logger.warning(f"Unknown edge type '{edge_type}', treating as sequential")
                self._add_sequential_edge(builder, executors, edge_def)
        
        # Build and return pipeline
        pipeline = builder.build()
        return pipeline
    
    def _determine_start_executor(
        self,
        executors: Dict[str, Any],
        edges: List[Dict[str, Any]],
        execution_sequence: Optional[List[str]] = None
    ) -> Any:
        """
        Determine the start executor from edges or execution sequence.
        
        Args:
            executors: Dict of executor instances
            edges: List of edge definitions
            execution_sequence: Optional execution sequence
            
        Returns:
            Start executor instance
        """
        # Try to find executor that is only a source (never a target)
        sources = set()
        targets = set()
        
        for edge_def in edges:
            from_exec = edge_def.get('from')
            to_exec = edge_def.get('to')
            
            # Handle from being a list or single value
            if isinstance(from_exec, list):
                sources.update(from_exec)
            elif from_exec:
                sources.add(from_exec)
            
            # Handle to being a list, dict list (conditional), or single value
            if isinstance(to_exec, list):
                if to_exec and isinstance(to_exec[0], dict):
                    # Conditional edges
                    targets.update(t.get('target') for t in to_exec if 'target' in t)
                else:
                    # Parallel edges
                    targets.update(to_exec)
            elif to_exec:
                targets.add(to_exec)
        
        # Start executor should be in sources but not in targets
        start_candidates = sources - targets
        
        if start_candidates:
            start_id = next(iter(start_candidates))
            logger.debug(f"Determined start executor from edges: {start_id}")
            return executors[start_id]
        elif execution_sequence:
            start_id = execution_sequence[0]
            logger.debug(f"Using first executor from execution_sequence: {start_id}")
            return executors[start_id]
        else:
            # Fallback to first executor in dict
            start_id = next(iter(executors.keys()))
            logger.warning(f"Could not determine start executor, using first: {start_id}")
            return executors[start_id]
    
    def _add_sequential_edge(
        self,
        builder: WorkflowBuilder,
        executors: Dict[str, Any],
        edge_def: Dict[str, Any]
    ) -> None:
        """Add a sequential edge: from -> to."""
        from_id = edge_def.get('from')
        to_id = edge_def.get('to')
        
        if not from_id or not to_id:
            logger.warning(f"Sequential edge missing from or to: {edge_def}")
            return
        
        if from_id not in executors or to_id not in executors:
            logger.warning(f"Sequential edge references unknown executor: {from_id} -> {to_id}")
            return
        
        from_executor = executors[from_id]
        to_executor = executors[to_id]
        
        builder.add_edge(from_executor, to_executor)
        logger.debug(f"Added sequential edge: {from_id} -> {to_id}")
    
    def _add_parallel_edges(
        self,
        builder: WorkflowBuilder,
        executors: Dict[str, Any],
        edge_def: Dict[str, Any]
    ) -> None:
        """Add parallel edges: from -> [to1, to2, to3] (fan-out)."""
        from_id = edge_def.get('from')
        to_ids = edge_def.get('to', [])
        
        if not from_id:
            logger.warning(f"Parallel edge missing from: {edge_def}")
            return
        
        if not isinstance(to_ids, list):
            to_ids = [to_ids]
        
        if from_id not in executors:
            logger.warning(f"Parallel edge references unknown source executor: {from_id}")
            return
        
        from_executor = executors[from_id]
        
        # Add edge to each target (parallel fan-out)
        for to_id in to_ids:
            if to_id not in executors:
                logger.warning(f"Parallel edge references unknown target executor: {to_id}")
                continue
            
            to_executor = executors[to_id]
            builder.add_edge(from_executor, to_executor)
            logger.debug(f"Added parallel edge: {from_id} -> {to_id}")
    
    def _add_join_edges(
        self,
        builder: WorkflowBuilder,
        executors: Dict[str, Any],
        edge_def: Dict[str, Any]
    ) -> None:
        """Add join edges: [from1, from2, from3] -> to (fan-in)."""
        from_ids = edge_def.get('from', [])
        to_id = edge_def.get('to')
        wait_strategy = edge_def.get('wait_strategy', 'all')
        
        if not isinstance(from_ids, list):
            from_ids = [from_ids]
        
        if not to_id:
            logger.warning(f"Join edge missing to: {edge_def}")
            return
        
        if to_id not in executors:
            logger.warning(f"Join edge references unknown target executor: {to_id}")
            return
        
        to_executor = executors[to_id]
        
        # Add edge from each source to target (fan-in)
        for from_id in from_ids:
            if from_id not in executors:
                logger.warning(f"Join edge references unknown source executor: {from_id}")
                continue
            
            from_executor = executors[from_id]
            builder.add_edge(from_executor, to_executor)
            logger.debug(f"Added join edge: {from_id} -> {to_id} (wait: {wait_strategy})")
        
        # Note: Agent Framework handles fan-in naturally when multiple edges point to same target
        # The wait_strategy is informational for now, could be used with custom executors
    
    def _add_conditional_edges(
        self,
        builder: WorkflowBuilder,
        executors: Dict[str, Any],
        edge_def: Dict[str, Any]
    ) -> None:
        """
        Add conditional edges: from -> [{target: to1, condition: "..."}, {target: to2, condition: "..."}].
        
        Note: Full conditional routing requires custom executor logic.
        This method sets up the edges; the source executor must implement routing logic.
        """
        from_id = edge_def.get('from')
        to_conditions = edge_def.get('to', [])
        
        if not from_id:
            logger.warning(f"Conditional edge missing from: {edge_def}")
            return
        
        if not isinstance(to_conditions, list):
            logger.warning(f"Conditional edge 'to' must be a list: {edge_def}")
            return
        
        if from_id not in executors:
            logger.warning(f"Conditional edge references unknown source executor: {from_id}")
            return
        
        from_executor = executors[from_id]
        
        # Add edge to each conditional target
        for condition_def in to_conditions:
            if isinstance(condition_def, dict):
                to_id = condition_def.get('target')
                condition = condition_def.get('condition', 'default')
            else:
                to_id = condition_def
                condition = 'default'
            
            if not to_id or to_id not in executors:
                logger.warning(f"Conditional edge references unknown target: {to_id}")
                continue
            
            to_executor = executors[to_id]
            builder.add_edge(from_executor, to_executor)
            logger.debug(f"Added conditional edge: {from_id} -> {to_id} (condition: {condition})")
        
        # Note: The from_executor needs to implement routing logic based on conditions
        # This typically requires a custom executor or router executor type
    
    def get_pipeline_names(self) -> List[str]:
        """Get list of available workflow names."""
        return list(self._pipeline_configs.keys())
    
    def get_executor_catalog(self) -> List[Dict[str, Any]]:
        """
        Get executor catalog information.
        
        Returns:
            List of executor configurations with metadata
        """
        if not self.use_dynamic_loading:
            # Return legacy executor types
            return [
                {
                    "id": executor_id,
                    "class": executor_class.__name__,
                    "module": executor_class.__module__,
                }
                for executor_id, executor_class in EXECUTOR_TYPES.items()
            ]
        
        # Return catalog executors
        executors = []
        for config in self.executor_registry.list_executors():
            executors.append({
                "id": config.id,
                "name": config.name,
                "description": config.description,
                "category": config.category,
                "tags": config.tags,
                "required_connectors": config.required_connectors,
                "settings_schema": {
                    key: {
                        "type": schema.type,
                        "title": schema.title,
                        "description": schema.description,
                        "required": schema.required,
                        "default": schema.default,
                    }
                    for key, schema in config.settings_schema.items()
                }
            })
        
        return executors
    
    def validate_pipeline_executors(
        self,
        pipeline_name: str
    ) -> Dict[str, Any]:
        """
        Validate executors in a workflow configuration.
        
        Args:
            pipeline_name: Name of workflow to validate
            
        Returns:
            Validation results dict with errors and warnings
        """
        if pipeline_name not in self._pipeline_configs:
            return {
                "valid": False,
                "errors": [f"Pipeline '{pipeline_name}' not found"],
                "warnings": []
            }
        
        pipeline_config = self._pipeline_configs[pipeline_name]
        errors = []
        warnings = []
        
        # Get available connectors
        available_connectors = self.get_connector_names()
        
        # Validate each executor
        for exec_def in pipeline_config.get('executors', []):
            executor_id = exec_def['id']
            executor_type = exec_def['type']
            
            # Check if executor type exists
            if self.use_dynamic_loading:
                if executor_type not in self.executor_registry:
                    errors.append(
                        f"Executor '{executor_id}': type '{executor_type}' not found in catalog"
                    )
                    continue
                
                # Get executor config
                executor_config = self.executor_registry.get_executor_config(executor_type)
                
                # Validate required connectors
                for required in executor_config.required_connectors:
                    executor_connectors = exec_def.get('connectors', [])
                    if required not in executor_connectors:
                        warnings.append(
                            f"Executor '{executor_id}': missing recommended connector '{required}'"
                        )
                
                # Validate settings
                try:
                    executor_config.validate_settings(exec_def.get('settings', {}))
                except Exception as e:
                    errors.append(
                        f"Executor '{executor_id}': invalid settings - {e}"
                    )
            
            else:
                # Legacy validation
                if executor_type not in EXECUTOR_TYPES:
                    errors.append(
                        f"Executor '{executor_id}': type '{executor_type}' not found"
                    )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
