"""
Contract Clause Extractor Executor.

Extracts and classifies specific contract clauses using Azure OpenAI
for intelligent clause identification and obligation extraction.
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


class ClauseType(str, Enum):
    """Standard contract clause types."""
    INDEMNIFICATION = "indemnification"
    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    TERMINATION = "termination"
    PAYMENT_TERMS = "payment_terms"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    CONFIDENTIALITY = "confidentiality"
    FORCE_MAJEURE = "force_majeure"
    DISPUTE_RESOLUTION = "dispute_resolution"
    GOVERNING_LAW = "governing_law"
    WARRANTIES = "warranties"
    NON_COMPETE = "non_compete"
    ASSIGNMENT = "assignment"
    NOTICE_PROVISIONS = "notice_provisions"
    ENTIRE_AGREEMENT = "entire_agreement"


class ContractClauseExtractorExecutor(BaseExecutor):
    """
    Extract and classify contract clauses using AI.
    
    This executor uses Azure OpenAI to identify, extract, and analyze
    specific types of contract clauses, along with associated obligations,
    rights, and important dates.
    
    Configuration (settings dict):
        - clause_types (list): Types of clauses to extract
          Default: All standard clause types
        - extract_obligations (bool): Extract obligations from clauses
          Default: True
        - extract_rights (bool): Extract rights from clauses
          Default: True
        - extract_dates (bool): Extract important dates
          Default: True
        - include_context (bool): Include surrounding context for each clause
          Default: True
        - confidence_threshold (float): Minimum confidence for clause identification
          Default: 0.7
        - input_field (str): Field containing contract text
          Default: "extracted_content.markdown"
        - output_field (str): Field name for extracted clauses
          Default: "clauses"
        - endpoint (str): Azure OpenAI endpoint URL
        - deployment_name (str): Azure OpenAI model deployment name
        - temperature (float): Temperature for LLM
          Default: 0.3
    
    Expected Input Data Structure:
        {
            "extracted_content": {
                "markdown": "Full contract text...",
                "text": "Plain text version..."
            }
        }
    
    Output:
        Content with added fields:
        - data[output_field]: Dictionary containing extracted clauses
        - summary_data["clause_extraction_status"]: Execution status
    
    Example:
        ```yaml
        - id: clause-extractor-1
          type: contract_clause_extractor
          settings:
            clause_types:
              - indemnification
              - limitation_of_liability
              - termination
              - payment_terms
            extract_obligations: true
            extract_dates: true
            endpoint: "${AZURE_OPENAI_ENDPOINT}"
            deployment_name: "gpt-4"
        ```
    """
    
    CLAUSE_DEFINITIONS = {
        ClauseType.INDEMNIFICATION: "Provisions where one party agrees to compensate the other for certain damages or losses",
        ClauseType.LIMITATION_OF_LIABILITY: "Provisions that limit the financial or legal liability of one or both parties",
        ClauseType.TERMINATION: "Conditions and procedures for ending the contract",
        ClauseType.PAYMENT_TERMS: "Terms regarding payment amounts, schedules, methods, and conditions",
        ClauseType.INTELLECTUAL_PROPERTY: "Provisions regarding ownership, licensing, and use of intellectual property",
        ClauseType.CONFIDENTIALITY: "Obligations to protect confidential information",
        ClauseType.FORCE_MAJEURE: "Provisions addressing performance obligations during extraordinary events",
        ClauseType.DISPUTE_RESOLUTION: "Procedures for resolving disputes (arbitration, mediation, litigation)",
        ClauseType.GOVERNING_LAW: "Which jurisdiction's laws govern the contract",
        ClauseType.WARRANTIES: "Guarantees or representations made by parties",
        ClauseType.NON_COMPETE: "Restrictions on competitive activities",
        ClauseType.ASSIGNMENT: "Rights and restrictions on transferring the contract to third parties",
        ClauseType.NOTICE_PROVISIONS: "Requirements for providing notices under the contract",
        ClauseType.ENTIRE_AGREEMENT: "Statements that the contract represents the complete agreement",
    }
    
    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        
        # Configuration
        self.clause_types = self.get_setting("clause_types", list(self.CLAUSE_DEFINITIONS.keys()))
        self.extract_obligations = self.get_setting("extract_obligations", True)
        self.extract_rights = self.get_setting("extract_rights", True)
        self.extract_dates = self.get_setting("extract_dates", True)
        self.include_context = self.get_setting("include_context", True)
        self.confidence_threshold = self.get_setting("confidence_threshold", 0.7)
        self.input_field = self.get_setting("input_field", "extracted_content.markdown")
        self.output_field = self.get_setting("output_field", "clauses")
        
        # Azure OpenAI configuration
        self.endpoint = self.get_setting("endpoint", None)
        self.deployment_name = self.get_setting("deployment_name", None)
        self.temperature = self.get_setting("temperature", 0.3)
        
        # Initialize Azure OpenAI client
        credential = get_azure_credential()
        self.client = AzureOpenAIResponsesClient(
            endpoint=self.endpoint,
            deployment_name=self.deployment_name,
            credential=credential
        )
        
        # Create specialized agent for clause extraction
        self._init_agent()
        
        if self.debug_mode:
            logger.debug(
                f"ContractClauseExtractorExecutor initialized: "
                f"clause_types={self.clause_types}"
            )

    def _init_agent(self) -> None:
        """Initialize AI agent for clause extraction."""
        # Build clause definitions for the agent
        clause_defs = "\n".join([
            f"- {clause_type}: {self.CLAUSE_DEFINITIONS.get(ClauseType(clause_type), 'Standard clause')}"
            for clause_type in self.clause_types
        ])
        
        instructions = f"""
You are an expert contract analyst specializing in identifying and extracting contract clauses.

Your task is to analyze contract text and extract the following types of clauses:

{clause_defs}

For each clause you identify:
1. Provide the clause type from the list above
2. Extract the full text of the clause
3. Provide a brief summary (1-2 sentences)
4. Rate your confidence in the identification (0.0 to 1.0)
{"5. Extract any obligations mentioned in the clause" if self.extract_obligations else ""}
{"6. Extract any rights granted in the clause" if self.extract_rights else ""}
{"7. Extract any important dates or deadlines" if self.extract_dates else ""}

Return your response as a JSON array with the following structure:
[
  {{
    "clause_type": "clause type from list",
    "text": "full clause text",
    "summary": "brief summary",
    "confidence": 0.85,
    "section_reference": "Section number or heading if available"
    {"obligations": ["obligation 1", "obligation 2"]," if self.extract_obligations else ""}
    {"rights": ["right 1", "right 2"]," if self.extract_rights else ""}
    {"dates": [{"date": "date string", "description": "what the date relates to"}]" if self.extract_dates else ""}
  }}
]

Guidelines:
- Only extract clauses with confidence >= {self.confidence_threshold}
- Be precise in identifying clause boundaries
- Include the complete clause text without truncation
- Identify all instances even if a clause type appears multiple times
- Note any unusual or non-standard provisions
"""
        
        self.agent: ChatAgent = self.client.create_agent(
            id=f"{self.id}_agent",
            name="ContractClauseExtractor",
            instructions=instructions,
            temperature=self.temperature
        )

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """Process contract documents and extract clauses."""
        items_to_process = input if isinstance(input, list) else [input]
        
        for item in items_to_process:
            await self._process_single_content(item)
            
        return input

    async def _process_single_content(self, content: Content) -> None:
        """Process a single contract document and extract clauses."""
        logger.info(f"Extracting contract clauses from content {content.id}")
        
        try:
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
            
            if not contract_text:
                logger.warning(f"No contract text found in content {content.id}")
                content.data[self.output_field] = {"error": "No contract text found"}
                content.summary_data["clause_extraction_status"] = "failed"
                return
            
            # Extract clauses using AI
            clauses = await self._extract_clauses(contract_text)
            
            # Analyze clause patterns
            analysis = self._analyze_clause_patterns(clauses)
            
            # Store results
            results = {
                "clauses": clauses,
                "analysis": analysis,
                "metadata": {
                    "total_clauses": len(clauses),
                    "clause_types_found": list(set(c["clause_type"] for c in clauses)),
                    "extraction_timestamp": datetime.now().isoformat(),
                }
            }
            
            content.data[self.output_field] = results
            content.summary_data["clause_extraction_status"] = "success"
            content.summary_data["clauses_extracted"] = len(clauses)
            
        except Exception as e:
            logger.error(f"Error extracting clauses from content {content.id}: {e}")
            content.data[self.output_field] = {"error": str(e)}
            content.summary_data["clause_extraction_status"] = "failed"

    async def _extract_clauses(self, contract_text: str) -> List[Dict[str, Any]]:
        """Extract clauses from contract text using AI."""
        # Truncate very long contracts for better performance
        max_length = 15000  # characters
        if len(contract_text) > max_length:
            logger.warning(f"Contract text truncated from {len(contract_text)} to {max_length} characters")
            contract_text = contract_text[:max_length] + "\n\n[Contract truncated for analysis]"
        
        query = f"""
Analyze the following contract and extract all relevant clauses:

{contract_text}

Return the clauses in the specified JSON format.
"""
        
        try:
            result = await self.agent.run(query, store=False)
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            # Parse JSON response
            clauses = self._parse_json_from_response(response_text)
            
            if not clauses or not isinstance(clauses, list):
                logger.warning("Failed to parse clauses from LLM response")
                clauses = []
            
            # Filter by confidence threshold
            clauses = [c for c in clauses if c.get("confidence", 0) >= self.confidence_threshold]
            
            return clauses
            
        except Exception as e:
            logger.error(f"Error calling LLM for clause extraction: {e}")
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

    def _analyze_clause_patterns(self, clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in extracted clauses."""
        analysis = {
            "clause_type_distribution": {},
            "missing_standard_clauses": [],
            "duplicate_clauses": [],
            "unusual_provisions": [],
        }
        
        # Count clause types
        clause_type_counts = {}
        for clause in clauses:
            clause_type = clause.get("clause_type", "unknown")
            clause_type_counts[clause_type] = clause_type_counts.get(clause_type, 0) + 1
        
        analysis["clause_type_distribution"] = clause_type_counts
        
        # Identify missing standard clauses
        found_types = set(clause_type_counts.keys())
        expected_types = set(self.clause_types)
        missing = expected_types - found_types
        analysis["missing_standard_clauses"] = list(missing)
        
        # Identify duplicates (same clause type appearing multiple times)
        for clause_type, count in clause_type_counts.items():
            if count > 1:
                analysis["duplicate_clauses"].append({
                    "clause_type": clause_type,
                    "count": count,
                    "note": "Multiple instances found - review for conflicts"
                })
        
        # Identify clauses with low confidence as potentially unusual
        for clause in clauses:
            if clause.get("confidence", 1.0) < 0.8:
                analysis["unusual_provisions"].append({
                    "clause_type": clause.get("clause_type"),
                    "summary": clause.get("summary"),
                    "confidence": clause.get("confidence"),
                })
        
        return analysis

    def _extract_obligations_and_rights(self, clause_text: str) -> Dict[str, List[str]]:
        """Extract obligations and rights from clause text (simple pattern-based)."""
        result = {
            "obligations": [],
            "rights": [],
        }
        
        # Simple pattern matching for obligations
        obligation_patterns = [
            "shall", "must", "will", "agrees to", "is required to",
            "is obligated to", "undertakes to"
        ]
        
        rights_patterns = [
            "may", "has the right to", "is entitled to", "can",
            "is permitted to", "reserves the right"
        ]
        
        # Split into sentences
        sentences = clause_text.replace('\n', ' ').split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check for obligations
            if any(pattern in sentence.lower() for pattern in obligation_patterns):
                result["obligations"].append(sentence)
            
            # Check for rights
            if any(pattern in sentence.lower() for pattern in rights_patterns):
                result["rights"].append(sentence)
        
        return result
