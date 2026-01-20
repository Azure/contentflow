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

class CommunicationProtocolDesignerExecutor(BaseExecutor):
    """
    Executor that designs inter-agent communication protocols.
    
    Uses Azure OpenAI to design optimal communication patterns and message flows
    between agents in a multi-agent system.
    """
    
    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        self.communication_patterns = self.get_setting("communication_patterns", [])
        self.message_format = self.get_setting("message_format", "structured_json")
        self.include_feedback_loops = self.get_setting("include_feedback_loops", True)
        self.define_termination_conditions = self.get_setting("define_termination_conditions", True)
        self.output_field = self.get_setting("output_field", "communication_protocol")
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
        
        # Create agent for protocol design
        patterns_str = ", ".join(self.communication_patterns) if self.communication_patterns else "sequential, parallel, debate, hierarchical"
        instructions = f"""
You are an expert in multi-agent system communication design. Design efficient communication protocols for agent coordination.

Available Communication Patterns: {patterns_str}
Message Format: {self.message_format}

For the communication protocol, provide:
1. patterns: List of communication patterns to use
2. format: Message format specification
3. flow: Array of message flow objects with 'from', 'to', 'type' fields
{"4. feedback_loops: Mechanisms for agents to provide feedback" if self.include_feedback_loops else ""}
{"5. termination_condition: When to end the multi-agent interaction" if self.define_termination_conditions else ""}

Return your response as a JSON object representing the communication protocol.
"""
        
        self.agent: ChatAgent = self.client.create_agent(
            id=f"{self.id}_agent",
            name="ProtocolDesigner",
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
        logger.info(f"Designing communication protocol for content {content.id}")
        
        # Get agent roles from previous step
        agent_roles = content.data.get(self.agent_roles_field, [])
        
        if not agent_roles:
            logger.warning(f"No agent roles found, using default protocol")
            content.data[self.output_field] = self._get_fallback_protocol()
            return
        
        # Prepare agent role summary for prompt
        role_summary = "\n".join([
            f"- {role['role_name']}: {role.get('archetype', 'N/A')} - {', '.join(role.get('capabilities', []))}"
            for role in agent_roles
        ])
        
        query = f"""
Design a communication protocol for the following agent roles:

{role_summary}

Provide a JSON object with structure:
{{
  "patterns": ["pattern1", "pattern2"],
  "format": "{self.message_format}",
  "flow": [
    {{"from": "Agent1", "to": "Agent2", "type": "handoff"}}
  ]{',"feedback_loops": []' if self.include_feedback_loops else ''}{',"termination_condition": "description"' if self.define_termination_conditions else ''}
}}
"""
        
        try:
            result = await self.agent.run(query, store=False)
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            # Parse JSON response
            protocol = self._extract_json_from_response(response_text)
            
            if not protocol or not isinstance(protocol, dict):
                logger.warning(f"Failed to parse protocol from LLM response, using fallback")
                protocol = self._get_fallback_protocol()
            
            content.data[self.output_field] = protocol
            content.data[f"{self.output_field}_raw_response"] = response_text
            
            logger.info(f"Successfully designed communication protocol")
            
        except Exception as e:
            logger.error(f"Error designing protocol: {e}", exc_info=True)
            content.data[self.output_field] = self._get_fallback_protocol()
    
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
    
    def _get_fallback_protocol(self) -> Dict:
        """Generate fallback protocol."""
        return {
            "patterns": ["sequential_handoff"],
            "format": self.message_format,
            "flow": [
                {"from": "Agent1", "to": "Agent2", "type": "handoff"},
                {"from": "Agent2", "to": "Agent3", "type": "verification"}
            ],
            "termination_condition": "All agents complete their tasks successfully"
        }
