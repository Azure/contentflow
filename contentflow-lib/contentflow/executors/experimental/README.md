# Multi-Agent Prompt Orchestration Executors

This directory contains executors for the Multi-Agent Prompt Orchestration Pipeline (Template #13 from Advanced Pipeline Templates). These executors enable automated design and optimization of multi-agent AI systems.

## Overview

These executors work together to:
1. Decompose complex tasks into subtasks
2. Design specialized agent roles
3. Generate agent-specific system prompts
4. Design inter-agent communication protocols
5. Create orchestration workflows
6. Simulate multi-agent execution
7. Optimize the system based on simulation results

## Executors

### 1. TaskDecomposerExecutor

**Purpose:** Breaks down complex tasks into manageable subtasks with dependencies.

**Configuration:**
```yaml
- id: task-decomposer-1
  type: task_decomposer
  settings:
    decomposition_strategy: "functional"  # or "sequential", "hierarchical"
    identify_dependencies: true
    estimate_complexity: true
    input_field: "text"
    output_field: "subtasks"
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    deployment_name: "gpt-4"
```

**Outputs:**
- `subtasks`: Array of subtask objects with id, name, description, dependencies, and complexity

---

### 2. AgentRoleDesignerExecutor

**Purpose:** Designs specialized agent roles based on task requirements.

**Configuration:**
```yaml
- id: agent-designer-1
  type: agent_role_designer
  settings:
    design_criteria: ["task_specialization", "expertise_domain"]
    agent_archetypes: ["researcher", "analyst", "validator", "coordinator"]
    optimize_agent_count: true
    subtasks_field: "subtasks"
    output_field: "agent_roles"
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    deployment_name: "gpt-4"
```

**Outputs:**
- `agent_roles`: Array of agent role specifications with capabilities and assigned tasks

---

### 3. AgentPromptGeneratorExecutor

**Purpose:** Generates specialized system prompts for each agent role.

**Configuration:**
```yaml
- id: prompt-generator-1
  type: agent_prompt_generator
  settings:
    prompt_components: ["role_definition", "expertise_specification", "task_instructions"]
    include_persona: true
    include_constraints: true
    agent_roles_field: "agent_roles"
    output_field: "agent_prompts"
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    deployment_name: "gpt-4"
```

**Outputs:**
- `agent_prompts`: Array of system prompts for each agent

---

### 4. CommunicationProtocolDesignerExecutor

**Purpose:** Designs inter-agent communication protocols and message flows.

**Configuration:**
```yaml
- id: protocol-designer-1
  type: communication_protocol_designer
  settings:
    communication_patterns: ["sequential_handoff", "parallel_execution", "debate_consensus"]
    message_format: "structured_json"
    include_feedback_loops: true
    define_termination_conditions: true
    agent_roles_field: "agent_roles"
    output_field: "communication_protocol"
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    deployment_name: "gpt-4"
```

**Outputs:**
- `communication_protocol`: Protocol specification with patterns, format, and flow

---

### 5. MultiAgentOrchestratorExecutor

**Purpose:** Creates orchestration logic and workflow for coordinating multiple agents.

**Configuration:**
```yaml
- id: orchestrator-1
  type: multi_agent_orchestrator
  settings:
    orchestration_strategy: "dynamic"  # or "static", "adaptive"
    include_error_handling: true
    include_retry_logic: true
    max_iterations: 10
    convergence_criteria: "consensus_threshold"
    protocol_field: "communication_protocol"
    agent_roles_field: "agent_roles"
    output_field: "orchestration_logic"
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    deployment_name: "gpt-4"
```

**Outputs:**
- `orchestration_logic`: Workflow specification with execution steps

---

### 6. MultiAgentSimulatorExecutor

**Purpose:** Simulates multi-agent system execution and collects performance metrics.

**Configuration:**
```yaml
- id: simulator-1
  type: multi_agent_simulator
  settings:
    simulation_mode: "full"  # or "dry_run", "partial"
    test_scenarios: ["happy_path", "error_scenarios", "edge_cases"]
    collect_metrics: ["task_completion_rate", "consensus_quality", "token_usage"]
    orchestration_field: "orchestration_logic"
    agent_prompts_field: "agent_prompts"
    output_field: "simulation_results"
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    deployment_name: "gpt-4"
```

**Outputs:**
- `simulation_results`: Metrics, logs, and performance data from simulation

---

### 7. AgentSystemOptimizerExecutor

**Purpose:** Optimizes agent configuration based on simulation results.

**Configuration:**
```yaml
- id: optimizer-1
  type: agent_system_optimizer
  settings:
    optimization_objectives: ["accuracy", "efficiency", "cost", "latency"]
    tunable_parameters: ["agent_count", "temperature", "communication_frequency"]
    optimization_method: "bayesian"
    simulation_field: "simulation_results"
    output_field: "optimized_system"
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    deployment_name: "gpt-4"
```

**Outputs:**
- `optimized_system`: Optimization recommendations with expected improvements

---

## Pipeline Integration Example

```yaml
pipeline:
  name: "Multi-Agent Prompt Orchestration"
  
  executors:
    - id: blob-discovery-1
      type: azure_blob_input_discovery
      settings:
        file_extensions: ".json,.yaml"
        blob_container_name: "task-specs"
    
    - id: blob-content-1
      type: azure_blob_content_retriever
    
    - id: task-decomposer-1
      type: task_decomposer
      settings:
        endpoint: "${AZURE_OPENAI_ENDPOINT}"
        deployment_name: "gpt-4"
    
    - id: agent-designer-1
      type: agent_role_designer
      settings:
        endpoint: "${AZURE_OPENAI_ENDPOINT}"
        deployment_name: "gpt-4"
    
    - id: prompt-generator-1
      type: agent_prompt_generator
      settings:
        endpoint: "${AZURE_OPENAI_ENDPOINT}"
        deployment_name: "gpt-4"
    
    - id: protocol-designer-1
      type: communication_protocol_designer
      settings:
        endpoint: "${AZURE_OPENAI_ENDPOINT}"
        deployment_name: "gpt-4"
    
    - id: orchestrator-1
      type: multi_agent_orchestrator
      settings:
        endpoint: "${AZURE_OPENAI_ENDPOINT}"
        deployment_name: "gpt-4"
    
    - id: simulator-1
      type: multi_agent_simulator
      settings:
        endpoint: "${AZURE_OPENAI_ENDPOINT}"
        deployment_name: "gpt-4"
    
    - id: optimizer-1
      type: agent_system_optimizer
      settings:
        endpoint: "${AZURE_OPENAI_ENDPOINT}"
        deployment_name: "gpt-4"
    
    - id: blob-output-1
      type: azure_blob_output
      settings:
        blob_container_name: "agent-systems-output"
  
  edges:
    - from: blob-discovery-1
      to: blob-content-1
      type: sequential
    - from: blob-content-1
      to: task-decomposer-1
      type: sequential
    - from: task-decomposer-1
      to: agent-designer-1
      type: sequential
    - from: agent-designer-1
      to: prompt-generator-1
      type: sequential
    - from: prompt-generator-1
      to: protocol-designer-1
      type: sequential
    - from: protocol-designer-1
      to: orchestrator-1
      type: sequential
    - from: orchestrator-1
      to: simulator-1
      type: sequential
    - from: simulator-1
      to: optimizer-1
      type: sequential
    - from: optimizer-1
      to: blob-output-1
      type: sequential
```

## Dependencies

All executors require:
- `agent-framework`: Microsoft Agent Framework for LLM interactions
- `azure-identity`: Azure authentication
- Azure OpenAI endpoint with appropriate deployment

Install dependencies:
```bash
pip install agent-framework azure-identity
```

## Environment Variables

Set the following environment variables:
```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
```

## Key Features

### 1. Production-Ready LLM Integration
- Uses Azure OpenAI via agent-framework
- Proper error handling and fallbacks
- JSON parsing with multiple strategies

### 2. Comprehensive Logging
- Detailed execution logs
- Warning for missing inputs
- Error tracking with stack traces

### 3. Flexible Configuration
- Configurable strategies and parameters
- Support for different orchestration modes
- Customizable optimization objectives

### 4. Real-World Simulation
- Actual agent creation and execution
- Token usage tracking
- Performance metrics collection

### 5. Intelligent Optimization
- Analysis of simulation results
- Prioritized recommendations
- Expected impact estimates

## Use Cases

1. **Automated Multi-Agent System Design**: Design complete multi-agent systems from task descriptions
2. **Agent Team Optimization**: Optimize existing multi-agent configurations
3. **Research & Development**: Experiment with different agent architectures
4. **Production Deployment**: Validate multi-agent systems before deployment
5. **Continuous Improvement**: Iteratively improve agent systems based on performance data

## Best Practices

1. **Use Clear Task Descriptions**: Provide detailed, unambiguous task descriptions for best results
2. **Set Appropriate Temperature**: Use lower temperatures (0.3-0.5) for structured outputs
3. **Monitor Token Usage**: Track token consumption in simulations for cost management
4. **Iterate on Results**: Use optimizer recommendations to refine the system
5. **Test Multiple Scenarios**: Include happy path, error cases, and edge cases in simulations

## Future Enhancements

- Support for custom agent archetypes
- Advanced optimization algorithms (genetic algorithms, reinforcement learning)
- Real-time multi-agent execution (not just simulation)
- Integration with agent monitoring and observability tools
- Support for tool-using agents
- Multi-modal agent support

## Contributing

When extending these executors:
1. Follow the existing patterns (inherit from BaseExecutor)
2. Use Azure OpenAI via agent-framework
3. Include comprehensive error handling
4. Add fallback logic for robustness
5. Update this README with new features
