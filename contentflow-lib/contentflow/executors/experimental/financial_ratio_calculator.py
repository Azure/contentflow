"""
Financial Ratio Calculator Executor.

Calculates standard financial ratios with industry benchmarking capabilities
for financial statement analysis and risk assessment workflows.
"""

import logging
import math
from typing import List, Union, Dict, Any, Optional
from enum import Enum

from agent_framework import WorkflowContext
from contentflow.models import Content
from contentflow.executors.base import BaseExecutor

logger = logging.getLogger(__name__)


class RatioCategory(str, Enum):
    """Categories of financial ratios."""
    LIQUIDITY = "liquidity"
    PROFITABILITY = "profitability"
    LEVERAGE = "leverage"
    EFFICIENCY = "efficiency"
    MARKET = "market"


# Industry benchmarks for common industries (simplified)
INDUSTRY_BENCHMARKS = {
    "technology": {
        "current_ratio": 2.5,
        "quick_ratio": 2.0,
        "debt_to_equity": 0.5,
        "return_on_equity": 0.15,
        "return_on_assets": 0.10,
        "gross_margin": 0.60,
        "net_margin": 0.15,
        "asset_turnover": 0.8,
    },
    "manufacturing": {
        "current_ratio": 1.8,
        "quick_ratio": 1.0,
        "debt_to_equity": 0.8,
        "return_on_equity": 0.12,
        "return_on_assets": 0.06,
        "gross_margin": 0.30,
        "net_margin": 0.05,
        "asset_turnover": 1.2,
    },
    "retail": {
        "current_ratio": 1.5,
        "quick_ratio": 0.5,
        "debt_to_equity": 1.0,
        "return_on_equity": 0.18,
        "return_on_assets": 0.08,
        "gross_margin": 0.35,
        "net_margin": 0.03,
        "asset_turnover": 2.5,
    },
    "financial_services": {
        "current_ratio": 1.2,
        "quick_ratio": 1.0,
        "debt_to_equity": 3.0,
        "return_on_equity": 0.10,
        "return_on_assets": 0.01,
        "gross_margin": 0.80,
        "net_margin": 0.20,
        "asset_turnover": 0.1,
    },
    "healthcare": {
        "current_ratio": 2.0,
        "quick_ratio": 1.5,
        "debt_to_equity": 0.6,
        "return_on_equity": 0.14,
        "return_on_assets": 0.08,
        "gross_margin": 0.45,
        "net_margin": 0.08,
        "asset_turnover": 1.0,
    },
    "default": {
        "current_ratio": 2.0,
        "quick_ratio": 1.0,
        "debt_to_equity": 1.0,
        "return_on_equity": 0.12,
        "return_on_assets": 0.06,
        "gross_margin": 0.40,
        "net_margin": 0.08,
        "asset_turnover": 1.0,
    },
}


class FinancialRatioCalculatorExecutor(BaseExecutor):
    """
    Calculate financial ratios from extracted financial statement data.
    
    This executor computes liquidity, profitability, leverage, efficiency,
    and market ratios with optional industry benchmarking for comparative analysis.
    
    Configuration (settings dict):
        - ratio_categories (list): Categories to calculate
          Options: "liquidity", "profitability", "leverage", "efficiency", "market"
          Default: ["liquidity", "profitability", "leverage"]
        - ratios (list): Specific ratios to calculate
          Default: All available ratios in selected categories
        - benchmark_comparison (bool): Compare against industry benchmarks
          Default: True
        - industry (str): Industry for benchmarking
          Default: "default"
        - input_field (str): Field containing financial data
          Default: "financial_data"
        - output_field (str): Field name for calculated ratios
          Default: "financial_ratios"
    
    Expected Input Data Structure:
        The input content should have financial data in the format:
        {
            "income_statement": {
                "revenue": 1000000,
                "cogs": 600000,
                "gross_profit": 400000,
                "operating_expenses": 200000,
                "operating_income": 200000,
                "interest_expense": 20000,
                "net_income": 150000,
                "ebit": 200000,
                "ebitda": 250000
            },
            "balance_sheet": {
                "current_assets": 500000,
                "inventory": 100000,
                "total_assets": 2000000,
                "current_liabilities": 300000,
                "total_liabilities": 800000,
                "total_equity": 1200000,
                "accounts_receivable": 200000,
                "accounts_payable": 150000
            },
            "market_data": {  # Optional, for market ratios
                "market_cap": 5000000,
                "share_price": 50,
                "shares_outstanding": 100000,
                "earnings_per_share": 1.5,
                "dividends_per_share": 0.5
            }
        }
    
    Output:
        Content with added fields:
        - data[output_field]: Dictionary of calculated ratios with interpretations
        - summary_data["ratio_calculation_status"]: Execution status
    
    Example:
        ```yaml
        - id: financial-ratios-1
          type: financial_ratio_calculator
          settings:
            ratio_categories: ["liquidity", "profitability", "leverage"]
            benchmark_comparison: true
            industry: "technology"
            input_field: "mapped_financials"
            output_field: "financial_ratios"
        ```
    """
    
    # Define available ratios by category
    AVAILABLE_RATIOS = {
        RatioCategory.LIQUIDITY: [
            "current_ratio",
            "quick_ratio",
            "cash_ratio",
            "working_capital",
        ],
        RatioCategory.PROFITABILITY: [
            "gross_margin",
            "operating_margin",
            "net_margin",
            "return_on_assets",
            "return_on_equity",
            "return_on_invested_capital",
        ],
        RatioCategory.LEVERAGE: [
            "debt_to_equity",
            "debt_to_assets",
            "interest_coverage",
            "equity_multiplier",
        ],
        RatioCategory.EFFICIENCY: [
            "asset_turnover",
            "inventory_turnover",
            "receivables_turnover",
            "payables_turnover",
            "days_sales_outstanding",
            "days_inventory_outstanding",
        ],
        RatioCategory.MARKET: [
            "price_to_earnings",
            "price_to_book",
            "dividend_yield",
            "earnings_yield",
        ],
    }
    
    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        
        # Configuration
        self.ratio_categories = self.get_setting(
            "ratio_categories", 
            ["liquidity", "profitability", "leverage"]
        )
        self.specific_ratios = self.get_setting("ratios", None)
        self.benchmark_comparison = self.get_setting("benchmark_comparison", True)
        self.industry = self.get_setting("industry", "default")
        self.input_field = self.get_setting("input_field", "financial_data")
        self.output_field = self.get_setting("output_field", "financial_ratios")
        
        if self.debug_mode:
            logger.debug(
                f"FinancialRatioCalculatorExecutor initialized: "
                f"categories={self.ratio_categories}, industry={self.industry}"
            )

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """Process financial data and calculate ratios."""
        items_to_process = input if isinstance(input, list) else [input]
        
        for item in items_to_process:
            await self._process_single_content(item)
            
        return input

    async def _process_single_content(self, content: Content) -> None:
        """Process a single content item and calculate financial ratios."""
        logger.info(f"Calculating financial ratios for content {content.id}")
        
        try:
            # Extract financial data
            financial_data = self.try_extract_nested_field_from_content(
                content=content,
                field_path=self.input_field
            )
            
            if not financial_data:
                # Try common alternative field names
                for alt_field in ["mapped_financials", "extracted_data", "data"]:
                    financial_data = content.data.get(alt_field)
                    if financial_data:
                        break
            
            if not financial_data:
                logger.warning(f"No financial data found in content {content.id}")
                content.data[self.output_field] = {"error": "No financial data found"}
                content.summary_data["ratio_calculation_status"] = "failed"
                return
            
            # Calculate ratios
            ratio_results = self._calculate_ratios(financial_data)
            
            # Add benchmark comparison if enabled
            if self.benchmark_comparison:
                ratio_results = self._add_benchmark_comparison(ratio_results)
            
            # Add overall financial health assessment
            ratio_results["financial_health_summary"] = self._assess_financial_health(ratio_results)
            
            # Store results
            content.data[self.output_field] = ratio_results
            content.summary_data["ratio_calculation_status"] = "success"
            content.summary_data["ratios_calculated"] = len(ratio_results.get("ratios", {}))
            
        except Exception as e:
            logger.error(f"Error calculating ratios for content {content.id}: {e}")
            content.data[self.output_field] = {"error": str(e)}
            content.summary_data["ratio_calculation_status"] = "failed"

    def _calculate_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all requested financial ratios."""
        results = {
            "ratios": {},
            "categories": {},
            "metadata": {
                "industry": self.industry,
                "categories_analyzed": self.ratio_categories,
            }
        }
        
        income_stmt = financial_data.get("income_statement", {})
        balance_sheet = financial_data.get("balance_sheet", {})
        market_data = financial_data.get("market_data", {})
        
        # Determine which ratios to calculate
        ratios_to_calculate = []
        if self.specific_ratios:
            ratios_to_calculate = self.specific_ratios
        else:
            for category in self.ratio_categories:
                cat_enum = RatioCategory(category)
                ratios_to_calculate.extend(self.AVAILABLE_RATIOS.get(cat_enum, []))
        
        # Calculate each ratio
        for ratio_name in ratios_to_calculate:
            value = self._calculate_single_ratio(
                ratio_name, income_stmt, balance_sheet, market_data
            )
            if value is not None:
                results["ratios"][ratio_name] = {
                    "value": value,
                    "formatted": self._format_ratio_value(ratio_name, value),
                    "interpretation": self._interpret_ratio(ratio_name, value),
                    "category": self._get_ratio_category(ratio_name),
                }
        
        # Group by category
        for ratio_name, ratio_data in results["ratios"].items():
            category = ratio_data["category"]
            if category not in results["categories"]:
                results["categories"][category] = {}
            results["categories"][category][ratio_name] = ratio_data
        
        return results

    def _calculate_single_ratio(
        self,
        ratio_name: str,
        income_stmt: Dict[str, Any],
        balance_sheet: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Optional[float]:
        """Calculate a single financial ratio."""
        try:
            # Liquidity Ratios
            if ratio_name == "current_ratio":
                current_assets = balance_sheet.get("current_assets", 0)
                current_liabilities = balance_sheet.get("current_liabilities", 0)
                return current_assets / current_liabilities if current_liabilities else None
            
            elif ratio_name == "quick_ratio":
                current_assets = balance_sheet.get("current_assets", 0)
                inventory = balance_sheet.get("inventory", 0)
                current_liabilities = balance_sheet.get("current_liabilities", 0)
                return (current_assets - inventory) / current_liabilities if current_liabilities else None
            
            elif ratio_name == "cash_ratio":
                cash = balance_sheet.get("cash", balance_sheet.get("cash_and_equivalents", 0))
                current_liabilities = balance_sheet.get("current_liabilities", 0)
                return cash / current_liabilities if current_liabilities else None
            
            elif ratio_name == "working_capital":
                current_assets = balance_sheet.get("current_assets", 0)
                current_liabilities = balance_sheet.get("current_liabilities", 0)
                return current_assets - current_liabilities
            
            # Profitability Ratios
            elif ratio_name == "gross_margin":
                revenue = income_stmt.get("revenue", 0)
                cogs = income_stmt.get("cogs", income_stmt.get("cost_of_goods_sold", 0))
                return (revenue - cogs) / revenue if revenue else None
            
            elif ratio_name == "operating_margin":
                operating_income = income_stmt.get("operating_income", 0)
                revenue = income_stmt.get("revenue", 0)
                return operating_income / revenue if revenue else None
            
            elif ratio_name == "net_margin":
                net_income = income_stmt.get("net_income", 0)
                revenue = income_stmt.get("revenue", 0)
                return net_income / revenue if revenue else None
            
            elif ratio_name == "return_on_assets":
                net_income = income_stmt.get("net_income", 0)
                total_assets = balance_sheet.get("total_assets", 0)
                return net_income / total_assets if total_assets else None
            
            elif ratio_name == "return_on_equity":
                net_income = income_stmt.get("net_income", 0)
                total_equity = balance_sheet.get("total_equity", 0)
                return net_income / total_equity if total_equity else None
            
            elif ratio_name == "return_on_invested_capital":
                ebit = income_stmt.get("ebit", income_stmt.get("operating_income", 0))
                tax_rate = income_stmt.get("effective_tax_rate", 0.25)
                total_assets = balance_sheet.get("total_assets", 0)
                current_liabilities = balance_sheet.get("current_liabilities", 0)
                invested_capital = total_assets - current_liabilities
                return (ebit * (1 - tax_rate)) / invested_capital if invested_capital else None
            
            # Leverage Ratios
            elif ratio_name == "debt_to_equity":
                total_liabilities = balance_sheet.get("total_liabilities", 0)
                total_equity = balance_sheet.get("total_equity", 0)
                return total_liabilities / total_equity if total_equity else None
            
            elif ratio_name == "debt_to_assets":
                total_liabilities = balance_sheet.get("total_liabilities", 0)
                total_assets = balance_sheet.get("total_assets", 0)
                return total_liabilities / total_assets if total_assets else None
            
            elif ratio_name == "interest_coverage":
                ebit = income_stmt.get("ebit", income_stmt.get("operating_income", 0))
                interest_expense = income_stmt.get("interest_expense", 0)
                return ebit / interest_expense if interest_expense else None
            
            elif ratio_name == "equity_multiplier":
                total_assets = balance_sheet.get("total_assets", 0)
                total_equity = balance_sheet.get("total_equity", 0)
                return total_assets / total_equity if total_equity else None
            
            # Efficiency Ratios
            elif ratio_name == "asset_turnover":
                revenue = income_stmt.get("revenue", 0)
                total_assets = balance_sheet.get("total_assets", 0)
                return revenue / total_assets if total_assets else None
            
            elif ratio_name == "inventory_turnover":
                cogs = income_stmt.get("cogs", income_stmt.get("cost_of_goods_sold", 0))
                inventory = balance_sheet.get("inventory", 0)
                return cogs / inventory if inventory else None
            
            elif ratio_name == "receivables_turnover":
                revenue = income_stmt.get("revenue", 0)
                accounts_receivable = balance_sheet.get("accounts_receivable", 0)
                return revenue / accounts_receivable if accounts_receivable else None
            
            elif ratio_name == "payables_turnover":
                cogs = income_stmt.get("cogs", income_stmt.get("cost_of_goods_sold", 0))
                accounts_payable = balance_sheet.get("accounts_payable", 0)
                return cogs / accounts_payable if accounts_payable else None
            
            elif ratio_name == "days_sales_outstanding":
                accounts_receivable = balance_sheet.get("accounts_receivable", 0)
                revenue = income_stmt.get("revenue", 0)
                return (accounts_receivable / revenue) * 365 if revenue else None
            
            elif ratio_name == "days_inventory_outstanding":
                inventory = balance_sheet.get("inventory", 0)
                cogs = income_stmt.get("cogs", income_stmt.get("cost_of_goods_sold", 0))
                return (inventory / cogs) * 365 if cogs else None
            
            # Market Ratios
            elif ratio_name == "price_to_earnings":
                share_price = market_data.get("share_price", 0)
                eps = market_data.get("earnings_per_share", 0)
                return share_price / eps if eps else None
            
            elif ratio_name == "price_to_book":
                market_cap = market_data.get("market_cap", 0)
                total_equity = balance_sheet.get("total_equity", 0)
                return market_cap / total_equity if total_equity else None
            
            elif ratio_name == "dividend_yield":
                dividends_per_share = market_data.get("dividends_per_share", 0)
                share_price = market_data.get("share_price", 0)
                return dividends_per_share / share_price if share_price else None
            
            elif ratio_name == "earnings_yield":
                eps = market_data.get("earnings_per_share", 0)
                share_price = market_data.get("share_price", 0)
                return eps / share_price if share_price else None
            
            return None
            
        except (ZeroDivisionError, TypeError):
            return None

    def _format_ratio_value(self, ratio_name: str, value: float) -> str:
        """Format ratio value for display."""
        if value is None:
            return "N/A"
        
        # Percentage ratios
        percentage_ratios = [
            "gross_margin", "operating_margin", "net_margin",
            "return_on_assets", "return_on_equity", "return_on_invested_capital",
            "dividend_yield", "earnings_yield"
        ]
        
        if ratio_name in percentage_ratios:
            return f"{value * 100:.2f}%"
        elif ratio_name == "working_capital":
            return f"${value:,.0f}"
        elif ratio_name in ["days_sales_outstanding", "days_inventory_outstanding"]:
            return f"{value:.1f} days"
        else:
            return f"{value:.2f}"

    def _interpret_ratio(self, ratio_name: str, value: float) -> str:
        """Provide interpretation of ratio value."""
        if value is None:
            return "Unable to calculate"
        
        interpretations = {
            "current_ratio": lambda v: "Strong liquidity" if v > 2 else ("Adequate liquidity" if v > 1 else "Potential liquidity concerns"),
            "quick_ratio": lambda v: "Strong quick liquidity" if v > 1 else "May need to rely on inventory",
            "debt_to_equity": lambda v: "Low leverage" if v < 0.5 else ("Moderate leverage" if v < 1.5 else "High leverage"),
            "return_on_equity": lambda v: "Strong returns" if v > 0.15 else ("Moderate returns" if v > 0.08 else "Low returns"),
            "return_on_assets": lambda v: "Efficient asset use" if v > 0.10 else ("Average efficiency" if v > 0.05 else "Low asset efficiency"),
            "gross_margin": lambda v: "High margins" if v > 0.40 else ("Average margins" if v > 0.25 else "Thin margins"),
            "net_margin": lambda v: "Highly profitable" if v > 0.15 else ("Profitable" if v > 0.05 else "Low profitability"),
            "interest_coverage": lambda v: "Strong coverage" if v > 5 else ("Adequate coverage" if v > 2 else "Potential risk"),
            "asset_turnover": lambda v: "High asset utilization" if v > 1.5 else ("Average utilization" if v > 0.8 else "Low utilization"),
        }
        
        interpreter = interpretations.get(ratio_name)
        if interpreter:
            return interpreter(value)
        return "See industry comparison"

    def _get_ratio_category(self, ratio_name: str) -> str:
        """Get the category for a ratio."""
        for category, ratios in self.AVAILABLE_RATIOS.items():
            if ratio_name in ratios:
                return category.value
        return "other"

    def _add_benchmark_comparison(self, ratio_results: Dict[str, Any]) -> Dict[str, Any]:
        """Add industry benchmark comparisons to ratio results."""
        benchmarks = INDUSTRY_BENCHMARKS.get(
            self.industry.lower().replace(" ", "_"),
            INDUSTRY_BENCHMARKS["default"]
        )
        
        for ratio_name, ratio_data in ratio_results.get("ratios", {}).items():
            benchmark_value = benchmarks.get(ratio_name)
            if benchmark_value is not None:
                actual_value = ratio_data.get("value")
                if actual_value is not None:
                    variance = ((actual_value - benchmark_value) / benchmark_value) * 100
                    ratio_data["benchmark"] = {
                        "industry_average": benchmark_value,
                        "formatted": self._format_ratio_value(ratio_name, benchmark_value),
                        "variance_percent": round(variance, 2),
                        "comparison": "above" if variance > 0 else ("below" if variance < 0 else "at"),
                    }
        
        ratio_results["benchmark_industry"] = self.industry
        return ratio_results

    def _assess_financial_health(self, ratio_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall financial health assessment."""
        ratios = ratio_results.get("ratios", {})
        
        health_score = 0
        max_score = 0
        issues = []
        strengths = []
        
        # Assess liquidity
        current_ratio = ratios.get("current_ratio", {}).get("value")
        if current_ratio is not None:
            max_score += 20
            if current_ratio >= 2:
                health_score += 20
                strengths.append("Strong liquidity position")
            elif current_ratio >= 1:
                health_score += 10
            else:
                issues.append("Potential liquidity concerns - current ratio below 1")
        
        # Assess profitability
        roe = ratios.get("return_on_equity", {}).get("value")
        if roe is not None:
            max_score += 20
            if roe >= 0.15:
                health_score += 20
                strengths.append("Strong return on equity")
            elif roe >= 0.08:
                health_score += 10
            elif roe < 0:
                issues.append("Negative return on equity")
        
        # Assess leverage
        debt_to_equity = ratios.get("debt_to_equity", {}).get("value")
        if debt_to_equity is not None:
            max_score += 20
            if debt_to_equity <= 0.5:
                health_score += 20
                strengths.append("Conservative leverage")
            elif debt_to_equity <= 1.5:
                health_score += 10
            else:
                issues.append("High debt-to-equity ratio")
        
        # Calculate overall score
        overall_score = (health_score / max_score * 100) if max_score > 0 else 0
        
        return {
            "overall_score": round(overall_score, 1),
            "rating": self._get_health_rating(overall_score),
            "strengths": strengths,
            "issues": issues,
            "recommendation": self._get_recommendation(overall_score, issues),
        }

    def _get_health_rating(self, score: float) -> str:
        """Convert health score to rating."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        elif score >= 20:
            return "Weak"
        else:
            return "Critical"

    def _get_recommendation(self, score: float, issues: List[str]) -> str:
        """Generate recommendation based on health assessment."""
        if score >= 80:
            return "Financial position is strong. Continue current strategies."
        elif score >= 60:
            return "Financial position is good with minor areas for improvement."
        elif issues:
            return f"Address the following concerns: {'; '.join(issues[:2])}"
        else:
            return "Consider comprehensive financial review."
