"""PII detection executor using Azure OpenAI Agent."""

import logging
import json
from typing import Dict, Any, Optional

from .azure_openai_agent_executor import AzureOpenAIAgentExecutor
from ..models import Content

logger = logging.getLogger(__name__)


class PIIDetectorExecutor(AzureOpenAIAgentExecutor):
    """
    Specialized executor for detecting Personally Identifiable Information (PII).
    
    This executor identifies and optionally redacts various types of PII such as
    names, email addresses, phone numbers, SSNs, credit cards, addresses, etc.
    
    Configuration (settings dict):
        - pii_types (list[str]): Types of PII to detect
          Options: "name", "email", "phone", "ssn", "credit_card", "address",
                   "date_of_birth", "passport", "license", "ip_address", 
                   "bank_account", "custom"
          Default: ["name", "email", "phone", "ssn", "credit_card", "address"]
        - action (str): What to do with detected PII
          Options: "detect" (only detect), "redact" (replace with [REDACTED]),
                   "mask" (replace with ***), "label" (tag in text)
          Default: "detect"
        - include_positions (bool): Include character positions of PII
          Default: True
        - confidence_threshold (float): Minimum confidence to report (0-1)
          Default: 0.7
        - custom_patterns (list[str]): Custom PII patterns to look for
          Default: None
        - input_field (str): Field containing text to analyze
          Default: "text"
        - output_field (str): Field name for PII detection results
          Default: "pii_detected"
        - redacted_field (str): Field for redacted text (if action != "detect")
          Default: "text_redacted"
        
        All AzureOpenAIAgentExecutor settings are also supported.
    
    Example:
        ```python
        executor = PIIDetectorExecutor(
            id="pii_detector",
            settings={
                "endpoint": "https://your-endpoint/",
                "deployment_name": "gpt-4",
                "pii_types": ["name", "email", "phone", "ssn"],
                "action": "redact",
                "include_positions": True,
                "input_field": "text",
                "output_field": "pii_detected",
                "redacted_field": "text_redacted"
            }
        )
        ```
    
    Input:
        Document with:
        - data[input_field]: Text to analyze for PII
        
    Output:
        Document with added fields:
        - data[output_field]: Detected PII (JSON format)
        - data[redacted_field]: Redacted text (if action != "detect")
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Extract PII-specific settings
        settings = settings or {}
        pii_types = settings.get("pii_types", 
            ["name", "email", "phone", "ssn", "credit_card", "address"])
        action = settings.get("action", "detect")
        include_positions = settings.get("include_positions", True)
        confidence_threshold = settings.get("confidence_threshold", 0.7)
        custom_patterns = settings.get("custom_patterns", None)
        
        # Build specialized instructions
        instructions = "You are an expert PII (Personally Identifiable Information) detection system. "
        instructions += f"Detect the following types of PII in the text: {', '.join(pii_types)}. "
        
        if custom_patterns:
            instructions += f"Also look for these custom PII patterns: {', '.join(custom_patterns)}. "
        
        instructions += f"Only report PII with confidence >= {confidence_threshold}. "
        
        # PII type descriptions for better accuracy
        pii_descriptions = {
            "name": "person names (first, last, full names)",
            "email": "email addresses",
            "phone": "phone numbers in any format",
            "ssn": "social security numbers (XXX-XX-XXXX)",
            "credit_card": "credit card numbers",
            "address": "physical addresses (street, city, state, zip)",
            "date_of_birth": "dates of birth",
            "passport": "passport numbers",
            "license": "driver's license numbers",
            "ip_address": "IP addresses",
            "bank_account": "bank account numbers"
        }
        
        instructions += "\n\nPII Types to detect:\n"
        for pii_type in pii_types:
            if pii_type in pii_descriptions:
                instructions += f"- {pii_type}: {pii_descriptions[pii_type]}\n"
        
        # Define output format based on action
        if action == "detect":
            instructions += "\n\nReturn results as a JSON object listing all detected PII. "
            if include_positions:
                instructions += 'Format: {"pii_found": [{"type": "pii_type", "value": "actual_value", "position": {"start": 0, "end": 10}, "confidence": 0.0-1.0}], "count": 0}. '
            else:
                instructions += 'Format: {"pii_found": [{"type": "pii_type", "value": "actual_value", "confidence": 0.0-1.0}], "count": 0}. '
        elif action in ["redact", "mask", "label"]:
            instructions += f"\n\nDetect PII and {action} it in the text. "
            instructions += "\n\nReturn results as a JSON object with two fields: "
            instructions += '1. "pii_found": list of detected PII '
            instructions += f'2. "{action}ed_text": the text with PII {action}ed. '
            
            if action == "redact":
                instructions += 'Replace each PII item with [REDACTED-TYPE] (e.g., [REDACTED-EMAIL]). '
            elif action == "mask":
                instructions += 'Replace each PII item with asterisks (***). '
            elif action == "label":
                instructions += 'Wrap each PII item with tags like <PII-TYPE>value</PII-TYPE>. '
            
            if include_positions:
                instructions += 'Format: {"pii_found": [{"type": "...", "value": "...", "position": {...}, "confidence": 0.0-1.0}], '
            else:
                instructions += 'Format: {"pii_found": [{"type": "...", "value": "...", "confidence": 0.0-1.0}], '
            
            instructions += f'"{action}ed_text": "text with PII {action}ed", "count": 0}}. '
        
        instructions += "\n\nBe thorough but conservative - only flag items you are confident are PII. "
        instructions += "Avoid false positives."
        
        # Set default fields
        if "input_field" not in settings:
            settings["input_field"] = "text"
        if "output_field" not in settings:
            settings["output_field"] = "pii_detected"
        
        # Store action and redacted field for post-processing
        self.pii_action = action
        self.redacted_field = settings.get("redacted_field", "text_redacted")
        
        # Override instructions
        settings["instructions"] = instructions
        
        # Call parent constructor
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        if self.debug_mode:
            logger.debug(
                f"PIIDetectorExecutor initialized with action={action}, "
                f"pii_types={pii_types}"
            )
    
    async def process_content_item(self, content: Content) -> Content:
        """Process content and parse JSON PII output."""
        content = await super().process_content_item(content)
        
        logger.debug(f"Processing PII detection results for content id={content.id}")
        
        # Try to parse JSON response
        if self.output_field in content.data:
            try:
                response_text = content.data[self.output_field]
                logger.debug(f"Raw PII detection response: {response_text}")
                
                if isinstance(response_text, str):
                    # Look for JSON block in the response
                    start = response_text.find('{')
                    end = response_text.rfind('}')
                    if start != -1 and end != -1:
                        json_str = response_text[start:end+1]
                        parsed = json.loads(json_str)
                        content.data[self.output_field] = parsed
                        
                        logger.debug(f"Parsed PII detection JSON: {parsed}")
                        
                        # Extract redacted text if action is not just detect
                        if self.pii_action != "detect" and f"{self.pii_action}ed_text" in parsed:
                            content.data[self.redacted_field] = parsed[f"{self.pii_action}ed_text"]
                        
                        # Add PII count to summary
                        if "count" in parsed:
                            content.summary_data['pii_count'] = parsed["count"]
                        elif "pii_found" in parsed:
                            content.summary_data['pii_count'] = len(parsed["pii_found"])
                            
            except json.JSONDecodeError:
                logger.warning(f"Could not parse PII detection as JSON for {content.id}")
        
        return content
