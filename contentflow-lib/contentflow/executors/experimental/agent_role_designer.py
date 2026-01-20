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

class AgentRoleDesignerExecutor(BaseExecutor):
    """
    Executor that designs specialized agent roles based on subtasks.
    
    Uses Azure OpenAI to analyze subtasks and design optimal agent roles
    with appropriate capabilities and responsibilities.
    """
    
    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        self.design_criteria = self.get_setting("design_criteria", [])
        self.agent_archetypes = self.get_setting("agent_archetypes", [])
        self.optimize_agent_count = self.get_setting("optimize_agent_count", True)
        self.output_field = self.get_setting("output_field", "agent_roles")
        self.subtasks_field = self.get_setting("subtasks_field", "subtasks")
        
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
        
        # Create agent for role design
        archetypes_str = ", ".join(self.agent_archetypes) if self.agent_archetypes else "researcher, analyst, validator, coordinator"
        instructions = f"""
You are an expert in multi-agent system design. Your role is to design specialized agent roles based on task requirements.

Available Agent Archetypes: {archetypes_str}

For each agent role, provide:
1. role_name: A descriptive name for the agent
2. archetype: The type of agent from available archetypes
3. capabilities: List of specific capabilities this agent needs
4. assigned_subtasks: List of subtask IDs this agent should handle
5. expertise_domain: The domain of expertise for this agent

{"Optimize for minimal number of agents while maintaining specialization." if self.optimize_agent_count else ""}

Return your response as a JSON array of agent role objects.
"""
        
        self.agent: ChatAgent = self.client.create_agent(
            id=f"{self.id}_agent",
            name="AgentRoleDesigner",
            instructions=instructions,
            temperature=0.4
        )

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        
        items_to_process = input if isinstance(input, list) else [input]
        
        for item in items_to_process:
            await self._process_single_content(item)
            
        return input

    async def _process_single_content(self, content: Content):
        logger.info(f"Designing agent roles for content {content.id}")
        
        # Get subtasks from previous step
        subtasks = content.data.get(self.subtasks_field, [])
        
        if not subtasks:
            logger.warning(f"No subtasks found for content {content.id}, using fallback roles")
            content.data[self.output_field] = self._get_fallback_roles()
            return
        
        # Prepare prompt
        query = f"""
Design agent roles for the following subtasks:

{json.dumps(subtasks, indent=2)}

Provide a JSON array of agent roles with structure:
[
  {{
    "role_name": "AgentName",
    "archetype": "type",
    "capabilities": ["capability1", "capability2"],
    "assigned_subtasks": ["subtask_id"],
    "expertise_domain": "domain description"
  }}
]
"""
        
        try:
            # Run agent
            result = await self.agent.run(query, store=False)
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            # Parse JSON response
            agent_roles = self._extract_json_from_response(response_text)
            
            if not agent_roles or not isinstance(agent_roles, list):
                logger.warning(f"Failed to parse agent roles from LLM response, using fallback")
                agent_roles = self._get_fallback_roles()
            
            content.data[self.output_field] = agent_roles
            content.data[f"{self.output_field}_raw_response"] = response_text
            
            logger.info(f"Successfully designed {len(agent_roles)} agent roles")
            
        except Exception as e:
            logger.error(f"Error designing agent roles: {e}", exc_info=True)
            content.data[self.output_field] = self._get_fallback_roles()
    
    def _extract_json_from_response(self, response: str) -> Optional[List[Dict]]:
        """Extract JSON array from LLM response."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            array_match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', response)
            if array_match:
                try:
                    return json.loads(array_match.group(0))
                except json.JSONDecodeError:
                    pass
        
        return None
    
    def _get_fallback_roles(self) -> List[Dict]:
        """Generate fallback agent roles."""
        return [
            {
                "role_name": "Analyst",
                "archetype": "analyst",
                "capabilities": ["analysis", "research"],
                "assigned_subtasks": [],
                "expertise_domain": "general analysis"
            },
            {
                "role_name": "Executor",
                "archetype": "coordinator",
                "capabilities": ["execution", "coordination"],
                "assigned_subtasks": [],
                "expertise_domain": "task execution"
            },
            {
                "role_name": "Validator",
                "archetype": "validator",
                "capabilities": ["validation", "quality_assurance"],
                "assigned_subtasks": [],
                "expertise_domain": "quality control"
            }
        ]
