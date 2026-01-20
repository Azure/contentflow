"""
Fraud Detection Analyzer Executor.

Detects potential fraud indicators using Benford's Law, ratio analysis,
trend analysis, and peer comparison for financial statement fraud detection.
"""

import logging
import math
from typing import List, Union, Dict, Any, Optional
from collections import Counter
from enum import Enum

from agent_framework import WorkflowContext
from contentflow.models import Content
from contentflow.executors.base import BaseExecutor

logger = logging.getLogger(__name__)


class FraudDetectionMethod(str, Enum):
    """Fraud detection methods."""
    BENFORDS_LAW = "benfords_law"
    RATIO_ANALYSIS = "ratio_analysis"
    TREND_ANALYSIS = "trend_analysis"
    PEER_COMPARISON = "peer_comparison"


# Benford's Law expected frequencies for first digit
BENFORD_EXPECTED = {
    1: 0.301,
    2: 0.176,
    3: 0.125,
    4: 0.097,
    5: 0.079,
    6: 0.067,
    7: 0.058,
    8: 0.051,
    9: 0.046,
}

# Common financial fraud red flags and their indicators
FRAUD_RED_FLAGS = {
    "revenue_recognition_anomalies": {
        "description": "Unusual patterns in revenue recognition",
        "indicators": ["revenue_spikes_end_of_period", "high_receivables_to_revenue", "round_numbers"],
    },
    "unusual_expense_patterns": {
        "description": "Abnormal expense categorization or timing",
        "indicators": ["expense_timing_shifts", "unusual_accruals", "below_threshold_amounts"],
    },
    "inventory_discrepancies": {
        "description": "Inventory valuation or count issues",
        "indicators": ["inventory_growth_vs_sales", "obsolescence_rates", "shrinkage_patterns"],
    },
    "related_party_transactions": {
        "description": "Suspicious transactions with related parties",
        "indicators": ["unusual_pricing", "circular_transactions", "undisclosed_relationships"],
    },
}


class FraudDetectionAnalyzerExecutor(BaseExecutor):
    """
    Detect potential fraud indicators in financial data.
    
    This executor implements multiple fraud detection methods:
    - Benford's Law analysis for digit distribution anomalies
    - Financial ratio analysis for manipulation indicators
    - Trend analysis for unusual patterns
    - Peer comparison for outlier detection
    
    Configuration (settings dict):
        - methods (list): Fraud detection methods to use
          Options: "benfords_law", "ratio_analysis", "trend_analysis", "peer_comparison"
          Default: ["benfords_law", "ratio_analysis"]
        - red_flags (list): Specific red flags to check
          Default: All available red flags
        - anomaly_threshold (float): Threshold for anomaly detection (0.0-1.0)
          Default: 0.95
        - input_field (str): Field containing financial data
          Default: "financial_data"
        - output_field (str): Field name for fraud indicators
          Default: "fraud_indicators"
        - include_raw_analysis (bool): Include detailed analysis data
          Default: True
    
    Expected Input Data Structure:
        {
            "income_statement": {
                "revenue": 1000000,
                "expenses": 800000,
                ...
            },
            "balance_sheet": {...},
            "transactions": [  # For Benford's Law analysis
                {"amount": 1234.56, "type": "revenue", ...},
                ...
            ],
            "historical_data": {  # For trend analysis
                "revenue": [900000, 950000, 1000000],
                "net_income": [80000, 85000, 90000],
                ...
            },
            "peer_data": {  # For peer comparison
                "industry_avg_margin": 0.10,
                "industry_avg_growth": 0.05,
                ...
            }
        }
    
    Output:
        Content with added fields:
        - data[output_field]: Dictionary containing fraud analysis results
        - summary_data["fraud_detection_status"]: Execution status
        - summary_data["risk_score"]: Overall fraud risk score
    
    Example:
        ```yaml
        - id: fraud-detection-1
          type: fraud_detection_analyzer
          settings:
            methods: ["benfords_law", "ratio_analysis", "trend_analysis"]
            anomaly_threshold: 0.95
            output_field: "fraud_indicators"
        ```
    """
    
    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        
        # Configuration
        self.methods = self.get_setting("methods", ["benfords_law", "ratio_analysis"])
        self.red_flags = self.get_setting("red_flags", list(FRAUD_RED_FLAGS.keys()))
        self.anomaly_threshold = self.get_setting("anomaly_threshold", 0.95)
        self.input_field = self.get_setting("input_field", "financial_data")
        self.output_field = self.get_setting("output_field", "fraud_indicators")
        self.include_raw_analysis = self.get_setting("include_raw_analysis", True)
        
        if self.debug_mode:
            logger.debug(
                f"FraudDetectionAnalyzerExecutor initialized: "
                f"methods={self.methods}, threshold={self.anomaly_threshold}"
            )

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """Process financial data and detect fraud indicators."""
        items_to_process = input if isinstance(input, list) else [input]
        
        for item in items_to_process:
            await self._process_single_content(item)
            
        return input

    async def _process_single_content(self, content: Content) -> None:
        """Process a single content item and detect fraud indicators."""
        logger.info(f"Analyzing fraud indicators for content {content.id}")
        
        try:
            # Extract financial data
            financial_data = self.try_extract_nested_field_from_content(
                content=content,
                field_path=self.input_field
            )
            
            if not financial_data:
                for alt_field in ["aggregated_data", "mapped_financials", "data"]:
                    financial_data = content.data.get(alt_field)
                    if financial_data:
                        break
            
            if not financial_data:
                logger.warning(f"No financial data found in content {content.id}")
                content.data[self.output_field] = {"error": "No financial data found"}
                content.summary_data["fraud_detection_status"] = "failed"
                return
            
            # Run fraud detection analysis
            fraud_results = {
                "methods_used": self.methods,
                "anomaly_threshold": self.anomaly_threshold,
                "analysis_results": {},
                "red_flags_detected": [],
                "warnings": [],
            }
            
            # Run each detection method
            for method in self.methods:
                if method == FraudDetectionMethod.BENFORDS_LAW.value:
                    fraud_results["analysis_results"]["benfords_law"] = \
                        self._analyze_benfords_law(financial_data)
                elif method == FraudDetectionMethod.RATIO_ANALYSIS.value:
                    fraud_results["analysis_results"]["ratio_analysis"] = \
                        self._analyze_ratios(financial_data)
                elif method == FraudDetectionMethod.TREND_ANALYSIS.value:
                    fraud_results["analysis_results"]["trend_analysis"] = \
                        self._analyze_trends(financial_data)
                elif method == FraudDetectionMethod.PEER_COMPARISON.value:
                    fraud_results["analysis_results"]["peer_comparison"] = \
                        self._compare_to_peers(financial_data)
            
            # Check for specific red flags
            fraud_results["red_flags_detected"] = self._check_red_flags(
                financial_data, fraud_results["analysis_results"]
            )
            
            # Calculate overall risk score
            risk_assessment = self._calculate_risk_score(fraud_results)
            fraud_results["risk_assessment"] = risk_assessment
            
            # Remove raw analysis if not requested
            if not self.include_raw_analysis:
                for method_result in fraud_results["analysis_results"].values():
                    if "raw_data" in method_result:
                        del method_result["raw_data"]
            
            # Store results
            content.data[self.output_field] = fraud_results
            content.summary_data["fraud_detection_status"] = "success"
            content.summary_data["risk_score"] = risk_assessment["overall_score"]
            content.summary_data["red_flags_count"] = len(fraud_results["red_flags_detected"])
            
        except Exception as e:
            logger.error(f"Error detecting fraud for content {content.id}: {e}")
            content.data[self.output_field] = {"error": str(e)}
            content.summary_data["fraud_detection_status"] = "failed"

    def _analyze_benfords_law(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze financial data using Benford's Law.
        
        Benford's Law states that in naturally occurring data, the leading digit
        is 1 about 30% of the time, and larger digits occur less frequently.
        Deviations can indicate data manipulation.
        """
        # Extract numerical values from financial data
        numbers = self._extract_numbers(financial_data)
        
        if len(numbers) < 50:
            return {
                "status": "insufficient_data",
                "message": f"Only {len(numbers)} numbers found. Need at least 50 for reliable analysis.",
                "sample_size": len(numbers),
            }
        
        # Get first digit distribution
        first_digits = self._get_first_digits(numbers)
        digit_counts = Counter(first_digits)
        total_count = len(first_digits)
        
        # Calculate observed frequencies
        observed_freq = {d: digit_counts.get(d, 0) / total_count for d in range(1, 10)}
        
        # Calculate chi-square statistic
        chi_square = 0
        for digit in range(1, 10):
            expected = BENFORD_EXPECTED[digit] * total_count
            observed = digit_counts.get(digit, 0)
            if expected > 0:
                chi_square += (observed - expected) ** 2 / expected
        
        # Chi-square critical value for 8 degrees of freedom at 95% confidence
        chi_square_critical = 15.507
        
        # Calculate Mean Absolute Deviation (MAD)
        mad = sum(abs(observed_freq[d] - BENFORD_EXPECTED[d]) for d in range(1, 10)) / 9
        
        # MAD thresholds (Nigrini's conformity levels)
        # < 0.006: Close conformity
        # 0.006-0.012: Acceptable conformity
        # 0.012-0.015: Marginally acceptable
        # > 0.015: Non-conformity
        
        if mad < 0.006:
            conformity = "Close Conformity"
            is_suspicious = False
        elif mad < 0.012:
            conformity = "Acceptable Conformity"
            is_suspicious = False
        elif mad < 0.015:
            conformity = "Marginally Acceptable"
            is_suspicious = True
        else:
            conformity = "Non-Conformity"
            is_suspicious = True
        
        # Identify specific digit anomalies
        anomalies = []
        for digit in range(1, 10):
            deviation = abs(observed_freq[digit] - BENFORD_EXPECTED[digit])
            if deviation > 0.05:  # 5% deviation threshold
                direction = "over" if observed_freq[digit] > BENFORD_EXPECTED[digit] else "under"
                anomalies.append({
                    "digit": digit,
                    "expected": round(BENFORD_EXPECTED[digit], 4),
                    "observed": round(observed_freq[digit], 4),
                    "deviation": round(deviation, 4),
                    "direction": f"{direction}-represented",
                })
        
        return {
            "status": "completed",
            "sample_size": total_count,
            "chi_square_statistic": round(chi_square, 4),
            "chi_square_critical": chi_square_critical,
            "passes_chi_square_test": chi_square < chi_square_critical,
            "mean_absolute_deviation": round(mad, 6),
            "conformity_level": conformity,
            "is_suspicious": is_suspicious,
            "digit_anomalies": anomalies,
            "distribution": {
                "observed": {str(d): round(observed_freq[d], 4) for d in range(1, 10)},
                "expected": {str(d): round(BENFORD_EXPECTED[d], 4) for d in range(1, 10)},
            },
            "interpretation": self._interpret_benfords(mad, conformity, anomalies),
        }

    def _analyze_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze financial ratios for manipulation indicators.
        
        Looks for:
        - Unusual ratio combinations
        - Ratios that deviate significantly from norms
        - Signs of earnings management
        """
        income_stmt = financial_data.get("income_statement", {})
        balance_sheet = financial_data.get("balance_sheet", {})
        
        warnings = []
        indicators = []
        
        # Calculate key ratios
        revenue = income_stmt.get("revenue", 0)
        net_income = income_stmt.get("net_income", 0)
        accounts_receivable = balance_sheet.get("accounts_receivable", 0)
        inventory = balance_sheet.get("inventory", 0)
        total_assets = balance_sheet.get("total_assets", 1)
        current_assets = balance_sheet.get("current_assets", 0)
        current_liabilities = balance_sheet.get("current_liabilities", 1)
        
        calculated_ratios = {}
        
        # Days Sales Outstanding (DSO)
        if revenue > 0:
            dso = (accounts_receivable / revenue) * 365
            calculated_ratios["days_sales_outstanding"] = round(dso, 1)
            if dso > 90:
                indicators.append({
                    "indicator": "high_dso",
                    "value": dso,
                    "threshold": 90,
                    "concern": "Unusually high DSO may indicate revenue recognition issues",
                    "severity": "medium" if dso < 120 else "high",
                })
        
        # Accounts Receivable to Revenue ratio
        if revenue > 0:
            ar_to_revenue = accounts_receivable / revenue
            calculated_ratios["ar_to_revenue"] = round(ar_to_revenue, 4)
            if ar_to_revenue > 0.30:
                indicators.append({
                    "indicator": "high_ar_ratio",
                    "value": round(ar_to_revenue, 4),
                    "threshold": 0.30,
                    "concern": "High receivables relative to revenue may indicate fictitious sales",
                    "severity": "medium" if ar_to_revenue < 0.40 else "high",
                })
        
        # Gross Margin analysis
        cogs = income_stmt.get("cogs", income_stmt.get("cost_of_goods_sold", 0))
        if revenue > 0 and cogs > 0:
            gross_margin = (revenue - cogs) / revenue
            calculated_ratios["gross_margin"] = round(gross_margin, 4)
            # Check for unusually high or negative margins
            if gross_margin > 0.90:
                indicators.append({
                    "indicator": "extremely_high_margin",
                    "value": round(gross_margin, 4),
                    "threshold": 0.90,
                    "concern": "Unusually high gross margin may warrant investigation",
                    "severity": "medium",
                })
            elif gross_margin < 0:
                indicators.append({
                    "indicator": "negative_margin",
                    "value": round(gross_margin, 4),
                    "threshold": 0,
                    "concern": "Negative gross margin indicates potential issues",
                    "severity": "high",
                })
        
        # Quality of Earnings indicators
        operating_cash_flow = income_stmt.get("operating_cash_flow", 
                             financial_data.get("cash_flow", {}).get("operating", 0))
        if net_income != 0 and operating_cash_flow != 0:
            quality_ratio = operating_cash_flow / net_income
            calculated_ratios["cash_to_earnings_ratio"] = round(quality_ratio, 4)
            if quality_ratio < 0.5:
                indicators.append({
                    "indicator": "low_earnings_quality",
                    "value": round(quality_ratio, 4),
                    "threshold": 0.5,
                    "concern": "Low cash flow relative to earnings may indicate accrual manipulation",
                    "severity": "high" if quality_ratio < 0.25 else "medium",
                })
        
        # Asset Quality indicator
        if total_assets > 0:
            soft_assets_ratio = (current_assets + balance_sheet.get("intangible_assets", 0)) / total_assets
            calculated_ratios["soft_assets_ratio"] = round(soft_assets_ratio, 4)
            if soft_assets_ratio > 0.70:
                indicators.append({
                    "indicator": "high_soft_assets",
                    "value": round(soft_assets_ratio, 4),
                    "threshold": 0.70,
                    "concern": "High proportion of soft assets increases manipulation risk",
                    "severity": "low",
                })
        
        return {
            "status": "completed",
            "calculated_ratios": calculated_ratios,
            "indicators": indicators,
            "indicator_count": len(indicators),
            "high_severity_count": sum(1 for i in indicators if i.get("severity") == "high"),
            "interpretation": self._interpret_ratio_analysis(indicators),
        }

    def _analyze_trends(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze trends in financial data for manipulation indicators.
        
        Looks for:
        - Unusual growth patterns
        - Trend reversals near reporting dates
        - Smoothing patterns suggesting earnings management
        """
        historical_data = financial_data.get("historical_data", {})
        
        if not historical_data:
            return {
                "status": "no_historical_data",
                "message": "Historical data required for trend analysis",
            }
        
        anomalies = []
        trend_metrics = {}
        
        # Analyze each metric with historical data
        for metric_name, values in historical_data.items():
            if isinstance(values, list) and len(values) >= 3:
                analysis = self._analyze_single_trend(metric_name, values)
                trend_metrics[metric_name] = analysis
                
                if analysis.get("is_anomalous"):
                    anomalies.append({
                        "metric": metric_name,
                        "anomaly_type": analysis.get("anomaly_type"),
                        "details": analysis.get("anomaly_details"),
                    })
        
        return {
            "status": "completed",
            "metrics_analyzed": len(trend_metrics),
            "trend_metrics": trend_metrics,
            "anomalies_detected": anomalies,
            "anomaly_count": len(anomalies),
            "interpretation": self._interpret_trend_analysis(anomalies),
        }

    def _analyze_single_trend(self, metric_name: str, values: List[float]) -> Dict[str, Any]:
        """Analyze trend for a single metric."""
        n = len(values)
        
        # Calculate growth rates
        growth_rates = []
        for i in range(1, n):
            if values[i-1] != 0:
                growth = (values[i] - values[i-1]) / abs(values[i-1])
                growth_rates.append(growth)
        
        if not growth_rates:
            return {"status": "insufficient_data"}
        
        avg_growth = sum(growth_rates) / len(growth_rates)
        
        # Calculate variance in growth
        variance = sum((g - avg_growth) ** 2 for g in growth_rates) / len(growth_rates)
        std_dev = math.sqrt(variance) if variance > 0 else 0
        
        # Detect anomalies
        is_anomalous = False
        anomaly_type = None
        anomaly_details = None
        
        # Check for suspiciously smooth growth (may indicate manipulation)
        if std_dev < 0.01 and len(growth_rates) >= 4:
            is_anomalous = True
            anomaly_type = "suspiciously_smooth"
            anomaly_details = f"Growth rate variance is unusually low ({std_dev:.4f})"
        
        # Check for extreme growth spikes
        for i, growth in enumerate(growth_rates):
            if abs(growth) > 0.50:  # 50% change in one period
                is_anomalous = True
                anomaly_type = "extreme_change"
                anomaly_details = f"Period {i+1} shows {growth*100:.1f}% change"
                break
        
        # Check for hockey stick pattern (flat then sudden spike)
        if len(growth_rates) >= 3:
            early_avg = sum(growth_rates[:-1]) / (len(growth_rates) - 1)
            last_growth = growth_rates[-1]
            if abs(early_avg) < 0.05 and last_growth > 0.20:
                is_anomalous = True
                anomaly_type = "hockey_stick"
                anomaly_details = "Flat trend followed by sudden end-of-period spike"
        
        return {
            "current_value": values[-1],
            "prior_value": values[-2] if len(values) >= 2 else None,
            "average_growth_rate": round(avg_growth, 4),
            "growth_volatility": round(std_dev, 4),
            "is_anomalous": is_anomalous,
            "anomaly_type": anomaly_type,
            "anomaly_details": anomaly_details,
        }

    def _compare_to_peers(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare financial metrics to peer/industry benchmarks.
        """
        peer_data = financial_data.get("peer_data", {})
        income_stmt = financial_data.get("income_statement", {})
        balance_sheet = financial_data.get("balance_sheet", {})
        
        if not peer_data:
            return {
                "status": "no_peer_data",
                "message": "Peer comparison data required",
            }
        
        outliers = []
        comparisons = {}
        
        # Calculate company metrics and compare to peers
        revenue = income_stmt.get("revenue", 0)
        net_income = income_stmt.get("net_income", 0)
        total_assets = balance_sheet.get("total_assets", 1)
        
        # Net margin comparison
        if revenue > 0 and "industry_avg_margin" in peer_data:
            company_margin = net_income / revenue
            industry_margin = peer_data["industry_avg_margin"]
            deviation = company_margin - industry_margin
            
            comparisons["net_margin"] = {
                "company": round(company_margin, 4),
                "industry_avg": round(industry_margin, 4),
                "deviation": round(deviation, 4),
            }
            
            # Flag if more than 2x industry average (could be legitimate but worth checking)
            if company_margin > industry_margin * 2:
                outliers.append({
                    "metric": "net_margin",
                    "company_value": round(company_margin, 4),
                    "industry_value": round(industry_margin, 4),
                    "deviation_multiplier": round(company_margin / industry_margin, 2),
                    "concern": "Margin significantly exceeds industry average",
                })
        
        # Growth comparison
        if "company_growth" in financial_data and "industry_avg_growth" in peer_data:
            company_growth = financial_data["company_growth"]
            industry_growth = peer_data["industry_avg_growth"]
            
            comparisons["growth_rate"] = {
                "company": round(company_growth, 4),
                "industry_avg": round(industry_growth, 4),
                "deviation": round(company_growth - industry_growth, 4),
            }
            
            if company_growth > industry_growth * 3:
                outliers.append({
                    "metric": "growth_rate",
                    "company_value": round(company_growth, 4),
                    "industry_value": round(industry_growth, 4),
                    "concern": "Growth rate far exceeds industry norms",
                })
        
        return {
            "status": "completed",
            "comparisons": comparisons,
            "outliers_detected": outliers,
            "outlier_count": len(outliers),
            "interpretation": self._interpret_peer_comparison(outliers),
        }

    def _check_red_flags(
        self, 
        financial_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check for specific fraud red flags."""
        detected_flags = []
        
        income_stmt = financial_data.get("income_statement", {})
        balance_sheet = financial_data.get("balance_sheet", {})
        
        for flag_name in self.red_flags:
            flag_config = FRAUD_RED_FLAGS.get(flag_name)
            if not flag_config:
                continue
            
            is_triggered = False
            evidence = []
            
            if flag_name == "revenue_recognition_anomalies":
                # Check for high receivables growth vs revenue
                revenue = income_stmt.get("revenue", 0)
                ar = balance_sheet.get("accounts_receivable", 0)
                if revenue > 0 and ar / revenue > 0.25:
                    is_triggered = True
                    evidence.append(f"Receivables are {ar/revenue*100:.1f}% of revenue")
                
                # Check Benford's analysis if available
                benford = analysis_results.get("benfords_law", {})
                if benford.get("is_suspicious"):
                    is_triggered = True
                    evidence.append(f"Benford's Law shows {benford.get('conformity_level')}")
            
            elif flag_name == "unusual_expense_patterns":
                # Check ratio analysis for expense-related indicators
                ratio_analysis = analysis_results.get("ratio_analysis", {})
                for indicator in ratio_analysis.get("indicators", []):
                    if "margin" in indicator.get("indicator", "").lower():
                        is_triggered = True
                        evidence.append(indicator.get("concern"))
            
            elif flag_name == "inventory_discrepancies":
                inventory = balance_sheet.get("inventory", 0)
                cogs = income_stmt.get("cogs", income_stmt.get("cost_of_goods_sold", 0))
                if cogs > 0 and inventory > 0:
                    inventory_days = (inventory / cogs) * 365
                    if inventory_days > 180:  # More than 6 months of inventory
                        is_triggered = True
                        evidence.append(f"Inventory days outstanding: {inventory_days:.0f}")
            
            if is_triggered:
                detected_flags.append({
                    "flag": flag_name,
                    "description": flag_config["description"],
                    "evidence": evidence,
                    "severity": "high" if len(evidence) > 1 else "medium",
                })
        
        return detected_flags

    def _calculate_risk_score(self, fraud_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall fraud risk score."""
        score = 0
        max_score = 100
        factors = []
        
        # Benford's Law contribution (up to 30 points)
        benford = fraud_results["analysis_results"].get("benfords_law", {})
        if benford.get("status") == "completed":
            mad = benford.get("mean_absolute_deviation", 0)
            if mad < 0.006:
                benford_score = 0
            elif mad < 0.012:
                benford_score = 10
            elif mad < 0.015:
                benford_score = 20
            else:
                benford_score = 30
            score += benford_score
            if benford_score > 10:
                factors.append(f"Benford's Law deviation ({benford.get('conformity_level')})")
        
        # Ratio analysis contribution (up to 30 points)
        ratio = fraud_results["analysis_results"].get("ratio_analysis", {})
        high_severity = ratio.get("high_severity_count", 0)
        indicator_count = ratio.get("indicator_count", 0)
        ratio_score = min(30, high_severity * 15 + (indicator_count - high_severity) * 5)
        score += ratio_score
        if ratio_score > 10:
            factors.append(f"{indicator_count} ratio anomalies detected")
        
        # Trend analysis contribution (up to 20 points)
        trend = fraud_results["analysis_results"].get("trend_analysis", {})
        anomaly_count = trend.get("anomaly_count", 0)
        trend_score = min(20, anomaly_count * 10)
        score += trend_score
        if trend_score > 0:
            factors.append(f"{anomaly_count} trend anomalies detected")
        
        # Red flags contribution (up to 20 points)
        red_flag_count = len(fraud_results.get("red_flags_detected", []))
        red_flag_score = min(20, red_flag_count * 10)
        score += red_flag_score
        if red_flag_count > 0:
            factors.append(f"{red_flag_count} red flags detected")
        
        # Determine risk level
        if score < 20:
            risk_level = "Low"
            recommendation = "No significant fraud indicators detected. Continue standard monitoring."
        elif score < 40:
            risk_level = "Moderate"
            recommendation = "Some indicators warrant attention. Consider enhanced review."
        elif score < 60:
            risk_level = "Elevated"
            recommendation = "Multiple fraud indicators present. Detailed investigation recommended."
        else:
            risk_level = "High"
            recommendation = "Significant fraud risk identified. Immediate forensic review recommended."
        
        return {
            "overall_score": score,
            "max_score": max_score,
            "risk_level": risk_level,
            "risk_percentage": round(score / max_score * 100, 1),
            "contributing_factors": factors,
            "recommendation": recommendation,
        }

    def _extract_numbers(self, data: Any, numbers: List[float] = None) -> List[float]:
        """Recursively extract all numeric values from financial data."""
        if numbers is None:
            numbers = []
        
        if isinstance(data, dict):
            for value in data.values():
                self._extract_numbers(value, numbers)
        elif isinstance(data, list):
            for item in data:
                self._extract_numbers(item, numbers)
        elif isinstance(data, (int, float)) and data != 0:
            numbers.append(abs(data))
        
        return numbers

    def _get_first_digits(self, numbers: List[float]) -> List[int]:
        """Extract first digit from each number."""
        first_digits = []
        for num in numbers:
            if num > 0:
                # Get first significant digit
                while num < 1:
                    num *= 10
                first_digit = int(str(abs(num))[0])
                if 1 <= first_digit <= 9:
                    first_digits.append(first_digit)
        return first_digits

    def _interpret_benfords(
        self, mad: float, conformity: str, anomalies: List[Dict]
    ) -> str:
        """Generate interpretation of Benford's Law analysis."""
        if conformity in ["Close Conformity", "Acceptable Conformity"]:
            return "Data distribution conforms to Benford's Law. No manipulation indicators."
        elif conformity == "Marginally Acceptable":
            if anomalies:
                digits = [str(a["digit"]) for a in anomalies[:3]]
                return f"Minor deviations detected in digits {', '.join(digits)}. Worth monitoring."
            return "Marginal conformity to Benford's Law. Consider additional review."
        else:
            return f"Significant deviation from Benford's Law (MAD={mad:.4f}). Data may be manipulated."

    def _interpret_ratio_analysis(self, indicators: List[Dict]) -> str:
        """Generate interpretation of ratio analysis."""
        if not indicators:
            return "Financial ratios are within normal ranges."
        
        high_severity = [i for i in indicators if i.get("severity") == "high"]
        if high_severity:
            concerns = [i["indicator"] for i in high_severity[:2]]
            return f"High-severity concerns: {', '.join(concerns)}. Detailed review recommended."
        
        return f"{len(indicators)} ratio anomalies detected. Further analysis suggested."

    def _interpret_trend_analysis(self, anomalies: List[Dict]) -> str:
        """Generate interpretation of trend analysis."""
        if not anomalies:
            return "Historical trends appear normal and consistent."
        
        types = set(a.get("anomaly_type") for a in anomalies)
        if "hockey_stick" in types:
            return "Hockey stick pattern detected - sudden end-of-period spikes may indicate manipulation."
        elif "suspiciously_smooth" in types:
            return "Unusually smooth trends may indicate earnings management."
        
        return f"{len(anomalies)} trend anomalies detected across metrics."

    def _interpret_peer_comparison(self, outliers: List[Dict]) -> str:
        """Generate interpretation of peer comparison."""
        if not outliers:
            return "Performance metrics are within industry norms."
        
        metrics = [o["metric"] for o in outliers]
        return f"Company significantly deviates from peers on: {', '.join(metrics)}."
