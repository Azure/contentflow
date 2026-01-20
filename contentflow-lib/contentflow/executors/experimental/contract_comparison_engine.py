"""
Contract Comparison Engine Executor.

Compares contracts against templates or previous versions to identify
deviations, inconsistencies, and non-standard provisions.
"""

import logging
import json
from typing import List, Union, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from difflib import SequenceMatcher
import re

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


class ComparisonMode(str, Enum):
    """Contract comparison modes."""
    TEMPLATE = "template"
    PREVIOUS_CONTRACT = "previous_contract"
    MULTI_VERSION = "multi_version"
    CLAUSE_BY_CLAUSE = "clause_by_clause"


class DeviationType(str, Enum):
    """Types of deviations."""
    MISSING_CLAUSE = "missing_clause"
    ADDED_CLAUSE = "added_clause"
    MODIFIED_TERMS = "modified_terms"
    DIFFERENT_WORDING = "different_wording"
    NUMERIC_DEVIATION = "numeric_deviation"


class ContractComparisonEngineExecutor(BaseExecutor):
    """
    Compare contracts against templates or previous versions.
    
    This executor uses a combination of text similarity analysis and AI-powered
    semantic comparison to identify deviations, non-standard provisions, and
    changes between contract versions.
    
    Configuration (settings dict):
        - comparison_mode (str): Mode of comparison (template, previous_contract, multi_version)
          Default: "template"
        - template_source (str): Path to template contract or field containing template
          Default: None (uses built-in standard template)
        - previous_contract_field (str): Field containing previous contract version
          Default: "previous_contract"
        - highlight_deviations (bool): Highlight specific deviations
          Default: True
        - deviation_threshold (float): Similarity threshold for flagging deviations (0.0-1.0)
          Default: 0.3
        - semantic_comparison (bool): Use AI for semantic comparison
          Default: True
        - include_suggestions (bool): Include suggestions for standardization
          Default: True
        - input_field (str): Field containing current contract text
          Default: "extracted_content.markdown"
        - clauses_field (str): Field containing pre-extracted clauses (optional)
          Default: "clauses"
        - output_field (str): Field name for comparison results
          Default: "comparison_results"
        - endpoint (str): Azure OpenAI endpoint URL
        - deployment_name (str): Azure OpenAI model deployment name
        - temperature (float): Temperature for LLM
          Default: 0.3
    
    Expected Input Data Structure:
        {
            "extracted_content": {
                "markdown": "Current contract text..."
            },
            "previous_contract": "Previous version text...",  # Optional
            "clauses": {  # Optional
                "clauses": [...]
            }
        }
    
    Output:
        Content with added fields:
        - data[output_field]: Dictionary containing comparison results
        - summary_data["comparison_status"]: Execution status
        - summary_data["deviation_count"]: Number of deviations found
    
    Example:
        ```yaml
        - id: comparison-engine-1
          type: contract_comparison_engine
          settings:
            comparison_mode: template
            deviation_threshold: 0.3
            semantic_comparison: true
            highlight_deviations: true
            endpoint: "${AZURE_OPENAI_ENDPOINT}"
            deployment_name: "gpt-4"
        ```
    """
    
    # Standard contract template for comparison
    STANDARD_TEMPLATE_CLAUSES = {
        "payment_terms": "Payment shall be made within thirty (30) days of invoice date. Late payments shall accrue interest at 1.5% per month.",
        "termination": "Either party may terminate this Agreement with sixty (60) days written notice. Termination for cause may be immediate upon written notice.",
        "liability_cap": "Except for breaches of confidentiality or IP rights, neither party's liability shall exceed the total fees paid in the twelve (12) months preceding the claim.",
        "confidentiality": "Each party shall maintain the confidentiality of the other party's Confidential Information for a period of three (3) years from disclosure.",
        "intellectual_property": "Each party retains ownership of its pre-existing IP. Any jointly developed IP shall be jointly owned.",
        "dispute_resolution": "Disputes shall first be resolved through good faith negotiation, then mediation, and finally binding arbitration.",
        "governing_law": "This Agreement shall be governed by the laws of [Jurisdiction], without regard to conflicts of law principles.",
        "force_majeure": "Neither party shall be liable for failure to perform due to circumstances beyond its reasonable control.",
        "assignment": "Neither party may assign this Agreement without the prior written consent of the other party.",
        "entire_agreement": "This Agreement constitutes the entire agreement between the parties and supersedes all prior agreements.",
    }

    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        
        # Configuration
        self.comparison_mode = self.get_setting("comparison_mode", ComparisonMode.TEMPLATE)
        self.template_source = self.get_setting("template_source", None)
        self.previous_contract_field = self.get_setting("previous_contract_field", "previous_contract")
        self.highlight_deviations = self.get_setting("highlight_deviations", True)
        self.deviation_threshold = self.get_setting("deviation_threshold", 0.3)
        self.semantic_comparison = self.get_setting("semantic_comparison", True)
        self.include_suggestions = self.get_setting("include_suggestions", True)
        self.input_field = self.get_setting("input_field", "extracted_content.markdown")
        self.clauses_field = self.get_setting("clauses_field", "clauses")
        self.output_field = self.get_setting("output_field", "comparison_results")
        
        # Azure OpenAI configuration
        self.endpoint = self.get_setting("endpoint", None)
        self.deployment_name = self.get_setting("deployment_name", None)
        self.temperature = self.get_setting("temperature", 0.3)
        
        # Initialize Azure OpenAI client if semantic comparison is enabled
        if self.semantic_comparison:
            credential = get_azure_credential()
            self.client = AzureOpenAIResponsesClient(
                endpoint=self.endpoint,
                deployment_name=self.deployment_name,
                credential=credential
            )
            self._init_agent()
        else:
            self.agent = None
        
        if self.debug_mode:
            logger.debug(
                f"ContractComparisonEngineExecutor initialized: "
                f"mode={self.comparison_mode}, threshold={self.deviation_threshold}"
            )

    def _init_agent(self) -> None:
        """Initialize AI agent for semantic comparison."""
        instructions = f"""
You are an expert contract analyst specializing in comparing contracts and identifying deviations from standard terms.

Your task is to perform semantic comparison between two contract versions or between a contract and a standard template.

When comparing contracts:
1. Identify clauses that are missing from the current contract but present in the reference
2. Identify clauses that are added in the current contract
3. Identify clauses with modified terms (substantive changes, not just wording)
4. Identify numeric or date changes (payment amounts, notice periods, etc.)
5. Assess whether changes are favorable, neutral, or unfavorable
6. Note any non-standard or unusual provisions
{"7. Provide suggestions for standardization" if self.include_suggestions else ""}

Focus on substantive differences, not minor wording variations.

Return your response as a JSON object with the following structure:
{{
  "deviations": [
    {{
      "deviation_type": "missing_clause|added_clause|modified_terms|numeric_deviation",
      "clause_type": "payment_terms, termination, etc.",
      "description": "clear description of the deviation",
      "reference_text": "text from reference/template",
      "current_text": "text from current contract",
      "impact_assessment": "favorable|neutral|unfavorable",
      "significance": "high|medium|low",
      {"suggestion": "recommendation for standardization"," if self.include_suggestions else ""}
      "details": "additional context"
    }}
  ],
  "summary": {{
    "total_deviations": 0,
    "favorable_changes": 0,
    "unfavorable_changes": 0,
    "missing_standard_clauses": [],
    "non_standard_provisions": []
  }}
}}
"""
        
        self.agent: ChatAgent = self.client.create_agent(
            id=f"{self.id}_agent",
            name="ContractComparisonEngine",
            instructions=instructions,
            temperature=self.temperature
        )

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """Process contract documents and compare them."""
        items_to_process = input if isinstance(input, list) else [input]
        
        for item in items_to_process:
            await self._process_single_content(item)
            
        return input

    async def _process_single_content(self, content: Content) -> None:
        """Process a single contract document and compare it."""
        logger.info(f"Comparing contract in content {content.id}")
        
        try:
            # Extract current contract text
            current_text = self.try_extract_nested_field_from_content(
                content=content,
                field_path=self.input_field
            )
            
            if not current_text:
                # Try alternative field paths
                for alt_field in ["extracted_content.text", "text", "content", "markdown"]:
                    current_text = self.try_extract_nested_field_from_content(
                        content=content,
                        field_path=alt_field
                    )
                    if current_text:
                        break
            
            if not current_text:
                logger.warning(f"No contract text found in content {content.id}")
                content.data[self.output_field] = {"error": "No contract text found"}
                content.summary_data["comparison_status"] = "failed"
                return
            
            # Get reference contract (template or previous version)
            reference_text = self._get_reference_contract(content)
            
            if not reference_text:
                logger.warning(f"No reference contract available for comparison")
                content.data[self.output_field] = {"error": "No reference contract available"}
                content.summary_data["comparison_status"] = "failed"
                return
            
            # Get pre-extracted clauses if available
            clauses_data = self.try_extract_nested_field_from_content(
                content=content,
                field_path=self.clauses_field
            )
            
            # Perform comparison
            if self.semantic_comparison and self.agent:
                results = await self._semantic_comparison(current_text, reference_text, clauses_data)
            else:
                results = self._textual_comparison(current_text, reference_text, clauses_data)
            
            # Store results
            results["metadata"] = {
                "comparison_mode": self.comparison_mode,
                "deviation_threshold": self.deviation_threshold,
                "comparison_timestamp": datetime.now().isoformat(),
            }
            
            content.data[self.output_field] = results
            content.summary_data["comparison_status"] = "success"
            content.summary_data["deviation_count"] = results.get("summary", {}).get("total_deviations", 0)
            
        except Exception as e:
            logger.error(f"Error comparing contract in content {content.id}: {e}")
            content.data[self.output_field] = {"error": str(e)}
            content.summary_data["comparison_status"] = "failed"

    def _get_reference_contract(self, content: Content) -> Optional[str]:
        """Get reference contract for comparison."""
        if self.comparison_mode == ComparisonMode.TEMPLATE:
            # Use provided template or built-in standard
            if self.template_source:
                # Try to load from file or field
                template = self.try_extract_nested_field_from_content(
                    content=content,
                    field_path=self.template_source
                )
                if template:
                    return template
            
            # Use built-in standard template
            return self._build_standard_template()
            
        elif self.comparison_mode == ComparisonMode.PREVIOUS_CONTRACT:
            # Get previous contract version
            previous = self.try_extract_nested_field_from_content(
                content=content,
                field_path=self.previous_contract_field
            )
            return previous
        
        return None

    def _build_standard_template(self) -> str:
        """Build standard template from built-in clauses."""
        template_parts = []
        for clause_type, clause_text in self.STANDARD_TEMPLATE_CLAUSES.items():
            template_parts.append(f"## {clause_type.replace('_', ' ').title()}\n\n{clause_text}\n")
        
        return "\n".join(template_parts)

    async def _semantic_comparison(
        self,
        current_text: str,
        reference_text: str,
        clauses_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform semantic comparison using AI."""
        # Truncate very long texts
        max_length = 10000
        if len(current_text) > max_length:
            current_text = current_text[:max_length] + "\n\n[Truncated]"
        if len(reference_text) > max_length:
            reference_text = reference_text[:max_length] + "\n\n[Truncated]"
        
        query = f"""
Compare the following contracts and identify all significant deviations:

REFERENCE CONTRACT (Template/Previous Version):
{reference_text}

CURRENT CONTRACT:
{current_text}

Perform a thorough comparison and return the analysis in the specified JSON format.
Focus on substantive differences that could impact rights, obligations, or risk exposure.
"""
        
        try:
            result = await self.agent.run(query, store=False)
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            # Parse JSON response
            comparison_results = self._parse_json_from_response(response_text)
            
            if not comparison_results or not isinstance(comparison_results, dict):
                logger.warning("Failed to parse comparison results from LLM response")
                # Fallback to textual comparison
                return self._textual_comparison(current_text, reference_text, clauses_data)
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Error in semantic comparison: {e}")
            # Fallback to textual comparison
            return self._textual_comparison(current_text, reference_text, clauses_data)

    def _textual_comparison(
        self,
        current_text: str,
        reference_text: str,
        clauses_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform textual comparison using sequence matching."""
        # Calculate overall similarity
        similarity = SequenceMatcher(None, reference_text, current_text).ratio()
        
        # Find added/removed sections
        deviations = []
        
        # Split into paragraphs for comparison
        ref_paragraphs = [p.strip() for p in reference_text.split('\n\n') if p.strip()]
        curr_paragraphs = [p.strip() for p in current_text.split('\n\n') if p.strip()]
        
        # Find missing paragraphs
        for ref_para in ref_paragraphs:
            best_match_ratio = 0
            for curr_para in curr_paragraphs:
                ratio = SequenceMatcher(None, ref_para, curr_para).ratio()
                best_match_ratio = max(best_match_ratio, ratio)
            
            if best_match_ratio < self.deviation_threshold:
                deviations.append({
                    "deviation_type": "missing_clause",
                    "clause_type": self._infer_clause_type(ref_para),
                    "description": "Clause from reference not found in current contract",
                    "reference_text": ref_para[:200] + "..." if len(ref_para) > 200 else ref_para,
                    "current_text": None,
                    "impact_assessment": "unfavorable",
                    "significance": "high" if best_match_ratio == 0 else "medium",
                    "similarity_score": best_match_ratio,
                })
        
        # Find added paragraphs
        for curr_para in curr_paragraphs:
            best_match_ratio = 0
            for ref_para in ref_paragraphs:
                ratio = SequenceMatcher(None, curr_para, ref_para).ratio()
                best_match_ratio = max(best_match_ratio, ratio)
            
            if best_match_ratio < self.deviation_threshold:
                deviations.append({
                    "deviation_type": "added_clause",
                    "clause_type": self._infer_clause_type(curr_para),
                    "description": "New clause not present in reference",
                    "reference_text": None,
                    "current_text": curr_para[:200] + "..." if len(curr_para) > 200 else curr_para,
                    "impact_assessment": "neutral",
                    "significance": "medium",
                    "similarity_score": best_match_ratio,
                })
        
        # Generate summary
        summary = {
            "total_deviations": len(deviations),
            "overall_similarity": round(similarity, 3),
            "missing_clauses": sum(1 for d in deviations if d["deviation_type"] == "missing_clause"),
            "added_clauses": sum(1 for d in deviations if d["deviation_type"] == "added_clause"),
            "assessment": self._assess_overall_deviation(similarity, deviations),
        }
        
        return {
            "deviations": deviations,
            "summary": summary,
        }

    def _infer_clause_type(self, text: str) -> str:
        """Infer clause type from text content."""
        text_lower = text.lower()
        
        keywords = {
            "payment": ["payment", "invoice", "fee", "compensation", "pay"],
            "termination": ["terminate", "termination", "cancel", "cancellation"],
            "liability": ["liability", "liable", "indemnify", "indemnification"],
            "confidentiality": ["confidential", "confidentiality", "secret", "proprietary"],
            "intellectual_property": ["intellectual property", "ip", "copyright", "patent", "trademark"],
            "dispute_resolution": ["dispute", "arbitration", "mediation", "litigation"],
            "governing_law": ["governing law", "jurisdiction", "applicable law"],
            "force_majeure": ["force majeure", "act of god", "beyond control"],
            "assignment": ["assign", "assignment", "transfer"],
            "warranty": ["warranty", "warrant", "guarantee", "representation"],
        }
        
        for clause_type, keywords_list in keywords.items():
            if any(keyword in text_lower for keyword in keywords_list):
                return clause_type
        
        return "general"

    def _assess_overall_deviation(self, similarity: float, deviations: List[Dict[str, Any]]) -> str:
        """Assess overall deviation level."""
        if similarity > 0.9 and len(deviations) < 3:
            return "minimal_deviation"
        elif similarity > 0.7 and len(deviations) < 5:
            return "moderate_deviation"
        else:
            return "significant_deviation"

    def _parse_json_from_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        try:
            # Try direct JSON parse
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON object in response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        return {}
