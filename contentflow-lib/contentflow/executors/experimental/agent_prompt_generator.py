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

class AgentPromptGeneratorExecutor(BaseExecutor):
    """
    Executor that generates specialized prompts for each agent.
    
    Uses Azure OpenAI to generate comprehensive system prompts for each agent role.
    """
    
    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        self.prompt_components = self.get_setting("prompt_components", [])
        self.include_persona = self.get_setting("include_persona", True)
        self.include_constraints = self.get_setting("include_constraints", True)
        self.output_field = self.get_setting("output_field", "agent_prompts")
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
        
        # Create agent for prompt generation
        components_str = ", ".join(self.prompt_components) if self.prompt_components else "role definition, expertise, task instructions, interaction protocols"
        instructions = f"""
You are an expert prompt engineer specializing in multi-agent systems. Generate high-quality system prompts for AI agents.

Each prompt should include:
- {components_str}
{"- Clear persona and voice" if self.include_persona else ""}
{"- Explicit constraints and guidelines" if self.include_constraints else ""}

Generate prompts that are:
1. Clear and specific
2. Action-oriented
3. Include success criteria
4. Define interaction patterns with other agents

Return your response as a JSON array of prompt objects.
"""
        
        self.agent: ChatAgent = self.client.create_agent(
            id=f"{self.id}_agent",
            name="PromptGenerator",
            instructions=instructions,
            temperature=0.6
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
        logger.info(f"Generating agent prompts for content {content.id}")
        
        # Get agent roles from previous step
        agent_roles = content.data.get(self.agent_roles_field, [])
        
        if not agent_roles:
            logger.warning(f"No agent roles found for content {content.id}, using fallback prompts")
            content.data[self.output_field] = self._get_fallback_prompts()
            return
        
        agent_prompts = []
        
        # Generate prompt for each agent role
        for role in agent_roles:
            role_name = role.get("role_name", "UnknownAgent")
            archetype = role.get("archetype", "general")
            capabilities = role.get("capabilities", [])
            expertise = role.get("expertise_domain", "general")
            
            query = f"""
Generate a comprehensive system prompt for an AI agent with the following specification:

Role Name: {role_name}
Archetype: {archetype}
Capabilities: {', '.join(capabilities)}
Expertise Domain: {expertise}

The prompt should:
1. Define the agent's role and responsibilities
2. Specify their expertise and knowledge domain
3. Provide clear task instructions
4. Define interaction protocols with other agents
{"5. Include a clear persona and voice" if self.include_persona else ""}
{"6. State explicit constraints and guidelines" if self.include_constraints else ""}

Return just the system prompt text, without any preamble.
"""
            
            try:
                result = await self.agent.run(query, store=False)
                prompt_text = result.text if hasattr(result, 'text') else str(result)
                
                agent_prompts.append({
                    "role_name": role_name,
                    "system_prompt": prompt_text.strip(),
                    "archetype": archetype
                })
                
            except Exception as e:
                logger.error(f"Error generating prompt for {role_name}: {e}")
                # Fallback prompt for this agent
                agent_prompts.append({
                    "role_name": role_name,
                    "system_prompt": f"You are {role_name}, a specialized {archetype} agent with expertise in {expertise}. Your capabilities include: {', '.join(capabilities)}."
                })
        
        content.data[self.output_field] = agent_prompts
        logger.info(f"Successfully generated prompts for {len(agent_prompts)} agents")
    
    def _get_fallback_prompts(self) -> List[Dict]:
        """Generate fallback prompts when no roles are provided."""
        return [
            {
                "role_name": "GeneralAssistant",
                "system_prompt": "You are a helpful AI assistant capable of handling various tasks."
            }
        ]
