"""
Obligation Tracker Executor.

Extracts and tracks obligations, deadlines, and deliverables from contracts,
with calendar generation for deadline management.
"""

import logging
import json
from typing import List, Union, Dict, Any, Optional
from datetime import datetime, timedelta
from dateutil import parser as date_parser
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


class ObligationType(str):
    """Types of obligations."""
    DEADLINE = "deadline"
    DELIVERABLE = "deliverable"
    MILESTONE = "milestone"
    RECURRING = "recurring"
    NOTICE_PERIOD = "notice_period"
    RENEWAL_DATE = "renewal_date"


class ObligationTrackerExecutor(BaseExecutor):
    """
    Track obligations, deadlines, and deliverables from contracts.
    
    This executor uses Azure OpenAI to extract actionable obligations,
    deadlines, and deliverables from contracts, and generates calendar
    files (iCal format) with reminders.
    
    Configuration (settings dict):
        - extract_deadlines (bool): Extract deadline obligations
          Default: True
        - extract_deliverables (bool): Extract deliverable obligations
          Default: True
        - extract_milestones (bool): Extract milestone obligations
          Default: True
        - extract_recurring (bool): Extract recurring obligations
          Default: True
        - calendar_format (str): Output calendar format (ical, json)
          Default: "ical"
        - create_reminders (bool): Create reminder events before deadlines
          Default: True
        - reminder_days (list): Days before deadline to create reminders
          Default: [7, 3, 1]
        - include_responsible_party (bool): Identify responsible party for each obligation
          Default: True
        - input_field (str): Field containing contract text
          Default: "extracted_content.markdown"
        - clauses_field (str): Field containing pre-extracted clauses (optional)
          Default: "clauses"
        - output_field (str): Field name for obligations
          Default: "obligations"
        - calendar_output_field (str): Field name for calendar file
          Default: "calendar"
        - endpoint (str): Azure OpenAI endpoint URL
        - deployment_name (str): Azure OpenAI model deployment name
        - temperature (float): Temperature for LLM
          Default: 0.2
    
    Expected Input Data Structure:
        {
            "extracted_content": {
                "markdown": "Full contract text..."
            },
            "clauses": {  # Optional
                "clauses": [...]
            }
        }
    
    Output:
        Content with added fields:
        - data[output_field]: Dictionary containing obligations
        - data[calendar_output_field]: Calendar file content
        - summary_data["obligation_tracking_status"]: Execution status
        - summary_data["total_obligations"]: Count of obligations
    
    Example:
        ```yaml
        - id: obligation-tracker-1
          type: obligation_tracker
          settings:
            extract_deadlines: true
            extract_deliverables: true
            calendar_format: ical
            create_reminders: true
            reminder_days: [7, 3, 1]
            endpoint: "${AZURE_OPENAI_ENDPOINT}"
            deployment_name: "gpt-4"
        ```
    """

    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        
        # Configuration
        self.extract_deadlines = self.get_setting("extract_deadlines", True)
        self.extract_deliverables = self.get_setting("extract_deliverables", True)
        self.extract_milestones = self.get_setting("extract_milestones", True)
        self.extract_recurring = self.get_setting("extract_recurring", True)
        self.calendar_format = self.get_setting("calendar_format", "ical")
        self.create_reminders = self.get_setting("create_reminders", True)
        self.reminder_days = self.get_setting("reminder_days", [7, 3, 1])
        self.include_responsible_party = self.get_setting("include_responsible_party", True)
        self.input_field = self.get_setting("input_field", "extracted_content.markdown")
        self.clauses_field = self.get_setting("clauses_field", "clauses")
        self.output_field = self.get_setting("output_field", "obligations")
        self.calendar_output_field = self.get_setting("calendar_output_field", "calendar")
        
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
        
        # Create specialized agent for obligation extraction
        self._init_agent()
        
        if self.debug_mode:
            logger.debug(
                f"ObligationTrackerExecutor initialized: "
                f"deadlines={self.extract_deadlines}, deliverables={self.extract_deliverables}"
            )

    def _init_agent(self) -> None:
        """Initialize AI agent for obligation extraction."""
        obligation_types = []
        if self.extract_deadlines:
            obligation_types.append("- Deadlines: Specific dates by which actions must be completed")
        if self.extract_deliverables:
            obligation_types.append("- Deliverables: Items or work products that must be provided")
        if self.extract_milestones:
            obligation_types.append("- Milestones: Significant events or achievements in the contract timeline")
        if self.extract_recurring:
            obligation_types.append("- Recurring obligations: Actions that must be performed periodically")
        
        types_text = "\n".join(obligation_types)
        
        instructions = f"""
You are an expert contract analyst specializing in identifying obligations, deadlines, and deliverables.

Your task is to extract all actionable obligations from contract text, focusing on:

{types_text}

For each obligation you identify:
1. Describe the obligation clearly and actionably
2. Specify the obligation type (deadline, deliverable, milestone, recurring, notice_period, renewal_date)
3. Extract any specific dates mentioned
4. Extract any time periods or durations (e.g., "30 days after", "within 60 days")
5. Identify the responsible party (who must perform the obligation)
6. Note any dependencies or conditions
7. Extract the specific contract clause or section reference
8. Assess the criticality (critical, high, medium, low)

Return your response as a JSON array with the following structure:
[
  {{
    "obligation_type": "deadline|deliverable|milestone|recurring|notice_period|renewal_date",
    "description": "clear description of what must be done",
    "responsible_party": "party name or role",
    "date": "YYYY-MM-DD if specific date mentioned",
    "time_period": "relative time period (e.g., '30 days after execution')",
    "frequency": "for recurring obligations (daily, weekly, monthly, quarterly, annually)",
    "criticality": "critical|high|medium|low",
    "contract_reference": "clause or section reference",
    "dependencies": "any conditions or dependencies",
    "notes": "additional context"
  }}
]

Guidelines:
- Extract all obligations, even those without specific dates
- For relative dates (e.g., "30 days after signing"), include the time_period field
- Identify both explicit obligations ("shall deliver") and implicit ones
- Note notice periods and renewal dates carefully
- Distinguish between one-time and recurring obligations
"""
        
        self.agent: ChatAgent = self.client.create_agent(
            id=f"{self.id}_agent",
            name="ObligationTracker",
            instructions=instructions,
            temperature=self.temperature
        )

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """Process contract documents and extract obligations."""
        items_to_process = input if isinstance(input, list) else [input]
        
        for item in items_to_process:
            await self._process_single_content(item)
            
        return input

    async def _process_single_content(self, content: Content) -> None:
        """Process a single contract document and extract obligations."""
        logger.info(f"Extracting obligations from content {content.id}")
        
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
                content.summary_data["obligation_tracking_status"] = "failed"
                return
            
            # Get pre-extracted clauses if available
            clauses_data = self.try_extract_nested_field_from_content(
                content=content,
                field_path=self.clauses_field
            )
            
            # Extract obligations using AI
            obligations = await self._extract_obligations(contract_text, clauses_data)
            
            # Parse and normalize dates
            obligations = self._normalize_dates(obligations, content)
            
            # Categorize obligations
            categorized = self._categorize_obligations(obligations)
            
            # Generate calendar if requested
            calendar_content = None
            if self.calendar_format:
                calendar_content = self._generate_calendar(obligations, content)
            
            # Store results
            results = {
                "obligations": obligations,
                "categorized": categorized,
                "metadata": {
                    "total_obligations": len(obligations),
                    "with_dates": sum(1 for o in obligations if o.get("parsed_date")),
                    "critical_obligations": sum(1 for o in obligations if o.get("criticality") == "critical"),
                    "extraction_timestamp": datetime.now().isoformat(),
                }
            }
            
            content.data[self.output_field] = results
            if calendar_content:
                content.data[self.calendar_output_field] = calendar_content
            
            content.summary_data["obligation_tracking_status"] = "success"
            content.summary_data["total_obligations"] = len(obligations)
            content.summary_data["critical_obligations"] = results["metadata"]["critical_obligations"]
            
        except Exception as e:
            logger.error(f"Error extracting obligations from content {content.id}: {e}")
            content.data[self.output_field] = {"error": str(e)}
            content.summary_data["obligation_tracking_status"] = "failed"

    async def _extract_obligations(
        self,
        contract_text: str,
        clauses_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract obligations from contract text using AI."""
        # Build context for extraction
        context_parts = [contract_text]
        
        # Include clause information if available
        if clauses_data and isinstance(clauses_data, dict):
            clauses = clauses_data.get("clauses", [])
            if clauses:
                # Focus on relevant clause types
                relevant_types = ["payment_terms", "termination", "deliverables", "milestones"]
                relevant_clauses = [
                    c for c in clauses
                    if any(rt in c.get("clause_type", "").lower() for rt in relevant_types)
                ]
                if relevant_clauses:
                    clause_text = "\n\n".join([
                        f"[{c.get('clause_type')}]: {c.get('text', '')[:300]}"
                        for c in relevant_clauses[:5]
                    ])
                    context_parts.append(f"\n\nRELEVANT CLAUSES:\n{clause_text}")
        
        context = "\n\n".join(context_parts)
        
        # Truncate if too long
        max_length = 12000
        if len(context) > max_length:
            logger.warning(f"Context truncated from {len(context)} to {max_length} characters")
            context = context[:max_length] + "\n\n[Contract truncated for analysis]"
        
        query = f"""
Analyze the following contract and extract all actionable obligations, deadlines, and deliverables:

{context}

Focus on identifying specific dates, time periods, and responsibilities.
Return the obligations in the specified JSON format.
"""
        
        try:
            result = await self.agent.run(query, store=False)
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            # Parse JSON response
            obligations = self._parse_json_from_response(response_text)
            
            if not obligations or not isinstance(obligations, list):
                logger.warning("Failed to parse obligations from LLM response")
                obligations = []
            
            return obligations
            
        except Exception as e:
            logger.error(f"Error calling LLM for obligation extraction: {e}")
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

    def _normalize_dates(self, obligations: List[Dict[str, Any]], content: Content) -> List[Dict[str, Any]]:
        """Parse and normalize dates in obligations."""
        # Try to get contract execution date from content metadata
        contract_date = content.summary_data.get("contract_date")
        if contract_date:
            try:
                base_date = date_parser.parse(contract_date)
            except:
                base_date = datetime.now()
        else:
            base_date = datetime.now()
        
        for obligation in obligations:
            # Parse explicit dates
            if obligation.get("date"):
                try:
                    parsed_date = date_parser.parse(obligation["date"])
                    obligation["parsed_date"] = parsed_date.isoformat()
                except:
                    logger.warning(f"Could not parse date: {obligation['date']}")
            
            # Parse relative time periods
            elif obligation.get("time_period"):
                parsed_date = self._parse_relative_date(obligation["time_period"], base_date)
                if parsed_date:
                    obligation["parsed_date"] = parsed_date.isoformat()
                    obligation["calculated_from"] = "contract_date"
        
        return obligations

    def _parse_relative_date(self, time_period: str, base_date: datetime) -> Optional[datetime]:
        """Parse relative time periods (e.g., '30 days after', 'within 60 days')."""
        # Extract number and unit
        match = re.search(r'(\d+)\s*(day|week|month|year)s?', time_period.lower())
        if not match:
            return None
        
        number = int(match.group(1))
        unit = match.group(2)
        
        if unit == "day":
            return base_date + timedelta(days=number)
        elif unit == "week":
            return base_date + timedelta(weeks=number)
        elif unit == "month":
            return base_date + timedelta(days=number * 30)  # Approximate
        elif unit == "year":
            return base_date + timedelta(days=number * 365)  # Approximate
        
        return None

    def _categorize_obligations(self, obligations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize obligations by type and criticality."""
        categorized = {
            "by_type": {},
            "by_criticality": {},
            "upcoming": [],
            "overdue": [],
            "no_date": [],
        }
        
        now = datetime.now()
        
        for obligation in obligations:
            # By type
            obl_type = obligation.get("obligation_type", "other")
            if obl_type not in categorized["by_type"]:
                categorized["by_type"][obl_type] = []
            categorized["by_type"][obl_type].append(obligation)
            
            # By criticality
            criticality = obligation.get("criticality", "medium")
            if criticality not in categorized["by_criticality"]:
                categorized["by_criticality"][criticality] = []
            categorized["by_criticality"][criticality].append(obligation)
            
            # By date status
            if obligation.get("parsed_date"):
                try:
                    obl_date = date_parser.parse(obligation["parsed_date"])
                    if obl_date < now:
                        categorized["overdue"].append(obligation)
                    elif obl_date < now + timedelta(days=90):
                        categorized["upcoming"].append(obligation)
                except:
                    pass
            else:
                categorized["no_date"].append(obligation)
        
        # Sort upcoming by date
        categorized["upcoming"].sort(
            key=lambda x: date_parser.parse(x["parsed_date"]) if x.get("parsed_date") else datetime.max
        )
        
        return categorized

    def _generate_calendar(self, obligations: List[Dict[str, Any]], content: Content) -> str:
        """Generate calendar file (iCal format) for obligations."""
        if self.calendar_format != "ical":
            # Return JSON format
            return json.dumps(obligations, indent=2)
        
        # Generate iCal format
        ical_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//ContentFlow//Obligation Tracker//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:Contract Obligations - {content.id}",
            "X-WR-TIMEZONE:UTC",
        ]
        
        for i, obligation in enumerate(obligations):
            if not obligation.get("parsed_date"):
                continue
            
            try:
                obl_date = date_parser.parse(obligation["parsed_date"])
                
                # Create main event
                event = self._create_ical_event(
                    uid=f"{content.id}-obl-{i}",
                    summary=obligation.get("description", "Contract Obligation"),
                    date=obl_date,
                    description=self._format_obligation_description(obligation),
                    priority=self._map_criticality_to_priority(obligation.get("criticality", "medium"))
                )
                ical_lines.extend(event)
                
                # Create reminder events
                if self.create_reminders:
                    for days_before in self.reminder_days:
                        reminder_date = obl_date - timedelta(days=days_before)
                        if reminder_date > datetime.now():
                            reminder_event = self._create_ical_event(
                                uid=f"{content.id}-obl-{i}-reminder-{days_before}d",
                                summary=f"REMINDER: {obligation.get('description', 'Obligation')} in {days_before} days",
                                date=reminder_date,
                                description=f"Reminder: The following obligation is due in {days_before} days.\n\n{self._format_obligation_description(obligation)}",
                                priority=5
                            )
                            ical_lines.extend(reminder_event)
                
            except Exception as e:
                logger.warning(f"Could not create calendar event for obligation: {e}")
                continue
        
        ical_lines.append("END:VCALENDAR")
        
        return "\n".join(ical_lines)

    def _create_ical_event(
        self,
        uid: str,
        summary: str,
        date: datetime,
        description: str,
        priority: int = 5
    ) -> List[str]:
        """Create iCal event lines."""
        now = datetime.now()
        
        return [
            "BEGIN:VEVENT",
            f"UID:{uid}@contentflow",
            f"DTSTAMP:{now.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART;VALUE=DATE:{date.strftime('%Y%m%d')}",
            f"SUMMARY:{self._escape_ical_text(summary)}",
            f"DESCRIPTION:{self._escape_ical_text(description)}",
            f"PRIORITY:{priority}",
            "STATUS:CONFIRMED",
            "TRANSP:OPAQUE",
            "END:VEVENT",
        ]

    def _escape_ical_text(self, text: str) -> str:
        """Escape text for iCal format."""
        # Replace newlines with \n
        text = text.replace('\n', '\\n')
        # Escape special characters
        text = text.replace(',', '\\,')
        text = text.replace(';', '\\;')
        return text

    def _format_obligation_description(self, obligation: Dict[str, Any]) -> str:
        """Format obligation details for calendar description."""
        parts = []
        
        if obligation.get("description"):
            parts.append(f"Obligation: {obligation['description']}")
        
        if obligation.get("responsible_party"):
            parts.append(f"Responsible Party: {obligation['responsible_party']}")
        
        if obligation.get("obligation_type"):
            parts.append(f"Type: {obligation['obligation_type']}")
        
        if obligation.get("criticality"):
            parts.append(f"Criticality: {obligation['criticality'].upper()}")
        
        if obligation.get("contract_reference"):
            parts.append(f"Reference: {obligation['contract_reference']}")
        
        if obligation.get("dependencies"):
            parts.append(f"Dependencies: {obligation['dependencies']}")
        
        if obligation.get("notes"):
            parts.append(f"Notes: {obligation['notes']}")
        
        return "\n".join(parts)

    def _map_criticality_to_priority(self, criticality: str) -> int:
        """Map criticality to iCal priority (1=highest, 9=lowest)."""
        mapping = {
            "critical": 1,
            "high": 3,
            "medium": 5,
            "low": 7,
        }
        return mapping.get(criticality.lower(), 5)
