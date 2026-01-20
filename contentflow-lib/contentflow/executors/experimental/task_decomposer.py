import logging
import json
from typing import List, Union, Dict, Any, Optional

try:
    from agent_framework.azure import AzureOpenAIResponsesClient
    from agent_framework import ChatAgent
except ImportError:
    raise ImportError(
        "agent-framework and azure-identity are required. "
        "Install them with: pip install agent-framework azure-identity"
    )

from agent_framework import WorkflowContext
from contentflow.models import Content
from contentflow.executors.base import BaseExecutor
from contentflow.utils.credential_provider import get_azure_credential

logger = logging.getLogger(__name__)

class TaskDecomposerExecutor(BaseExecutor):
    """
    Executor for decomposing complex tasks into subtasks for agent assignment.
    
    Uses Azure OpenAI to analyze task descriptions and break them down into
    subtasks with dependencies and complexity estimates.
    
    Configuration:
        - decomposition_strategy: Strategy for decomposition (functional, sequential, hierarchical)
        - identify_dependencies: Whether to identify task dependencies
        - estimate_complexity: Whether to estimate complexity for each subtask
        - output_field: Field name for output (default: "subtasks")
        - endpoint: Azure OpenAI endpoint URL
        - deployment_name: Azure OpenAI model deployment name
        - input_field: Field containing task description (default: "text")
    """
    
    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        self.decomposition_strategy = self.get_setting("decomposition_strategy", "functional")
        self.identify_dependencies = self.get_setting("identify_dependencies", True)
        self.estimate_complexity = self.get_setting("estimate_complexity", True)
        self.output_field = self.get_setting("output_field", "subtasks")
        self.input_field = self.get_setting("input_field", "text")
        
        # Azure OpenAI configuration
        self.endpoint = self.get_setting("endpoint", None)
        self.deployment_name = self.get_setting("deployment_name", None)
        
        # Initialize Azure OpenAI client
        credential = get_azure_credential()
        self.client = AzureOpenAIResponsesClient(
            endpoint=self.endpoint,
            deployment_name=self.deployment_name,
            credential=credential
        )
        
        # Create agent for task decomposition
        instructions = f"""
You are an expert task decomposition specialist. Your role is to analyze complex tasks and break them down into manageable subtasks.

Decomposition Strategy: {self.decomposition_strategy}
- functional: Organize by functional areas or capabilities
- sequential: Order by execution sequence
- hierarchical: Create parent-child task relationships

For each subtask, provide:
1. A unique ID (subtask_1, subtask_2, etc.)
2. A clear name
3. A detailed description
{"4. Dependencies (list of subtask IDs this depends on)" if self.identify_dependencies else ""}
{"5. Estimated complexity (low, medium, high)" if self.estimate_complexity else ""}

Return your response as a JSON array of subtask objects.
"""
        
        self.agent: ChatAgent = self.client.create_agent(
            id=f"{self.id}_agent",
            name="TaskDecomposer",
            instructions=instructions,
            temperature=0.3  # Lower temperature for more structured output
        )

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """
        Process the input content by decomposing tasks.
        """
        # Handle both single item and list inputs
        items_to_process = input if isinstance(input, list) else [input]
        
        for item in items_to_process:
            await self._process_single_content(item)
            
        return input

    async def _process_single_content(self, content: Content):
        """
        Process a single content item using Azure OpenAI for task decomposition.
        """
        logger.info(f"Decomposing task for content {content.id} with strategy {self.decomposition_strategy}")
        
        # Extract task description from content
        task_description = self.try_extract_nested_field_from_content(
            content=content, 
            field_path=self.input_field
        )
        
        if not task_description:
            task_description = content.data.get("description", "")
            
        if not task_description:
            logger.warning(f"No task description found for content {content.id}, using fallback")
            task_description = "Unknown task"
        
        # Prepare prompt for the agent
        query = f"""
Decompose the following task into subtasks:

Task: {task_description}

Provide a JSON array of subtasks with the structure:
[
  {{
    "id": "subtask_1",
    "name": "Task Name",
    "description": "Detailed description"{',"dependencies": ["subtask_id"]' if self.identify_dependencies else ''}{',"estimated_complexity": "low|medium|high"' if self.estimate_complexity else ''}
  }}
]
"""
        
        try:
            # Run agent
            result = await self.agent.run(query, store=False)
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            # Parse JSON response
            # Try to extract JSON from response
            subtasks = self._extract_json_from_response(response_text)
            
            if not subtasks or not isinstance(subtasks, list):
                logger.warning(f"Failed to parse subtasks from LLM response, using fallback")
                subtasks = self._get_fallback_subtasks(task_description)
            
            content.data[self.output_field] = subtasks
            content.data[f"{self.output_field}_raw_response"] = response_text
            
            logger.info(f"Successfully decomposed task into {len(subtasks)} subtasks")
            
        except Exception as e:
            logger.error(f"Error decomposing task: {e}", exc_info=True)
            # Use fallback
            content.data[self.output_field] = self._get_fallback_subtasks(task_description)
    
    def _extract_json_from_response(self, response: str) -> Optional[List[Dict]]:
        """Extract JSON array from LLM response."""
        try:
            # Try direct JSON parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Try to find array pattern
            array_match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', response)
            if array_match:
                try:
                    return json.loads(array_match.group(0))
                except json.JSONDecodeError:
                    pass
        
        return None
    
    def _get_fallback_subtasks(self, task_description: str) -> List[Dict]:
        """Generate fallback subtasks when LLM fails."""
        subtasks = [
            {
                "id": "subtask_1",
                "name": "Analyze Requirements",
                "description": f"Analyze requirements for: {task_description[:100]}",
                "dependencies": []
            },
            {
                "id": "subtask_2",
                "name": "Execute Task",
                "description": "Execute the main task logic",
                "dependencies": ["subtask_1"]
            },
            {
                "id": "subtask_3",
                "name": "Validate Results",
                "description": "Validate and verify the results",
                "dependencies": ["subtask_2"]
            }
        ]
        
        if self.estimate_complexity:
            for task in subtasks:
                task["estimated_complexity"] = "medium"
        
        return subtasks
