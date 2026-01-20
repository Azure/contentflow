"""
Financial Report Generator Executor.

Generates comprehensive financial analysis reports using Azure OpenAI
for narrative generation and structured report formatting.
"""

import logging
import json
from typing import List, Union, Dict, Any, Optional
from enum import Enum

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


class ReportSection(str, Enum):
    """Standard report sections."""
    EXECUTIVE_SUMMARY = "executive_summary"
    FINANCIAL_POSITION = "financial_position"
    RATIO_ANALYSIS = "ratio_analysis"
    TREND_ANALYSIS = "trend_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    PEER_COMPARISON = "peer_comparison"
    RECOMMENDATIONS = "recommendations"


class OutputFormat(str, Enum):
    """Output formats for reports."""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    PDF = "pdf"


class FinancialReportGeneratorExecutor(BaseExecutor):
    """
    Generate comprehensive financial analysis reports using AI.
    
    This executor uses Azure OpenAI to generate professional financial
    analysis reports with customizable sections, visualizations descriptions,
    and actionable recommendations.
    
    Configuration (settings dict):
        - report_sections (list): Sections to include in the report
          Options: "executive_summary", "financial_position", "ratio_analysis",
                   "trend_analysis", "risk_assessment", "peer_comparison", "recommendations"
          Default: All sections
        - include_visualizations (bool): Include chart/visualization descriptions
          Default: True
        - chart_types (list): Types of charts to describe
          Options: "line", "bar", "waterfall", "spider", "pie"
          Default: ["line", "bar"]
        - output_format (str): Output format for the report
          Options: "markdown", "html", "json", "pdf"
          Default: "markdown"
        - report_style (str): Style/tone of the report
          Options: "executive", "technical", "investor", "regulatory"
          Default: "executive"
        - company_name (str): Company name for the report
          Default: "The Company"
        - reporting_period (str): Period covered by the report
          Default: "Current Period"
        - input_field (str): Field containing aggregated financial analysis data
          Default: "aggregated_data"
        - output_field (str): Field name for the generated report
          Default: "financial_report"
        - endpoint (str): Azure OpenAI endpoint URL
        - deployment_name (str): Azure OpenAI model deployment name
    
    Expected Input Data Structure:
        The executor expects aggregated results from previous analysis steps:
        {
            "financial_data": {...},
            "financial_ratios": {...},  # From FinancialRatioCalculatorExecutor
            "credit_risk_score": {...},  # From CreditRiskScorerExecutor
            "fraud_indicators": {...},   # From FraudDetectionAnalyzerExecutor
        }
    
    Output:
        Content with added fields:
        - data[output_field]: Dictionary containing the generated report
        - summary_data["report_generation_status"]: Execution status
    
    Example:
        ```yaml
        - id: report-generator-1
          type: financial_report_generator
          settings:
            report_sections:
              - executive_summary
              - ratio_analysis
              - risk_assessment
              - recommendations
            include_visualizations: true
            output_format: markdown
            report_style: executive
            company_name: "Acme Corporation"
            endpoint: "${AZURE_OPENAI_ENDPOINT}"
            deployment_name: "gpt-4"
        ```
    """
    
    DEFAULT_SECTIONS = [
        ReportSection.EXECUTIVE_SUMMARY.value,
        ReportSection.FINANCIAL_POSITION.value,
        ReportSection.RATIO_ANALYSIS.value,
        ReportSection.RISK_ASSESSMENT.value,
        ReportSection.RECOMMENDATIONS.value,
    ]
    
    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        
        # Report configuration
        self.report_sections = self.get_setting("report_sections", self.DEFAULT_SECTIONS)
        self.include_visualizations = self.get_setting("include_visualizations", True)
        self.chart_types = self.get_setting("chart_types", ["line", "bar"])
        self.output_format = self.get_setting("output_format", "markdown")
        self.report_style = self.get_setting("report_style", "executive")
        self.company_name = self.get_setting("company_name", "The Company")
        self.reporting_period = self.get_setting("reporting_period", "Current Period")
        self.input_field = self.get_setting("input_field", "aggregated_data")
        self.output_field = self.get_setting("output_field", "financial_report")
        
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
        
        # Create specialized agents for different report sections
        self._init_agents()
        
        if self.debug_mode:
            logger.debug(
                f"FinancialReportGeneratorExecutor initialized: "
                f"sections={self.report_sections}, format={self.output_format}"
            )

    def _init_agents(self) -> None:
        """Initialize AI agents for report generation."""
        # Main report generation agent
        report_instructions = f"""
You are an expert financial analyst and report writer. Your role is to generate 
professional financial analysis reports based on provided data and analysis results.

Report Style: {self.report_style}
- executive: High-level summary for C-suite executives, focus on key metrics and strategic implications
- technical: Detailed analysis with methodology explanations for financial professionals
- investor: Investment-focused analysis with emphasis on value and risk
- regulatory: Compliance-focused report with regulatory considerations

Guidelines:
1. Use clear, professional language appropriate for the intended audience
2. Support all claims with specific data points from the provided analysis
3. Highlight key findings prominently
4. Provide actionable insights and recommendations
5. Use appropriate formatting for the output format
6. Be objective and balanced, noting both strengths and concerns

Format your output in {self.output_format} format.
"""
        
        self.report_agent: ChatAgent = self.client.create_agent(
            id=f"{self.id}_report_agent",
            name="FinancialReportWriter",
            instructions=report_instructions,
            temperature=0.4
        )
        
        # Visualization description agent
        if self.include_visualizations:
            viz_instructions = """
You are a data visualization specialist. Given financial data, describe what 
visualizations would best represent the data and what insights they would show.

For each suggested visualization, provide:
1. Chart type and title
2. Axes labels and data series
3. Key insights the visualization would highlight
4. Any notable patterns or trends to call out

Keep descriptions concise but informative.
"""
            self.viz_agent: ChatAgent = self.client.create_agent(
                id=f"{self.id}_viz_agent",
                name="VisualizationDescriber",
                instructions=viz_instructions,
                temperature=0.3
            )

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """Process analysis data and generate financial reports."""
        items_to_process = input if isinstance(input, list) else [input]
        
        for item in items_to_process:
            await self._process_single_content(item)
            
        return input

    async def _process_single_content(self, content: Content) -> None:
        """Process a single content item and generate a financial report."""
        logger.info(f"Generating financial report for content {content.id}")
        
        try:
            # Extract aggregated analysis data
            analysis_data = self.try_extract_nested_field_from_content(
                content=content,
                field_path=self.input_field
            )
            
            # Also look for individual analysis results
            if not analysis_data:
                analysis_data = self._collect_analysis_data(content)
            
            if not analysis_data:
                logger.warning(f"No analysis data found in content {content.id}")
                content.data[self.output_field] = {"error": "No analysis data found"}
                content.summary_data["report_generation_status"] = "failed"
                return
            
            # Generate report
            report = await self._generate_report(analysis_data)
            
            # Store results
            content.data[self.output_field] = report
            content.summary_data["report_generation_status"] = "success"
            content.summary_data["report_sections_generated"] = len(report.get("sections", {}))
            
        except Exception as e:
            logger.error(f"Error generating report for content {content.id}: {e}")
            content.data[self.output_field] = {"error": str(e)}
            content.summary_data["report_generation_status"] = "failed"

    def _collect_analysis_data(self, content: Content) -> Dict[str, Any]:
        """Collect analysis data from various executor outputs."""
        analysis_data = {}
        
        # Look for standard output fields from other executors
        field_mappings = {
            "financial_data": ["financial_data", "mapped_financials", "extracted_data"],
            "financial_ratios": ["financial_ratios"],
            "credit_risk": ["credit_risk_score", "credit_risk"],
            "fraud_analysis": ["fraud_indicators", "fraud_analysis"],
        }
        
        for key, possible_fields in field_mappings.items():
            for field in possible_fields:
                if field in content.data:
                    analysis_data[key] = content.data[field]
                    break
        
        return analysis_data if analysis_data else None

    async def _generate_report(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the complete financial report."""
        report = {
            "metadata": {
                "company_name": self.company_name,
                "reporting_period": self.reporting_period,
                "report_style": self.report_style,
                "output_format": self.output_format,
                "sections_included": self.report_sections,
            },
            "sections": {},
            "visualizations": [],
        }
        
        # Generate each requested section
        for section in self.report_sections:
            section_content = await self._generate_section(section, analysis_data)
            report["sections"][section] = section_content
        
        # Generate visualization descriptions if requested
        if self.include_visualizations:
            report["visualizations"] = await self._generate_visualizations(analysis_data)
        
        # Compile full report
        report["full_report"] = self._compile_full_report(report)
        
        return report

    async def _generate_section(
        self, 
        section: str, 
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content for a specific report section."""
        
        # Prepare section-specific prompt
        section_prompts = {
            ReportSection.EXECUTIVE_SUMMARY.value: self._get_executive_summary_prompt,
            ReportSection.FINANCIAL_POSITION.value: self._get_financial_position_prompt,
            ReportSection.RATIO_ANALYSIS.value: self._get_ratio_analysis_prompt,
            ReportSection.TREND_ANALYSIS.value: self._get_trend_analysis_prompt,
            ReportSection.RISK_ASSESSMENT.value: self._get_risk_assessment_prompt,
            ReportSection.PEER_COMPARISON.value: self._get_peer_comparison_prompt,
            ReportSection.RECOMMENDATIONS.value: self._get_recommendations_prompt,
        }
        
        prompt_func = section_prompts.get(section)
        if not prompt_func:
            return {"error": f"Unknown section: {section}"}
        
        prompt = prompt_func(analysis_data)
        
        try:
            result = await self.report_agent.run(prompt, store=False)
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            return {
                "title": self._get_section_title(section),
                "content": response_text,
                "generated": True,
            }
            
        except Exception as e:
            logger.error(f"Error generating section {section}: {e}")
            return {
                "title": self._get_section_title(section),
                "content": f"Error generating section: {str(e)}",
                "generated": False,
                "error": str(e),
            }

    def _get_section_title(self, section: str) -> str:
        """Get display title for a section."""
        titles = {
            ReportSection.EXECUTIVE_SUMMARY.value: "Executive Summary",
            ReportSection.FINANCIAL_POSITION.value: "Financial Position Overview",
            ReportSection.RATIO_ANALYSIS.value: "Financial Ratio Analysis",
            ReportSection.TREND_ANALYSIS.value: "Historical Trend Analysis",
            ReportSection.RISK_ASSESSMENT.value: "Risk Assessment",
            ReportSection.PEER_COMPARISON.value: "Peer & Industry Comparison",
            ReportSection.RECOMMENDATIONS.value: "Recommendations & Action Items",
        }
        return titles.get(section, section.replace("_", " ").title())

    def _get_executive_summary_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Generate prompt for executive summary section."""
        summary_data = self._prepare_summary_data(analysis_data)
        
        return f"""
Generate an executive summary for {self.company_name}'s financial analysis report 
for {self.reporting_period}.

Based on the following analysis data:
{json.dumps(summary_data, indent=2, default=str)}

The executive summary should:
1. Start with a one-paragraph overview of overall financial health
2. Highlight 3-5 key findings (both positive and concerning)
3. Summarize the credit risk position
4. Mention any fraud indicators or red flags if present
5. Conclude with a high-level recommendation

Keep it concise but comprehensive - approximately 300-400 words.
Format appropriately for {self.output_format} output.
"""

    def _get_financial_position_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Generate prompt for financial position section."""
        financial_data = analysis_data.get("financial_data", {})
        ratios = analysis_data.get("financial_ratios", {})
        
        return f"""
Generate a Financial Position Overview section for {self.company_name}.

Financial Data:
{json.dumps(financial_data, indent=2, default=str)}

Key Ratios:
{json.dumps(ratios.get("ratios", {}), indent=2, default=str)}

The section should cover:
1. Balance sheet highlights (assets, liabilities, equity)
2. Income statement summary (revenue, profitability)
3. Liquidity position
4. Capital structure analysis
5. Working capital assessment

Use specific numbers from the data. Approximately 400-500 words.
Format for {self.output_format} output.
"""

    def _get_ratio_analysis_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Generate prompt for ratio analysis section."""
        ratios = analysis_data.get("financial_ratios", {})
        
        return f"""
Generate a Financial Ratio Analysis section for {self.company_name}.

Ratio Analysis Results:
{json.dumps(ratios, indent=2, default=str)}

The section should:
1. Analyze liquidity ratios (current ratio, quick ratio)
2. Discuss profitability ratios (ROE, ROA, margins)
3. Evaluate leverage ratios (debt-to-equity, interest coverage)
4. Assess efficiency ratios (asset turnover, inventory turnover)
5. Compare to industry benchmarks if available
6. Highlight concerning or exceptional ratios

Include the actual ratio values and their interpretations.
Approximately 500-600 words. Format for {self.output_format} output.
"""

    def _get_trend_analysis_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Generate prompt for trend analysis section."""
        historical = analysis_data.get("historical_data", {})
        
        return f"""
Generate a Historical Trend Analysis section for {self.company_name}.

Historical Data:
{json.dumps(historical, indent=2, default=str)}

The section should:
1. Describe revenue and profitability trends
2. Analyze changes in key metrics over time
3. Identify any inflection points or significant changes
4. Discuss growth rates and their sustainability
5. Note any concerning patterns

If historical data is limited, focus on available period-over-period comparisons.
Approximately 300-400 words. Format for {self.output_format} output.
"""

    def _get_risk_assessment_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Generate prompt for risk assessment section."""
        credit_risk = analysis_data.get("credit_risk", {})
        fraud = analysis_data.get("fraud_analysis", {})
        
        return f"""
Generate a comprehensive Risk Assessment section for {self.company_name}.

Credit Risk Analysis:
{json.dumps(credit_risk, indent=2, default=str)}

Fraud Detection Analysis:
{json.dumps(fraud, indent=2, default=str)}

The section should:
1. Summarize credit risk findings (Z-score, ratings, default probability)
2. Discuss any fraud indicators or red flags detected
3. Assess overall risk level (low/moderate/elevated/high)
4. Identify specific risk factors requiring attention
5. Discuss potential mitigating factors

Be factual and balanced. Note both risks and mitigating factors.
Approximately 500-600 words. Format for {self.output_format} output.
"""

    def _get_peer_comparison_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Generate prompt for peer comparison section."""
        ratios = analysis_data.get("financial_ratios", {})
        benchmarks = ratios.get("benchmark_industry", "industry")
        
        return f"""
Generate a Peer & Industry Comparison section for {self.company_name}.

Company Ratios with Benchmarks:
{json.dumps(ratios, indent=2, default=str)}

Industry: {benchmarks}

The section should:
1. Compare key metrics to industry averages
2. Identify areas where the company outperforms peers
3. Highlight areas where the company underperforms
4. Discuss competitive positioning implications
5. Note any data limitations

Approximately 300-400 words. Format for {self.output_format} output.
"""

    def _get_recommendations_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Generate prompt for recommendations section."""
        summary_data = self._prepare_summary_data(analysis_data)
        
        return f"""
Generate a Recommendations & Action Items section for {self.company_name}.

Based on all analysis data:
{json.dumps(summary_data, indent=2, default=str)}

Provide:
1. 3-5 prioritized strategic recommendations
2. Specific action items for each recommendation
3. Timeline suggestions (immediate, short-term, long-term)
4. Expected impact of each recommendation
5. Key metrics to monitor going forward

Recommendations should be:
- Specific and actionable
- Based on the actual analysis findings
- Realistic and practical
- Prioritized by impact and urgency

Approximately 400-500 words. Format for {self.output_format} output.
"""

    def _prepare_summary_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare condensed summary data for prompts."""
        summary = {}
        
        # Extract key financial health indicators
        ratios = analysis_data.get("financial_ratios", {})
        if ratios:
            health = ratios.get("financial_health_summary", {})
            summary["financial_health"] = {
                "overall_score": health.get("overall_score"),
                "rating": health.get("rating"),
                "strengths": health.get("strengths", []),
                "issues": health.get("issues", []),
            }
            summary["key_ratios"] = {
                k: v.get("formatted", v.get("value")) 
                for k, v in ratios.get("ratios", {}).items()
            }
        
        # Extract credit risk summary
        credit = analysis_data.get("credit_risk", {})
        if credit:
            composite = credit.get("composite_assessment", {})
            summary["credit_risk"] = {
                "rating": composite.get("rating"),
                "default_probability": composite.get("default_probability_formatted"),
                "risk_classification": composite.get("risk_classification"),
            }
        
        # Extract fraud analysis summary
        fraud = analysis_data.get("fraud_analysis", {})
        if fraud:
            risk = fraud.get("risk_assessment", {})
            summary["fraud_risk"] = {
                "risk_level": risk.get("risk_level"),
                "risk_score": risk.get("overall_score"),
                "red_flags_count": len(fraud.get("red_flags_detected", [])),
                "contributing_factors": risk.get("contributing_factors", []),
            }
        
        return summary

    async def _generate_visualizations(
        self, 
        analysis_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate descriptions of recommended visualizations."""
        visualizations = []
        
        prompt = f"""
Based on the following financial analysis data, recommend appropriate visualizations 
to include in a financial report. For each visualization, provide a structured description.

Analysis Data:
{json.dumps(self._prepare_summary_data(analysis_data), indent=2, default=str)}

Preferred chart types: {', '.join(self.chart_types)}

For each recommended visualization, provide:
1. chart_type: The type of chart
2. title: A descriptive title
3. description: What the chart would show
4. data_series: Key data points to include
5. insights: 2-3 key insights the visualization would highlight

Recommend 3-5 visualizations that would be most impactful.
Return as a JSON array.
"""
        
        try:
            result = await self.viz_agent.run(prompt, store=False)
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            # Try to parse JSON from response
            visualizations = self._parse_json_from_response(response_text)
            if not visualizations:
                # Fallback to default visualizations
                visualizations = self._get_default_visualizations(analysis_data)
                
        except Exception as e:
            logger.warning(f"Error generating visualizations: {e}")
            visualizations = self._get_default_visualizations(analysis_data)
        
        return visualizations

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
        
        return []

    def _get_default_visualizations(
        self, 
        analysis_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get default visualization descriptions."""
        return [
            {
                "chart_type": "bar",
                "title": "Key Financial Ratios vs Industry Benchmarks",
                "description": "Horizontal bar chart comparing company ratios to industry averages",
                "data_series": ["Current Ratio", "ROE", "Debt-to-Equity", "Net Margin"],
                "insights": [
                    "Shows relative positioning versus peers",
                    "Highlights areas of strength and weakness",
                ]
            },
            {
                "chart_type": "line",
                "title": "Revenue and Profitability Trends",
                "description": "Multi-line chart showing revenue and net income over time",
                "data_series": ["Revenue", "Net Income", "Operating Income"],
                "insights": [
                    "Visualizes growth trajectory",
                    "Shows margin expansion or compression",
                ]
            },
            {
                "chart_type": "spider",
                "title": "Financial Health Scorecard",
                "description": "Radar chart showing scores across key financial dimensions",
                "data_series": ["Liquidity", "Profitability", "Leverage", "Efficiency", "Risk"],
                "insights": [
                    "Provides holistic view of financial health",
                    "Identifies areas requiring attention",
                ]
            },
        ]

    def _compile_full_report(self, report: Dict[str, Any]) -> str:
        """Compile all sections into a complete report document."""
        if self.output_format == "markdown":
            return self._compile_markdown_report(report)
        elif self.output_format == "html":
            return self._compile_html_report(report)
        elif self.output_format == "json":
            return json.dumps(report, indent=2, default=str)
        else:
            return self._compile_markdown_report(report)

    def _compile_markdown_report(self, report: Dict[str, Any]) -> str:
        """Compile report in Markdown format."""
        lines = []
        metadata = report.get("metadata", {})
        
        # Title
        lines.append(f"# Financial Analysis Report: {metadata.get('company_name', 'Company')}")
        lines.append(f"**Reporting Period:** {metadata.get('reporting_period', 'N/A')}")
        lines.append(f"**Report Style:** {metadata.get('report_style', 'executive').title()}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Table of Contents
        lines.append("## Table of Contents")
        for i, section in enumerate(report.get("sections", {}).keys(), 1):
            title = self._get_section_title(section)
            lines.append(f"{i}. [{title}](#{section.replace('_', '-')})")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Sections
        for section_key, section_data in report.get("sections", {}).items():
            title = section_data.get("title", section_key)
            content = section_data.get("content", "")
            
            lines.append(f"## {title}")
            lines.append("")
            lines.append(content)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Visualizations
        visualizations = report.get("visualizations", [])
        if visualizations:
            lines.append("## Recommended Visualizations")
            lines.append("")
            for i, viz in enumerate(visualizations, 1):
                lines.append(f"### {i}. {viz.get('title', 'Chart')}")
                lines.append(f"**Type:** {viz.get('chart_type', 'N/A')}")
                lines.append(f"**Description:** {viz.get('description', '')}")
                if viz.get("insights"):
                    lines.append("**Key Insights:**")
                    for insight in viz["insights"]:
                        lines.append(f"- {insight}")
                lines.append("")
        
        return "\n".join(lines)

    def _compile_html_report(self, report: Dict[str, Any]) -> str:
        """Compile report in HTML format."""
        metadata = report.get("metadata", {})
        
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>Financial Analysis Report - {metadata.get('company_name', 'Company')}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }",
            "h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }",
            "h2 { color: #34495e; margin-top: 30px; }",
            ".metadata { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }",
            ".section { margin-bottom: 30px; }",
            ".visualization { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>Financial Analysis Report: {metadata.get('company_name', 'Company')}</h1>",
            "<div class='metadata'>",
            f"<strong>Reporting Period:</strong> {metadata.get('reporting_period', 'N/A')}<br>",
            f"<strong>Report Style:</strong> {metadata.get('report_style', 'executive').title()}",
            "</div>",
        ]
        
        # Sections
        for section_key, section_data in report.get("sections", {}).items():
            title = section_data.get("title", section_key)
            content = section_data.get("content", "").replace("\n", "<br>")
            html_parts.append("<div class='section'>")
            html_parts.append(f"<h2>{title}</h2>")
            html_parts.append(f"<p>{content}</p>")
            html_parts.append("</div>")
        
        html_parts.extend(["</body>", "</html>"])
        
        return "\n".join(html_parts)
