# AI Agent PDF Processing Pipeline Templates

This document outlines advanced pipeline templates using collaborative AI Agents in hand-off and group chat patterns to parse, process, and extract structured information from PDF documents across various industries.

## Table of Contents

- [Overview: Agent Collaboration Patterns](#overview-agent-collaboration-patterns)
  - [Hand-Off Pattern](#hand-off-pattern)
  - [Group Chat Pattern](#group-chat-pattern)
  - [MCP Tool Integration](#mcp-tool-integration)
- [Template 1: Legal Contract Analysis with Specialist Agent Hand-Off](#template-1-legal-contract-analysis-with-specialist-agent-hand-off)
- [Template 2: Financial Report Analysis with Group Chat Agent Collaboration](#template-2-financial-report-analysis-with-group-chat-agent-collaboration)
- [Template 3: Medical Records Processing with Hierarchical Agent Teams](#template-3-medical-records-processing-with-hierarchical-agent-teams)
- [Template 4: Research Paper Analysis with Swarm Intelligence Pattern](#template-4-research-paper-analysis-with-swarm-intelligence-pattern)
- [Template 5: Insurance Claims Processing with Agent Negotiation Pattern](#template-5-insurance-claims-processing-with-agent-negotiation-pattern)
- [Template 6: Generic Document Intelligence Extraction with Dynamic Agent Routing](#template-6-generic-document-intelligence-extraction-with-dynamic-agent-routing)
- [Invoice-Focused Templates (Agent Collaboration Patterns)](#invoice-focused-templates-agent-collaboration-patterns)
- [Template 7: Invoice Extraction & Normalization with Specialist Hand-Off](#template-7-invoice-extraction--normalization-with-specialist-hand-off)
- [Template 8: Invoice Exception Triage with Group Chat (Best Fit for Ambiguity)](#template-8-invoice-exception-triage-with-group-chat-best-fit-for-ambiguity)
- [Template 9: Invoice ↔ PO ↔ Receipt 3-Way Match with Negotiation/Consensus](#template-9-invoice--po--receipt-3-way-match-with-negotiationconsensus)
- [Template 10: Invoice Fraud & Anomaly Detection with Swarm + Convergence](#template-10-invoice-fraud--anomaly-detection-with-swarm--convergence)
- [Template 11: Invoice Line-Item GL Coding & Cost Center Allocation (Hierarchical Teams)](#template-11-invoice-line-item-gl-coding--cost-center-allocation-hierarchical-teams)
- [MCP Tool Integration Guide](#mcp-tool-integration-guide)
- [Implementation Requirements](#implementation-requirements)
  - [New Executor Types Needed](#new-executor-types-needed)
- [Additional Financial Document Templates (Agent Collaboration Patterns)](#additional-financial-document-templates-agent-collaboration-patterns)
  - [Template F1: Bank Statement Reconciliation (Swarm + Convergence)](#template-f1-bank-statement-reconciliation-swarm--convergence)
  - [Template F2: Trade Confirmation / Term Sheet Normalization (Specialists + Coordinator)](#template-f2-trade-confirmation--term-sheet-normalization-specialists--coordinator)
  - [Template F3: Annual Report (10-K/10-Q) KPI + Risk + Footnote Extraction (Hierarchical Teams)](#template-f3-annual-report-10-k10-q-kpi--risk--footnote-extraction-hierarchical-teams)
  - [Template F4: Loan Agreement Covenant Extraction + Monitoring Checklist (Hand-Off)](#template-f4-loan-agreement-covenant-extraction--monitoring-checklist-hand-off)
- [Best Practices](#best-practices)
  - [Agent Design](#agent-design)
  - [Collaboration Patterns](#collaboration-patterns)
  - [MCP Tool Usage](#mcp-tool-usage)
  - [Performance](#performance)
- [Next Steps](#next-steps)

---

## Overview: Agent Collaboration Patterns

### Hand-Off Pattern
Agents work sequentially, each specializing in a specific task. Output from one agent becomes input for the next, creating a processing chain.

### Group Chat Pattern
Multiple agents collaborate simultaneously in a discussion-like pattern, with a coordinator agent managing the conversation and aggregating results.

### MCP Tool Integration
Agents leverage Model Context Protocol (MCP) tools to access specialized functions, APIs, and services for document processing, data extraction, and validation.

---

## Template 1: Legal Contract Analysis with Specialist Agent Hand-Off

**Description**: Sequential agent workflow where specialized legal AI agents analyze different aspects of a contract document, each building upon the previous agent's analysis.

**Use Cases**:
- Contract Review Automation: Analyze vendor agreements, employment contracts, NDAs
- Legal Due Diligence: Extract key terms, obligations, and risk factors
- Compliance Verification: Ensure contracts meet regulatory and policy requirements
- Contract Repository: Build searchable contract databases with structured metadata

**Agent Architecture**:
```
Document Intake Agent → Contract Classifier Agent → Terms Extractor Agent → 
Risk Analyzer Agent → Compliance Checker Agent → Summary Generator Agent
```

**Pipeline Steps**:

1. **Azure Blob Input Discovery** - Discover contract PDFs
2. **Azure Blob Content Retriever** - Retrieve PDF documents
3. **Azure Document Intelligence Extractor** - OCR and initial document parsing
4. **Document Intake Agent** (MCP-enabled)
   - **Role**: Initial document assessment and preparation
   - **MCP Tools**: 
     - `pdf_analyzer`: Assess document quality, page count, language
     - `metadata_extractor`: Extract basic metadata (dates, parties)
   - **Output**: Document overview, quality assessment, routing recommendations
   
5. **Contract Classifier Agent** (MCP-enabled)
   - **Role**: Classify contract type and identify relevant legal frameworks
   - **Input**: Document Intake Agent output
   - **MCP Tools**:
     - `legal_taxonomy_lookup`: Match contract to legal categories
     - `jurisdiction_detector`: Identify governing law and jurisdiction
   - **Output**: Contract type (MSA, SLA, NDA, etc.), jurisdiction, applicable laws
   
6. **Terms Extractor Agent** (MCP-enabled)
   - **Role**: Extract key contract terms, clauses, and obligations
   - **Input**: Contract Classifier Agent output
   - **MCP Tools**:
     - `clause_identifier`: Detect standard clauses (termination, liability, IP, etc.)
     - `party_extractor`: Extract contracting parties and their roles
     - `date_parser`: Extract key dates (effective date, term, renewal dates)
     - `financial_terms_extractor`: Extract payment terms, amounts, penalties
   - **Output**: Structured contract terms with confidence scores
   
7. **Risk Analyzer Agent** (MCP-enabled)
   - **Role**: Assess legal risks and non-standard provisions
   - **Input**: Terms Extractor Agent output
   - **MCP Tools**:
     - `risk_scorer`: Calculate risk scores for different clauses
     - `clause_comparator`: Compare against standard clause library
     - `redline_detector`: Identify unusual or high-risk language
   - **Output**: Risk assessment, flagged clauses, risk score by category
   
8. **Compliance Checker Agent** (MCP-enabled)
   - **Role**: Verify compliance with regulations and company policies
   - **Input**: Terms Extractor Agent + Risk Analyzer Agent outputs
   - **MCP Tools**:
     - `regulatory_validator`: Check against regulatory requirements (GDPR, CCPA, etc.)
     - `policy_matcher`: Compare against company contracting policies
     - `missing_clause_detector`: Identify required clauses that are missing
   - **Output**: Compliance report, policy violations, required modifications
   
9. **Summary Generator Agent** (MCP-enabled)
   - **Role**: Create executive summary and structured contract data
   - **Input**: All previous agent outputs
   - **MCP Tools**:
     - `executive_summarizer`: Generate plain-language summary
     - `json_formatter`: Format extracted data as structured JSON
     - `action_items_extractor`: Identify required actions and decisions
   - **Output**: Executive summary, structured contract JSON, action items
   
10. **Field Mapper** - Normalize to standard contract schema
11. **Azure Blob Output** - Save structured contract data
12. **AI Search Index Output** - Index for contract search and analytics

**Estimated Time**: 5-8 minutes per contract

**Features**:
- Specialized agent expertise for each analysis phase
- MCP tool integration for specialized legal processing
- Comprehensive risk and compliance analysis
- Structured data extraction with high accuracy

**Agent Configuration YAML**:
```yaml
pipeline:
  name: "Legal Contract Analysis with Specialist Agent Hand-Off"
  description: "Sequential agent workflow for comprehensive contract analysis"
  
  agents:
    - id: document-intake-agent
      name: "Document Intake Agent"
      type: ai_agent
      position: { x: 250, y: 350 }
      settings:
        role: "Document Assessment Specialist"
        system_prompt: |
          You are a document intake specialist. Your role is to assess the PDF document's 
          quality, structure, and readiness for processing. Analyze the document and provide:
          - Document quality assessment (OCR quality, completeness)
          - Basic metadata (parties mentioned, dates found)
          - Document type preliminary assessment
          - Processing recommendations for downstream agents
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        max_tokens: 2000
        mcp_tools_enabled: true
        mcp_tools:
          - name: "pdf_analyzer"
            description: "Analyze PDF structure and quality"
            server: "pdf-analysis-mcp-server"
          - name: "metadata_extractor"
            description: "Extract basic document metadata"
            server: "metadata-mcp-server"
        input_field: "ocr_result.markdown"
        output_field: "intake_analysis"
        
    - id: contract-classifier-agent
      name: "Contract Classifier Agent"
      type: ai_agent
      position: { x: 250, y: 500 }
      settings:
        role: "Legal Contract Classifier"
        system_prompt: |
          You are a legal contract classification expert. Based on the document intake analysis,
          classify this contract into specific categories and identify applicable legal frameworks.
          Determine:
          - Contract type (MSA, SLA, NDA, Employment Agreement, etc.)
          - Governing jurisdiction and applicable law
          - Industry-specific regulations that apply
          - Contract complexity level
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        mcp_tools_enabled: true
        mcp_tools:
          - name: "legal_taxonomy_lookup"
            description: "Match contract to legal taxonomy"
            server: "legal-reference-mcp-server"
          - name: "jurisdiction_detector"
            description: "Identify governing law jurisdiction"
            server: "legal-reference-mcp-server"
        input_field: "intake_analysis"
        output_field: "contract_classification"
        handoff_to: "terms-extractor-agent"
        
    - id: terms-extractor-agent
      name: "Terms Extractor Agent"
      type: ai_agent
      position: { x: 250, y: 650 }
      settings:
        role: "Contract Terms Extraction Specialist"
        system_prompt: |
          You are a contract terms extraction expert. Extract all key terms, clauses, 
          obligations, and rights from the contract. For each extracted element, provide:
          - Clause type and category
          - Exact text reference
          - Parties involved and their obligations
          - Key dates and deadlines
          - Financial terms and conditions
          - Confidence score for extraction accuracy
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "clause_identifier"
            description: "Identify and categorize contract clauses"
            server: "legal-nlp-mcp-server"
          - name: "party_extractor"
            description: "Extract contracting parties and roles"
            server: "legal-nlp-mcp-server"
          - name: "date_parser"
            description: "Parse and normalize contract dates"
            server: "date-processing-mcp-server"
          - name: "financial_terms_extractor"
            description: "Extract financial terms and amounts"
            server: "financial-analysis-mcp-server"
        input_field: "contract_classification"
        output_field: "extracted_terms"
        handoff_to: "risk-analyzer-agent"
        
    - id: risk-analyzer-agent
      name: "Risk Analyzer Agent"
      type: ai_agent
      position: { x: 250, y: 800 }
      settings:
        role: "Legal Risk Assessment Specialist"
        system_prompt: |
          You are a legal risk analysis expert. Review the extracted contract terms and assess:
          - Risk level for each clause (low, medium, high, critical)
          - Unusual or non-standard provisions
          - Unfavorable terms or one-sided obligations
          - Potential liability exposure
          - Missing risk mitigation clauses
          Provide specific recommendations for risk mitigation.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.2
        mcp_tools_enabled: true
        mcp_tools:
          - name: "risk_scorer"
            description: "Calculate risk scores for clauses"
            server: "risk-assessment-mcp-server"
          - name: "clause_comparator"
            description: "Compare against standard clause library"
            server: "legal-reference-mcp-server"
          - name: "redline_detector"
            description: "Detect unusual legal language"
            server: "legal-nlp-mcp-server"
        input_field: "extracted_terms"
        output_field: "risk_analysis"
        handoff_to: "compliance-checker-agent"
        
    - id: compliance-checker-agent
      name: "Compliance Checker Agent"
      type: ai_agent
      position: { x: 250, y: 950 }
      settings:
        role: "Legal Compliance Verification Specialist"
        system_prompt: |
          You are a legal compliance expert. Verify that the contract complies with:
          - Applicable regulatory requirements (GDPR, CCPA, industry-specific regulations)
          - Company contracting policies and standards
          - Required clause inclusion (force majeure, dispute resolution, etc.)
          - Jurisdiction-specific legal requirements
          Flag any compliance issues and required modifications.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        mcp_tools_enabled: true
        mcp_tools:
          - name: "regulatory_validator"
            description: "Validate against regulations"
            server: "compliance-mcp-server"
          - name: "policy_matcher"
            description: "Check company policy compliance"
            server: "policy-management-mcp-server"
          - name: "missing_clause_detector"
            description: "Identify missing required clauses"
            server: "legal-nlp-mcp-server"
        input_field: "risk_analysis"
        output_field: "compliance_report"
        handoff_to: "summary-generator-agent"
        
    - id: summary-generator-agent
      name: "Summary Generator Agent"
      type: ai_agent
      position: { x: 250, y: 1100 }
      settings:
        role: "Executive Summary Specialist"
        system_prompt: |
          You are an executive communication expert. Create a comprehensive yet concise
          summary of the contract analysis, including:
          - Executive summary (2-3 paragraphs)
          - Key terms and obligations at a glance
          - Critical risk factors and recommendations
          - Compliance status and required actions
          - Next steps and decision points
          Format the output for business stakeholders.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.3
        mcp_tools_enabled: true
        mcp_tools:
          - name: "executive_summarizer"
            description: "Generate business-friendly summaries"
            server: "summarization-mcp-server"
          - name: "json_formatter"
            description: "Format data as structured JSON"
            server: "data-formatting-mcp-server"
          - name: "action_items_extractor"
            description: "Extract actionable next steps"
            server: "task-management-mcp-server"
        input_field: "compliance_report"
        output_field: "final_summary"
        
  executors:
    - id: blob-discovery-1
      name: "Discover Contracts"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      settings:
        file_extensions: ".pdf"
        blob_container_name: "legal-contracts"
        max_results: 50
        
    - id: blob-retrieval-1
      name: "Retrieve Contract PDFs"
      type: azure_blob_content_retriever
      position: { x: 250, y: 150 }
      settings:
        use_temp_file_for_content: true
        
    - id: doc-intelligence-1
      name: "OCR Contract Document"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 250 }
      settings:
        model_id: "prebuilt-read"
        output_format: "markdown"
        output_field: "ocr_result"
        
    - id: field-mapper-1
      name: "Normalize Contract Schema"
      type: field_mapper
      position: { x: 250, y: 1250 }
      settings:
        mappings: |
          {
            "final_summary.contract_type": "document_type",
            "extracted_terms.parties": "contracting_parties",
            "extracted_terms.effective_date": "effective_date",
            "extracted_terms.term_length": "contract_term",
            "risk_analysis.overall_risk_score": "risk_score",
            "compliance_report.compliance_status": "compliance_status"
          }
        
    - id: blob-output-1
      name: "Save Analyzed Contracts"
      type: azure_blob_output
      position: { x: 250, y: 1400 }
      settings:
        output_container_name: "analyzed-contracts"
        
    - id: ai-search-output-1
      name: "Index Contracts"
      type: ai_search_index_output
      position: { x: 250, y: 1550 }
      settings:
        index_name: "contracts-index"
        
  edges:
    - from: blob-discovery-1
      to: blob-retrieval-1
      type: sequential
    - from: blob-retrieval-1
      to: doc-intelligence-1
      type: sequential
    - from: doc-intelligence-1
      to: document-intake-agent
      type: agent_handoff
    - from: document-intake-agent
      to: contract-classifier-agent
      type: agent_handoff
    - from: contract-classifier-agent
      to: terms-extractor-agent
      type: agent_handoff
    - from: terms-extractor-agent
      to: risk-analyzer-agent
      type: agent_handoff
    - from: risk-analyzer-agent
      to: compliance-checker-agent
      type: agent_handoff
    - from: compliance-checker-agent
      to: summary-generator-agent
      type: agent_handoff
    - from: summary-generator-agent
      to: field-mapper-1
      type: sequential
    - from: field-mapper-1
      to: blob-output-1
      type: sequential
    - from: blob-output-1
      to: ai-search-output-1
      type: sequential
```

---

## Template 2: Financial Report Analysis with Group Chat Agent Collaboration

**Description**: Multiple specialist agents collaborate in a group chat pattern to analyze financial reports, with a coordinator agent managing the discussion and aggregating insights.

**Use Cases**:
- Quarterly/Annual Report Analysis: Extract financial metrics from 10-K, 10-Q filings
- Investment Research: Analyze company financials for investment decisions
- Credit Assessment: Evaluate financial health for lending decisions
- Regulatory Reporting: Extract data for compliance reporting

**Agent Architecture**:
```
Coordinator Agent manages discussion between:
├── Financial Data Extractor Agent
├── Ratio Analysis Agent
├── Trend Analysis Agent
├── Risk Assessment Agent
└── Narrative Analysis Agent
```

**Pipeline Steps**:

1. **Azure Blob Input Discovery** - Discover financial report PDFs
2. **Azure Blob Content Retriever** - Retrieve PDF documents
3. **Azure Document Intelligence Extractor** - OCR with table extraction
4. **Coordinator Agent** (Group Chat Manager) - Orchestrates multi-agent collaboration
   - **Role**: Manage group chat, synthesize insights, resolve conflicts
   - **Participants**: 5 specialist agents
   - **MCP Tools**:
     - `conversation_manager`: Manage turn-taking and agent coordination
     - `conflict_resolver`: Resolve disagreements between agents
     - `synthesis_engine`: Aggregate and synthesize agent outputs
     
5. **Group Chat Participants**:

   **a) Financial Data Extractor Agent**
   - **Role**: Extract financial statements, tables, and metrics
   - **MCP Tools**:
     - `table_parser`: Parse financial statement tables
     - `number_extractor`: Extract monetary values with accuracy
     - `financial_statement_classifier`: Identify statement types
   - **Output**: Structured financial data (balance sheet, income statement, cash flow)
   
   **b) Ratio Analysis Agent**
   - **Role**: Calculate and interpret financial ratios
   - **MCP Tools**:
     - `ratio_calculator`: Calculate financial ratios
     - `benchmark_comparator`: Compare against industry benchmarks
     - `ratio_interpreter`: Interpret ratio meanings
   - **Output**: Financial ratios, peer comparisons, ratio interpretations
   
   **c) Trend Analysis Agent**
   - **Role**: Analyze multi-period trends and growth patterns
   - **MCP Tools**:
     - `trend_calculator`: Calculate YoY, QoQ growth rates
     - `seasonality_detector`: Identify seasonal patterns
     - `anomaly_detector`: Flag unusual changes
   - **Output**: Trend analysis, growth trajectories, anomaly flags
   
   **d) Risk Assessment Agent**
   - **Role**: Evaluate financial risks and red flags
   - **MCP Tools**:
     - `risk_indicator_scanner`: Scan for risk indicators
     - `debt_analyzer`: Analyze debt structure and coverage
     - `liquidity_assessor`: Evaluate liquidity position
   - **Output**: Risk assessment, warning signals, risk score
   
   **e) Narrative Analysis Agent**
   - **Role**: Analyze management discussion and narrative sections
   - **MCP Tools**:
     - `sentiment_analyzer`: Assess management tone and sentiment
     - `forward_looking_extractor`: Extract guidance and forecasts
     - `risk_factor_parser`: Parse risk factor disclosures
   - **Output**: Sentiment analysis, forward guidance, qualitative insights

6. **Field Mapper** - Normalize to financial data schema
7. **Azure Blob Output** - Save structured financial analysis
8. **AI Search Index Output** - Index for financial research

**Estimated Time**: 8-12 minutes per report

**Features**:
- Multi-agent collaboration for comprehensive analysis
- Quantitative and qualitative analysis combined
- Peer benchmarking and trend analysis
- Risk identification and assessment

**Agent Configuration YAML**:
```yaml
pipeline:
  name: "Financial Report Analysis with Group Chat"
  description: "Multi-agent collaboration for comprehensive financial analysis"
  
  agents:
    - id: coordinator-agent
      name: "Financial Analysis Coordinator"
      type: group_chat_coordinator
      position: { x: 250, y: 350 }
      settings:
        role: "Financial Analysis Coordinator"
        system_prompt: |
          You are coordinating a team of financial analysis specialists to comprehensively
          analyze a financial report. Your responsibilities:
          - Manage discussion flow between specialist agents
          - Ensure all aspects of the report are analyzed
          - Resolve conflicting interpretations
          - Synthesize insights into a cohesive financial analysis
          - Identify gaps and request additional analysis
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.2
        max_rounds: 10
        speaker_selection_mode: "auto"
        mcp_tools_enabled: true
        mcp_tools:
          - name: "conversation_manager"
            description: "Manage agent turn-taking"
            server: "collaboration-mcp-server"
          - name: "conflict_resolver"
            description: "Resolve agent disagreements"
            server: "collaboration-mcp-server"
          - name: "synthesis_engine"
            description: "Synthesize agent outputs"
            server: "analysis-mcp-server"
        participants:
          - financial-data-extractor-agent
          - ratio-analysis-agent
          - trend-analysis-agent
          - risk-assessment-agent
          - narrative-analysis-agent
        input_field: "ocr_result"
        output_field: "coordinated_analysis"
        
    - id: financial-data-extractor-agent
      name: "Financial Data Extractor"
      type: ai_agent
      position: { x: 100, y: 500 }
      settings:
        role: "Financial Data Extraction Specialist"
        system_prompt: |
          You extract financial data from reports. Focus on:
          - Balance sheet items (assets, liabilities, equity)
          - Income statement (revenue, expenses, net income)
          - Cash flow statement (operating, investing, financing)
          - Key metrics (EPS, revenue, margins)
          Extract with precision and verify calculations.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "table_parser"
            server: "financial-data-mcp-server"
          - name: "number_extractor"
            server: "financial-data-mcp-server"
          - name: "financial_statement_classifier"
            server: "financial-data-mcp-server"
        group_chat_participant: true
        
    - id: ratio-analysis-agent
      name: "Ratio Analysis Agent"
      type: ai_agent
      position: { x: 200, y: 500 }
      settings:
        role: "Financial Ratio Analysis Specialist"
        system_prompt: |
          You calculate and interpret financial ratios. Analyze:
          - Profitability ratios (ROE, ROA, margins)
          - Liquidity ratios (current ratio, quick ratio)
          - Leverage ratios (debt-to-equity, interest coverage)
          - Efficiency ratios (asset turnover, inventory turnover)
          Compare against industry benchmarks and historical trends.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        mcp_tools_enabled: true
        mcp_tools:
          - name: "ratio_calculator"
            server: "financial-analysis-mcp-server"
          - name: "benchmark_comparator"
            server: "financial-data-mcp-server"
          - name: "ratio_interpreter"
            server: "financial-analysis-mcp-server"
        group_chat_participant: true
        
    - id: trend-analysis-agent
      name: "Trend Analysis Agent"
      type: ai_agent
      position: { x: 300, y: 500 }
      settings:
        role: "Financial Trend Analysis Specialist"
        system_prompt: |
          You analyze trends across reporting periods. Focus on:
          - Year-over-year and quarter-over-quarter growth
          - Revenue and profit trends
          - Margin progression
          - Seasonal patterns
          Identify positive trends, concerning declines, and inflection points.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        mcp_tools_enabled: true
        mcp_tools:
          - name: "trend_calculator"
            server: "statistical-analysis-mcp-server"
          - name: "seasonality_detector"
            server: "statistical-analysis-mcp-server"
          - name: "anomaly_detector"
            server: "statistical-analysis-mcp-server"
        group_chat_participant: true
        
    - id: risk-assessment-agent
      name: "Risk Assessment Agent"
      type: ai_agent
      position: { x: 400, y: 500 }
      settings:
        role: "Financial Risk Assessment Specialist"
        system_prompt: |
          You assess financial risks. Evaluate:
          - Credit risk (debt levels, coverage ratios)
          - Liquidity risk (working capital, cash position)
          - Operational risk (margin pressure, cost structure)
          - Market risk (revenue concentration, market exposure)
          Flag red flags and assign risk scores.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.2
        mcp_tools_enabled: true
        mcp_tools:
          - name: "risk_indicator_scanner"
            server: "risk-analysis-mcp-server"
          - name: "debt_analyzer"
            server: "financial-analysis-mcp-server"
          - name: "liquidity_assessor"
            server: "financial-analysis-mcp-server"
        group_chat_participant: true
        
    - id: narrative-analysis-agent
      name: "Narrative Analysis Agent"
      type: ai_agent
      position: { x: 500, y: 500 }
      settings:
        role: "Financial Narrative Analysis Specialist"
        system_prompt: |
          You analyze management discussion and narrative sections. Extract:
          - Management tone and sentiment
          - Forward-looking statements and guidance
          - Risk factor disclosures
          - Strategic initiatives and outlook
          Provide qualitative context to complement quantitative analysis.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.2
        mcp_tools_enabled: true
        mcp_tools:
          - name: "sentiment_analyzer"
            server: "nlp-analysis-mcp-server"
          - name: "forward_looking_extractor"
            server: "financial-nlp-mcp-server"
          - name: "risk_factor_parser"
            server: "financial-nlp-mcp-server"
        group_chat_participant: true
        
  executors:
    - id: blob-discovery-1
      name: "Discover Financial Reports"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      settings:
        file_extensions: ".pdf"
        blob_container_name: "financial-reports"
        
    - id: blob-retrieval-1
      name: "Retrieve Reports"
      type: azure_blob_content_retriever
      position: { x: 250, y: 150 }
      settings:
        use_temp_file_for_content: true
        
    - id: doc-intelligence-1
      name: "OCR with Tables"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 250 }
      settings:
        model_id: "prebuilt-layout"
        output_format: "markdown"
        output_field: "ocr_result"
        extract_tables: true
        
    - id: field-mapper-1
      name: "Normalize Financial Schema"
      type: field_mapper
      position: { x: 250, y: 650 }
      settings:
        mappings: |
          {
            "coordinated_analysis.financial_data": "statements",
            "coordinated_analysis.ratios": "financial_ratios",
            "coordinated_analysis.trends": "trend_analysis",
            "coordinated_analysis.risks": "risk_assessment",
            "coordinated_analysis.narrative_insights": "qualitative_analysis"
          }
        
    - id: blob-output-1
      name: "Save Financial Analysis"
      type: azure_blob_output
      position: { x: 250, y: 800 }
      settings:
        output_container_name: "analyzed-financials"
        
    - id: ai-search-output-1
      name: "Index for Research"
      type: ai_search_index_output
      position: { x: 250, y: 950 }
      settings:
        index_name: "financial-reports-index"
        
  edges:
    - from: blob-discovery-1
      to: blob-retrieval-1
      type: sequential
    - from: blob-retrieval-1
      to: doc-intelligence-1
      type: sequential
    - from: doc-intelligence-1
      to: coordinator-agent
      type: group_chat_initiation
    - from: coordinator-agent
      to: field-mapper-1
      type: sequential
    - from: field-mapper-1
      to: blob-output-1
      type: sequential
    - from: blob-output-1
      to: ai-search-output-1
      type: sequential
```

---

## Template 3: Medical Records Processing with Hierarchical Agent Teams

**Description**: Hierarchical agent structure where a Lead Medical Agent coordinates specialized sub-teams for comprehensive medical record analysis and structured data extraction.

**Use Cases**:
- Electronic Health Record (EHR) Migration: Extract data from legacy PDF records
- Medical Coding: Extract diagnoses and procedures for billing codes
- Clinical Research: Extract patient data for research studies
- Insurance Claims: Process medical documentation for claims adjudication

**Agent Architecture**:
```
Lead Medical Agent
├── Demographics Team
│   ├── Patient Info Agent
│   └── Contact Info Agent
├── Clinical Team
│   ├── Diagnosis Agent
│   ├── Medication Agent
│   ├── Procedure Agent
│   └── Vitals Agent
└── Administrative Team
    ├── Insurance Agent
    └── Billing Agent
```

**Pipeline Steps**:

1. **Azure Blob Input Discovery** - Discover medical record PDFs
2. **Azure Blob Content Retriever** - Retrieve medical documents
3. **Azure Document Intelligence Extractor** - OCR medical records
4. **PII Detector** - Identify PHI/PII for compliance
5. **Lead Medical Agent** (Hierarchical Coordinator)
   - **Role**: Coordinate specialized sub-teams
   - **MCP Tools**:
     - `team_coordinator`: Manage sub-team assignments
     - `medical_terminology_validator`: Validate medical terms
     - `completeness_checker`: Ensure all sections processed
   
6. **Demographics Team** (Parallel Processing)
   - **Patient Info Agent**:
     - Extract: Name, DOB, MRN, gender, race/ethnicity
     - MCP Tools: `patient_identifier`, `demographic_parser`
   - **Contact Info Agent**:
     - Extract: Address, phone, emergency contacts, PCP
     - MCP Tools: `contact_extractor`, `address_validator`
   
7. **Clinical Team** (Parallel Processing)
   - **Diagnosis Agent**:
     - Extract: Diagnoses, ICD codes, problem list
     - MCP Tools: `diagnosis_extractor`, `icd_code_mapper`
   - **Medication Agent**:
     - Extract: Medications, dosages, frequencies, allergies
     - MCP Tools: `medication_parser`, `drug_database_lookup`
   - **Procedure Agent**:
     - Extract: Procedures performed, CPT codes, dates
     - MCP Tools: `procedure_extractor`, `cpt_code_mapper`
   - **Vitals Agent**:
     - Extract: Vital signs, measurements, lab results
     - MCP Tools: `vitals_extractor`, `lab_result_parser`
   
8. **Administrative Team** (Parallel Processing)
   - **Insurance Agent**:
     - Extract: Insurance info, policy numbers, authorization
     - MCP Tools: `insurance_extractor`, `policy_validator`
   - **Billing Agent**:
     - Extract: Billing codes, charges, payment info
     - MCP Tools: `billing_code_extractor`, `charge_calculator`

9. **Medical Code Validator** - Validate ICD/CPT codes via MCP tools
10. **Field Mapper** - Normalize to FHIR or HL7 schema
11. **Azure Blob Output** - Save structured medical data
12. **Compliance Logger** - Log PHI access for HIPAA compliance

**Estimated Time**: 6-10 minutes per medical record

**Features**:
- Hierarchical agent coordination
- Specialized extraction for each data category
- Medical coding validation
- HIPAA compliance tracking

**Agent Configuration YAML**:
```yaml
pipeline:
  name: "Medical Records Processing with Hierarchical Agents"
  description: "Hierarchical agent teams for comprehensive medical record extraction"
  
  agents:
    - id: lead-medical-agent
      name: "Lead Medical Agent"
      type: hierarchical_coordinator
      position: { x: 250, y: 400 }
      settings:
        role: "Chief Medical Information Coordinator"
        system_prompt: |
          You coordinate specialized medical record extraction teams. Your responsibilities:
          - Assign sections of the medical record to appropriate sub-teams
          - Ensure comprehensive data extraction across all record sections
          - Validate medical terminology and coding accuracy
          - Coordinate dependencies between teams
          - Quality check extracted data for completeness and accuracy
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        mcp_tools_enabled: true
        mcp_tools:
          - name: "team_coordinator"
            server: "orchestration-mcp-server"
          - name: "medical_terminology_validator"
            server: "medical-reference-mcp-server"
          - name: "completeness_checker"
            server: "quality-assurance-mcp-server"
        sub_teams:
          - demographics-team
          - clinical-team
          - administrative-team
        input_field: "ocr_result"
        output_field: "medical_record_data"
        
    # Demographics Team
    - id: patient-info-agent
      name: "Patient Info Agent"
      type: ai_agent
      position: { x: 100, y: 550 }
      settings:
        role: "Patient Demographics Specialist"
        system_prompt: |
          Extract patient demographic information:
          - Full legal name, preferred name
          - Date of birth, age
          - Medical record number (MRN)
          - Gender, sex assigned at birth
          - Race, ethnicity
          Ensure accuracy and handle name variations.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "patient_identifier"
            server: "medical-data-mcp-server"
          - name: "demographic_parser"
            server: "medical-data-mcp-server"
        team: "demographics-team"
        
    - id: contact-info-agent
      name: "Contact Info Agent"
      type: ai_agent
      position: { x: 200, y: 550 }
      settings:
        role: "Contact Information Specialist"
        system_prompt: |
          Extract patient contact and related party information:
          - Current address (with validation)
          - Phone numbers (mobile, home)
          - Email address
          - Emergency contacts (name, relationship, phone)
          - Primary care physician
          - Preferred contact method
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "contact_extractor"
            server: "medical-data-mcp-server"
          - name: "address_validator"
            server: "address-verification-mcp-server"
        team: "demographics-team"
        
    # Clinical Team
    - id: diagnosis-agent
      name: "Diagnosis Agent"
      type: ai_agent
      position: { x: 100, y: 700 }
      settings:
        role: "Diagnosis and Problem List Specialist"
        system_prompt: |
          Extract diagnosis and problem list information:
          - Primary and secondary diagnoses
          - ICD-10 codes (map if not present)
          - Active problem list
          - Diagnosis dates and status (active/resolved)
          - Severity and clinical context
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "diagnosis_extractor"
            server: "clinical-nlp-mcp-server"
          - name: "icd_code_mapper"
            server: "medical-coding-mcp-server"
        team: "clinical-team"
        
    - id: medication-agent
      name: "Medication Agent"
      type: ai_agent
      position: { x: 200, y: 700 }
      settings:
        role: "Medication and Allergy Specialist"
        system_prompt: |
          Extract medication and allergy information:
          - Current medications (name, dosage, frequency, route)
          - Medication start and end dates
          - Prescribing physician
          - Allergies and adverse reactions
          - Drug interactions and contraindications
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "medication_parser"
            server: "clinical-nlp-mcp-server"
          - name: "drug_database_lookup"
            server: "pharmacy-reference-mcp-server"
        team: "clinical-team"
        
    - id: procedure-agent
      name: "Procedure Agent"
      type: ai_agent
      position: { x: 300, y: 700 }
      settings:
        role: "Procedure and Treatment Specialist"
        system_prompt: |
          Extract procedure and treatment information:
          - Procedures performed (description, date, provider)
          - CPT codes (map if not present)
          - Surgical history
          - Treatment plans and interventions
          - Procedure outcomes and complications
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "procedure_extractor"
            server: "clinical-nlp-mcp-server"
          - name: "cpt_code_mapper"
            server: "medical-coding-mcp-server"
        team: "clinical-team"
        
    - id: vitals-agent
      name: "Vitals Agent"
      type: ai_agent
      position: { x: 400, y: 700 }
      settings:
        role: "Vitals and Lab Results Specialist"
        system_prompt: |
          Extract vital signs and lab results:
          - Vital signs (BP, HR, temp, RR, SpO2, weight, height, BMI)
          - Lab results with reference ranges
          - Diagnostic test results
          - Measurement dates and trends
          - Abnormal findings and flags
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "vitals_extractor"
            server: "clinical-data-mcp-server"
          - name: "lab_result_parser"
            server: "laboratory-mcp-server"
        team: "clinical-team"
        
    # Administrative Team
    - id: insurance-agent
      name: "Insurance Agent"
      type: ai_agent
      position: { x: 150, y: 850 }
      settings:
        role: "Insurance Information Specialist"
        system_prompt: |
          Extract insurance and coverage information:
          - Primary and secondary insurance
          - Policy numbers and group numbers
          - Insurance company name and contact
          - Authorization numbers and dates
          - Coverage details and limitations
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "insurance_extractor"
            server: "billing-mcp-server"
          - name: "policy_validator"
            server: "insurance-verification-mcp-server"
        team: "administrative-team"
        
    - id: billing-agent
      name: "Billing Agent"
      type: ai_agent
      position: { x: 350, y: 850 }
      settings:
        role: "Billing and Charges Specialist"
        system_prompt: |
          Extract billing and charge information:
          - Service codes and billing codes
          - Charges and payment amounts
          - Payment method and transaction details
          - Balance and outstanding amounts
          - Billing provider and facility
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "billing_code_extractor"
            server: "billing-mcp-server"
          - name: "charge_calculator"
            server: "billing-mcp-server"
        team: "administrative-team"
        
  executors:
    - id: blob-discovery-1
      name: "Discover Medical Records"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      settings:
        file_extensions: ".pdf"
        blob_container_name: "medical-records"
        
    - id: blob-retrieval-1
      name: "Retrieve Records"
      type: azure_blob_content_retriever
      position: { x: 250, y: 150 }
      settings:
        use_temp_file_for_content: true
        
    - id: doc-intelligence-1
      name: "OCR Medical Record"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 250 }
      settings:
        model_id: "prebuilt-read"
        output_format: "markdown"
        output_field: "ocr_result"
        
    - id: pii-detector-1
      name: "Detect PHI/PII"
      type: pii_detector
      position: { x: 250, y: 350 }
      settings:
        input_field: "ocr_result"
        output_field: "phi_detected"
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        
    - id: field-mapper-1
      name: "Normalize to FHIR"
      type: field_mapper
      position: { x: 250, y: 1000 }
      settings:
        mappings: |
          {
            "medical_record_data.patient_info": "patient",
            "medical_record_data.diagnoses": "condition",
            "medical_record_data.medications": "medicationStatement",
            "medical_record_data.procedures": "procedure",
            "medical_record_data.vitals": "observation"
          }
        schema: "FHIR_R4"
        
    - id: blob-output-1
      name: "Save Structured Records"
      type: azure_blob_output
      position: { x: 250, y: 1150 }
      settings:
        output_container_name: "structured-medical-records"
        
  edges:
    - from: blob-discovery-1
      to: blob-retrieval-1
      type: sequential
    - from: blob-retrieval-1
      to: doc-intelligence-1
      type: sequential
    - from: doc-intelligence-1
      to: pii-detector-1
      type: sequential
    - from: pii-detector-1
      to: lead-medical-agent
      type: hierarchical_coordination
    - from: lead-medical-agent
      to: field-mapper-1
      type: sequential
    - from: field-mapper-1
      to: blob-output-1
      type: sequential
```

---

## Template 4: Research Paper Analysis with Swarm Intelligence Pattern

**Description**: A swarm of specialized agents work independently then converge to analyze academic research papers, extracting methodology, findings, and citations.

**Use Cases**:
- Literature Review Automation: Extract key insights from research papers
- Citation Analysis: Build citation networks and track research lineage
- Research Synthesis: Summarize findings across multiple papers
- Grant Proposal Research: Find relevant prior work and methodologies

**Agent Architecture**:
```
Swarm Agents (Independent Processing):
├── Abstract Analyzer Agent
├── Methodology Extractor Agent
├── Results Analyzer Agent
├── Citation Extractor Agent
├── Statistical Analysis Agent
└── Novelty Assessment Agent

Convergence Agent: Synthesizes all agent outputs
```

**Pipeline Steps**:

1. **Azure Blob Input Discovery** - Discover research paper PDFs
2. **Azure Blob Content Retriever** - Retrieve papers
3. **Azure Document Intelligence Extractor** - OCR with figures/tables
4. **Section Identifier** - Identify paper sections (abstract, methods, results, etc.)
5. **Swarm Deployment** - Launch independent agents simultaneously
   
   **Parallel Agent Swarm**:
   
   **a) Abstract Analyzer Agent**
   - Extract: Research question, hypothesis, main findings
   - MCP Tools: `abstract_parser`, `research_question_extractor`
   
   **b) Methodology Extractor Agent**
   - Extract: Methods, datasets, experimental design, tools used
   - MCP Tools: `methodology_classifier`, `dataset_identifier`
   
   **c) Results Analyzer Agent**
   - Extract: Key findings, statistics, performance metrics
   - MCP Tools: `results_parser`, `metric_extractor`
   
   **d) Citation Extractor Agent**
   - Extract: References, citations, bibliography
   - MCP Tools: `citation_parser`, `doi_resolver`, `reference_formatter`
   
   **e) Statistical Analysis Agent**
   - Extract: Statistical tests, p-values, confidence intervals
   - MCP Tools: `statistics_extractor`, `significance_tester`
   
   **f) Novelty Assessment Agent**
   - Assess: Novelty claims, contributions, limitations
   - MCP Tools: `novelty_evaluator`, `contribution_ranker`

6. **Convergence Agent** - Synthesize swarm intelligence
   - Aggregate all agent findings
   - Resolve conflicts and inconsistencies
   - Generate comprehensive paper summary
   - MCP Tools: `swarm_synthesizer`, `conflict_resolver`, `summary_generator`

7. **Field Mapper** - Normalize to research metadata schema
8. **Azure Blob Output** - Save structured research data
9. **AI Search Index Output** - Index for research discovery

**Estimated Time**: 5-8 minutes per paper

**Features**:
- Parallel swarm processing for speed
- Comprehensive multi-aspect analysis
- Citation network extraction
- Research contribution assessment

**Agent Configuration YAML**:
```yaml
pipeline:
  name: "Research Paper Analysis with Swarm Intelligence"
  description: "Swarm agents independently analyze research papers then converge findings"
  
  agents:
    # Swarm Agents (Process Independently in Parallel)
    - id: abstract-analyzer-agent
      name: "Abstract Analyzer"
      type: swarm_agent
      position: { x: 100, y: 500 }
      settings:
        role: "Abstract Analysis Specialist"
        system_prompt: |
          Analyze the research paper abstract. Extract:
          - Research question and hypothesis
          - Main objectives and goals
          - Key findings and contributions
          - Significance and impact claims
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.1
        mcp_tools_enabled: true
        mcp_tools:
          - name: "abstract_parser"
            server: "research-nlp-mcp-server"
          - name: "research_question_extractor"
            server: "research-nlp-mcp-server"
        swarm_behavior: "independent"
        input_field: "sections.abstract"
        output_field: "abstract_analysis"
        
    - id: methodology-extractor-agent
      name: "Methodology Extractor"
      type: swarm_agent
      position: { x: 200, y: 500 }
      settings:
        role: "Methodology Extraction Specialist"
        system_prompt: |
          Extract methodology details from the research paper:
          - Research design and approach
          - Datasets used (name, size, source)
          - Experimental setup and parameters
          - Tools, frameworks, and technologies
          - Evaluation metrics and baselines
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "methodology_classifier"
            server: "research-taxonomy-mcp-server"
          - name: "dataset_identifier"
            server: "research-data-mcp-server"
        swarm_behavior: "independent"
        input_field: "sections.methodology"
        output_field: "methodology_data"
        
    - id: results-analyzer-agent
      name: "Results Analyzer"
      type: swarm_agent
      position: { x: 300, y: 500 }
      settings:
        role: "Results Analysis Specialist"
        system_prompt: |
          Analyze the results section. Extract:
          - Key findings and outcomes
          - Performance metrics and scores
          - Comparisons with baselines
          - Result tables and figures
          - Unexpected findings or limitations
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        mcp_tools_enabled: true
        mcp_tools:
          - name: "results_parser"
            server: "research-nlp-mcp-server"
          - name: "metric_extractor"
            server: "performance-metrics-mcp-server"
        swarm_behavior: "independent"
        input_field: "sections.results"
        output_field: "results_analysis"
        
    - id: citation-extractor-agent
      name: "Citation Extractor"
      type: swarm_agent
      position: { x: 400, y: 500 }
      settings:
        role: "Citation Extraction Specialist"
        system_prompt: |
          Extract and structure citation information:
          - All references and bibliography entries
          - In-text citations with context
          - DOIs and external identifiers
          - Citation relationships and networks
          - Influential references
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "citation_parser"
            server: "bibliography-mcp-server"
          - name: "doi_resolver"
            server: "doi-resolution-mcp-server"
          - name: "reference_formatter"
            server: "bibliography-mcp-server"
        swarm_behavior: "independent"
        input_field: "sections.references"
        output_field: "citation_data"
        
    - id: statistical-analysis-agent
      name: "Statistical Analysis Agent"
      type: swarm_agent
      position: { x: 500, y: 500 }
      settings:
        role: "Statistical Analysis Specialist"
        system_prompt: |
          Extract statistical information:
          - Statistical tests performed
          - P-values and significance levels
          - Confidence intervals
          - Effect sizes
          - Sample sizes and power analysis
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "statistics_extractor"
            server: "statistical-analysis-mcp-server"
          - name: "significance_tester"
            server: "statistical-analysis-mcp-server"
        swarm_behavior: "independent"
        input_field: "sections.results"
        output_field: "statistical_analysis"
        
    - id: novelty-assessment-agent
      name: "Novelty Assessment Agent"
      type: swarm_agent
      position: { x: 600, y: 500 }
      settings:
        role: "Research Novelty Specialist"
        system_prompt: |
          Assess the novelty and contributions:
          - Claimed contributions and innovations
          - Comparison with prior work
          - Stated limitations
          - Future work directions
          - Overall novelty assessment
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.2
        mcp_tools_enabled: true
        mcp_tools:
          - name: "novelty_evaluator"
            server: "research-evaluation-mcp-server"
          - name: "contribution_ranker"
            server: "research-evaluation-mcp-server"
        swarm_behavior: "independent"
        input_field: "full_text"
        output_field: "novelty_assessment"
        
    # Convergence Agent (Synthesizes Swarm Outputs)
    - id: convergence-agent
      name: "Swarm Convergence Agent"
      type: convergence_agent
      position: { x: 350, y: 700 }
      settings:
        role: "Research Synthesis Coordinator"
        system_prompt: |
          You synthesize outputs from the research analysis swarm. Your tasks:
          - Aggregate findings from all swarm agents
          - Resolve any conflicting interpretations
          - Generate a comprehensive research paper summary
          - Highlight key insights and contributions
          - Assess overall paper quality and impact
          - Create structured metadata for indexing
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.2
        mcp_tools_enabled: true
        mcp_tools:
          - name: "swarm_synthesizer"
            server: "synthesis-mcp-server"
          - name: "conflict_resolver"
            server: "synthesis-mcp-server"
          - name: "summary_generator"
            server: "summarization-mcp-server"
        swarm_inputs:
          - abstract_analysis
          - methodology_data
          - results_analysis
          - citation_data
          - statistical_analysis
          - novelty_assessment
        output_field: "synthesized_research_data"
        
  executors:
    - id: blob-discovery-1
      name: "Discover Research Papers"
      type: azure_blob_input_discovery
      position: { x: 350, y: 50 }
      settings:
        file_extensions: ".pdf"
        blob_container_name: "research-papers"
        
    - id: blob-retrieval-1
      name: "Retrieve Papers"
      type: azure_blob_content_retriever
      position: { x: 350, y: 150 }
      settings:
        use_temp_file_for_content: true
        
    - id: doc-intelligence-1
      name: "OCR with Figures"
      type: azure_document_intelligence_extractor
      position: { x: 350, y: 250 }
      settings:
        model_id: "prebuilt-layout"
        output_format: "markdown"
        output_field: "ocr_result"
        extract_figures: true
        extract_tables: true
        
    - id: section-identifier-1
      name: "Identify Sections"
      type: content_classifier
      position: { x: 350, y: 350 }
      settings:
        categories: "abstract, introduction, methodology, results, discussion, conclusion, references"
        input_field: "ocr_result"
        output_field: "sections"
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        
    - id: field-mapper-1
      name: "Normalize Research Metadata"
      type: field_mapper
      position: { x: 350, y: 850 }
      settings:
        mappings: |
          {
            "synthesized_research_data.title": "paper_title",
            "synthesized_research_data.authors": "authors",
            "synthesized_research_data.abstract": "abstract",
            "synthesized_research_data.methodology": "methods",
            "synthesized_research_data.findings": "key_findings",
            "synthesized_research_data.citations": "references"
          }
        
    - id: blob-output-1
      name: "Save Research Data"
      type: azure_blob_output
      position: { x: 350, y: 1000 }
      settings:
        output_container_name: "analyzed-research-papers"
        
    - id: ai-search-output-1
      name: "Index for Discovery"
      type: ai_search_index_output
      position: { x: 350, y: 1150 }
      settings:
        index_name: "research-papers-index"
        
  edges:
    - from: blob-discovery-1
      to: blob-retrieval-1
      type: sequential
    - from: blob-retrieval-1
      to: doc-intelligence-1
      type: sequential
    - from: doc-intelligence-1
      to: section-identifier-1
      type: sequential
    - from: section-identifier-1
      to: [abstract-analyzer-agent, methodology-extractor-agent, results-analyzer-agent, citation-extractor-agent, statistical-analysis-agent, novelty-assessment-agent]
      type: swarm_deployment
    - from: [abstract-analyzer-agent, methodology-extractor-agent, results-analyzer-agent, citation-extractor-agent, statistical-analysis-agent, novelty-assessment-agent]
      to: convergence-agent
      type: swarm_convergence
    - from: convergence-agent
      to: field-mapper-1
      type: sequential
    - from: field-mapper-1
      to: blob-output-1
      type: sequential
    - from: blob-output-1
      to: ai-search-output-1
      type: sequential
```

---

## Template 5: Insurance Claims Processing with Agent Negotiation Pattern

**Description**: Multiple validation agents negotiate and reach consensus on claim validity, coverage, and payout amounts through iterative discussion.

**Use Cases**:
- Auto Insurance Claims: Process accident reports and damage assessments
- Health Insurance Claims: Validate medical necessity and coverage
- Property Insurance Claims: Assess damage and determine payouts
- Fraud Detection: Identify suspicious claims through multi-agent validation

**Agent Architecture**:
```
Negotiation Round-Robin:
├── Claims Intake Agent (Initial Assessment)
├── Coverage Validation Agent
├── Damage Assessment Agent
├── Fraud Detection Agent
├── Medical Necessity Agent (Health Claims)
└── Settlement Negotiation Agent (Reaches Consensus)
```

**Pipeline Steps**:

1. **Azure Blob Input Discovery** - Discover claim documents (forms, photos, medical records)
2. **Azure Blob Content Retriever** - Retrieve claim documentation
3. **Azure Document Intelligence Extractor** - OCR claim forms and supporting docs
4. **Claims Intake Agent** - Initial claim assessment and categorization
   - Extract: Claimant info, policy number, incident details, claim amount
   - MCP Tools: `policy_lookup`, `claimant_verification`, `incident_classifier`
   
5. **Agent Negotiation Round** (Iterative Discussion):

   **Round 1: Initial Assessments**
   
   **Coverage Validation Agent**:
   - Verify: Policy active, coverage applicable, limits sufficient
   - MCP Tools: `policy_database_query`, `coverage_calculator`, `exclusion_checker`
   - Output: Coverage determination with reasoning
   
   **Damage Assessment Agent**:
   - Analyze: Photos, repair estimates, damage extent
   - MCP Tools: `image_analyzer`, `cost_estimator`, `damage_classifier`
   - Output: Damage assessment and estimated cost
   
   **Fraud Detection Agent**:
   - Check: Claim patterns, fraud indicators, inconsistencies
   - MCP Tools: `fraud_scorer`, `pattern_matcher`, `anomaly_detector`
   - Output: Fraud risk score and suspicious elements
   
   **Medical Necessity Agent** (if health claim):
   - Verify: Medical necessity, treatment appropriateness
   - MCP Tools: `medical_necessity_validator`, `cpt_reasonableness_checker`
   - Output: Medical necessity determination
   
   **Round 2-N: Negotiation and Consensus**
   
   **Settlement Negotiation Agent** (Moderator):
   - Synthesize agent opinions
   - Identify disagreements
   - Request additional analysis if needed
   - Reach consensus on claim validity and payout
   - MCP Tools: `consensus_builder`, `payout_calculator`, `settlement_optimizer`

6. **Field Mapper** - Normalize claim decision data
7. **Conditional Router** - Route based on decision
   - Approved: Generate payment
   - Denied: Generate denial letter
   - Needs Review: Flag for adjuster
8. **Azure Blob Output** - Save claim decision with agent discussion log
9. **Alert Executor** - Notify stakeholders

**Estimated Time**: 6-10 minutes per claim

**Features**:
- Multi-agent validation for accuracy
- Fraud detection through collaborative analysis
- Consensus-based decision making
- Audit trail of agent negotiations

**Agent Configuration YAML**:
```yaml
pipeline:
  name: "Insurance Claims Processing with Agent Negotiation"
  description: "Multi-agent negotiation for collaborative claim adjudication"
  
  agents:
    - id: claims-intake-agent
      name: "Claims Intake Agent"
      type: ai_agent
      position: { x: 250, y: 400 }
      settings:
        role: "Claims Intake Specialist"
        system_prompt: |
          You perform initial claim intake and assessment. Extract:
          - Claimant information and policy details
          - Incident date, location, and description
          - Claimed amount and loss type
          - Supporting documentation inventory
          Categorize the claim type and route to appropriate validation agents.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        mcp_tools_enabled: true
        mcp_tools:
          - name: "policy_lookup"
            server: "insurance-database-mcp-server"
          - name: "claimant_verification"
            server: "identity-verification-mcp-server"
          - name: "incident_classifier"
            server: "claims-taxonomy-mcp-server"
        input_field: "ocr_result"
        output_field: "intake_assessment"
        handoff_to: "settlement-negotiation-agent"
        
    - id: coverage-validation-agent
      name: "Coverage Validation Agent"
      type: negotiation_agent
      position: { x: 100, y: 600 }
      settings:
        role: "Coverage Validation Specialist"
        system_prompt: |
          You validate insurance coverage for claims. Determine:
          - Is the policy active and in force?
          - Does coverage apply to this type of loss?
          - Are policy limits sufficient?
          - Do any exclusions apply?
          - What is the applicable deductible?
          Provide clear reasoning for your coverage determination.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        negotiation_rounds: 3
        mcp_tools_enabled: true
        mcp_tools:
          - name: "policy_database_query"
            server: "insurance-database-mcp-server"
          - name: "coverage_calculator"
            server: "insurance-rules-mcp-server"
          - name: "exclusion_checker"
            server: "insurance-rules-mcp-server"
        negotiation_group: "claim-validation"
        output_field: "coverage_validation"
        
    - id: damage-assessment-agent
      name: "Damage Assessment Agent"
      type: negotiation_agent
      position: { x: 250, y: 600 }
      settings:
        role: "Damage Assessment Specialist"
        system_prompt: |
          You assess damage and estimate repair/replacement costs. Analyze:
          - Extent of damage from photos and descriptions
          - Reasonableness of repair estimates
          - Actual cash value vs replacement cost
          - Depreciation and betterment
          Provide detailed assessment with cost breakdown.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        negotiation_rounds: 3
        mcp_tools_enabled: true
        mcp_tools:
          - name: "image_analyzer"
            server: "vision-analysis-mcp-server"
          - name: "cost_estimator"
            server: "repair-cost-mcp-server"
          - name: "damage_classifier"
            server: "damage-taxonomy-mcp-server"
        negotiation_group: "claim-validation"
        output_field: "damage_assessment"
        
    - id: fraud-detection-agent
      name: "Fraud Detection Agent"
      type: negotiation_agent
      position: { x: 400, y: 600 }
      settings:
        role: "Fraud Detection Specialist"
        system_prompt: |
          You detect potential fraud in insurance claims. Look for:
          - Inconsistencies in claim details
          - Unusual patterns or timing
          - Claimant history and prior claims
          - Suspicious documentation
          - Known fraud indicators
          Calculate fraud risk score and flag suspicious elements.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.2
        negotiation_rounds: 3
        mcp_tools_enabled: true
        mcp_tools:
          - name: "fraud_scorer"
            server: "fraud-detection-mcp-server"
          - name: "pattern_matcher"
            server: "pattern-analysis-mcp-server"
          - name: "anomaly_detector"
            server: "statistical-analysis-mcp-server"
        negotiation_group: "claim-validation"
        output_field: "fraud_assessment"
        
    - id: settlement-negotiation-agent
      name: "Settlement Negotiation Agent"
      type: negotiation_moderator
      position: { x: 250, y: 800 }
      settings:
        role: "Settlement Negotiation Coordinator"
        system_prompt: |
          You moderate the claim validation discussion and reach consensus. Your tasks:
          - Synthesize opinions from validation agents
          - Identify and resolve disagreements
          - Request additional analysis if needed
          - Calculate final settlement amount considering all factors
          - Make final determination: Approve, Deny, or Request Manual Review
          - Provide clear justification for the decision
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.2
        max_negotiation_rounds: 5
        consensus_threshold: 0.75
        mcp_tools_enabled: true
        mcp_tools:
          - name: "consensus_builder"
            server: "negotiation-mcp-server"
          - name: "payout_calculator"
            server: "insurance-rules-mcp-server"
          - name: "settlement_optimizer"
            server: "claims-optimization-mcp-server"
        participants:
          - coverage-validation-agent
          - damage-assessment-agent
          - fraud-detection-agent
        input_field: "intake_assessment"
        output_field: "claim_decision"
        
  executors:
    - id: blob-discovery-1
      name: "Discover Claim Documents"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      settings:
        file_extensions: ".pdf,.jpg,.png"
        blob_container_name: "insurance-claims"
        
    - id: blob-retrieval-1
      name: "Retrieve Documents"
      type: azure_blob_content_retriever
      position: { x: 250, y: 150 }
      settings:
        use_temp_file_for_content: true
        
    - id: doc-intelligence-1
      name: "OCR Claim Documents"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 250 }
      settings:
        model_id: "prebuilt-document"
        output_format: "markdown"
        output_field: "ocr_result"
        
    - id: field-mapper-1
      name: "Normalize Claim Data"
      type: field_mapper
      position: { x: 250, y: 950 }
      settings:
        mappings: |
          {
            "claim_decision.decision": "claim_status",
            "claim_decision.payout_amount": "settlement_amount",
            "claim_decision.reasoning": "decision_rationale"
          }
        
    - id: blob-output-1
      name: "Save Claim Decision"
      type: azure_blob_output
      position: { x: 250, y: 1100 }
      settings:
        output_container_name: "processed-claims"
        
  edges:
    - from: blob-discovery-1
      to: blob-retrieval-1
      type: sequential
    - from: blob-retrieval-1
      to: doc-intelligence-1
      type: sequential
    - from: doc-intelligence-1
      to: claims-intake-agent
      type: agent_handoff
    - from: claims-intake-agent
      to: settlement-negotiation-agent
      type: negotiation_initiation
    - from: settlement-negotiation-agent
      to: field-mapper-1
      type: sequential
    - from: field-mapper-1
      to: blob-output-1
      type: sequential
```

---

## Template 6: Generic Document Intelligence Extraction with Dynamic Agent Routing

**Description**: A flexible template that dynamically routes any PDF to appropriate specialist agents based on document type classification.

**Use Cases**:
- Mixed Document Batches: Process diverse document types in one pipeline
- Enterprise Document Management: Centralized processing for all document types
- Mailroom Automation: Route incoming documents to appropriate teams
- Digital Transformation: Migrate any legacy document to structured data

**Agent Architecture**:
```
Document Classifier Agent
         ↓
Dynamic Router (selects appropriate specialist agents)
         ↓
Specialist Agent Pool:
├── Invoice Processing Team
├── Contract Analysis Team
├── Resume/CV Parsing Team
├── Form Extraction Team
├── Report Analysis Team
└── General Document Team
```

**Pipeline Steps**:

1. **Azure Blob Input Discovery** - Discover any PDF documents
2. **Azure Blob Content Retriever** - Retrieve PDFs
3. **Azure Document Intelligence Extractor** - OCR with layout analysis
4. **Document Classifier Agent** - Classify document type
   - Categories: Invoice, Contract, Resume, Form, Report, Letter, Other
   - MCP Tools: `document_type_classifier`, `layout_analyzer`
   
5. **Dynamic Routing Agent** - Route to specialist team based on classification
   - MCP Tools: `agent_selector`, `capability_matcher`
   
6. **Specialist Agent Teams** (Conditional Execution):

   **Invoice Team** (if document_type == "Invoice"):
   - Invoice Data Extractor Agent
   - Line Item Parser Agent
   - Tax Calculator Agent
   
   **Contract Team** (if document_type == "Contract"):
   - Contract Terms Extractor Agent
   - Clause Analyzer Agent
   - Risk Assessment Agent
   
   **Resume Team** (if document_type == "Resume"):
   - Contact Info Extractor Agent
   - Experience Parser Agent
   - Skills Extractor Agent
   
   **Form Team** (if document_type == "Form"):
   - Field Identifier Agent
   - Checkbox/Selection Parser Agent
   - Signature Detector Agent
   
   **Report Team** (if document_type == "Report"):
   - Executive Summary Extractor Agent
   - Data Table Parser Agent
   - Chart/Graph Analyzer Agent
   
   **General Team** (if document_type == "Other"):
   - General Content Extractor Agent
   - Entity Recognition Agent
   - Summarization Agent

7. **Output Standardizer Agent** - Normalize outputs across specialist teams
8. **Field Mapper** - Map to common schema
9. **Azure Blob Output** - Save structured data
10. **AI Search Index Output** - Index for universal search

**Estimated Time**: 3-10 minutes (varies by document type)

**Features**:
- Universal document processing
- Dynamic agent selection
- Extensible specialist teams
- Standardized output format

**Agent Configuration YAML**:
```yaml
pipeline:
  name: "Generic Document Intelligence with Dynamic Routing"
  description: "Universal PDF processing with dynamic specialist agent routing"
  
  agents:
    - id: document-classifier-agent
      name: "Document Classifier"
      type: ai_agent
      position: { x: 250, y: 350 }
      settings:
        role: "Document Type Classification Specialist"
        system_prompt: |
          You classify documents into specific types for routing to specialist agents.
          Analyze the document structure, content, and layout to determine:
          - Document type (Invoice, Contract, Resume, Form, Report, Letter, Other)
          - Confidence level of classification
          - Key characteristics that informed the classification
          - Recommended specialist agents for processing
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        mcp_tools_enabled: true
        mcp_tools:
          - name: "document_type_classifier"
            server: "document-taxonomy-mcp-server"
          - name: "layout_analyzer"
            server: "document-analysis-mcp-server"
        input_field: "ocr_result"
        output_field: "document_classification"
        handoff_to: "dynamic-routing-agent"
        
    - id: dynamic-routing-agent
      name: "Dynamic Routing Agent"
      type: routing_agent
      position: { x: 250, y: 500 }
      settings:
        role: "Dynamic Agent Router"
        system_prompt: |
          Based on document classification, route to the appropriate specialist agent team.
          Select the team best suited to extract structured data from this document type.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "agent_selector"
            server: "orchestration-mcp-server"
          - name: "capability_matcher"
            server: "agent-registry-mcp-server"
        routing_map:
          invoice: "invoice-processing-team"
          contract: "contract-analysis-team"
          resume: "resume-parsing-team"
          form: "form-extraction-team"
          report: "report-analysis-team"
          other: "general-document-team"
        input_field: "document_classification"
        output_field: "routing_decision"
        
    # Invoice Processing Team
    - id: invoice-data-extractor
      name: "Invoice Data Extractor"
      type: specialist_agent
      position: { x: 100, y: 700 }
      settings:
        role: "Invoice Data Extraction Specialist"
        system_prompt: |
          Extract structured data from invoices:
          - Vendor details and invoice number
          - Dates, amounts, and payment terms
          - Line items with descriptions and prices
          - Tax and total calculations
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        activation_condition: "document_classification.type == 'invoice'"
        mcp_tools_enabled: true
        mcp_tools:
          - name: "invoice_parser"
            server: "financial-doc-mcp-server"
        specialist_team: "invoice-processing-team"
        output_field: "extracted_invoice_data"
        
    # Contract Analysis Team
    - id: contract-terms-extractor
      name: "Contract Terms Extractor"
      type: specialist_agent
      position: { x: 200, y: 700 }
      settings:
        role: "Contract Terms Extraction Specialist"
        system_prompt: |
          Extract key terms from contracts:
          - Parties, effective date, term length
          - Payment terms and financial obligations
          - Key clauses (termination, liability, IP)
          - Obligations and deliverables
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        activation_condition: "document_classification.type == 'contract'"
        mcp_tools_enabled: true
        mcp_tools:
          - name: "contract_parser"
            server: "legal-doc-mcp-server"
        specialist_team: "contract-analysis-team"
        output_field: "extracted_contract_data"
        
    # Resume Parsing Team
    - id: resume-parser
      name: "Resume Parser"
      type: specialist_agent
      position: { x: 300, y: 700 }
      settings:
        role: "Resume Parsing Specialist"
        system_prompt: |
          Extract structured data from resumes/CVs:
          - Contact information
          - Work experience (company, title, dates, responsibilities)
          - Education (degree, institution, dates)
          - Skills and certifications
          - Summary/objective
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        activation_condition: "document_classification.type == 'resume'"
        mcp_tools_enabled: true
        mcp_tools:
          - name: "resume_parser"
            server: "hr-doc-mcp-server"
          - name: "skills_extractor"
            server: "hr-taxonomy-mcp-server"
        specialist_team: "resume-parsing-team"
        output_field: "extracted_resume_data"
        
    # Form Extraction Team
    - id: form-field-extractor
      name: "Form Field Extractor"
      type: specialist_agent
      position: { x: 400, y: 700 }
      settings:
        role: "Form Field Extraction Specialist"
        system_prompt: |
          Extract data from forms:
          - Identify all form fields and labels
          - Extract filled values
          - Parse checkboxes and selections
          - Detect signatures and dates
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        activation_condition: "document_classification.type == 'form'"
        mcp_tools_enabled: true
        mcp_tools:
          - name: "form_parser"
            server: "form-processing-mcp-server"
        specialist_team: "form-extraction-team"
        output_field: "extracted_form_data"
        
    # Report Analysis Team
    - id: report-analyzer
      name: "Report Analyzer"
      type: specialist_agent
      position: { x: 500, y: 700 }
      settings:
        role: "Report Analysis Specialist"
        system_prompt: |
          Extract structured data from reports:
          - Executive summary
          - Key findings and metrics
          - Data tables and statistics
          - Charts and visualizations
          - Recommendations and conclusions
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        activation_condition: "document_classification.type == 'report'"
        mcp_tools_enabled: true
        mcp_tools:
          - name: "report_parser"
            server: "report-analysis-mcp-server"
        specialist_team: "report-analysis-team"
        output_field: "extracted_report_data"
        
    # General Document Team
    - id: general-content-extractor
      name: "General Content Extractor"
      type: specialist_agent
      position: { x: 600, y: 700 }
      settings:
        role: "General Content Extraction Specialist"
        system_prompt: |
          Extract general structured data from unclassified documents:
          - Document title and metadata
          - Main content and sections
          - Named entities (people, organizations, locations)
          - Key dates and numbers
          - Document summary
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        activation_condition: "document_classification.type == 'other'"
        mcp_tools_enabled: true
        mcp_tools:
          - name: "entity_extractor"
            server: "nlp-analysis-mcp-server"
          - name: "summarizer"
            server: "summarization-mcp-server"
        specialist_team: "general-document-team"
        output_field: "extracted_general_data"
        
    - id: output-standardizer-agent
      name: "Output Standardizer"
      type: ai_agent
      position: { x: 350, y: 900 }
      settings:
        role: "Output Standardization Specialist"
        system_prompt: |
          Normalize outputs from different specialist teams into a common format.
          Ensure all extracted data follows a consistent schema regardless of document type.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        input_field: "specialist_output"
        output_field: "standardized_data"
        
  executors:
    - id: blob-discovery-1
      name: "Discover Documents"
      type: azure_blob_input_discovery
      position: { x: 350, y: 50 }
      settings:
        file_extensions: ".pdf"
        blob_container_name: "mixed-documents"
        
    - id: blob-retrieval-1
      name: "Retrieve Documents"
      type: azure_blob_content_retriever
      position: { x: 350, y: 150 }
      settings:
        use_temp_file_for_content: true
        
    - id: doc-intelligence-1
      name: "OCR with Layout"
      type: azure_document_intelligence_extractor
      position: { x: 350, y: 250 }
      settings:
        model_id: "prebuilt-layout"
        output_format: "markdown"
        output_field: "ocr_result"
        
    - id: field-mapper-1
      name: "Map to Common Schema"
      type: field_mapper
      position: { x: 350, y: 1050 }
      settings:
        mappings: |
          {
            "standardized_data.document_type": "type",
            "standardized_data.extracted_fields": "data",
            "standardized_data.confidence": "confidence_score"
          }
        
    - id: blob-output-1
      name: "Save Processed Documents"
      type: azure_blob_output
      position: { x: 350, y: 1200 }
      settings:
        output_container_name: "processed-documents"
        
    - id: ai-search-output-1
      name: "Index All Documents"
      type: ai_search_index_output
      position: { x: 350, y: 1350 }
      settings:
        index_name: "universal-documents-index"
        
  edges:
    - from: blob-discovery-1
      to: blob-retrieval-1
      type: sequential
    - from: blob-retrieval-1
      to: doc-intelligence-1
      type: sequential
    - from: doc-intelligence-1
      to: document-classifier-agent
      type: agent_handoff
    - from: document-classifier-agent
      to: dynamic-routing-agent
      type: agent_handoff
    - from: dynamic-routing-agent
      to: [invoice-data-extractor, contract-terms-extractor, resume-parser, form-field-extractor, report-analyzer, general-content-extractor]
      type: conditional_routing
    - from: [invoice-data-extractor, contract-terms-extractor, resume-parser, form-field-extractor, report-analyzer, general-content-extractor]
      to: output-standardizer-agent
      type: convergence
    - from: output-standardizer-agent
      to: field-mapper-1
      type: sequential
    - from: field-mapper-1
      to: blob-output-1
      type: sequential
    - from: blob-output-1
      to: ai-search-output-1
      type: sequential
```

---

## Invoice-Focused Templates (Agent Collaboration Patterns)

These invoice templates are designed to fit common AP automation realities:
- Deterministic extraction and normalization → best with **hand-off**
- Ambiguous exceptions → best with **group chat** + coordinator
- 3-way matching disputes → best with **negotiation/consensus**
- Fraud/anomaly signals → best with **swarm + convergence**
- Line-item coding at scale → best with **hierarchical teams**

---

## Template 7: Invoice Extraction & Normalization with Specialist Hand-Off

**Description**: A sequential “handoff” chain optimized for accuracy and traceability: extract fields, normalize to your AP schema, validate totals, enrich vendor metadata, then generate a clean JSON record ready for downstream posting/indexing.

**Use Cases**:
- Multi-vendor invoice ingestion (PDF + scanned images)
- Consistent AP schema normalization across vendors
- Early detection of missing fields and arithmetic mismatches
- Vendor master enrichment (payment terms, tax IDs, bank accounts)

**Agent Architecture**:
```
Invoice Intake Agent → Invoice Extractor Agent → Normalizer Agent →
Validation Agent → Vendor Enrichment Agent → Output Builder Agent
```

**Pipeline Steps**:
1. **Azure Blob Input Discovery** - Discover invoice PDFs
2. **Azure Blob Content Retriever** - Retrieve invoice documents
3. **Azure Document Intelligence Extractor** - OCR + layout (table/line item helpful)
4. **Invoice Intake Agent** (MCP-enabled)
   - Identify invoice language, scan quality, page count, attachments
   - MCP tools: `pdf_analyzer`, `document_quality_scorer`
5. **Invoice Extractor Agent** (MCP-enabled)
   - Extract invoice header + line items; prefer deterministic extraction
   - MCP tools: `invoice_field_extractor`, `table_parser`, `number_extractor`, `date_parser`
6. **Normalizer Agent** (MCP-enabled)
   - Map vendor-specific phrasing into canonical AP fields
   - MCP tools: `schema_mapper`, `currency_normalizer`
7. **Validation Agent** (MCP-enabled)
   - Validate required fields, types, and cross-field checks (line items sum to total)
   - MCP tools: `data_validator`, `math_checker`
8. **Vendor Enrichment Agent** (MCP-enabled)
   - Enrich vendor profile and payment terms from master data
   - MCP tools: `vendor_master_lookup`, `watchlist_checker`
9. **Output Builder Agent**
   - Produce a single normalized JSON + extraction/validation metadata
10. **Azure Blob Output** - Save normalized invoice JSON
11. **AI Search Index Output** - Index invoice content + structured fields

**Estimated Time**: 2-4 minutes per invoice

**Pipeline YAML (sketch)**:
```yaml
pipeline:
  name: "Invoice Extraction & Normalization with Specialist Hand-Off"
  description: "Sequential specialist agents extract, normalize, validate, and enrich invoices"

  executors:
    - id: blob-discovery-1
      name: "Discover Invoices"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      settings:
        file_extensions: ".pdf,.png,.jpg,.jpeg,.tiff"
        blob_container_name: "invoices"

    - id: blob-retrieval-1
      name: "Retrieve Invoices"
      type: azure_blob_content_retriever
      position: { x: 250, y: 150 }
      settings:
        use_temp_file_for_content: true

    - id: doc-intelligence-1
      name: "OCR + Layout"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 250 }
      settings:
        model_id: "prebuilt-layout"
        output_format: "markdown"
        output_field: "ocr_result"
        extract_tables: true

  agents:
    - id: invoice-intake-agent
      name: "Invoice Intake Agent"
      type: ai_agent
      position: { x: 250, y: 360 }
      settings:
        role: "Invoice Intake Specialist"
        system_prompt: |
          Assess the invoice document quality and structure. Output:
          - page_count, language, scan_quality_score
          - any indicators of multi-invoice bundles
          - recommendations (e.g., requires second OCR pass)
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "pdf_analyzer"
            server: "pdf-analysis-mcp-server"
          - name: "document_quality_scorer"
            server: "quality-assurance-mcp-server"
        input_field: "ocr_result"
        output_field: "intake"

    - id: invoice-extractor-agent
      name: "Invoice Extractor Agent"
      type: ai_agent
      position: { x: 250, y: 510 }
      settings:
        role: "Invoice Extraction Specialist"
        system_prompt: |
          Extract invoice fields and line items. Provide a structured output with:
          invoice_number, vendor_name, vendor_address, invoice_date, due_date,
          subtotal, tax, total, currency, line_items[].
          Include confidence per field.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "invoice_field_extractor"
            server: "financial-doc-mcp-server"
          - name: "table_parser"
            server: "document-analysis-mcp-server"
          - name: "number_extractor"
            server: "document-analysis-mcp-server"
          - name: "date_parser"
            server: "date-processing-mcp-server"
        input_field: "ocr_result"
        output_field: "raw_invoice"
        handoff_to: "normalizer-agent"

    - id: normalizer-agent
      name: "Normalizer Agent"
      type: ai_agent
      position: { x: 250, y: 660 }
      settings:
        role: "AP Schema Normalizer"
        system_prompt: |
          Normalize extracted invoice fields into the target AP schema.
          Normalize dates (ISO), currency codes, and numeric formats.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "schema_mapper"
            server: "data-formatting-mcp-server"
          - name: "currency_normalizer"
            server: "financial-analysis-mcp-server"
        input_field: "raw_invoice"
        output_field: "normalized_invoice"
        handoff_to: "validation-agent"

    - id: validation-agent
      name: "Validation Agent"
      type: ai_agent
      position: { x: 250, y: 810 }
      settings:
        role: "Invoice Validator"
        system_prompt: |
          Validate required fields and cross-field consistency.
          - required: invoice_number, vendor_name, invoice_date, total
          - check: sum(line_items) ~= total within tolerance
          Output is_valid, errors[], warnings[].
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "data_validator"
            server: "quality-assurance-mcp-server"
          - name: "math_checker"
            server: "quality-assurance-mcp-server"
        input_field: "normalized_invoice"
        output_field: "validation"
        handoff_to: "vendor-enrichment-agent"

    - id: vendor-enrichment-agent
      name: "Vendor Enrichment Agent"
      type: ai_agent
      position: { x: 250, y: 960 }
      settings:
        role: "Vendor Master Enrichment"
        system_prompt: |
          Enrich vendor information and payment terms from master data.
          Add vendor_id, default_terms, bank_account_last4 (if allowed), tax_id.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "vendor_master_lookup"
            server: "erp-mcp-server"
          - name: "watchlist_checker"
            server: "risk-analysis-mcp-server"
        input_field: "normalized_invoice"
        output_field: "vendor_enrichment"

    - id: output-builder-agent
      name: "Output Builder Agent"
      type: ai_agent
      position: { x: 250, y: 1110 }
      settings:
        role: "Invoice Output Builder"
        system_prompt: |
          Build final structured output combining:
          normalized_invoice, validation, vendor_enrichment.
          Include trace metadata (doc_id, extraction_confidence_summary).
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        input_field: "vendor_enrichment"
        output_field: "final_invoice_json"

    - id: blob-output-1
      name: "Save Normalized Invoice"
      type: azure_blob_output
      position: { x: 250, y: 1260 }
      settings:
        output_container_name: "processed-invoices"

    - id: ai-search-output-1
      name: "Index Invoice"
      type: ai_search_index_output
      position: { x: 250, y: 1410 }
      settings:
        index_name: "invoices-index"

  edges:
    - from: blob-discovery-1
      to: blob-retrieval-1
      type: sequential
    - from: blob-retrieval-1
      to: doc-intelligence-1
      type: sequential
    - from: doc-intelligence-1
      to: invoice-intake-agent
      type: agent_handoff
    - from: invoice-intake-agent
      to: invoice-extractor-agent
      type: agent_handoff
    - from: invoice-extractor-agent
      to: normalizer-agent
      type: agent_handoff
    - from: normalizer-agent
      to: validation-agent
      type: agent_handoff
    - from: validation-agent
      to: vendor-enrichment-agent
      type: agent_handoff
    - from: vendor-enrichment-agent
      to: output-builder-agent
      type: agent_handoff
    - from: output-builder-agent
      to: blob-output-1
      type: sequential
    - from: blob-output-1
      to: ai-search-output-1
      type: sequential
```

---

## Template 8: Invoice Exception Triage with Group Chat (Best Fit for Ambiguity)

**Description**: When extraction is “good enough” but the decision isn’t (missing PO, mismatch totals, duplicate suspicion), a group-chat pattern is ideal: specialists provide opinions, and a coordinator produces a single routing decision and rationale.

**Use Cases**:
- Discrepancies (totals mismatch, tax anomalies)
- Missing PO number or unclear cost center
- Duplicate/near-duplicate invoice detection
- Escalation to human review with a clean, explainable packet

**Agent Architecture**:
```
Coordinator Agent moderates:
├── Validation Specialist Agent
├── Duplicate Detection Agent
├── PO Matching Agent
└── Payment Terms / Vendor Policy Agent
```

**Pipeline Steps**:
1. Extract invoice fields (Doc Intelligence / Content Understanding)
2. Run lightweight validation rules
3. **Group Chat**: each specialist explains findings + recommended route
4. Coordinator outputs: route + evidence + recommended next action
5. Conditional Router sends to: auto-post, needs human review, request vendor clarification

**Coordinator Output Example (structured)**:
```json
{
  "route": "manual_review",
  "reason_codes": ["TOTAL_MISMATCH", "MISSING_PO"],
  "evidence": {
    "computed_line_items_sum": 1042.18,
    "invoice_total": 1104.18,
    "po_candidates": []
  },
  "recommended_actions": ["Request PO number", "Verify tax line"]
}
```

**Pipeline YAML (sketch)**:
```yaml
pipeline:
  name: "Invoice Exception Triage with Group Chat"
  description: "Group chat specialists triage invoice exceptions and produce a single routing decision"

  executors:
    - id: blob-discovery-1
      name: "Discover Invoices"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      settings:
        file_extensions: ".pdf,.png,.jpg,.jpeg"
        blob_container_name: "incoming-invoices"

    - id: blob-retrieval-1
      name: "Retrieve Invoices"
      type: azure_blob_content_retriever
      position: { x: 250, y: 150 }
      settings:
        use_temp_file_for_content: true

    - id: doc-intelligence-1
      name: "OCR + Layout"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 250 }
      settings:
        model_id: "prebuilt-layout"
        output_format: "markdown"
        output_field: "ocr_result"
        extract_tables: true

    - id: field-mapper-1
      name: "Basic Field Map"
      type: field_mapper
      position: { x: 250, y: 350 }
      settings:
        mappings: |
          {
            "ocr_result": "invoice_text"
          }

  agents:
    - id: exception-triage-coordinator
      name: "Exception Triage Coordinator"
      type: group_chat_coordinator
      position: { x: 250, y: 500 }
      settings:
        role: "Invoice Exception Triage Coordinator"
        system_prompt: |
          You coordinate specialists to triage invoice exceptions. Produce a single JSON decision:
          - route: auto_post | manual_review | request_vendor | request_po | hold
          - reason_codes: []
          - evidence: {}
          - recommended_actions: []
          Use specialist messages as evidence; do not invent values.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        max_rounds: 8
        speaker_selection_mode: "auto"
        mcp_tools_enabled: true
        mcp_tools:
          - name: "conversation_manager"
            server: "collaboration-mcp-server"
          - name: "conflict_resolver"
            server: "collaboration-mcp-server"
        participants:
          - validation-specialist-agent
          - duplicate-detection-agent
          - po-matching-agent
          - vendor-policy-agent
        input_field: "invoice_text"
        output_field: "triage_decision"

    - id: validation-specialist-agent
      name: "Validation Specialist"
      type: ai_agent
      position: { x: 60, y: 650 }
      settings:
        role: "Invoice Validation Specialist"
        system_prompt: |
          Validate invoice fields and arithmetic:
          - required fields present
          - totals consistent with line items
          - tax reasonable (non-negative, within configured range)
          Return findings and recommended route.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "data_validator"
            server: "quality-assurance-mcp-server"
          - name: "math_checker"
            server: "quality-assurance-mcp-server"
        group_chat_participant: true

    - id: duplicate-detection-agent
      name: "Duplicate Detection"
      type: ai_agent
      position: { x: 220, y: 650 }
      settings:
        role: "Duplicate Invoice Specialist"
        system_prompt: |
          Determine if this invoice is a duplicate or near-duplicate.
          Check invoice_number/vendor/amount/date similarity.
          Return suspected duplicates and confidence.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "duplicate_search"
            server: "ap-history-mcp-server"
          - name: "similarity_matcher"
            server: "pattern-analysis-mcp-server"
        group_chat_participant: true

    - id: po-matching-agent
      name: "PO Matching"
      type: ai_agent
      position: { x: 380, y: 650 }
      settings:
        role: "PO Matching Specialist"
        system_prompt: |
          Identify PO references and propose PO candidates.
          Use any detected PO number and vendor match to look up candidates.
          Return candidate list with match scores.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "erp_po_lookup"
            server: "erp-mcp-server"
          - name: "line_item_matcher"
            server: "ap-matching-mcp-server"
        group_chat_participant: true

    - id: vendor-policy-agent
      name: "Vendor Policy"
      type: ai_agent
      position: { x: 540, y: 650 }
      settings:
        role: "Vendor Policy & Terms Specialist"
        system_prompt: |
          Check vendor policies and payment terms.
          Flag blocked/hold vendors, terms mismatch, bank change risk.
          Return findings and recommended route.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "vendor_master_lookup"
            server: "erp-mcp-server"
          - name: "watchlist_checker"
            server: "risk-analysis-mcp-server"
        group_chat_participant: true

  executors_after:
    - id: conditional-router-1
      name: "Route by Triage Decision"
      type: conditional_router
      position: { x: 250, y: 850 }
      settings:
        routes: |
          [
            {"name": "auto_post", "condition": "triage_decision.route == 'auto_post'"},
            {"name": "manual_review", "condition": "triage_decision.route == 'manual_review'"},
            {"name": "request_po", "condition": "triage_decision.route == 'request_po'"},
            {"name": "request_vendor", "condition": "triage_decision.route == 'request_vendor'"},
            {"name": "hold", "condition": "triage_decision.route == 'hold'"}
          ]
        default_route: "manual_review"

    - id: blob-output-1
      name: "Archive with Triage"
      type: azure_blob_output
      position: { x: 250, y: 1000 }
      settings:
        output_container_name: "invoice-triage-results"

  edges:
    - from: blob-discovery-1
      to: blob-retrieval-1
      type: sequential
    - from: blob-retrieval-1
      to: doc-intelligence-1
      type: sequential
    - from: doc-intelligence-1
      to: field-mapper-1
      type: sequential
    - from: field-mapper-1
      to: exception-triage-coordinator
      type: group_chat_initiation
    - from: exception-triage-coordinator
      to: conditional-router-1
      type: sequential
    - from: conditional-router-1
      to: blob-output-1
      type: sequential
```

---

## Template 9: Invoice ↔ PO ↔ Receipt 3-Way Match with Negotiation/Consensus

**Description**: 3-way matching is inherently adversarial: different match strategies can disagree (exact PO match vs fuzzy item match). A negotiation moderator produces a single “best match” decision with confidence.

**Use Cases**:
- PO referenced but ambiguous
- Partial receipts / partial invoicing
- Price/quantity variances requiring tolerance logic
- Vendor uses different item descriptions than PO

**Agent Architecture**:
```
Match Moderator negotiates among:
├── Exact Match Agent (PO#/line)
├── Fuzzy Line Item Match Agent
├── Variance Policy Agent (tolerances)
└── Receipt Coverage Agent
```

**Key MCP Tools**:
- `erp_po_lookup` (retrieve PO + lines)
- `receipt_lookup` (goods receipt / service entry)
- `line_item_matcher` (exact/fuzzy)
- `variance_calculator` (qty/price)
- `policy_tolerance_lookup` (buyer/BU rules)

**Outputs**:
- `match_result`: matched PO + line mapping
- `variance_analysis`: issues, tolerances, approvals needed
- `decision`: approve/hold/escalate

**Pipeline YAML (sketch)**:
```yaml
pipeline:
  name: "Invoice ↔ PO ↔ Receipt 3-Way Match (Negotiation/Consensus)"
  description: "Multiple match strategies negotiate; moderator produces best-match decision and variance outcomes"

  executors:
    - id: blob-discovery-1
      name: "Discover Invoices"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      settings:
        file_extensions: ".pdf"
        blob_container_name: "invoices"

    - id: blob-retrieval-1
      name: "Retrieve Invoice"
      type: azure_blob_content_retriever
      position: { x: 250, y: 150 }
      settings:
        use_temp_file_for_content: true

    - id: doc-intelligence-1
      name: "OCR + Layout"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 250 }
      settings:
        model_id: "prebuilt-layout"
        output_format: "markdown"
        output_field: "ocr_result"
        extract_tables: true

  agents:
    - id: invoice-structurer-agent
      name: "Invoice Structurer"
      type: ai_agent
      position: { x: 250, y: 360 }
      settings:
        role: "Invoice Structuring Agent"
        system_prompt: |
          Convert invoice text into a structured representation:
          vendor, invoice_number, invoice_date, currency, total,
          line_items[] with sku/desc/qty/unit_price/amount.
          Output must be machine-readable JSON.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "table_parser"
            server: "document-analysis-mcp-server"
          - name: "number_extractor"
            server: "document-analysis-mcp-server"
          - name: "date_parser"
            server: "date-processing-mcp-server"
        input_field: "ocr_result"
        output_field: "invoice_struct"
        handoff_to: "match-moderator"

    - id: exact-match-agent
      name: "Exact Match Agent"
      type: negotiation_agent
      position: { x: 60, y: 560 }
      settings:
        role: "Exact PO/Line Match"
        system_prompt: |
          Prefer exact matches:
          - PO number present
          - line item IDs match
          - vendor IDs match
          Return match candidates with explicit evidence.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "erp_po_lookup"
            server: "erp-mcp-server"
        negotiation_group: "three-way-match"
        output_field: "exact_match"

    - id: fuzzy-match-agent
      name: "Fuzzy Line Item Match Agent"
      type: negotiation_agent
      position: { x: 220, y: 560 }
      settings:
        role: "Fuzzy Line Item Match"
        system_prompt: |
          Match invoice line items to PO lines using fuzzy description and unit price proximity.
          Provide match score and explain mismatches.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "line_item_matcher"
            server: "ap-matching-mcp-server"
          - name: "erp_po_lookup"
            server: "erp-mcp-server"
        negotiation_group: "three-way-match"
        output_field: "fuzzy_match"

    - id: variance-policy-agent
      name: "Variance Policy Agent"
      type: negotiation_agent
      position: { x: 380, y: 560 }
      settings:
        role: "Variance Policy / Tolerances"
        system_prompt: |
          Apply tolerance rules to qty/price/tax variances.
          Decide what is auto-approvable and what needs approval.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "policy_tolerance_lookup"
            server: "policy-management-mcp-server"
          - name: "variance_calculator"
            server: "ap-matching-mcp-server"
        negotiation_group: "three-way-match"
        output_field: "variance_policy"

    - id: receipt-coverage-agent
      name: "Receipt Coverage Agent"
      type: negotiation_agent
      position: { x: 540, y: 560 }
      settings:
        role: "Receipt / Service Entry Coverage"
        system_prompt: |
          Verify goods receipts / service entry cover the invoiced quantities.
          Identify partial receipts and backorders.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "receipt_lookup"
            server: "erp-mcp-server"
        negotiation_group: "three-way-match"
        output_field: "receipt_coverage"

    - id: match-moderator
      name: "Match Moderator"
      type: negotiation_moderator
      position: { x: 250, y: 720 }
      settings:
        role: "3-Way Match Moderator"
        system_prompt: |
          Moderate matching strategies and produce:
          - match_result: selected PO + line mapping
          - variance_analysis: computed variances + tolerance outcomes
          - decision: approve | hold | escalate
          Use only evidence from tools/agents.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        max_negotiation_rounds: 5
        consensus_threshold: 0.75
        participants:
          - exact-match-agent
          - fuzzy-match-agent
          - variance-policy-agent
          - receipt-coverage-agent
        input_field: "invoice_struct"
        output_field: "three_way_result"

  executors_after:
    - id: conditional-router-1
      name: "Route by Match Decision"
      type: conditional_router
      position: { x: 250, y: 860 }
      settings:
        routes: |
          [
            {"name": "approve", "condition": "three_way_result.decision == 'approve'"},
            {"name": "hold", "condition": "three_way_result.decision == 'hold'"},
            {"name": "escalate", "condition": "three_way_result.decision == 'escalate'"}
          ]
        default_route: "escalate"

    - id: blob-output-1
      name: "Archive 3-Way Match Result"
      type: azure_blob_output
      position: { x: 250, y: 1010 }
      settings:
        output_container_name: "three-way-match-results"

  edges:
    - from: blob-discovery-1
      to: blob-retrieval-1
      type: sequential
    - from: blob-retrieval-1
      to: doc-intelligence-1
      type: sequential
    - from: doc-intelligence-1
      to: invoice-structurer-agent
      type: agent_handoff
    - from: invoice-structurer-agent
      to: match-moderator
      type: negotiation_initiation
    - from: match-moderator
      to: conditional-router-1
      type: sequential
    - from: conditional-router-1
      to: blob-output-1
      type: sequential
```

---

## Template 10: Invoice Fraud & Anomaly Detection with Swarm + Convergence

**Description**: Fraud detection is multi-signal. Swarm agents independently scan for different indicators; a convergence agent produces a risk score and explainable signals.

**Use Cases**:
- Duplicate invoice attempts / near duplicates
- “Threshold gaming” (amounts just under approval limits)
- Suspicious bank account changes
- Vendor category mismatch
- Unusual payment terms / rush requests

**Swarm Agents**:
- Duplicate/Similarity Agent (hashing + fuzzy)
- Threshold-Gaming Agent (policy boundary checks)
- Bank-Change Agent (vendor master diff)
- Amount/Pattern Agent (historical distributions)
- Content Anomaly Agent (unusual language, urgency)

**Convergence Output**:
- `risk_score` (0..1)
- `signals[]` with weights and evidence
- `recommended_route` (low/medium/high risk)

**Pipeline YAML (sketch)**:
```yaml
pipeline:
  name: "Invoice Fraud & Anomaly Detection (Swarm + Convergence)"
  description: "Parallel swarm detectors generate signals; convergence agent produces risk score and routing"

  executors:
    - id: blob-discovery-1
      name: "Discover Invoices"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      settings:
        file_extensions: ".pdf"
        blob_container_name: "invoices"

    - id: blob-retrieval-1
      name: "Retrieve Invoice"
      type: azure_blob_content_retriever
      position: { x: 250, y: 150 }
      settings:
        use_temp_file_for_content: true

    - id: doc-intelligence-1
      name: "OCR + Layout"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 250 }
      settings:
        model_id: "prebuilt-layout"
        output_format: "markdown"
        output_field: "ocr_result"
        extract_tables: true

  agents:
    - id: invoice-facts-agent
      name: "Invoice Facts Extractor"
      type: ai_agent
      position: { x: 250, y: 360 }
      settings:
        role: "Invoice Facts Extractor"
        system_prompt: |
          Extract stable identifying fields to support fraud checks:
          vendor_name/vendor_id (if known), invoice_number, invoice_date,
          totals (subtotal/tax/total), currency, bank details if present.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "number_extractor"
            server: "document-analysis-mcp-server"
          - name: "date_parser"
            server: "date-processing-mcp-server"
        input_field: "ocr_result"
        output_field: "invoice_facts"

    - id: duplicate-similarity-agent
      name: "Duplicate/Similarity Agent"
      type: swarm_agent
      position: { x: 60, y: 520 }
      settings:
        role: "Duplicate Detection"
        system_prompt: |
          Look for duplicates / near duplicates using invoice_number/vendor/amount/date.
          Return signal with evidence and confidence.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "duplicate_search"
            server: "ap-history-mcp-server"
          - name: "similarity_matcher"
            server: "pattern-analysis-mcp-server"
        swarm_behavior: "independent"
        input_field: "invoice_facts"
        output_field: "signal_duplicate"

    - id: threshold-gaming-agent
      name: "Threshold Gaming Agent"
      type: swarm_agent
      position: { x: 220, y: 520 }
      settings:
        role: "Approval Threshold Gaming"
        system_prompt: |
          Detect if amounts are suspiciously near approval thresholds.
          Return signal with threshold context.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "approval_policy_lookup"
            server: "policy-management-mcp-server"
        swarm_behavior: "independent"
        input_field: "invoice_facts"
        output_field: "signal_threshold"

    - id: bank-change-agent
      name: "Bank Change Agent"
      type: swarm_agent
      position: { x: 380, y: 520 }
      settings:
        role: "Vendor Bank Change Risk"
        system_prompt: |
          Compare bank/payment instructions in invoice vs vendor master.
          Flag changes requiring verification.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "vendor_master_lookup"
            server: "erp-mcp-server"
          - name: "bank_details_diff"
            server: "risk-analysis-mcp-server"
        swarm_behavior: "independent"
        input_field: "invoice_facts"
        output_field: "signal_bank_change"

    - id: historical-pattern-agent
      name: "Amount/Pattern Agent"
      type: swarm_agent
      position: { x: 540, y: 520 }
      settings:
        role: "Historical Spend Pattern"
        system_prompt: |
          Compare invoice amount and timing to vendor history.
          Flag unusual spikes, frequency changes, or outliers.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "vendor_history_lookup"
            server: "ap-history-mcp-server"
          - name: "anomaly_detector"
            server: "statistical-analysis-mcp-server"
        swarm_behavior: "independent"
        input_field: "invoice_facts"
        output_field: "signal_pattern"

    - id: convergence-agent
      name: "Fraud Signal Convergence"
      type: convergence_agent
      position: { x: 250, y: 700 }
      settings:
        role: "Fraud Risk Synthesizer"
        system_prompt: |
          Combine fraud/anomaly signals into:
          - risk_score (0..1)
          - signals[] with weights and evidence
          - recommended_route: low_risk | medium_risk | high_risk
          Be conservative: if evidence is weak, lower confidence.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        mcp_tools_enabled: true
        mcp_tools:
          - name: "risk_scorer"
            server: "risk-analysis-mcp-server"
        swarm_inputs:
          - signal_duplicate
          - signal_threshold
          - signal_bank_change
          - signal_pattern
        output_field: "fraud_result"

  executors_after:
    - id: conditional-router-1
      name: "Route by Fraud Risk"
      type: conditional_router
      position: { x: 250, y: 860 }
      settings:
        routes: |
          [
            {"name": "low_risk", "condition": "fraud_result.recommended_route == 'low_risk'"},
            {"name": "medium_risk", "condition": "fraud_result.recommended_route == 'medium_risk'"},
            {"name": "high_risk", "condition": "fraud_result.recommended_route == 'high_risk'"}
          ]
        default_route: "medium_risk"

    - id: blob-output-1
      name: "Archive Fraud Result"
      type: azure_blob_output
      position: { x: 250, y: 1010 }
      settings:
        output_container_name: "invoice-fraud-results"

  edges:
    - from: blob-discovery-1
      to: blob-retrieval-1
      type: sequential
    - from: blob-retrieval-1
      to: doc-intelligence-1
      type: sequential
    - from: doc-intelligence-1
      to: invoice-facts-agent
      type: agent_handoff
    - from: invoice-facts-agent
      to: [duplicate-similarity-agent, threshold-gaming-agent, bank-change-agent, historical-pattern-agent]
      type: swarm_deployment
    - from: [duplicate-similarity-agent, threshold-gaming-agent, bank-change-agent, historical-pattern-agent]
      to: convergence-agent
      type: swarm_convergence
    - from: convergence-agent
      to: conditional-router-1
      type: sequential
    - from: conditional-router-1
      to: blob-output-1
      type: sequential
```

---

## Template 11: Invoice Line-Item GL Coding & Cost Center Allocation (Hierarchical Teams)

**Description**: Line-item allocation is high-volume and benefits from a lead coordinator + specialized sub-agents (IT spend vs travel vs facilities). Hierarchical coordination increases consistency and reduces hallucinated coding.

**Use Cases**:
- Automated GL coding and cost center allocation
- Multi-project splitting rules
- Department-specific policy enforcement
- Allocation completeness checks before posting

**Agent Architecture**:
```
Allocation Lead Agent
├── Category Router Agent (classifies line items)
├── IT Spend Coding Agent
├── Travel & Expense Coding Agent
├── Facilities Coding Agent
└── Allocation Validator Agent
```

**Key MCP Tools**:
- `gl_account_rules_lookup` (policy/rules)
- `cost_center_rules_lookup`
- `project_code_lookup`
- `budget_checker`
- `allocation_sum_checker`

**Outputs**:
- per-line `gl_code`, `cost_center`, `project_code`, `split_allocations[]`
- `allocation_validation` (complete/incomplete + errors)

**Pipeline YAML (sketch)**:
```yaml
pipeline:
  name: "Invoice Line-Item GL Coding & Cost Center Allocation (Hierarchical)"
  description: "Lead agent coordinates category-specific coders; outputs validated allocations"

  executors:
    - id: blob-discovery-1
      name: "Discover Invoices"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      settings:
        file_extensions: ".pdf"
        blob_container_name: "invoices"

    - id: blob-retrieval-1
      name: "Retrieve Invoice"
      type: azure_blob_content_retriever
      position: { x: 250, y: 150 }
      settings:
        use_temp_file_for_content: true

    - id: doc-intelligence-1
      name: "OCR + Layout"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 250 }
      settings:
        model_id: "prebuilt-layout"
        output_format: "markdown"
        output_field: "ocr_result"
        extract_tables: true

  agents:
    - id: line-item-structurer
      name: "Line Item Structurer"
      type: ai_agent
      position: { x: 250, y: 360 }
      settings:
        role: "Line Item Structuring"
        system_prompt: |
          Extract line items into structured JSON:
          line_items[] with description, qty, unit_price, amount, tax_code (if present).
          Also extract invoice_total and vendor_name.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "table_parser"
            server: "document-analysis-mcp-server"
        input_field: "ocr_result"
        output_field: "invoice_lines"
        handoff_to: "allocation-lead-agent"

    - id: allocation-lead-agent
      name: "Allocation Lead Agent"
      type: hierarchical_coordinator
      position: { x: 250, y: 520 }
      settings:
        role: "Allocation Coordinator"
        system_prompt: |
          Coordinate GL/cost-center allocation for each line item.
          - First classify each line item into a spend category.
          - Delegate to category-specific coders.
          - Ensure outputs include evidence (rule hit, lookup result).
          - Produce final allocations and run completeness checks.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o"
        temperature: 0.1
        mcp_tools_enabled: true
        mcp_tools:
          - name: "team_coordinator"
            server: "orchestration-mcp-server"
        sub_teams:
          - coding-team
          - validation-team
        input_field: "invoice_lines"
        output_field: "allocation_result"

    - id: category-router-agent
      name: "Category Router Agent"
      type: ai_agent
      position: { x: 80, y: 700 }
      settings:
        role: "Spend Category Router"
        system_prompt: |
          Classify each line item into a spend category:
          it, travel, facilities, professional_services, subscriptions, other.
          Output category per line_item index.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        team: "coding-team"

    - id: it-coding-agent
      name: "IT Spend Coding Agent"
      type: ai_agent
      position: { x: 240, y: 700 }
      settings:
        role: "IT Spend Coder"
        system_prompt: |
          Assign GL and cost center for IT-related line items.
          Use rules/lookup tools; return gl_code, cost_center, and evidence.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "gl_account_rules_lookup"
            server: "policy-management-mcp-server"
          - name: "cost_center_rules_lookup"
            server: "policy-management-mcp-server"
        team: "coding-team"

    - id: travel-coding-agent
      name: "Travel & Expense Coding Agent"
      type: ai_agent
      position: { x: 400, y: 700 }
      settings:
        role: "Travel & Expense Coder"
        system_prompt: |
          Assign GL/cost center for travel-related line items.
          Return allocations and evidence.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "gl_account_rules_lookup"
            server: "policy-management-mcp-server"
          - name: "cost_center_rules_lookup"
            server: "policy-management-mcp-server"
        team: "coding-team"

    - id: facilities-coding-agent
      name: "Facilities Coding Agent"
      type: ai_agent
      position: { x: 560, y: 700 }
      settings:
        role: "Facilities Coder"
        system_prompt: |
          Assign GL/cost center for facilities-related line items.
          Return allocations and evidence.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "gl_account_rules_lookup"
            server: "policy-management-mcp-server"
          - name: "cost_center_rules_lookup"
            server: "policy-management-mcp-server"
        team: "coding-team"

    - id: allocation-validator-agent
      name: "Allocation Validator Agent"
      type: ai_agent
      position: { x: 250, y: 860 }
      settings:
        role: "Allocation Validator"
        system_prompt: |
          Validate allocations:
          - every line has gl_code and cost_center
          - splits sum correctly
          - optional: budget check warnings
          Output allocation_validation with errors/warnings.
        model_endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4o-mini"
        temperature: 0.0
        mcp_tools_enabled: true
        mcp_tools:
          - name: "allocation_sum_checker"
            server: "quality-assurance-mcp-server"
          - name: "budget_checker"
            server: "finance-controls-mcp-server"
        team: "validation-team"

  executors_after:
    - id: conditional-router-1
      name: "Route by Allocation Completeness"
      type: conditional_router
      position: { x: 250, y: 1010 }
      settings:
        routes: |
          [
            {"name": "complete", "condition": "allocation_result.allocation_validation.is_complete == true"},
            {"name": "incomplete", "condition": "allocation_result.allocation_validation.is_complete == false"}
          ]
        default_route: "incomplete"

    - id: blob-output-1
      name: "Archive Allocations"
      type: azure_blob_output
      position: { x: 250, y: 1160 }
      settings:
        output_container_name: "invoice-allocations"

  edges:
    - from: blob-discovery-1
      to: blob-retrieval-1
      type: sequential
    - from: blob-retrieval-1
      to: doc-intelligence-1
      type: sequential
    - from: doc-intelligence-1
      to: line-item-structurer
      type: agent_handoff
    - from: line-item-structurer
      to: allocation-lead-agent
      type: hierarchical_coordination
    - from: allocation-lead-agent
      to: conditional-router-1
      type: sequential
    - from: conditional-router-1
      to: blob-output-1
      type: sequential
```

---

## MCP Tool Integration Guide

### Common MCP Tool Categories

**1. Document Analysis Tools**
- `pdf_analyzer`: Analyze PDF structure, quality, page count
- `layout_analyzer`: Detect document layout and structure
- `table_parser`: Extract tables from documents
- `image_analyzer`: Analyze images and photos

**2. Data Extraction Tools**
- `number_extractor`: Extract numerical values with precision
- `date_parser`: Parse and normalize dates
- `entity_extractor`: Extract named entities (NER)
- `field_identifier`: Identify form fields and labels

**3. Validation & Verification Tools**
- `policy_validator`: Validate against policies
- `regulatory_validator`: Check regulatory compliance
- `data_validator`: Validate data types and formats
- `confidence_checker`: Evaluate extraction confidence

**4. Domain-Specific Tools**
- `icd_code_mapper`: Map diagnoses to ICD codes
- `cpt_code_mapper`: Map procedures to CPT codes
- `legal_taxonomy_lookup`: Legal classification
- `financial_ratio_calculator`: Calculate financial ratios

**5. Database & API Tools**
- `database_query`: Query databases
- `api_caller`: Call external APIs
- `cache_manager`: Manage cached data
- `lookup_service`: Reference data lookups

**6. Collaboration Tools**
- `conversation_manager`: Manage multi-agent conversations
- `conflict_resolver`: Resolve agent disagreements
- `consensus_builder`: Build consensus among agents
- `team_coordinator`: Coordinate agent teams

**7. Output & Formatting Tools**
- `json_formatter`: Format as JSON
- `summary_generator`: Generate summaries
- `report_builder`: Build formatted reports
- `data_normalizer`: Normalize data to schemas

---

## Implementation Requirements

### New Executor Types Needed

1. **AI Agent Executor**
   - Capabilities: Invoke LLM with system prompts, manage conversations
   - MCP Integration: Call MCP tools during agent execution
   - Settings: Model endpoint, temperature, max tokens, tools list

2. **Group Chat Coordinator Executor**
   - Capabilities: Manage multi-agent group discussions
   - Features: Turn-taking, speaker selection, synthesis
   - Settings: Participants, max rounds, coordination strategy

3. **Hierarchical Coordinator Executor**
   - Capabilities: Manage sub-teams of agents
   - Features: Team assignment, dependency management, quality checks
   - Settings: Sub-teams, coordination rules

4. **Swarm Agent Executor**
   - Capabilities: Independent parallel agent execution
   - Features: Swarm deployment, convergence
   - Settings: Swarm behavior, convergence strategy

5. **Negotiation Agent Executor**
   - Capabilities: Iterative negotiation and consensus building
   - Features: Round-robin discussion, voting, conflict resolution
   - Settings: Max rounds, consensus threshold

6. **Convergence Agent Executor**
   - Capabilities: Synthesize multiple agent outputs
   - Features: Aggregation, conflict resolution, summary generation
   - Settings: Synthesis strategy, conflict handling

7. **Routing Agent Executor**
   - Capabilities: Dynamic agent selection and routing
   - Features: Conditional routing, capability matching
   - Settings: Routing rules, agent registry

8. **Specialist Agent Executor**
   - Capabilities: Domain-specific data extraction
   - Features: Conditional activation, team membership
   - Settings: Activation conditions, specialist domain

---

## Additional Financial Document Templates (Agent Collaboration Patterns)

### Template F1: Bank Statement Reconciliation (Swarm + Convergence)
**Best-fit pattern**: Swarm (parallel specialists) + Convergence (single reconciled output)

**Description**: Extract statement transactions and produce an evidence-backed reconciliation report by running multiple specialist agents in parallel (swarm) and synthesizing their outputs into a single convergence decision.

**Use Cases**:
- Month-end bank reconciliation
- Treasury monitoring of fees and unusual cash movements
- Audit support (exception evidence and traceability)
- Rapid triage of statement anomalies (duplicates, reversals, spikes)

**Agent Architecture**:
```
Swarm Specialists (parallel)
├── Transaction Extractor Agent
├── Matching Strategy Agent
└── Anomaly Detector Agent
        │
        ▼
Convergence Coordinator Agent
```

**Pipeline Steps**:

1. **Azure Blob Input Discovery** - Discover bank statement PDFs
2. **Azure Blob Content Retriever** - Retrieve statement bytes
3. **Azure Document Intelligence Extractor** - OCR + layout/table extraction
4. **Field Mapper** - Normalize extracted text to `text`
5. **Swarm Specialists (parallel)**
   - **Transaction Extractor**: Build normalized `transactions[]` (date/description/amount/balance)
   - **Matching Strategy**: Propose matching rules (date window, amount tolerance, description normalization)
   - **Anomaly Detector**: Flag duplicates/outliers/fee patterns with evidence
6. **Fan-In Aggregator** - Merge specialist outputs
7. **Convergence Coordinator** - Produce `reconciliation_report` (exceptions + recommended actions + confidence)
8. **Azure Blob Output** - Save results

**Suggested MCP Tools** (optional, per agent):
- `table_parser`, `number_extractor`, `date_parser`
- `anomaly_detector`, `similarity_matcher`
- `json_formatter`, `report_builder`

**Outputs**:
- `transactions[]`
- `exceptions[]` (each with `evidence_snippet`)
- `reconciliation_report` (summary + next steps)
- `confidence`

**Pipeline YAML (sketch)**:
```yaml
pipeline:
  name: "Bank Statement Reconciliation (Agent Swarm + Convergence)"
  description: "Parallel specialists extract transactions and anomalies; convergence outputs a reconciliation report"

  executors:
    - id: blob-discovery-1
      name: "Discover Bank Statements"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      description: "Discover bank statement PDFs"
      settings:
        file_extensions: ".pdf"
        blob_container_name: "bank-statements"
        max_results: 25

    - id: blob-content-retrieval-1
      name: "Retrieve Statements"
      type: azure_blob_content_retriever
      position: { x: 250, y: 180 }
      description: "Retrieve statement content"
      settings:
        use_temp_file_for_content: true

    - id: doc-intel-1
      name: "OCR + Layout"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 320 }
      description: "Extract statement text and tables"
      settings:
        model_id: "prebuilt-layout"
        output_format: "markdown"

    - id: field-mapper-1
      name: "Normalize Input"
      type: field_mapper
      position: { x: 250, y: 460 }
      description: "Map extracted text to the default agent input field"
      settings:
        mappings: |-
          {
            "doc_intell_output.text": "text"
          }

    - id: agent-transaction-extractor
      name: "Agent: Transaction Extractor"
      type: azure_openai_agent
      position: { x: 60, y: 620 }
      description: "Extract normalized transaction list"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "transactions"
        temperature: 0.0
        instructions: |-
          Extract a normalized JSON transaction list from the bank statement.
          Output {account_id, statement_period, transactions[]}.
          Each transaction: {date, description, amount, direction, balance}.

    - id: agent-matching-strategy
      name: "Agent: Matching Strategy"
      type: azure_openai_agent
      position: { x: 250, y: 620 }
      description: "Propose reconciliation match rules"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "match_hypotheses"
        temperature: 0.1
        instructions: |-
          Propose evidence-based reconciliation rules and exception triggers.
          Do not fabricate ledger entries.

    - id: agent-anomaly-detector
      name: "Agent: Anomaly Detector"
      type: azure_openai_agent
      position: { x: 440, y: 620 }
      description: "Detect suspicious or unusual patterns"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "anomalies"
        temperature: 0.0
        instructions: |-
          Identify anomalies (duplicates, unusual fees, spikes, reversals).
          Output anomalies[] with evidence_snippet and severity.

    - id: fan-in-1
      name: "Aggregate Agent Outputs"
      type: fan_in_aggregator
      position: { x: 250, y: 790 }
      description: "Merge outputs from parallel agent branches"

    - id: agent-convergence
      name: "Agent: Convergence Coordinator"
      type: azure_openai_agent
      position: { x: 250, y: 920 }
      description: "Combine signals into a single reconciliation report"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1"
        input_field: "text"
        output_field: "reconciliation_report"
        temperature: 0.1
        instructions: |-
          Produce a reconciliation report JSON using transactions, match_hypotheses, anomalies.
          Output {summary, exceptions[], recommended_next_steps[], confidence}.

    - id: blob-output-1
      name: "Save Reconciliation"
      type: azure_blob_output
      position: { x: 250, y: 1080 }
      description: "Save reconciliation artifacts"

  edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: blob-content-retrieval-1
      to: doc-intel-1
      type: sequential
    - from: doc-intel-1
      to: field-mapper-1
      type: sequential
    - from: field-mapper-1
      to: [agent-transaction-extractor, agent-matching-strategy, agent-anomaly-detector]
      type: parallel
    - from: [agent-transaction-extractor, agent-matching-strategy, agent-anomaly-detector]
      to: fan-in-1
      type: join
      wait_strategy: all
    - from: fan-in-1
      to: agent-convergence
      type: sequential
    - from: agent-convergence
      to: blob-output-1
      type: sequential
```

---

### Template F2: Trade Confirmation / Term Sheet Normalization (Specialists + Coordinator)
**Best-fit pattern**: Group-chat style specialization (parallel extraction) + coordinator conflict resolution

**Description**: Normalize trade confirmations/term sheets into a canonical JSON record by splitting extraction into specialist roles and using a coordinator agent to resolve conflicts.

**Use Cases**:
- Capital markets operations (normalize confirmations into downstream systems)
- Risk reporting (extract product, notional, dates, pay/receive)
- Compliance record-keeping (evidence-backed trade terms)
- Data engineering (PDF → canonical schema)

**Agent Architecture**:
```
Specialists (parallel)
├── Product Classifier Agent
├── Economic Terms Extractor Agent
├── Counterparty Extractor Agent
└── Settlement Extractor Agent
        │
        ▼
Normalization Coordinator Agent
```

**Pipeline Steps**:

1. **Azure Blob Input Discovery** - Discover trade confirmations (PDF)
2. **Azure Blob Content Retriever** - Retrieve bytes
3. **Azure Document Intelligence Extractor** - OCR + tables
4. **Field Mapper** - Normalize extracted content to `text`
5. **Specialist Agents (parallel)** - Extract: product class, economics, counterparties, settlement
6. **Fan-In Aggregator** - Merge specialist outputs
7. **Normalization Coordinator** - Output one `normalized_trade` JSON + `conflicts[]`
8. **Azure Blob Output** - Save normalized trade record

**Suggested MCP Tools** (optional, per agent):
- `table_parser`, `number_extractor`, `date_parser`
- `entity_extractor` (counterparties)
- `json_formatter`, `data_normalizer`

**Outputs**:
- `normalized_trade`
- `conflicts[]` (what disagreed + chosen resolution)
- `confidence`

**Pipeline YAML (sketch)**:
```yaml
pipeline:
  name: "Trade Confirmation Normalization (Specialists + Coordinator)"
  description: "Specialists extract trade facets; coordinator resolves conflicts into canonical JSON"

  executors:
    - id: blob-discovery-1
      name: "Discover Trade Confirmations"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      description: "Discover confirmation PDFs"
      settings:
        file_extensions: ".pdf"
        blob_container_name: "trade-confirmations"
        max_results: 25

    - id: blob-content-retrieval-1
      name: "Retrieve Confirmations"
      type: azure_blob_content_retriever
      position: { x: 250, y: 180 }
      description: "Retrieve confirmation content"
      settings:
        use_temp_file_for_content: true

    - id: doc-intel-1
      name: "OCR + Layout"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 320 }
      description: "Extract confirmation text and tables"
      settings:
        model_id: "prebuilt-layout"
        output_format: "markdown"

    - id: field-mapper-1
      name: "Normalize Input"
      type: field_mapper
      position: { x: 250, y: 460 }
      description: "Map extracted text to agent input"
      settings:
        mappings: |-
          {
            "doc_intell_output.text": "text"
          }

    - id: agent-product-classifier
      name: "Agent: Product Classifier"
      type: azure_openai_agent
      position: { x: 60, y: 620 }
      description: "Classify product type and trade family"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "product_classification"
        temperature: 0.0
        instructions: |-
          Classify product type (e.g., FX Forward, IRS, CDS, Equity Option, Repo).
          Output {product_type, asset_class, confidence}.

    - id: agent-economic-terms
      name: "Agent: Economic Terms"
      type: azure_openai_agent
      position: { x: 250, y: 620 }
      description: "Extract notional, rates, dates, and key economics"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1"
        input_field: "text"
        output_field: "economic_terms"
        temperature: 0.0
        instructions: |-
          Extract economic terms into JSON: notional, currency, trade_date, effective_date, maturity_date,
          fixed_rate / float_index / spread as applicable.

    - id: agent-counterparty
      name: "Agent: Counterparty"
      type: azure_openai_agent
      position: { x: 440, y: 620 }
      description: "Extract party identifiers"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "counterparty_details"
        temperature: 0.0
        instructions: |-
          Extract parties, identifiers (LEI if present), and any relevant references.
          Output parties[] with evidence_snippet.

    - id: agent-settlement
      name: "Agent: Settlement"
      type: azure_openai_agent
      position: { x: 630, y: 620 }
      description: "Extract settlement/payment instructions"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "settlement_terms"
        temperature: 0.0
        instructions: |-
          Extract settlement terms: pay/receive, settlement_date, settlement_currency,
          and payment instructions if present.

    - id: fan-in-1
      name: "Aggregate Specialist Outputs"
      type: fan_in_aggregator
      position: { x: 250, y: 790 }
      description: "Merge outputs from specialist agents"

    - id: agent-coordinator
      name: "Agent: Normalization Coordinator"
      type: azure_openai_agent
      position: { x: 250, y: 920 }
      description: "Resolve conflicts and output canonical trade JSON"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1"
        input_field: "text"
        output_field: "normalized_trade"
        temperature: 0.1
        instructions: |-
          Combine product_classification, economic_terms, counterparty_details, settlement_terms.
          Resolve conflicts and output {normalized_trade, conflicts[], confidence}.

    - id: blob-output-1
      name: "Save Normalized Trade"
      type: azure_blob_output
      position: { x: 250, y: 1080 }
      description: "Save normalized trade JSON"

  edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: blob-content-retrieval-1
      to: doc-intel-1
      type: sequential
    - from: doc-intel-1
      to: field-mapper-1
      type: sequential
    - from: field-mapper-1
      to: [agent-product-classifier, agent-economic-terms, agent-counterparty, agent-settlement]
      type: parallel
    - from: [agent-product-classifier, agent-economic-terms, agent-counterparty, agent-settlement]
      to: fan-in-1
      type: join
      wait_strategy: all
    - from: fan-in-1
      to: agent-coordinator
      type: sequential
    - from: agent-coordinator
      to: blob-output-1
      type: sequential
```

---

### Template F3: Annual Report (10-K/10-Q) KPI + Risk + Footnote Extraction (Hierarchical Teams)
**Best-fit pattern**: Hierarchical coordinator + specialist subteams

**Description**: Analyze long-form annual/quarterly reports by splitting responsibilities across specialist agents (KPIs, segments, cash flow, non-GAAP adjustments, accounting policies/estimates, risks, legal contingencies, ESG, and outlook) under a lead coordinator that produces a single evidence-backed executive brief.

**Use Cases**:
- Equity research KPI extraction and summarization
- Compliance monitoring of risk disclosures
- Corporate strategy competitive benchmarking
- Knowledge management (turn narrative reports into structured datasets)

**Agent Architecture**:
```
Lead Coordinator Agent
├── KPI Extractor Agent
├── Segment & Geography Extractor Agent
├── Cash Flow & Liquidity Agent
├── Capital Allocation Agent
├── Non-GAAP & Adjustments Agent
├── Risk Factors Analyst Agent
├── Footnotes/Accounting Policies Agent
├── Critical Accounting Estimates & Changes Agent
├── Legal / Commitments / Contingencies Agent
├── ESG / Sustainability Agent (optional)
└── Guidance / Outlook Agent
        │
        ▼
Executive Brief Agent
```

**Pipeline Steps**:

1. **Azure Blob Input Discovery** - Discover 10-K / 10-Q PDFs
2. **Azure Blob Content Retriever** - Retrieve bytes
3. **Azure Content Understanding Extractor** - Long-doc extraction to markdown
4. **Field Mapper** - Normalize markdown to `text`
5. **Specialist Agents (parallel)** - Extract complementary facets (each returns structured JSON + evidence snippets)
  - **KPI Extractor Agent**: Standardized KPIs with period normalization
  - **Segment & Geography Extractor Agent**: Segment reporting, geo mix, customer concentration
  - **Cash Flow & Liquidity Agent**: OCF, capex, free cash flow, liquidity sources/uses, debt maturities
  - **Capital Allocation Agent**: Dividends, buybacks, M&A, debt paydown/issuance, stated priorities
  - **Non-GAAP & Adjustments Agent**: Non-GAAP measures, key adjustments, reconciliation cues
  - **Risk Factors Analyst Agent**: Material risks, changes vs prior period, ranked by materiality
  - **Footnotes/Accounting Policies Agent**: Critical footnotes and significant accounting policies
  - **Critical Accounting Estimates & Changes Agent**: Estimates (impairment, revenue recognition, reserves), policy changes
  - **Legal / Commitments / Contingencies Agent**: Litigation, regulatory matters, commitments, contingencies
  - **ESG / Sustainability Agent (optional)**: Climate/human-capital disclosures when present
  - **Guidance / Outlook Agent**: Forward-looking guidance, strategic initiatives, key watch items
6. **Fan-In Aggregator** - Merge specialist findings
7. **Lead Coordinator / Executive Brief Agent** - Produce highlights/concerns/open questions + confidence (with cited evidence snippets)
8. **Azure Blob Output** - Save structured results

**Suggested MCP Tools** (optional):
- `financial_ratio_calculator` (ratios from KPIs)
- `table_parser`, `number_extractor`, `date_parser`
- `entity_extractor` (segments, counterparties, geographies)
- `sentiment_analyzer`, `forward_looking_extractor` (outlook)
- `summary_generator`, `report_builder`, `json_formatter`

**Outputs**:
- `kpis` (structured)
- `segments_geography` (structured)
- `cash_flow_liquidity` (structured)
- `capital_allocation` (structured)
- `non_gaap_adjustments` (structured)
- `risk_factors[]`
- `footnotes[]`
- `accounting_estimates_changes[]`
- `legal_commitments_contingencies[]`
- `esg_disclosures[]` (optional)
- `guidance_outlook` (structured)
- `executive_brief`

**Coordinator synthesis rubric (Lead Coordinator / Executive Brief Agent)**:
- **Source precedence (tie-breaker)**: Financial statements/tables → Footnotes → MD&A narrative → Risk factors → ESG/other narrative.
- **No invention rule**: Never infer missing numbers; if a value is not explicitly present, set it to `null` and add a `missing_data[]` item describing what’s missing.
- **Evidence-first outputs**: Every extracted claim should include an `evidence_snippet` (and optional `section_hint`, e.g., “Item 7 MD&A”, “Note 12”).
- **Period alignment**: Normalize all metrics to a canonical `period` key (FY, Q4, YoY) and explicitly label units (USD, millions, per-share).
- **Numeric consistency checks**: If KPIs conflict across sections, prefer audited statements/footnotes; if still ambiguous, surface a `conflicts[]` entry and avoid choosing a number.
- **Non-GAAP handling**: Keep GAAP and non-GAAP separate; for each non-GAAP measure capture the stated reconciliation cues/adjustments and any management caveats.
- **Risk ranking rules**: Rank risk factors by (1) explicit “material” language, (2) quantified exposure, (3) novelty/change vs prior period, (4) recurrence.
- **Liquidity flags**: Escalate to `concerns[]` if the text mentions going-concern language, covenant pressure, near-term maturities, or constrained revolver capacity.
- **Confidence scoring**: Provide `confidence` per output domain (0..1) based on evidence density, consistency, and extraction clarity; the overall confidence is the minimum of critical domains (KPIs, liquidity, risks).
- **Deduplication**: Merge repeated disclosures; keep the strongest evidence snippet and list `supporting_snippets[]` when helpful.

**Pipeline YAML (sketch)**:
```yaml
pipeline:
  name: "Annual Report KPI + Risk Extraction (Agent Teams)"
  description: "Long-doc extraction + specialist agents + executive brief synthesis"

  executors:
    - id: blob-discovery-1
      name: "Discover Annual Reports"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      description: "Discover annual/quarterly report PDFs"
      settings:
        file_extensions: ".pdf"
        blob_container_name: "annual-reports"
        max_results: 10

    - id: blob-content-retrieval-1
      name: "Retrieve Reports"
      type: azure_blob_content_retriever
      position: { x: 250, y: 180 }
      description: "Retrieve report content"
      settings:
        use_temp_file_for_content: true

    - id: pdf_extractor-1
      name: PDF Extractor
      type: pdf_extractor
      position: { x: 250, y: 320 }
      description: Extracts text, pages, and images from PDF documents using PyMuPDF
      settings:
        enabled: true
        condition: ''
        fail_pipeline_on_error: true
        debug_mode: false
        content_field: ''
        temp_file_path_field: temp_file_path
        output_field: pdf_output
        max_concurrent: 3
        continue_on_error: true
        extract_text: true
        extract_pages: true
        extract_images: false
        image_format: png
        image_output_mode: base64
        min_image_size: 100
        page_separator: |+


          ---

    - id: field-mapper-1
      name: "Normalize Input"
      type: field_mapper
      position: { x: 250, y: 460 }
      description: "Map markdown to agent input"
      settings:
        mappings: |-
          {
            "content_understanding_result.result.contents.markdown": "text"
          }
        join_separator: "\n\n---\n\n"

    - id: agent-kpi
      name: "Agent: KPI Extractor"
      type: azure_openai_agent
      position: { x: 250, y: 620 }
      description: "Extract KPIs and periods"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1"
        input_field: "text"
        output_field: "kpis"
        temperature: 0.0
        max_tokens: 4000
        instructions: |-
          Extract normalized KPIs with period alignment into JSON.
          Output {company_name, period, kpis:{...}, evidence_snippets[]}.

    - id: agent-segments
      name: "Agent: Segments & Geography"
      type: azure_openai_agent
      position: { x: 500, y: 620 }
      description: "Extract segment reporting and geographic mix"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "segments_geography"
        temperature: 0.0
        max_tokens: 4000
        instructions: |-
          Extract segment and geographic disclosures into JSON.
          Output {segments:[{name, metrics:{revenue, operating_income, growth}, notes, evidence_snippet}],
          geographies:[{region, revenue, growth, evidence_snippet}], customer_concentration:{top_customers?, evidence_snippet?}}.

    - id: agent-cashflow
      name: "Agent: Cash Flow & Liquidity"
      type: azure_openai_agent
      position: { x: 250, y: 720 }
      description: "Extract cash flow, liquidity, and debt maturity highlights"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "cash_flow_liquidity"
        temperature: 0.0
        max_tokens: 4000
        instructions: |-
          Extract cash flow and liquidity facts into JSON.
          Output {period, operating_cash_flow, capex, free_cash_flow?, working_capital_notes?,
          liquidity:{cash, revolver?, covenants?, debt_maturities?, evidence_snippets[]}}.

    - id: agent-capalloc
      name: "Agent: Capital Allocation"
      type: azure_openai_agent
      position: { x: 500, y: 720 }
      description: "Extract capital allocation actions and stated priorities"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "capital_allocation"
        temperature: 0.0
        max_tokens: 4000
        instructions: |-
          Extract capital allocation details into JSON.
          Output {dividends, buybacks, mna, debt_actions, capex_plans, stated_priorities, evidence_snippets[]}.

    - id: agent-nongaap
      name: "Agent: Non-GAAP & Adjustments"
      type: azure_openai_agent
      position: { x: 250, y: 820 }
      description: "Extract non-GAAP metrics and key adjustments"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "non_gaap_adjustments"
        temperature: 0.0
        max_tokens: 4000
        instructions: |-
          Identify non-GAAP measures and the largest adjustments/reconciliation cues into JSON.
          Output {measures:[{name, value?, period?, adjustments:[{label, amount?, evidence_snippet}], evidence_snippet}], caveats[]}.

    - id: agent-risks
      name: "Agent: Risk Factors"
      type: azure_openai_agent
      position: { x: 100, y: 780 }
      description: "Extract and rank risk factors"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "risk_factors"
        temperature: 0.1
        max_tokens: 4000
        instructions: |-
          Extract risk factors with materiality and evidence_snippet into JSON.
            Output [{risk, materiality_rank, change_vs_prior?, evidence_snippet}].

    - id: agent-footnotes
      name: "Agent: Footnotes"
      type: azure_openai_agent
      position: { x: 400, y: 780 }
      description: "Summarize key footnotes and accounting policies"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "footnotes"
        temperature: 0.1
        max_tokens: 4000
        instructions: |-
          Summarize key policies/footnotes with evidence_snippet into JSON.
          Output [{topic, summary, evidence_snippet}].

    - id: agent-accounting
      name: "Agent: Critical Estimates & Accounting Changes"
      type: azure_openai_agent
      position: { x: 100, y: 900 }
      description: "Extract critical accounting estimates and policy changes"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "accounting_estimates_changes"
        temperature: 0.0
        max_tokens: 4000
        instructions: |-
          Extract critical accounting estimates and accounting policy changes into JSON.
          Output [{topic, why_it_matters, period_impact?, evidence_snippet}].

    - id: agent-legal
      name: "Agent: Legal / Commitments / Contingencies"
      type: azure_openai_agent
      position: { x: 400, y: 900 }
      description: "Extract litigation, regulatory matters, commitments, and contingencies"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "legal_commitments_contingencies"
        temperature: 0.0
        max_tokens: 4000
        instructions: |-
          Extract material legal proceedings, investigations, commitments, and contingencies into JSON.
          Output [{matter, status, potential_impact?, evidence_snippet}].

    - id: agent-esg
      name: "Agent: ESG / Sustainability"
      type: azure_openai_agent
      position: { x: 500, y: 900 }
      description: "Extract ESG and sustainability disclosures when present"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "esg_disclosures"
        temperature: 0.0
        max_tokens: 4000
        instructions: |-
          Extract ESG disclosures only if present (otherwise return []) into JSON.
          Output [{area, metric_or_claim, target?, timeframe?, evidence_snippet}].

    - id: agent-outlook
      name: "Agent: Guidance / Outlook"
      type: azure_openai_agent
      position: { x: 250, y: 900 }
      description: "Extract guidance, outlook, and strategic initiatives"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "guidance_outlook"
        temperature: 0.1
        max_tokens: 4000
        instructions: |-
          Extract forward-looking guidance, key initiatives, and watch items into JSON.
          Output {guidance:[{metric, range_or_target?, period, evidence_snippet}], initiatives[], watch_items[]}.

    - id: fan-in-1
      name: "Aggregate Findings"
      type: fan_in_aggregator
      position: { x: 250, y: 940 }
      description: "Merge KPI + risk + footnote outputs"

    - id: agent-brief
      name: "Agent: Executive Brief"
      type: azure_openai_agent
      position: { x: 250, y: 1080 }
      description: "Synthesize into executive brief"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1"
        input_field: "text"
        output_field: "executive_brief"
        temperature: 0.2
        max_tokens: 8000
        instructions: |-
          Produce a concise brief JSON: highlights, concerns, open_questions, confidence.
          Cite evidence_snippets from merged findings.
          Output {highlights[], concerns[], open_questions[], confidence}.

    - id: blob-output-1
      name: "Save Results"
      type: azure_blob_output
      position: { x: 250, y: 1220 }
      description: "Save extracted KPIs and brief"

  edges:
    edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: field-mapper-1
      to: agent-cashflow
      type: sequential
    - from: agent-brief
      to: blob-output-1
      type: sequential
    - from: blob-content-retrieval-1
      to: pdf_extractor-1
      type: sequential
    - from: pdf_extractor-1
      to: field-mapper-1
      type: sequential
    - from: agent-cashflow
      to: agent-kpi
      type: sequential
    - from: agent-kpi
      to: agent-risks
      type: sequential
    - from: agent-risks
      to: agent-nongaap
      type: sequential
    - from: agent-nongaap
      to: agent-accounting
      type: sequential
    - from: agent-esg
      to: agent-capalloc
      type: sequential
    - from: agent-capalloc
      to: agent-segments
      type: sequential
    - from: agent-segments
      to: agent-footnotes
      type: sequential
    - from: agent-footnotes
      to: agent-legal
      type: sequential
    - from: agent-legal
      to: agent-outlook
      type: sequential
    - from: agent-accounting
      to: agent-esg
      type: sequential
    - from: agent-outlook
      to: agent-brief
      type: sequential
```

---

### Template F4: Loan Agreement Covenant Extraction + Monitoring Checklist (Hand-Off)
**Best-fit pattern**: Hand-off chain (extract → structure → operationalize)

**Description**: Extract covenant obligations and convert them into a monitoring checklist suitable for ongoing compliance tracking.

**Use Cases**:
- Credit risk covenant tracking
- Legal/finance covenant standardization across lenders
- Ongoing reporting cadence management (deadlines, cure periods)
- Audit support with evidence-backed covenant summaries

**Agent Architecture**:
```
Covenant Extractor Agent
        │
        ▼
Monitoring Checklist Builder Agent
```

**Pipeline Steps**:

1. **Azure Blob Input Discovery** - Discover loan agreement PDFs
2. **Azure Blob Content Retriever** - Retrieve bytes
3. **Azure Document Intelligence Extractor** - OCR and layout extraction
4. **Field Mapper** - Normalize extracted text to `text`
5. **Covenant Extractor Agent** - Extract covenants, formulas, thresholds, periods, deadlines
6. **Monitoring Checklist Builder Agent** - Convert covenants into checklist items and escalation conditions
7. **Azure Blob Output** - Save covenant pack

**Suggested MCP Tools** (optional):
- `entity_extractor` (borrower/lender identification)
- `date_parser` (deadline normalization)
- `policy_validator`, `json_formatter`, `report_builder`

**Outputs**:
- `covenants[]` (each with `evidence_snippet`)
- `monitoring_checklist[]` (cadence + required data + alert conditions)

**Pipeline YAML (sketch)**:
```yaml
pipeline:
  name: "Loan Covenant Extraction + Monitoring Checklist (Agent Handoff)"
  description: "Extract covenants and convert them into a monitoring checklist"

  executors:
    - id: blob-discovery-1
      name: "Discover Loan Agreements"
      type: azure_blob_input_discovery
      position: { x: 250, y: 50 }
      description: "Discover loan agreement PDFs"
      settings:
        file_extensions: ".pdf"
        blob_container_name: "loan-agreements"
        max_results: 25

    - id: blob-content-retrieval-1
      name: "Retrieve Agreement"
      type: azure_blob_content_retriever
      position: { x: 250, y: 180 }
      description: "Retrieve agreement content"
      settings:
        use_temp_file_for_content: true

    - id: doc-intel-1
      name: "OCR + Layout"
      type: azure_document_intelligence_extractor
      position: { x: 250, y: 320 }
      description: "Extract agreement text"
      settings:
        model_id: "prebuilt-layout"
        output_format: "markdown"

    - id: field-mapper-1
      name: "Normalize Input"
      type: field_mapper
      position: { x: 250, y: 460 }
      description: "Map extracted text to agent input"
      settings:
        mappings: |-
          {
            "doc_intell_output.text": "text"
          }

    - id: agent-covenants
      name: "Agent: Covenant Extractor"
      type: azure_openai_agent
      position: { x: 250, y: 620 }
      description: "Extract covenants and thresholds"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1"
        input_field: "text"
        output_field: "covenants"
        temperature: 0.0
        instructions: |-
          Extract covenants into JSON: {borrower, lender, covenants[]}.
          Each covenant: {name, type, threshold_or_formula, measurement_period, reporting_deadline, cure_period, evidence_snippet}.

    - id: agent-checklist
      name: "Agent: Monitoring Checklist"
      type: azure_openai_agent
      position: { x: 250, y: 780 }
      description: "Create a monitoring checklist"
      settings:
        endpoint: "https://<foundry-resource>.openai.azure.com/openai/v1/"
        deployment_name: "gpt-4.1-mini"
        input_field: "text"
        output_field: "monitoring_checklist"
        temperature: 0.1
        instructions: |-
          Convert extracted covenants into checklist_items[] with:
          data_requirements, calculation_steps, cadence, alert_conditions, escalation.

    - id: blob-output-1
      name: "Save Covenant Pack"
      type: azure_blob_output
      position: { x: 250, y: 940 }
      description: "Save covenant extraction and checklist"

  edges:
    - from: blob-discovery-1
      to: blob-content-retrieval-1
      type: sequential
    - from: blob-content-retrieval-1
      to: doc-intel-1
      type: sequential
    - from: doc-intel-1
      to: field-mapper-1
      type: sequential
    - from: field-mapper-1
      to: agent-covenants
      type: sequential
    - from: agent-covenants
      to: agent-checklist
      type: sequential
    - from: agent-checklist
      to: blob-output-1
      type: sequential
```

## Best Practices

### Agent Design
- **Single Responsibility**: Each agent should have one clear role
- **Clear Prompts**: Provide detailed system prompts with examples
- **Tool Selection**: Only include relevant MCP tools per agent
- **Temperature Control**: Use low temperature (0.0-0.1) for extraction, higher (0.2-0.3) for analysis

### Collaboration Patterns
- **Hand-Off**: Use for sequential, dependent tasks
- **Group Chat**: Use when agents need to discuss and reach consensus
- **Hierarchical**: Use for complex workflows with sub-tasks
- **Swarm**: Use when tasks can be parallelized independently
- **Negotiation**: Use when multiple perspectives needed for decisions

### MCP Tool Usage
- **Specific Tools**: Select tools specific to agent's role
- **Error Handling**: Handle MCP tool failures gracefully
- **Caching**: Use caching for repeated lookups
- **Rate Limiting**: Respect API rate limits

### Performance
- **Parallel When Possible**: Use swarm/parallel patterns for speed
- **Minimize Rounds**: Limit negotiation/discussion rounds
- **Efficient Prompts**: Keep prompts focused and concise
- **Model Selection**: Use appropriate model sizes (mini vs full)

---

## Next Steps

1. **Implement Core Agent Executors**: Start with AI Agent, Group Chat, and Hand-Off patterns
2. **Build MCP Tool Framework**: Create MCP server infrastructure and tool registry
3. **Prototype Template 1**: Implement Legal Contract Analysis as proof-of-concept
4. **Develop Domain Tools**: Build industry-specific MCP tools (legal, medical, financial)
5. **User Testing**: Validate agent collaboration patterns with real documents
6. **Expand Catalog**: Add more industry-specific templates based on feedback
