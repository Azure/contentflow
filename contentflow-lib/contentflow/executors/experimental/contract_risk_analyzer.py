"""
Contract Risk Analyzer Executor.

Identifies and assesses risks in contracts using AI-powered analysis
with severity scoring and template benchmarking.
"""

import logging
import json
from typing import List, Union, Dict, Any, Optional
from enum import Enum
from datetime import datetime

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


class RiskCategory(str, Enum):
    """Contract risk categories."""
    FINANCIAL_EXPOSURE = "financial_exposure"
    LIABILITY_CAPS = "liability_caps"
    TERMINATION_RIGHTS = "termination_rights"
    IP_OWNERSHIP = "ip_ownership"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    DATA_PRIVACY = "data_privacy"
    PAYMENT_TERMS = "payment_terms"
    PERFORMANCE_OBLIGATIONS = "performance_obligations"
    INDEMNIFICATION = "indemnification"
    DISPUTE_RESOLUTION = "dispute_resolution"


class RiskSeverity(str, Enum):
    """Risk severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ContractRiskAnalyzerExecutor(BaseExecutor):
    """
    Analyze contract risks using AI.
    
    This executor uses Azure OpenAI to identify unfavorable terms,
    assess compliance risks, and provide risk mitigation recommendations.
    
    Configuration (settings dict):
        - risk_categories (list): Risk categories to analyze
          Default: All standard risk categories
        - severity_scoring (bool): Include severity scores for each risk
          Default: True
        - benchmark_against_templates (bool): Compare against standard templates
          Default: True
        - include_recommendations (bool): Provide mitigation recommendations
          Default: True
        - template_source (str): Source for template benchmarking
          Default: "industry_standard"
        - risk_threshold (str): Minimum severity to report (low, medium, high, critical)
          Default: "low"
        - input_field (str): Field containing contract text or clauses
          Default: "extracted_content.markdown"
        - clauses_field (str): Field containing pre-extracted clauses (optional)
          Default: "clauses"
        - output_field (str): Field name for risk analysis results
          Default: "risk_analysis"
        - endpoint (str): Azure OpenAI endpoint URL
        - deployment_name (str): Azure OpenAI model deployment name
        - temperature (float): Temperature for LLM
          Default: 0.2
    
    Expected Input Data Structure:
        {
            "extracted_content": {
                "markdown": "Full contract text..."
            },
            "clauses": {  # Optional - will use if available
                "clauses": [...]
            }
        }
    
    Output:
        Content with added fields:
        - data[output_field]: Dictionary containing risk analysis
        - summary_data["risk_analysis_status"]: Execution status
        - summary_data["risk_score"]: Overall risk score (0-100)
    
    Example:
        ```yaml
        - id: risk-analyzer-1
          type: contract_risk_analyzer
          settings:
            risk_categories:
              - financial_exposure
              - liability_caps
              - termination_rights
            severity_scoring: true
            benchmark_against_templates: true
            endpoint: "${AZURE_OPENAI_ENDPOINT}"
            deployment_name: "gpt-4"
        ```
    """
    
    RISK_DEFINITIONS = {
        RiskCategory.FINANCIAL_EXPOSURE: "Unlimited or excessive financial obligations and liabilities",
        RiskCategory.LIABILITY_CAPS: "Absence or inadequacy of liability limitations",
        RiskCategory.TERMINATION_RIGHTS: "Unfavorable or one-sided termination provisions",
        RiskCategory.IP_OWNERSHIP: "Unclear or unfavorable intellectual property ownership",
        RiskCategory.REGULATORY_COMPLIANCE: "Failure to address regulatory requirements",
        RiskCategory.DATA_PRIVACY: "Inadequate data protection and privacy provisions",
        RiskCategory.PAYMENT_TERMS: "Unfavorable payment schedules or conditions",
        RiskCategory.PERFORMANCE_OBLIGATIONS: "Unrealistic or one-sided performance requirements",
        RiskCategory.INDEMNIFICATION: "One-sided or overly broad indemnification obligations",
        RiskCategory.DISPUTE_RESOLUTION: "Unfavorable dispute resolution mechanisms",
    }
    
    SEVERITY_WEIGHTS = {
        RiskSeverity.CRITICAL: 100,
        RiskSeverity.HIGH: 75,
        RiskSeverity.MEDIUM: 50,
        RiskSeverity.LOW: 25,
        RiskSeverity.INFORMATIONAL: 10,
    }
    
    # Standard template benchmarks
    STANDARD_PROVISIONS = {
        "liability_cap": {
            "standard": "Liability capped at 12 months of fees paid",
            "red_flags": ["unlimited liability", "no cap", "all damages"]
        },
        "termination_notice": {
            "standard": "30-60 days written notice",
            "red_flags": ["immediate termination", "no notice", "at any time"]
        },
        "payment_terms": {
            "standard": "Net 30-45 days",
            "red_flags": ["advance payment", "non-refundable", "all fees due immediately"]
        },
        "ip_ownership": {
            "standard": "Creator retains ownership, grants license",
            "red_flags": ["work for hire", "all rights transferred", "perpetual assignment"]
        },
        "indemnification": {
            "standard": "Mutual indemnification with carve-outs",
            "red_flags": ["one-way indemnification", "unlimited indemnification", "indemnify all claims"]
        }
    }

    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        
        # Configuration
        self.risk_categories = self.get_setting("risk_categories", list(self.RISK_DEFINITIONS.keys()))
        self.severity_scoring = self.get_setting("severity_scoring", True)
        self.benchmark_against_templates = self.get_setting("benchmark_against_templates", True)
        self.include_recommendations = self.get_setting("include_recommendations", True)
        self.template_source = self.get_setting("template_source", "industry_standard")
        self.risk_threshold = self.get_setting("risk_threshold", "low")
        self.input_field = self.get_setting("input_field", "extracted_content.markdown")
        self.clauses_field = self.get_setting("clauses_field", "clauses")
        self.output_field = self.get_setting("output_field", "risk_analysis")
        
        # Azure OpenAI configuration
        self.endpoint = self.get_setting("endpoint", None)
        self.deployment_name = self.get_setting("deployment_name", None)
        self.temperature = self.get_setting("temperature", 0.2)
        
        # Initialize Azure OpenAI client
        credential = get_azure_credential()
        self.client = AzureOpenAIResponsesClient(
            endpoint=self.endpoint,
            deployment_name=self.deployment_name,
            credential=credential
        )
        
        # Create specialized agent for risk analysis
        self._init_agent()
        
        if self.debug_mode:
            logger.debug(
                f"ContractRiskAnalyzerExecutor initialized: "
                f"risk_categories={self.risk_categories}"
            )

    def _init_agent(self) -> None:
        """Initialize AI agent for risk analysis."""
        # Build risk definitions for the agent
        risk_defs = "\n".join([
            f"- {category}: {self.RISK_DEFINITIONS.get(RiskCategory(category), 'Risk area')}"
            for category in self.risk_categories
        ])
        
        # Build standard provisions reference
        provisions_ref = ""
        if self.benchmark_against_templates:
            provisions_ref = "\n\nSTANDARD PROVISIONS FOR BENCHMARKING:\n"
            for provision, details in self.STANDARD_PROVISIONS.items():
                provisions_ref += f"\n{provision}:\n"
                provisions_ref += f"  Standard: {details['standard']}\n"
                provisions_ref += f"  Red Flags: {', '.join(details['red_flags'])}\n"
        
        instructions = f"""
You are an expert contract risk analyst with deep knowledge of contract law and commercial negotiations.

Your task is to identify and assess risks in the following categories:

{risk_defs}

{provisions_ref}

For each risk you identify:
1. Specify the risk category from the list above
2. Describe the specific risk or unfavorable term
3. Explain why it's concerning
4. Rate the severity (critical, high, medium, low, informational)
5. Identify the specific clause or section where the risk appears
{"6. Compare against standard provisions and note deviations" if self.benchmark_against_templates else ""}
{"7. Provide specific mitigation recommendations" if self.include_recommendations else ""}

Return your response as a JSON array with the following structure:
[
  {{
    "risk_category": "category from list",
    "risk_description": "specific risk identified",
    "explanation": "why this is concerning",
    "severity": "critical|high|medium|low|informational",
    "affected_clauses": ["clause references"],
    "contract_provision": "actual contract language",
    {"template_comparison": "how it deviates from standard"," if self.benchmark_against_templates else ""}
    {"recommendations": ["recommendation 1", "recommendation 2"]," if self.include_recommendations else ""}
    "financial_impact": "potential financial impact if applicable"
  }}
]

Severity Guidelines:
- CRITICAL: Could result in business failure, unlimited liability, or major legal issues
- HIGH: Significant financial exposure, one-sided terms, missing protections
- MEDIUM: Suboptimal terms that should be negotiated
- LOW: Minor issues or opportunities for improvement
- INFORMATIONAL: Notable provisions that require awareness

Focus on:
- Unfavorable or one-sided terms
- Missing standard protections
- Ambiguous language that could be exploited
- Compliance gaps
- Financial exposure and liability issues
"""
        
        self.agent: ChatAgent = self.client.create_agent(
            id=f"{self.id}_agent",
            name="ContractRiskAnalyzer",
            instructions=instructions,
            temperature=self.temperature
        )

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """Process contract documents and analyze risks."""
        items_to_process = input if isinstance(input, list) else [input]
        
        for item in items_to_process:
            await self._process_single_content(item)
            
        return input

    async def _process_single_content(self, content: Content) -> None:
        """Process a single contract document and analyze risks."""
        logger.info(f"Analyzing contract risks in content {content.id}")
        
        try:
            # Try to get pre-extracted clauses first
            clauses_data = self.try_extract_nested_field_from_content(
                content=content,
                field_path=self.clauses_field
            )
            
            # Extract contract text
            contract_text = self.try_extract_nested_field_from_content(
                content=content,
                field_path=self.input_field
            )
            
            if not contract_text:
                # Try alternative field paths
                for alt_field in ["extracted_content.text", "text", "content", "markdown"]:
                    contract_text = self.try_extract_nested_field_from_content(
                        content=content,
                        field_path=alt_field
                    )
                    if contract_text:
                        break
            
            if not contract_text and not clauses_data:
                logger.warning(f"No contract text or clauses found in content {content.id}")
                content.data[self.output_field] = {"error": "No contract data found"}
                content.summary_data["risk_analysis_status"] = "failed"
                return
            
            # Analyze risks using AI
            risks = await self._analyze_risks(contract_text, clauses_data)
            
            # Calculate overall risk score
            risk_score = self._calculate_risk_score(risks)
            
            # Generate risk summary
            summary = self._generate_risk_summary(risks, risk_score)
            
            # Store results
            results = {
                "risks": risks,
                "risk_score": risk_score,
                "summary": summary,
                "metadata": {
                    "total_risks": len(risks),
                    "critical_risks": sum(1 for r in risks if r.get("severity") == "critical"),
                    "high_risks": sum(1 for r in risks if r.get("severity") == "high"),
                    "analysis_timestamp": datetime.now().isoformat(),
                }
            }
            
            content.data[self.output_field] = results
            content.summary_data["risk_analysis_status"] = "success"
            content.summary_data["risk_score"] = risk_score
            content.summary_data["critical_risks"] = results["metadata"]["critical_risks"]
            
        except Exception as e:
            logger.error(f"Error analyzing risks in content {content.id}: {e}")
            content.data[self.output_field] = {"error": str(e)}
            content.summary_data["risk_analysis_status"] = "failed"

    async def _analyze_risks(
        self,
        contract_text: Optional[str],
        clauses_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze risks in contract using AI."""
        # Build context for analysis
        context_parts = []
        
        if contract_text:
            # Truncate very long contracts
            max_length = 12000
            if len(contract_text) > max_length:
                logger.warning(f"Contract text truncated from {len(contract_text)} to {max_length} characters")
                contract_text = contract_text[:max_length] + "\n\n[Contract truncated for analysis]"
            context_parts.append(f"FULL CONTRACT TEXT:\n{contract_text}")
        
        if clauses_data and isinstance(clauses_data, dict):
            clauses = clauses_data.get("clauses", [])
            if clauses:
                clause_summary = "\n\n".join([
                    f"Clause: {c.get('clause_type', 'unknown')}\n{c.get('text', '')[:500]}"
                    for c in clauses[:10]  # Limit to first 10 clauses
                ])
                context_parts.append(f"\n\nEXTRACTED CLAUSES:\n{clause_summary}")
        
        context = "\n\n".join(context_parts)
        
        query = f"""
Analyze the following contract for risks and unfavorable terms:

{context}

Identify all significant risks, focusing on the specified risk categories.
Return the analysis in the specified JSON format.
"""
        
        try:
            result = await self.agent.run(query, store=False)
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            # Parse JSON response
            risks = self._parse_json_from_response(response_text)
            
            if not risks or not isinstance(risks, list):
                logger.warning("Failed to parse risks from LLM response")
                risks = []
            
            # Filter by risk threshold
            risks = self._filter_by_threshold(risks)
            
            return risks
            
        except Exception as e:
            logger.error(f"Error calling LLM for risk analysis: {e}")
            return []

    def _parse_json_from_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse JSON from LLM response."""
        try:
            # Try direct JSON parse
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON array in response
        import re
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON objects and combine them
        json_objects = re.findall(r'\{[\s\S]*?\}(?=\s*[,\]]|\s*$)', response)
        if json_objects:
            try:
                objects = [json.loads(obj) for obj in json_objects]
                return objects
            except json.JSONDecodeError:
                pass
        
        return []

    def _filter_by_threshold(self, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter risks by severity threshold."""
        threshold_order = ["informational", "low", "medium", "high", "critical"]
        threshold_index = threshold_order.index(self.risk_threshold.lower())
        
        return [
            risk for risk in risks
            if threshold_order.index(risk.get("severity", "low").lower()) >= threshold_index
        ]

    def _calculate_risk_score(self, risks: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score (0-100)."""
        if not risks:
            return 0.0
        
        total_weight = 0
        for risk in risks:
            severity = risk.get("severity", "low")
            try:
                weight = self.SEVERITY_WEIGHTS.get(RiskSeverity(severity.lower()), 25)
                total_weight += weight
            except ValueError:
                total_weight += 25  # Default to low
        
        # Normalize to 0-100 scale
        # Assume 5 medium risks = 100% (5 * 50 = 250)
        max_reasonable_score = 250
        risk_score = min(100.0, (total_weight / max_reasonable_score) * 100)
        
        return round(risk_score, 2)

    def _generate_risk_summary(self, risks: List[Dict[str, Any]], risk_score: float) -> Dict[str, Any]:
        """Generate executive summary of risk analysis."""
        # Categorize risks by severity
        by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "informational": []
        }
        
        for risk in risks:
            severity = risk.get("severity", "low").lower()
            by_severity.get(severity, by_severity["low"]).append(risk)
        
        # Determine overall risk rating
        if risk_score >= 75:
            rating = "HIGH_RISK"
            recommendation = "Significant risks identified. Recommend thorough legal review and substantial negotiation."
        elif risk_score >= 50:
            rating = "MODERATE_RISK"
            recommendation = "Several concerns identified. Recommend targeted negotiation on key terms."
        elif risk_score >= 25:
            rating = "LOW_RISK"
            recommendation = "Minor issues identified. Consider negotiating specific provisions."
        else:
            rating = "MINIMAL_RISK"
            recommendation = "Contract appears reasonable. Standard review recommended."
        
        # Identify top concerns
        top_concerns = sorted(
            [r for r in risks if r.get("severity") in ["critical", "high"]],
            key=lambda x: self.SEVERITY_WEIGHTS.get(RiskSeverity(x.get("severity", "low").lower()), 0),
            reverse=True
        )[:5]
        
        return {
            "overall_rating": rating,
            "risk_score": risk_score,
            "recommendation": recommendation,
            "risk_counts": {
                "critical": len(by_severity["critical"]),
                "high": len(by_severity["high"]),
                "medium": len(by_severity["medium"]),
                "low": len(by_severity["low"]),
            },
            "top_concerns": [
                {
                    "category": c.get("risk_category"),
                    "description": c.get("risk_description"),
                    "severity": c.get("severity")
                }
                for c in top_concerns
            ]
        }
