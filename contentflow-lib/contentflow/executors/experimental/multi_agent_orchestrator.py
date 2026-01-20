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

class MultiAgentOrchestratorExecutor(BaseExecutor):
    """
    Executor that generates orchestration logic and workflow for multi-agent systems.
    
    Uses Azure OpenAI to design the orchestration workflow that coordinates
    multiple agents based on their roles and communication protocols.
    """
    
    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        self.orchestration_strategy = self.get_setting("orchestration_strategy", "dynamic")
        self.include_error_handling = self.get_setting("include_error_handling", True)
        self.include_retry_logic = self.get_setting("include_retry_logic", True)
        self.max_iterations = self.get_setting("max_iterations", 10)
        self.convergence_criteria = self.get_setting("convergence_criteria", "consensus_threshold")
        self.output_field = self.get_setting("output_field", "orchestration_logic")
        self.protocol_field = self.get_setting("protocol_field", "communication_protocol")
        self.agent_roles_field = self.get_setting("agent_roles_field", "agent_roles")
        
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
        
        # Create agent for orchestration design
        instructions = f"""
You are an expert in multi-agent workflow orchestration. Design efficient execution workflows for coordinating multiple AI agents.

Orchestration Strategy: {self.orchestration_strategy}
- dynamic: Adaptive workflow that adjusts based on runtime conditions
- static: Fixed workflow with predefined steps
- adaptive: Learns from execution patterns

Generate an orchestration plan with:
1. strategy: The orchestration approach
2. max_iterations: Maximum workflow iterations ({self.max_iterations})
3. convergence: Criteria for completion ("{self.convergence_criteria}")
4. workflow_steps: Detailed execution steps with agent invocations
{"5. error_handling: Error recovery strategies" if self.include_error_handling else ""}
{"6. retry_logic: Retry policies for failed operations" if self.include_retry_logic else ""}

Return your response as a JSON object representing the orchestration logic.
"""
        
        self.agent: ChatAgent = self.client.create_agent(
            id=f"{self.id}_agent",
            name="Orchestrator",
            instructions=instructions,
            temperature=0.3
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
        logger.info(f"Creating orchestration logic for content {content.id}")
        
        # Get agent roles and protocol from previous steps
        agent_roles = content.data.get(self.agent_roles_field, [])
        protocol = content.data.get(self.protocol_field, {})
        
        if not agent_roles:
            logger.warning(f"No agent roles found, using fallback orchestration")
            content.data[self.output_field] = self._get_fallback_orchestration()
            return
        
        # Prepare context for orchestration
        role_names = [role['role_name'] for role in agent_roles]
        flows = protocol.get('flow', [])
        
        query = f"""
Design an orchestration workflow for the following multi-agent system:

Agents: {', '.join(role_names)}

Communication Flow:
{json.dumps(flows, indent=2)}

Provide orchestration logic as a JSON object with structure:
{{
  "strategy": "{self.orchestration_strategy}",
  "max_iterations": {self.max_iterations},
  "convergence": "{self.convergence_criteria}",
  "workflow_steps": [
    "step1: description",
    "step2: description"
  ]{',"error_handling": {{}}' if self.include_error_handling else ''}{',"retry_logic": {{}}' if self.include_retry_logic else ''}
}}

Each workflow step should clearly specify which agent to invoke and with what input.
"""
        
        try:
            result = await self.agent.run(query, store=False)
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            # Parse JSON response
            orchestration_logic = self._extract_json_from_response(response_text)
            
            if not orchestration_logic or not isinstance(orchestration_logic, dict):
                logger.warning(f"Failed to parse orchestration from LLM response, using fallback")
                orchestration_logic = self._get_fallback_orchestration()
            
            content.data[self.output_field] = orchestration_logic
            content.data[f"{self.output_field}_raw_response"] = response_text
            
            logger.info(f"Successfully created orchestration logic")
            
        except Exception as e:
            logger.error(f"Error creating orchestration: {e}", exc_info=True)
            content.data[self.output_field] = self._get_fallback_orchestration()
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """Extract JSON object from LLM response."""
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
            
            obj_match = re.search(r'\{[\s\S]*\}', response)
            if obj_match:
                try:
                    return json.loads(obj_match.group(0))
                except json.JSONDecodeError:
                    pass
        
        return None
    
    def _get_fallback_orchestration(self) -> Dict:
        """Generate fallback orchestration logic."""
        return {
            "strategy": self.orchestration_strategy,
            "max_iterations": self.max_iterations,
            "convergence": self.convergence_criteria,
            "workflow_steps": [
                "step1: Initialize and invoke first agent",
                "step2: Process results and invoke subsequent agents",
                "step3: Aggregate results and check convergence",
                "step4: If not converged and iterations < max, goto step1 else end"
            ]
        }
