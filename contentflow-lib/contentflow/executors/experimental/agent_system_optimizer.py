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

class AgentSystemOptimizerExecutor(BaseExecutor):
    """
    Executor that optimizes agent configuration based on simulation results.
    
    Uses Azure OpenAI to analyze simulation results and propose optimizations
    to improve the multi-agent system's performance.
    """
    
    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        self.optimization_objectives = self.get_setting("optimization_objectives", ["accuracy"])
        self.tunable_parameters = self.get_setting("tunable_parameters", [])
        self.optimization_method = self.get_setting("optimization_method", "bayesian")
        self.output_field = self.get_setting("output_field", "optimized_system")
        self.simulation_field = self.get_setting("simulation_field", "simulation_results")
        
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
        
        # Create agent for optimization
        objectives_str = ", ".join(self.optimization_objectives)
        parameters_str = ", ".join(self.tunable_parameters) if self.tunable_parameters else "agent count, prompt complexity, temperature"
        instructions = f"""
You are an expert in multi-agent system optimization. Analyze simulation results and propose improvements.

Optimization Objectives: {objectives_str}
Tunable Parameters: {parameters_str}
Optimization Method: {self.optimization_method}

For each optimization, provide:
1. Analysis of current performance
2. Identified bottlenecks or issues
3. Specific improvement recommendations
4. Expected impact on metrics
5. Updated configuration parameters

Return your response as a JSON object with optimization recommendations.
"""
        
        self.agent: ChatAgent = self.client.create_agent(
            id=f"{self.id}_agent",
            name="SystemOptimizer",
            instructions=instructions,
            temperature=0.5
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
        logger.info(f"Optimizing agent system for content {content.id}")
        
        # Get simulation results
        simulation_results = content.data.get(self.simulation_field, {})
        
        if not simulation_results:
            logger.warning(f"No simulation results found, skipping optimization")
            content.data[self.output_field] = self._get_fallback_optimization()
            return
        
        # Extract metrics and prepare analysis
        metrics = simulation_results.get("metrics", {})
        logs = simulation_results.get("logs", [])
        
        query = f"""
Analyze the following multi-agent system simulation results and provide optimization recommendations:

Simulation Metrics:
{json.dumps(metrics, indent=2)}

Simulation Logs (sample):
{chr(10).join(logs[:10])}

Optimization Objectives: {', '.join(self.optimization_objectives)}

Provide optimization recommendations as a JSON object with structure:
{{
  "current_performance": {{"metric": "value"}},
  "identified_issues": ["issue1", "issue2"],
  "improvements": [
    {{
      "parameter": "parameter_name",
      "current_value": "value",
      "recommended_value": "value",
      "expected_impact": "description",
      "priority": "high|medium|low"
    }}
  ],
  "estimated_improvement": {{"metric": "percentage"}}
}}
"""
        
        try:
            result = await self.agent.run(query, store=False)
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            # Parse JSON response
            optimization = self._extract_json_from_response(response_text)
            
            if not optimization or not isinstance(optimization, dict):
                logger.warning(f"Failed to parse optimization from LLM response, using fallback")
                optimization = self._get_fallback_optimization()
            
            # Add configuration summary
            optimization["original_metrics"] = metrics
            optimization["optimization_method"] = self.optimization_method
            
            content.data[self.output_field] = optimization
            content.data[f"{self.output_field}_raw_response"] = response_text
            
            logger.info(f"Successfully generated optimization recommendations")
            
        except Exception as e:
            logger.error(f"Error optimizing system: {e}", exc_info=True)
            content.data[self.output_field] = self._get_fallback_optimization()
    
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
    
    def _get_fallback_optimization(self) -> Dict:
        """Generate fallback optimization recommendations."""
        return {
            "current_performance": {"note": "Analysis pending"},
            "identified_issues": ["Insufficient simulation data"],
            "improvements": [
                {
                    "parameter": "temperature",
                    "current_value": "0.7",
                    "recommended_value": "0.5",
                    "expected_impact": "More consistent outputs",
                    "priority": "medium"
                }
            ],
            "estimated_improvement": {"accuracy": "5-10%"},
            "note": "These are generic recommendations. Run simulation for specific optimizations."
        }
