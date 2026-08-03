"""
Pharmacy License Validation Executor for the SARSP project.

Validates pharmacy license applications (Nueva / Renovación) against
configurable regulatory rules using AI-powered document analysis.

This executor reads extracted document data from upstream executors, detects the
transaction type, applies shared and transaction-specific validation rules via
Azure OpenAI, and produces a structured Approve/Decline recommendation with
specific correction messages for each failed rule.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

try:
    from agent_framework.openai import OpenAIChatClient
    from agent_framework import Agent, AgentResponse
except ImportError:
    raise ImportError(
        "agent-framework import error. Either the library is not installed or there is "
        "an issue with the version of the installed library."
    )

from agent_framework import WorkflowContext

from .base import BaseExecutor
from ..models import Content, ExecutorLogEntry
from ..connectors import AzureBlobConnector
from ..utils.credential_provider import get_azure_credential

logger = logging.getLogger("contentflow.executors.pharmacy_license_validation_executor")


# Transaction type constants
TRANSACTION_NUEVA = "Nueva"
TRANSACTION_RENOVACION = "Renovación"
TRANSACTION_TYPES = (TRANSACTION_NUEVA, TRANSACTION_RENOVACION)


class PharmacyLicenseValidationExecutor(BaseExecutor):
    """
    AI-powered pharmacy license application validation for the SARSP project.

    Validates pharmacy license applications (new and renewal) against Puerto Rico
    Health Department regulatory rules. Uses Azure OpenAI GPT-4.1 for complex
    document analysis including completeness checks, legibility assessment,
    name/address matching, and regulatory compliance verification.

    Workflow:
        1. Detect transaction type (Nueva or Renovación) from application data.
        2. Load validation rules from rules configuration.
        3. For each document, apply shared validation rules.
        4. Apply transaction-specific rules based on detected type.
        5. Use GPT-4.1 for complex validations (completeness, legibility, matching).
        6. Generate structured Approve/Decline recommendation with correction messages.
        7. Write results.json to blob storage.

    Configuration (settings dict):
        Blob Storage:
            - blob_storage_account (str): Azure Storage account name. Required.
            - blob_container_name (str): Container for case files. Required.
            - blob_storage_credential_type (str): Credential type.
              Default: "default_azure_credential"
            - blob_storage_account_key (str): Storage key (if using key credential).
              Default: None

        Rules:
            - rules_filename (str): Name of the rules configuration file.
              Default: "sarsp_rules.json"
            - rules_base_path (str): Blob path prefix for rules file.
              Default: "" (container root)

        File Naming:
            - provided_details_filename (str): Application form data filename.
              Default: "ProvidedDetails.json"
            - fetched_details_prefix (str): Prefix for extracted document files.
              Default: "FetchedDetails_"
            - output_filename (str): Output results filename.
              Default: "results.json"

        AI Configuration:
            - endpoint (str): Azure OpenAI endpoint URL. Required.
            - deployment_name (str): Model deployment name. Required.
            - credential_type (str): OpenAI credential type.
              Default: "default_azure_credential"
            - api_key (str): API key (if using key credential). Default: None
            - temperature (float): Sampling temperature. Default: 0.1
            - max_tokens (int): Max tokens for validation response. Default: 2000

        Path Settings:
            - input_prefix_field (str): Field in content.data for blob folder path.
              Default: "blob_path"
            - fetched_details_path_field (str): Dot-path to blob output paths.
              Default: "blob_output.blob_path"
            - transaction_type_field (str): Field containing detected transaction type.
              Default: "transaction_type"

        Behaviour:
            - cleanup_input_after_results (bool): Delete intermediate files after results.
              Default: False
            - cleanup_preserve_files (str): Comma-separated files to preserve.
              Default: "results.json"

    Example Pipeline YAML:
        ```yaml
        - id: pharmacy_validator
          type: pharmacy_license_validation
          settings:
            blob_storage_account: "${AZURE_STORAGE_ACCOUNT_NAME}"
            blob_container_name: "content"
            endpoint: "${AZURE_OPENAI_ENDPOINT}"
            deployment_name: "gpt-4.1"
            rules_filename: "sarsp_rules.json"
            transaction_type_field: "transaction_type"
        ```

    Input:
        Content item(s) representing processed documents for a pharmacy license case.

    Output:
        Content with data["validation_results"] containing:
        - transactionType: "Nueva" or "Renovación"
        - recommendation: "Approve" or "Decline"
        - summary: pass/fail counts
        - documentResults: per-document validation results with correction messages
    """

    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(id=id, settings=settings, **kwargs)

        # ---- Blob storage config ----
        self.blob_storage_account = self.get_setting("blob_storage_account", required=True)
        self.blob_container_name = self.get_setting("blob_container_name", required=True)
        self.blob_storage_credential_type = self.get_setting(
            "blob_storage_credential_type", default="default_azure_credential"
        )
        self.blob_storage_account_key = self.get_setting("blob_storage_account_key", default=None)

        # ---- Rules config ----
        self.rules_filename = self.get_setting("rules_filename", default="sarsp_rules.json")
        self.rules_base_path = self.settings.get("rules_base_path", None)
        if isinstance(self.rules_base_path, str):
            self.rules_base_path = self.rules_base_path.strip()

        # ---- File names ----
        self.provided_details_filename = self.get_setting(
            "provided_details_filename", default="ProvidedDetails.json"
        )
        self.fetched_details_prefix = self.get_setting("fetched_details_prefix", default="FetchedDetails_")
        self.output_filename = self.get_setting("output_filename", default="results.json")

        # ---- Path settings ----
        self.input_prefix_field = self.get_setting("input_prefix_field", default="blob_path")
        self.fetched_details_path_field = self.get_setting(
            "fetched_details_path_field", default="blob_output.blob_path"
        )
        self.transaction_type_field = self.get_setting("transaction_type_field", default="transaction_type")

        # ---- AI config ----
        self.openai_endpoint = self.get_setting("endpoint", required=True)
        self.openai_deployment_name = self.get_setting("deployment_name", required=True)
        self.openai_credential_type = self.get_setting("credential_type", default="default_azure_credential")
        self.openai_api_key = self.get_setting("api_key", default=None)
        self.temperature = self.get_setting("temperature", default=0.1)
        self.max_tokens = self.get_setting("max_tokens", default=2000)

        # Validate credential config
        if self.openai_credential_type not in ("default_azure_credential", "azure_key_credential"):
            raise ValueError(f"{self.id}: Invalid credential_type '{self.openai_credential_type}'")
        if self.openai_credential_type == "azure_key_credential" and not self.openai_api_key:
            raise ValueError(f"{self.id}: api_key required for azure_key_credential")

        # ---- Cleanup settings ----
        self.cleanup_input_after_results = self.get_setting("cleanup_input_after_results", default=False)
        self.cleanup_preserve_files = self.get_setting("cleanup_preserve_files", default="results.json")

        # ---- Lazy-init resources ----
        self.blob_connector = AzureBlobConnector(
            name="pharmacy_validation_blob",
            settings={
                "account_name": self.blob_storage_account,
                "credential_type": self.blob_storage_credential_type,
                "credential_key": self.blob_storage_account_key,
            },
        )
        self._validation_agent: Optional[Agent] = None
        self._transaction_detection_agent: Optional[Agent] = None

        if self.debug_mode:
            logger.debug(f"PharmacyLicenseValidationExecutor '{self.id}' initialized")

    # ------------------------------------------------------------------
    # AI Agent initialization
    # ------------------------------------------------------------------

    def _init_validation_agent(self) -> None:
        """Initialize the AI agent for document validation."""
        client_kwargs = {
            "model": self.openai_deployment_name,
            "azure_endpoint": self.openai_endpoint,
            "credential": get_azure_credential() if self.openai_credential_type == "default_azure_credential" else None,
            "api_key": self.openai_api_key if self.openai_credential_type == "azure_key_credential" else None,
        }
        client = OpenAIChatClient(**client_kwargs)

        instructions = (
            "You are an expert document compliance validator for the Puerto Rico Health Department "
            "(Departamento de Salud de Puerto Rico). You validate pharmacy license applications "
            "against regulatory requirements.\n\n"
            "For each document, you will be given:\n"
            "1. The document type and its extracted content/fields\n"
            "2. The validation rules that must be checked\n"
            "3. The application data (applicant information) for cross-reference\n\n"
            "You must evaluate each validation rule and return a structured JSON response with:\n"
            "- rule_id: The rule identifier\n"
            "- result: 'pass' or 'fail'\n"
            "- confidence: 0.0 to 1.0\n"
            "- message_en: English explanation of the result\n"
            "- message_es: Spanish explanation of the result\n"
            "- correction: If failed, specific actionable correction guidance (in Spanish)\n\n"
            "Be thorough but fair. If a document is partially compliant, note what passes and what fails. "
            "Always provide specific correction guidance in Spanish for failed rules.\n\n"
            "Respond ONLY with a valid JSON array of rule results."
        )

        self._validation_agent = client.as_agent(
            id=f"{self.id}_validation_agent",
            name=f"{self.id}_validation_agent",
            instructions=instructions,
            default_options={
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
        )

    def _init_transaction_detection_agent(self) -> None:
        """Initialize the AI agent for transaction type detection."""
        client_kwargs = {
            "model": self.openai_deployment_name,
            "azure_endpoint": self.openai_endpoint,
            "credential": get_azure_credential() if self.openai_credential_type == "default_azure_credential" else None,
            "api_key": self.openai_api_key if self.openai_credential_type == "azure_key_credential" else None,
        }
        client = OpenAIChatClient(**client_kwargs)

        instructions = (
            "You are a document classification expert for Puerto Rico pharmacy license applications.\n"
            "Your task is to determine whether an application is:\n"
            "- 'Nueva' (new license application)\n"
            "- 'Renovación' (license renewal)\n\n"
            "Look for indicators such as:\n"
            "- Nueva: New license number to be assigned, no existing license reference, "
            "phrases like 'solicitud nueva', 'nueva licencia', layout/schematic documents present\n"
            "- Renovación: Existing license number, expiration date of current license, "
            "phrases like 'renovación', 'renewal', current pharmacy license document present\n\n"
            "Respond with ONLY a JSON object: "
            "{\"transaction_type\": \"Nueva\" or \"Renovación\", \"confidence\": 0.0-1.0, \"reason\": \"brief explanation\"}"
        )

        self._transaction_detection_agent = client.as_agent(
            id=f"{self.id}_transaction_detection",
            name=f"{self.id}_transaction_detection",
            instructions=instructions,
            default_options={
                "temperature": 0.0,
                "max_tokens": 200,
            },
        )

    # ------------------------------------------------------------------
    # Main processing
    # ------------------------------------------------------------------

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]],
    ) -> Union[Content, List[Content]]:
        """Main entry: load documents, detect transaction type, validate, produce results."""
        start_time = datetime.now(timezone.utc)
        contents = input if isinstance(input, list) else [input]

        # Collect FetchedDetails paths from current run
        current_run_blob_paths = self._collect_current_run_fetched_paths(contents)

        content = contents[0]
        content_id = content.id.canonical_id if content.id else "unknown"
        logger.info(f"{self.id}: Starting pharmacy license validation for: {content_id}")

        try:
            await self.blob_connector.initialize()

            # Determine blob prefix
            base_prefix = self._get_base_prefix(content)
            fetched_prefix = self._get_fetched_details_prefix(content)

            # Step 1: Load application data (ProvidedDetails) from container root
            provided_details = {}
            if self.provided_details_filename:
                try:
                    provided_details = await self._load_json_from_blob("", self.provided_details_filename)
                except (ValueError, Exception) as e:
                    logger.warning(f"{self.id}: ProvidedDetails not found at container root, proceeding without it: {e}")
                    provided_details = {}

            # Step 2: Load rules
            rules_prefix = self._get_rules_prefix()
            if rules_prefix is None:
                rules_prefix = base_prefix
            rules = await self._load_json_from_blob(rules_prefix, self.rules_filename)

            # Step 3: Load extracted document data
            fetched_details_list = await self._load_fetched_details(current_run_blob_paths, fetched_prefix)

            # Step 4: Detect transaction type
            transaction_type = await self._detect_transaction_type(
                provided_details, fetched_details_list, content
            )
            logger.info(f"{self.id}: Detected transaction type: {transaction_type}")

            # Step 5: Run validation
            results = await self._run_validation(
                transaction_type, provided_details, fetched_details_list, rules
            )

            # Step 6: Write results to blob
            await self._write_results_to_blob(base_prefix, results)

            # Step 7: Store in content
            content.data["validation_results"] = results
            content.summary_data["validation_status"] = results.get("recommendation", "unknown")
            content.summary_data["transaction_type"] = transaction_type
            content.summary_data["executor_status"] = "success"

            # Cleanup if configured
            if self.cleanup_input_after_results:
                await self._cleanup_case_folder(base_prefix)

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                f"{self.id}: Validation complete in {elapsed:.2f}s — "
                f"Recommendation: {results['recommendation']}, "
                f"Passed: {results['summary']['passed']}, Failed: {results['summary']['failed']}"
            )

            content.executor_logs.append(ExecutorLogEntry(
                executor_id=self.id,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                status="completed",
                details={
                    "transaction_type": transaction_type,
                    "recommendation": results["recommendation"],
                    "total_documents": results["summary"]["totalDocuments"],
                    "passed": results["summary"]["passed"],
                    "failed": results["summary"]["failed"],
                },
                errors=[],
            ))

        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"{self.id}: Validation failed after {elapsed:.2f}s: {e}", exc_info=True)
            content.summary_data["executor_status"] = "failed"
            content.executor_logs.append(ExecutorLogEntry(
                executor_id=self.id,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                status="failed",
                details={},
                errors=[str(e)],
            ))
            raise

        return content if not isinstance(input, list) else contents

    # ------------------------------------------------------------------
    # Transaction type detection
    # ------------------------------------------------------------------

    async def _detect_transaction_type(
        self,
        provided_details: dict,
        fetched_details: List[dict],
        content: Content,
    ) -> str:
        """Detect whether this is a Nueva or Renovación application.

        Priority:
          1. Explicit field from upstream (e.g., from SQL query result)
          2. Field in ProvidedDetails
          3. AI-based detection from document contents
        """
        # Check if transaction type was set by upstream executor (e.g., SQL query)
        upstream_type = self.try_extract_nested_field_from_content(content, self.transaction_type_field)
        if upstream_type and str(upstream_type) in TRANSACTION_TYPES:
            return str(upstream_type)

        # Check ProvidedDetails
        provided_type = provided_details.get("transactionType") or provided_details.get("transaction_type")
        if provided_type and str(provided_type) in TRANSACTION_TYPES:
            return str(provided_type)

        # Fall back to AI detection
        return await self._ai_detect_transaction_type(provided_details, fetched_details)

    async def _ai_detect_transaction_type(
        self, provided_details: dict, fetched_details: List[dict]
    ) -> str:
        """Use GPT-4.1 to detect transaction type from document content."""
        if not self._transaction_detection_agent:
            self._init_transaction_detection_agent()

        # Build context from available documents
        doc_summaries = []
        for doc in fetched_details[:5]:  # Limit to first 5 for token efficiency
            doc_type = doc.get("document_type", "Unknown")
            filename = doc.get("filename", "")
            # Include some extracted text/fields for classification
            details = doc.get("details", {})
            fields_preview = json.dumps(details, ensure_ascii=False, default=str)[:500]
            doc_summaries.append(f"- {doc_type} ({filename}): {fields_preview}")

        provided_summary = json.dumps(provided_details, ensure_ascii=False, default=str)[:1000]

        query = (
            f"Application data:\n{provided_summary}\n\n"
            f"Documents found:\n" + "\n".join(doc_summaries) + "\n\n"
            "Based on these documents and application data, is this a 'Nueva' or 'Renovación' application?"
        )

        try:
            response: AgentResponse = await self._transaction_detection_agent.run(query)
            response_text = response.content if hasattr(response, "content") else str(response)
            parsed = json.loads(response_text)
            detected_type = parsed.get("transaction_type", TRANSACTION_NUEVA)
            if detected_type in TRANSACTION_TYPES:
                logger.info(
                    f"{self.id}: AI detected transaction type: {detected_type} "
                    f"(confidence: {parsed.get('confidence', 'N/A')})"
                )
                return detected_type
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"{self.id}: AI transaction detection failed: {e}")

        # Default to Nueva if detection fails
        logger.warning(f"{self.id}: Defaulting to '{TRANSACTION_NUEVA}' transaction type")
        return TRANSACTION_NUEVA

    # ------------------------------------------------------------------
    # Validation logic
    # ------------------------------------------------------------------

    async def _run_validation(
        self,
        transaction_type: str,
        provided_details: dict,
        fetched_details: List[dict],
        rules: dict,
    ) -> dict:
        """Run all applicable validation rules and produce results."""
        results = {
            "validationTimestamp": datetime.now(timezone.utc).isoformat(),
            "transactionType": transaction_type,
            "recommendation": "Approve",
            "summary": {
                "totalDocuments": 0,
                "passed": 0,
                "failed": 0,
                "notFound": 0,
                "warnings": 0,
                "overallStatus": "passed",
            },
            "documentResults": [],
            "missingDocuments": [],
            "correctionMessages": [],
        }

        # Get applicable rules for this transaction type
        shared_rules = rules.get("shared_rules", [])
        type_specific_rules = rules.get(
            "nueva_rules" if transaction_type == TRANSACTION_NUEVA else "renovacion_rules", []
        )
        all_applicable_rules = shared_rules + type_specific_rules

        # Build a map of document_type → rules
        rules_by_doc_type: Dict[str, List[dict]] = {}
        for rule in all_applicable_rules:
            doc_type = rule.get("documentType", "")
            if doc_type not in rules_by_doc_type:
                rules_by_doc_type[doc_type] = []
            rules_by_doc_type[doc_type].append(rule)

        # Check which required documents are present
        required_doc_types = set(rules_by_doc_type.keys())
        found_doc_types = set()
        for doc in fetched_details:
            doc_type = doc.get("document_type", "") or ""
            # If document_type is null/empty, try to extract from classification field
            if not doc_type:
                classification = doc.get("classification", {})
                if isinstance(classification, dict):
                    doc_type = classification.get("category", "")
                elif isinstance(classification, str):
                    try:
                        import json as _json
                        parsed = _json.loads(classification)
                        doc_type = parsed.get("category", "")
                    except (ValueError, _json.JSONDecodeError):
                        doc_type = classification
            # If still empty, try to detect from document content (markdown/title)
            if not doc_type:
                doc_type = self._detect_doc_type_from_content(doc)
            # Store back for downstream use
            doc["document_type"] = doc_type
            found_doc_types.add(doc_type)
            # Also try fuzzy matching
            for req_type in required_doc_types:
                if self._doc_type_matches(doc_type, req_type):
                    found_doc_types.add(req_type)

        # Report missing required documents
        missing = required_doc_types - found_doc_types
        for missing_type in missing:
            results["missingDocuments"].append({
                "documentType": missing_type,
                "message_en": f"Required document '{missing_type}' was not found in the submission.",
                "message_es": f"El documento requerido '{missing_type}' no se encontró en la solicitud.",
            })
            results["summary"]["notFound"] += 1

        # Validate each submitted document
        for doc in fetched_details:
            doc_result = await self._validate_document(
                doc, provided_details, rules_by_doc_type, transaction_type
            )
            results["documentResults"].append(doc_result)
            results["summary"]["totalDocuments"] += 1

            if doc_result["status"] == "passed":
                results["summary"]["passed"] += 1
            elif doc_result["status"] == "failed":
                results["summary"]["failed"] += 1
                # Collect correction messages
                for rule_result in doc_result.get("ruleResults", []):
                    if rule_result["result"] == "fail" and rule_result.get("correction"):
                        results["correctionMessages"].append({
                            "documentType": doc_result["documentType"],
                            "ruleId": rule_result["rule_id"],
                            "correction": rule_result["correction"],
                        })

        # Determine overall recommendation
        if (results["summary"]["failed"] > 0 or
                results["summary"]["notFound"] > 0):
            results["recommendation"] = "Decline"
            results["summary"]["overallStatus"] = "failed"

        return results

    async def _validate_document(
        self,
        doc: dict,
        provided_details: dict,
        rules_by_doc_type: Dict[str, List[dict]],
        transaction_type: str,
    ) -> dict:
        """Validate a single document against applicable rules using AI."""
        doc_type = doc.get("document_type", "Unknown")
        filename = doc.get("filename", "")

        doc_result = {
            "documentType": doc_type,
            "filename": filename,
            "status": "passed",
            "ruleResults": [],
            "errors": [],
        }

        # Find matching rules for this document type
        applicable_rules = self._find_matching_rules(doc_type, rules_by_doc_type)

        if not applicable_rules:
            # No rules for this document type — mark as info only
            doc_result["status"] = "info"
            doc_result["errors"].append({
                "message_en": f"No validation rules defined for document type '{doc_type}'.",
                "message_es": f"No hay reglas de validación definidas para el tipo de documento '{doc_type}'.",
            })
            return doc_result

        # Use AI to validate the document against rules
        rule_results = await self._ai_validate_document(
            doc, provided_details, applicable_rules, transaction_type
        )

        doc_result["ruleResults"] = rule_results

        # Determine document status from rule results
        has_failures = any(r["result"] == "fail" for r in rule_results)
        if has_failures:
            doc_result["status"] = "failed"

        return doc_result

    async def _ai_validate_document(
        self,
        doc: dict,
        provided_details: dict,
        rules: List[dict],
        transaction_type: str,
    ) -> List[dict]:
        """Use GPT-4.1 to validate a document against specific rules."""
        if not self._validation_agent:
            self._init_validation_agent()

        # Build the validation prompt
        doc_type = doc.get("document_type", "Unknown")
        doc_content = json.dumps(doc.get("details", {}), ensure_ascii=False, default=str)
        app_data = json.dumps(provided_details, ensure_ascii=False, default=str)[:2000]

        # Add image context for photo documents
        image_context = ""
        if doc_type == "Fotos 2x2 de Farmacéuticos":
            filename = doc.get("filename", "")
            # Extract image dimensions from the details
            try:
                pages = doc.get("details", {}).get("result", {}).get("contents", [{}])[0].get("pages", [{}])
                if pages:
                    width = pages[0].get("width", 0)
                    height = pages[0].get("height", 0)
                    mime = doc.get("details", {}).get("result", {}).get("contents", [{}])[0].get("mimeType", "")
                    image_context = (
                        f"\nIMAGE METADATA: This is a {mime} image file ({width}x{height} pixels). "
                        f"The file was classified as a pharmacist photo based on file type (.jpg) and "
                        f"absence of document text content. It IS a photo of a person (headshot). "
                        f"Validate based on the pixel dimensions: a proper 2x2 inch photo at 300 DPI "
                        f"should be approximately 600x600 pixels. This image is {width}x{height} pixels.\n"
                    )
            except (IndexError, KeyError, TypeError):
                pass

        rules_description = []
        for rule in rules:
            rules_description.append(
                f"- rule_id: \"{rule['ruleId']}\"\n"
                f"  description: \"{rule.get('description', '')}\"\n"
                f"  validation_criteria: \"{rule.get('criteria', '')}\"\n"
                f"  applies_to: \"{rule.get('appliesTo', 'Both')}\""
            )

        query = (
            f"TRANSACTION TYPE: {transaction_type}\n\n"
            f"DOCUMENT TYPE: {doc_type}\n\n"
            f"DOCUMENT EXTRACTED CONTENT:\n{doc_content}\n"
            f"{image_context}\n"
            f"APPLICATION DATA (for cross-reference):\n{app_data}\n\n"
            f"VALIDATION RULES TO CHECK:\n" + "\n".join(rules_description) + "\n\n"
            f"Validate the document against each rule. Return a JSON array with one entry per rule."
        )

        try:
            response: AgentResponse = await self._validation_agent.run(query)
            response_text = response.content if hasattr(response, "content") else str(response)

            # Parse JSON response — handle markdown code blocks
            text = response_text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                text = text.rsplit("```", 1)[0]

            rule_results = json.loads(text)
            if not isinstance(rule_results, list):
                rule_results = [rule_results]

            # Normalize results
            normalized = []
            for r in rule_results:
                normalized.append({
                    "rule_id": r.get("rule_id", "unknown"),
                    "result": r.get("result", "pass"),
                    "confidence": r.get("confidence", 0.0),
                    "message_en": r.get("message_en", ""),
                    "message_es": r.get("message_es", ""),
                    "correction": r.get("correction", None),
                })
            return normalized

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(
                f"{self.id}: AI validation failed for document '{doc_type}': {e}",
                exc_info=True,
            )
            # Return warning results for all rules
            return [
                {
                    "rule_id": rule.get("ruleId", "unknown"),
                    "result": "warning",
                    "confidence": 0.0,
                    "message_en": f"AI validation could not be completed: {e}",
                    "message_es": f"La validación por IA no pudo completarse: {e}",
                    "correction": None,
                }
                for rule in rules
            ]

    # ------------------------------------------------------------------
    # Document type matching
    # ------------------------------------------------------------------

    def _detect_doc_type_from_content(self, doc: dict) -> str:
        """Detect document type from the extracted markdown/content when classification is missing."""
        try:
            filename = doc.get("filename", "")

            # Check if HeadshotAnalyzer result is available
            headshot_data = doc.get("headshot_analysis", {})
            if headshot_data:
                # Parse HeadshotAnalyzer fields
                try:
                    contents = headshot_data.get("result", {}).get("contents", [])
                    if contents:
                        fields = contents[0].get("fields", {})
                        is_headshot = fields.get("isHeadshot", {}).get("valueBoolean", False)
                        if is_headshot:
                            return "Fotos 2x2 de Farmacéuticos"
                except (KeyError, IndexError, TypeError):
                    pass

            contents = doc.get("details", {}).get("result", {}).get("contents", [])
            if not contents:
                # No OCR content at all — for JPEG images this typically means a photo
                if filename:
                    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
                    if ext in ("jpg", "jpeg"):
                        return "Fotos 2x2 de Farmacéuticos"
                return ""
            
            markdown = contents[0].get("markdown", "")
            if not markdown or not markdown.strip():
                # Empty OCR text — for JPEG images this typically means a photo
                # (floor plans/drawings with readable text are caught by keyword matching below)
                if filename:
                    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
                    if ext in ("jpg", "jpeg"):
                        return "Fotos 2x2 de Farmacéuticos"
                return ""
            
            # Check for known document type indicators in the content
            markdown_lower = markdown.lower()
            type_indicators = {
                "Certificación de Horarios de Farmacéuticos": ["certificación de horarios", "horarios de farmacéuticos"],
                "Patente Municipal": ["patente municipal"],
                "Solicitud de Servicio": ["solicitud de servicio"],
                "Licencia Profesional": ["licencia profesional", "departamento de salud"],
                "Registro Profesional": ["registro profesional", "junta de farmacia", "junta examinadora"],
                "Colegiación de Farmacéuticos": ["colegiación de farmacéuticos", "colegio de farmacéuticos"],
                "Certificado de Good Standing": ["good standing", "certificado de existencia"],
                "Permiso Único": ["permiso único", "permiso unico"],
                "Advertencia Legal": ["advertencia legal"],
                "Diseño esquemático": ["diseño esquemático", "layout", "plano", "construction drawings", "arquitectos", "floor plan", "gondolas", "almacen", "entrada"],
                "Licencia de Farmacia vigente": ["licencia de farmacia"],
                "Licencia de Productos Biológicos": ["productos biológicos"],
            }
            for doc_type, keywords in type_indicators.items():
                for keyword in keywords:
                    if keyword.lower() in markdown_lower:
                        return doc_type
            return ""
        except Exception:
            return ""

    def _doc_type_matches(self, fetched_type: str, rule_type: str) -> bool:
        """Flexible document type matching (case-insensitive, partial)."""
        if not fetched_type or not rule_type:
            return False
        f = fetched_type.lower().strip()
        r = rule_type.lower().strip()
        return f == r or f in r or r in f

    def _find_matching_rules(
        self, doc_type: str, rules_by_doc_type: Dict[str, List[dict]]
    ) -> List[dict]:
        """Find rules matching the document type (exact, case-insensitive, partial)."""
        # Exact match
        if doc_type in rules_by_doc_type:
            return rules_by_doc_type[doc_type]
        # Case-insensitive
        for key, rules in rules_by_doc_type.items():
            if key.lower() == doc_type.lower():
                return rules
        # Partial match
        for key, rules in rules_by_doc_type.items():
            if self._doc_type_matches(doc_type, key):
                return rules
        return []

    # ------------------------------------------------------------------
    # Blob helpers
    # ------------------------------------------------------------------

    def _get_base_prefix(self, content: Content) -> str:
        """Get the base blob path prefix."""
        prefix = self.try_extract_nested_field_from_content(content, self.input_prefix_field)
        if prefix:
            return prefix if prefix.endswith("/") else prefix + "/"
        if content.id and content.id.path:
            path = content.id.path
            if "/" in path:
                path = path.rsplit("/", 1)[0]
            return f"{path}/" if path else ""
        raise ValueError(f"{self.id}: Cannot determine base path.")

    def _get_fetched_details_prefix(self, content: Content) -> str:
        """Get path where FetchedDetails files are stored."""
        upstream_path = self._resolve_nested_field(content.summary_data, self.fetched_details_path_field)
        if upstream_path and "/" in upstream_path:
            folder = upstream_path.rsplit("/", 1)[0]
            return f"{folder}/"
        return self._get_base_prefix(content)

    def _get_rules_prefix(self) -> Optional[str]:
        """Get path prefix for rules file."""
        if self.rules_base_path is not None:
            path = self.rules_base_path.strip("/")
            return f"{path}/" if path else ""
        return None

    def _resolve_nested_field(self, data: dict, field_path: str):
        """Resolve a dot-notation field path from a dictionary."""
        if not data or not field_path:
            return None
        parts = field_path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value if value is not data else None

    def _collect_current_run_fetched_paths(self, contents: List[Content]) -> List[str]:
        """Collect FetchedDetails blob paths from current run."""
        paths = []
        for content in contents:
            blob_path = self._resolve_nested_field(content.summary_data, self.fetched_details_path_field)
            if blob_path and isinstance(blob_path, str):
                filename = blob_path.split("/")[-1] if "/" in blob_path else blob_path
                if filename.startswith(self.fetched_details_prefix) and filename.endswith(".json"):
                    paths.append(blob_path)
            for log in content.executor_logs:
                if log.details and "blob_path" in log.details:
                    bp = log.details["blob_path"]
                    if isinstance(bp, str):
                        filename = bp.split("/")[-1] if "/" in bp else bp
                        if filename.startswith(self.fetched_details_prefix) and filename.endswith(".json"):
                            if bp not in paths:
                                paths.append(bp)
        return paths

    async def _load_json_from_blob(self, prefix: str, filename: str) -> dict:
        """Download and parse a JSON file from blob storage."""
        blob_path = f"{prefix}{filename}"
        try:
            content_bytes = await self.blob_connector.download_blob(
                container_name=self.blob_container_name,
                blob_path=blob_path,
            )
            return json.loads(content_bytes.decode("utf-8"))
        except Exception as e:
            logger.error(f"{self.id}: Failed to load {blob_path}: {e}", exc_info=True)
            raise ValueError(f"Failed to load '{filename}' from {blob_path}: {e}")

    async def _load_fetched_details(
        self, current_run_paths: List[str], fetched_prefix: str
    ) -> List[dict]:
        """Load FetchedDetails files."""
        if current_run_paths:
            return await self._load_by_paths(current_run_paths)
        return await self._load_from_folder(fetched_prefix)

    async def _load_by_paths(self, blob_paths: List[str]) -> List[dict]:
        """Load FetchedDetails from specific blob paths."""
        all_fetched = []
        for blob_path in blob_paths:
            try:
                content_bytes = await self.blob_connector.download_blob(
                    container_name=self.blob_container_name,
                    blob_path=blob_path,
                )
                fetched = json.loads(content_bytes.decode("utf-8"))
                if isinstance(fetched, list):
                    all_fetched.extend(fetched)
                else:
                    all_fetched.append(fetched)
            except Exception as e:
                logger.warning(f"{self.id}: Failed to load {blob_path}: {e}")
        return all_fetched

    async def _load_from_folder(self, prefix: str) -> List[dict]:
        """Fallback: load all FetchedDetails from a folder."""
        all_fetched = []
        async for blobs in self.blob_connector.list_blobs(
            container_name=self.blob_container_name,
            prefix=prefix,
            max_results=100,
            batch_size=100,
        ):
            if not blobs:
                continue
            for blob in blobs:
                blob_name = blob.get("name", "")
                filename = blob_name.split("/")[-1] if "/" in blob_name else blob_name
                if filename.startswith(self.fetched_details_prefix) and filename.endswith(".json"):
                    try:
                        content_bytes = await self.blob_connector.download_blob(
                            container_name=self.blob_container_name,
                            blob_path=blob_name,
                        )
                        fetched = json.loads(content_bytes.decode("utf-8"))
                        if isinstance(fetched, list):
                            all_fetched.extend(fetched)
                        else:
                            all_fetched.append(fetched)
                    except Exception as e:
                        logger.warning(f"{self.id}: Failed to load {blob_name}: {e}")
        return all_fetched

    async def _write_results_to_blob(self, prefix: str, results: dict) -> None:
        """Write results.json to blob storage."""
        blob_path = f"{prefix}{self.output_filename}"
        content_bytes = json.dumps(results, indent=2, ensure_ascii=False).encode("utf-8")
        await self.blob_connector.upload_blob(
            container_name=self.blob_container_name,
            blob_path=blob_path,
            data=content_bytes,
            overwrite=True,
        )
        logger.info(f"{self.id}: Wrote results to {blob_path}")

    async def _cleanup_case_folder(self, base_prefix: str) -> None:
        """Delete intermediate blobs, preserving only specified files."""
        preserve_set = set()
        if self.cleanup_preserve_files:
            preserve_set = {f.strip() for f in self.cleanup_preserve_files.split(",") if f.strip()}

        deleted_count = 0
        async for blobs in self.blob_connector.list_blobs(
            container_name=self.blob_container_name,
            prefix=base_prefix,
            max_results=1000,
            batch_size=100,
        ):
            if not blobs:
                continue
            for blob in blobs:
                blob_name = blob.get("name", "")
                filename = blob_name.split("/")[-1] if "/" in blob_name else blob_name
                if filename in preserve_set:
                    continue
                try:
                    await self.blob_connector.delete_blob(
                        container_name=self.blob_container_name,
                        blob_path=blob_name,
                    )
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"{self.id}: Failed to delete {blob_name}: {e}")

        logger.info(f"{self.id}: Cleanup complete — deleted {deleted_count} blob(s)")
