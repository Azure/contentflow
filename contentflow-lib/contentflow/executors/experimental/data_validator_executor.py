"""
Data Validator Executor for validating extracted data against business rules.

This executor validates content data against configurable validation rules including
required fields, data types, ranges, and custom validation logic.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from decimal import Decimal, InvalidOperation

try:
    from agent_framework.azure import AzureOpenAIResponsesClient
    from agent_framework import ChatAgent
except ImportError:
    raise ImportError(
        "agent-framework and azure-identity are required for AI-powered validation. "
        "Install them with: pip install agent-framework azure-identity"
    )

from ...utils.credential_provider import get_azure_credential
from .. import ParallelExecutor
from ...models import Content

logger = logging.getLogger("contentflow.executors.experimental.data_validator_executor")


class DataValidatorExecutor(ParallelExecutor):
    """
    Validate extracted data against business rules and constraints.
    
    This executor validates content data using a combination of rule-based
    validation (required fields, data types, ranges) and optional AI-powered
    validation for complex business logic.
    
    Configuration (settings dict):
        - validation_rules (dict): Validation rules configuration
          Structure: {
              "required_fields": ["field1", "field2"],
              "field_validations": {
                  "field_name": {
                      "type": "string|number|date|boolean",
                      "min": value,  # for numbers/dates
                      "max": value,  # for numbers/dates
                      "pattern": "regex",  # for strings
                      "allowed_values": ["val1", "val2"]
                  }
              },
              "cross_field_validations": [
                  {
                      "description": "Validation description",
                      "fields": ["field1", "field2"],
                      "validation_type": "sum_match|date_order|custom",
                      "target_field": "field3",  # for sum_match
                      "tolerance": 0.01  # for numeric comparisons
                  }
              ]
          }
        - use_ai_validation (bool): Enable AI-powered validation
          Default: False
        - ai_validation_instructions (str): Instructions for AI validation
          Default: None
        - endpoint (str): Azure OpenAI endpoint for AI validation
          Default: None
        - deployment_name (str): Azure OpenAI deployment name
          Default: None
        - credential_type (str): Azure credential type
          Default: "default_azure_credential"
        - api_key (str): API key for Azure OpenAI
          Default: None
        - output_field (str): Field name for validation results
          Default: "validation_result"
        - include_validation_details (bool): Include detailed validation info
          Default: True
        - fail_on_validation_error (bool): Fail pipeline if validation fails
          Default: False (differs from fail_pipeline_on_error)
    
    Example:
        ```python
        executor = DataValidatorExecutor(
            id="invoice_validator",
            settings={
                "validation_rules": {
                    "required_fields": ["invoice_number", "vendor_name", "total_amount"],
                    "field_validations": {
                        "total_amount": {
                            "type": "number",
                            "min": 0
                        },
                        "invoice_date": {
                            "type": "date"
                        }
                    },
                    "cross_field_validations": [
                        {
                            "description": "Line items sum to total",
                            "fields": ["line_items"],
                            "validation_type": "sum_match",
                            "target_field": "total_amount",
                            "tolerance": 0.01
                        }
                    ]
                },
                "use_ai_validation": True,
                "ai_validation_instructions": "Verify the invoice data is reasonable and consistent",
                "output_field": "validation_result",
                "fail_on_validation_error": False
            }
        )
        ```
    
    Input:
        Content or List[Content] with data fields to validate
        
    Output:
        Content or List[Content] with added fields:
        - data[output_field]: Validation result summary
          {
              "is_valid": bool,
              "errors": [{"field": str, "error": str, "severity": str}],
              "warnings": [{"field": str, "warning": str}],
              "validation_score": float  # 0.0 to 1.0
          }
        - summary_data['validation_status']: "passed" | "failed" | "warnings"
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        # Extract validation configuration
        self.validation_rules = self.get_setting("validation_rules", default={})
        self.use_ai_validation = self.get_setting("use_ai_validation", default=False)
        self.ai_validation_instructions = self.get_setting("ai_validation_instructions", default=None)
        self.output_field = self.get_setting("output_field", default="validation_result")
        self.include_validation_details = self.get_setting("include_validation_details", default=True)
        self.fail_on_validation_error = self.get_setting("fail_on_validation_error", default=False)
        
        # AI validation setup
        self.agent = None
        if self.use_ai_validation:
            self.endpoint = self.get_setting("endpoint", default=None)
            self.deployment_name = self.get_setting("deployment_name", default=None)
            self.credential_type = self.get_setting("credential_type", default="default_azure_credential")
            self.api_key = self.get_setting("api_key", default=None)
            
            if not self.ai_validation_instructions:
                self.ai_validation_instructions = (
                    "You are a data validation expert. Review the provided data and identify "
                    "any inconsistencies, anomalies, or issues. Return a JSON object with "
                    "'is_valid' (boolean) and 'issues' (array of issue descriptions)."
                )
            
            # Initialize AI client
            credential = None
            if self.credential_type == "default_azure_credential":
                credential = get_azure_credential()
            elif self.credential_type == "azure_key_credential":
                if not self.api_key:
                    raise ValueError(f"{self.id}: api_key required for azure_key_credential")
            
            client_kwargs = {
                'deployment_name': self.deployment_name,
                'endpoint': self.endpoint,
                'credential': credential if self.credential_type == "default_azure_credential" else None,
                'api_key': self.api_key if self.credential_type == "azure_key_credential" else None,
            }
            
            self.client = AzureOpenAIResponsesClient(**client_kwargs)
            
            # Create agent
            self.agent: ChatAgent = self.client.create_agent(
                id=f"{self.id}_validation_agent",
                name=f"{self.id}_validation_agent",
                instructions=self.ai_validation_instructions
            )
        
        if self.debug_mode:
            logger.debug(
                f"DataValidatorExecutor {self.id} initialized: "
                f"ai_validation={self.use_ai_validation}"
            )
    
    async def process_content_item(
        self,
        content: Content
    ) -> Content:
        """Validate a single content item."""
        
        try:
            if not content or not content.data:
                raise ValueError("Content must have data")
            
            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "validation_score": 1.0
            }
            
            # Rule-based validation
            await self._validate_required_fields(content, validation_result)
            await self._validate_field_types_and_constraints(content, validation_result)
            await self._validate_cross_field_rules(content, validation_result)
            
            # AI-powered validation (optional)
            if self.use_ai_validation and self.agent:
                await self._validate_with_ai(content, validation_result)
            
            # Calculate overall validation score
            total_checks = len(validation_result["errors"]) + len(validation_result["warnings"]) + 1
            error_weight = len(validation_result["errors"]) * 1.0
            warning_weight = len(validation_result["warnings"]) * 0.3
            validation_result["validation_score"] = max(0.0, 1.0 - (error_weight + warning_weight) / total_checks)
            
            # Determine overall status
            if validation_result["errors"]:
                validation_result["is_valid"] = False
                content.summary_data['validation_status'] = "failed"
            elif validation_result["warnings"]:
                content.summary_data['validation_status'] = "warnings"
            else:
                content.summary_data['validation_status'] = "passed"
            
            # Store validation result
            if self.include_validation_details:
                content.data[self.output_field] = validation_result
            else:
                content.data[self.output_field] = {
                    "is_valid": validation_result["is_valid"],
                    "validation_score": validation_result["validation_score"],
                    "error_count": len(validation_result["errors"]),
                    "warning_count": len(validation_result["warnings"])
                }
            
            if self.debug_mode:
                logger.debug(
                    f"Validation for {content.id}: "
                    f"valid={validation_result['is_valid']}, "
                    f"errors={len(validation_result['errors'])}, "
                    f"warnings={len(validation_result['warnings'])}"
                )
            
            # Optionally fail on validation error
            if self.fail_on_validation_error and not validation_result["is_valid"]:
                error_details = "; ".join([e["error"] for e in validation_result["errors"]])
                raise ValueError(f"Validation failed: {error_details}")
        
        except Exception as e:
            logger.error(
                f"DataValidatorExecutor {self.id} failed validating content {content.id}",
                exc_info=True
            )
            raise
        
        return content
    
    async def _validate_required_fields(
        self,
        content: Content,
        validation_result: Dict[str, Any]
    ) -> None:
        """Validate that required fields are present."""
        required_fields = self.validation_rules.get("required_fields", [])
        
        for field in required_fields:
            value = self.try_extract_nested_field_from_content(content, field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                validation_result["errors"].append({
                    "field": field,
                    "error": f"Required field '{field}' is missing or empty",
                    "severity": "error"
                })
    
    async def _validate_field_types_and_constraints(
        self,
        content: Content,
        validation_result: Dict[str, Any]
    ) -> None:
        """Validate field types and constraints."""
        field_validations = self.validation_rules.get("field_validations", {})
        
        for field, rules in field_validations.items():
            value = self.try_extract_nested_field_from_content(content, field)
            
            if value is None:
                continue  # Skip if field not present (caught by required_fields check)
            
            # Type validation
            expected_type = rules.get("type")
            if expected_type:
                if not self._validate_type(value, expected_type):
                    validation_result["errors"].append({
                        "field": field,
                        "error": f"Field '{field}' has invalid type. Expected {expected_type}",
                        "severity": "error"
                    })
                    continue
            
            # Range validation for numbers
            if expected_type == "number":
                try:
                    num_value = float(value)
                    if "min" in rules and num_value < rules["min"]:
                        validation_result["errors"].append({
                            "field": field,
                            "error": f"Field '{field}' value {num_value} is below minimum {rules['min']}",
                            "severity": "error"
                        })
                    if "max" in rules and num_value > rules["max"]:
                        validation_result["errors"].append({
                            "field": field,
                            "error": f"Field '{field}' value {num_value} exceeds maximum {rules['max']}",
                            "severity": "error"
                        })
                except (ValueError, TypeError):
                    pass  # Type error already caught above
            
            # Pattern validation for strings
            if expected_type == "string" and "pattern" in rules:
                import re
                if not re.match(rules["pattern"], str(value)):
                    validation_result["errors"].append({
                        "field": field,
                        "error": f"Field '{field}' does not match required pattern",
                        "severity": "error"
                    })
            
            # Allowed values validation
            if "allowed_values" in rules:
                if value not in rules["allowed_values"]:
                    validation_result["warnings"].append({
                        "field": field,
                        "warning": f"Field '{field}' value '{value}' not in allowed values: {rules['allowed_values']}"
                    })
    
    async def _validate_cross_field_rules(
        self,
        content: Content,
        validation_result: Dict[str, Any]
    ) -> None:
        """Validate cross-field business rules."""
        cross_validations = self.validation_rules.get("cross_field_validations", [])
        
        for rule in cross_validations:
            validation_type = rule.get("validation_type")
            
            if validation_type == "sum_match":
                await self._validate_sum_match(content, rule, validation_result)
            elif validation_type == "date_order":
                await self._validate_date_order(content, rule, validation_result)
            elif validation_type == "custom":
                # Custom validations can be extended here
                pass
    
    async def _validate_sum_match(
        self,
        content: Content,
        rule: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> None:
        """Validate that sum of field values matches target."""
        fields = rule.get("fields", [])
        target_field = rule.get("target_field")
        tolerance = rule.get("tolerance", 0.01)
        description = rule.get("description", "Sum validation")
        
        if not fields or not target_field:
            return
        
        try:
            # Get target value
            target_value = self.try_extract_nested_field_from_content(content, target_field)
            if target_value is None:
                return
            
            target_value = float(target_value)
            
            # Calculate sum
            total = 0.0
            for field in fields:
                field_value = self.try_extract_nested_field_from_content(content, field)
                
                # Handle list of items (e.g., line_items)
                if isinstance(field_value, list):
                    for item in field_value:
                        if isinstance(item, dict):
                            # Look for amount/total/price fields
                            amount = item.get("amount") or item.get("total") or item.get("price") or 0
                            total += float(amount)
                        else:
                            total += float(item)
                else:
                    total += float(field_value) if field_value else 0
            
            # Check if sum matches target within tolerance
            diff = abs(total - target_value)
            if diff > tolerance:
                validation_result["errors"].append({
                    "field": target_field,
                    "error": f"{description}: Sum ({total}) does not match target ({target_value}). Difference: {diff}",
                    "severity": "error"
                })
        
        except (ValueError, TypeError) as e:
            validation_result["warnings"].append({
                "field": target_field,
                "warning": f"{description}: Unable to validate sum due to data type issue: {str(e)}"
            })
    
    async def _validate_date_order(
        self,
        content: Content,
        rule: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> None:
        """Validate that dates are in correct order."""
        fields = rule.get("fields", [])
        description = rule.get("description", "Date order validation")
        
        if len(fields) < 2:
            return
        
        try:
            dates = []
            for field in fields:
                value = self.try_extract_nested_field_from_content(content, field)
                if value:
                    # Try to parse date
                    if isinstance(value, str):
                        from dateutil import parser
                        date_value = parser.parse(value)
                    else:
                        date_value = value
                    dates.append((field, date_value))
            
            # Check order
            for i in range(len(dates) - 1):
                if dates[i][1] > dates[i + 1][1]:
                    validation_result["warnings"].append({
                        "field": dates[i][0],
                        "warning": f"{description}: Date {dates[i][0]} is after {dates[i + 1][0]}"
                    })
        
        except Exception as e:
            validation_result["warnings"].append({
                "field": fields[0],
                "warning": f"{description}: Unable to validate date order: {str(e)}"
            })
    
    async def _validate_with_ai(
        self,
        content: Content,
        validation_result: Dict[str, Any]
    ) -> None:
        """Perform AI-powered validation."""
        try:
            import json
            
            # Prepare data for AI validation
            data_summary = {
                k: v for k, v in content.data.items()
                if not k.startswith('_') and not isinstance(v, bytes)
            }
            
            query = f"Validate the following data and identify any issues:\n\n{json.dumps(data_summary, indent=2, default=str)}"
            
            response = await self.agent.run(query, store=False)
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Try to parse AI response
            try:
                ai_result = json.loads(response_text)
                if not ai_result.get("is_valid", True):
                    issues = ai_result.get("issues", [])
                    for issue in issues:
                        validation_result["warnings"].append({
                            "field": "ai_validation",
                            "warning": f"AI detected issue: {issue}"
                        })
            except json.JSONDecodeError:
                # If not JSON, treat entire response as a warning if it suggests issues
                if any(keyword in response_text.lower() for keyword in ["issue", "problem", "error", "inconsistent", "invalid"]):
                    validation_result["warnings"].append({
                        "field": "ai_validation",
                        "warning": f"AI validation note: {response_text[:200]}"
                    })
        
        except Exception as e:
            logger.warning(f"AI validation failed: {str(e)}")
            # Don't fail the validation, just log
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type."""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "date":
            if isinstance(value, datetime):
                return True
            if isinstance(value, str):
                try:
                    from dateutil import parser
                    parser.parse(value)
                    return True
                except:
                    return False
            return False
        
        return True  # Unknown type, assume valid
