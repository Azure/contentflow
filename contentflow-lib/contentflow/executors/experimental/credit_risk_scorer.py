"""
Credit Risk Scorer Executor.

Implements credit scoring models including Altman Z-score, Merton model,
and simplified CreditMetrics for credit risk assessment in financial workflows.
"""

import logging
import math
from typing import List, Union, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

from agent_framework import WorkflowContext
from contentflow.models import Content
from contentflow.executors.base import BaseExecutor

logger = logging.getLogger(__name__)


class CreditRatingScale(str, Enum):
    """Credit rating scales."""
    SP = "S&P"
    MOODYS = "Moody's"
    FITCH = "Fitch"


class TimeHorizon(str, Enum):
    """Time horizons for default probability."""
    ONE_YEAR = "1_year"
    THREE_YEAR = "3_year"
    FIVE_YEAR = "5_year"


# Mapping of Z-scores to credit ratings
ZSCORE_TO_RATING = {
    "SP": [
        (3.0, "AAA"), (2.7, "AA"), (2.4, "A"), (2.0, "BBB"),
        (1.8, "BB"), (1.5, "B"), (1.2, "CCC"), (0.0, "D")
    ],
    "Moody's": [
        (3.0, "Aaa"), (2.7, "Aa"), (2.4, "A"), (2.0, "Baa"),
        (1.8, "Ba"), (1.5, "B"), (1.2, "Caa"), (0.0, "C")
    ],
    "Fitch": [
        (3.0, "AAA"), (2.7, "AA"), (2.4, "A"), (2.0, "BBB"),
        (1.8, "BB"), (1.5, "B"), (1.2, "CCC"), (0.0, "D")
    ],
}

# Default probability by rating (1-year PD approximations)
DEFAULT_PROBABILITIES = {
    "AAA": 0.0001, "Aaa": 0.0001,
    "AA": 0.0002, "Aa": 0.0002,
    "A": 0.0005, 
    "BBB": 0.002, "Baa": 0.002,
    "BB": 0.01, "Ba": 0.01,
    "B": 0.05, 
    "CCC": 0.15, "Caa": 0.15,
    "CC": 0.25, "Ca": 0.25,
    "C": 0.35,
    "D": 1.0,
}


@dataclass
class ZScoreResult:
    """Result of Altman Z-score calculation."""
    z_score: float
    classification: str
    rating: str
    default_probability: float
    components: Dict[str, float]


@dataclass
class MertonResult:
    """Result of Merton model calculation."""
    distance_to_default: float
    default_probability: float
    asset_value: float
    asset_volatility: float
    rating: str


class CreditRiskScorerExecutor(BaseExecutor):
    """
    Calculate credit risk scores using multiple models.
    
    This executor implements credit scoring models including:
    - Altman Z-score (original, Z'-score for private firms, Z''-score for non-manufacturing)
    - Merton structural model (distance to default)
    - Simplified CreditMetrics approach
    
    Configuration (settings dict):
        - models (list): Credit risk models to use
          Options: "altman_z_score", "merton_model", "creditmetrics"
          Default: ["altman_z_score"]
        - default_probability (bool): Calculate probability of default
          Default: True
        - rating_scale (str): Rating scale for output
          Options: "S&P", "Moody's", "Fitch"
          Default: "S&P"
        - time_horizon (str): Time horizon for default probability
          Options: "1_year", "3_year", "5_year"
          Default: "1_year"
        - company_type (str): Type of company for Z-score variant
          Options: "public_manufacturing", "private", "non_manufacturing"
          Default: "public_manufacturing"
        - input_field (str): Field containing financial data
          Default: "financial_data"
        - output_field (str): Field name for credit risk results
          Default: "credit_risk_score"
    
    Expected Input Data Structure:
        {
            "income_statement": {
                "revenue": 1000000,
                "ebit": 200000,
                "retained_earnings": 150000
            },
            "balance_sheet": {
                "total_assets": 2000000,
                "current_assets": 500000,
                "current_liabilities": 300000,
                "total_liabilities": 800000,
                "total_equity": 1200000,
                "working_capital": 200000
            },
            "market_data": {  # Required for Merton model
                "market_cap": 5000000,
                "equity_volatility": 0.30,
                "risk_free_rate": 0.05
            }
        }
    
    Output:
        Content with added fields:
        - data[output_field]: Dictionary containing credit risk assessment
        - summary_data["credit_risk_status"]: Execution status
    
    Example:
        ```yaml
        - id: credit-risk-1
          type: credit_risk_scorer
          settings:
            models: ["altman_z_score", "merton_model"]
            default_probability: true
            rating_scale: "S&P"
            time_horizon: "1_year"
            output_field: "credit_risk_score"
        ```
    """
    
    def __init__(self, id: str, settings: Dict[str, Any] = None):
        super().__init__(id, settings)
        
        # Configuration
        self.models = self.get_setting("models", ["altman_z_score"])
        self.calculate_default_probability = self.get_setting("default_probability", True)
        self.rating_scale = self.get_setting("rating_scale", "S&P")
        self.time_horizon = self.get_setting("time_horizon", "1_year")
        self.company_type = self.get_setting("company_type", "public_manufacturing")
        self.input_field = self.get_setting("input_field", "financial_data")
        self.output_field = self.get_setting("output_field", "credit_risk_score")
        
        if self.debug_mode:
            logger.debug(
                f"CreditRiskScorerExecutor initialized: "
                f"models={self.models}, rating_scale={self.rating_scale}"
            )

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext[Union[Content, List[Content]], Union[Content, List[Content]]]
    ) -> Union[Content, List[Content]]:
        """Process financial data and calculate credit risk scores."""
        items_to_process = input if isinstance(input, list) else [input]
        
        for item in items_to_process:
            await self._process_single_content(item)
            
        return input

    async def _process_single_content(self, content: Content) -> None:
        """Process a single content item and calculate credit risk scores."""
        logger.info(f"Calculating credit risk for content {content.id}")
        
        try:
            # Extract financial data
            financial_data = self.try_extract_nested_field_from_content(
                content=content,
                field_path=self.input_field
            )
            
            if not financial_data:
                for alt_field in ["mapped_financials", "extracted_data", "data"]:
                    financial_data = content.data.get(alt_field)
                    if financial_data:
                        break
            
            if not financial_data:
                logger.warning(f"No financial data found in content {content.id}")
                content.data[self.output_field] = {"error": "No financial data found"}
                content.summary_data["credit_risk_status"] = "failed"
                return
            
            # Calculate credit risk using selected models
            risk_results = {
                "models_used": self.models,
                "rating_scale": self.rating_scale,
                "time_horizon": self.time_horizon,
                "model_results": {},
            }
            
            for model in self.models:
                if model == "altman_z_score":
                    risk_results["model_results"]["altman_z_score"] = self._calculate_altman_zscore(financial_data)
                elif model == "merton_model":
                    risk_results["model_results"]["merton_model"] = self._calculate_merton_model(financial_data)
                elif model == "creditmetrics":
                    risk_results["model_results"]["creditmetrics"] = self._calculate_creditmetrics(financial_data)
            
            # Generate composite score and rating
            risk_results["composite_assessment"] = self._generate_composite_assessment(risk_results["model_results"])
            
            # Store results
            content.data[self.output_field] = risk_results
            content.summary_data["credit_risk_status"] = "success"
            content.summary_data["credit_rating"] = risk_results["composite_assessment"].get("rating", "N/A")
            
        except Exception as e:
            logger.error(f"Error calculating credit risk for content {content.id}: {e}")
            content.data[self.output_field] = {"error": str(e)}
            content.summary_data["credit_risk_status"] = "failed"

    def _calculate_altman_zscore(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Altman Z-score.
        
        Original Z-score formula (for public manufacturing companies):
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
        
        Where:
        X1 = Working Capital / Total Assets
        X2 = Retained Earnings / Total Assets
        X3 = EBIT / Total Assets
        X4 = Market Value of Equity / Total Liabilities
        X5 = Sales / Total Assets
        """
        income_stmt = financial_data.get("income_statement", {})
        balance_sheet = financial_data.get("balance_sheet", {})
        market_data = financial_data.get("market_data", {})
        
        # Extract required values
        total_assets = balance_sheet.get("total_assets", 0)
        if total_assets == 0:
            return {"error": "Total assets is zero or missing"}
        
        working_capital = balance_sheet.get("working_capital")
        if working_capital is None:
            current_assets = balance_sheet.get("current_assets", 0)
            current_liabilities = balance_sheet.get("current_liabilities", 0)
            working_capital = current_assets - current_liabilities
        
        retained_earnings = income_stmt.get("retained_earnings", 
                           balance_sheet.get("retained_earnings", 0))
        ebit = income_stmt.get("ebit", income_stmt.get("operating_income", 0))
        revenue = income_stmt.get("revenue", income_stmt.get("sales", 0))
        total_liabilities = balance_sheet.get("total_liabilities", 0)
        
        # Market value of equity (use market cap if available, else book equity)
        market_value_equity = market_data.get("market_cap", 
                             balance_sheet.get("total_equity", 0))
        
        # Calculate components
        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit / total_assets
        x4 = market_value_equity / total_liabilities if total_liabilities > 0 else 0
        x5 = revenue / total_assets
        
        # Apply appropriate coefficients based on company type
        if self.company_type == "public_manufacturing":
            # Original Z-score
            z_score = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5
            zones = {"safe": 2.99, "grey_upper": 1.81}
        elif self.company_type == "private":
            # Z'-score for private firms (uses book value instead of market value)
            book_equity = balance_sheet.get("total_equity", 0)
            x4 = book_equity / total_liabilities if total_liabilities > 0 else 0
            z_score = 0.717*x1 + 0.847*x2 + 3.107*x3 + 0.420*x4 + 0.998*x5
            zones = {"safe": 2.90, "grey_upper": 1.23}
        else:  # non_manufacturing
            # Z''-score for non-manufacturing and emerging markets
            z_score = 6.56*x1 + 3.26*x2 + 6.72*x3 + 1.05*x4
            zones = {"safe": 2.60, "grey_upper": 1.10}
        
        # Determine classification
        if z_score > zones["safe"]:
            classification = "Safe Zone"
            risk_level = "Low"
        elif z_score > zones["grey_upper"]:
            classification = "Grey Zone"
            risk_level = "Medium"
        else:
            classification = "Distress Zone"
            risk_level = "High"
        
        # Map to credit rating
        rating = self._zscore_to_rating(z_score)
        
        # Calculate default probability
        default_prob = DEFAULT_PROBABILITIES.get(rating, 0.10)
        if self.time_horizon == "3_year":
            default_prob = 1 - (1 - default_prob) ** 3
        elif self.time_horizon == "5_year":
            default_prob = 1 - (1 - default_prob) ** 5
        
        return {
            "z_score": round(z_score, 4),
            "classification": classification,
            "risk_level": risk_level,
            "rating": rating,
            "default_probability": round(default_prob, 6),
            "default_probability_formatted": f"{default_prob * 100:.4f}%",
            "model_type": self.company_type,
            "components": {
                "X1_working_capital_ratio": round(x1, 4),
                "X2_retained_earnings_ratio": round(x2, 4),
                "X3_ebit_ratio": round(x3, 4),
                "X4_equity_to_liabilities": round(x4, 4),
                "X5_asset_turnover": round(x5, 4),
            },
            "interpretation": self._interpret_zscore(z_score, classification),
        }

    def _calculate_merton_model(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate distance to default using the Merton structural model.
        
        The Merton model treats equity as a call option on the firm's assets.
        Distance to Default (DD) = [ln(V/D) + (μ - σ²/2)T] / (σ√T)
        
        Probability of Default = N(-DD)
        """
        balance_sheet = financial_data.get("balance_sheet", {})
        market_data = financial_data.get("market_data", {})
        
        # Get required inputs
        market_cap = market_data.get("market_cap")
        equity_volatility = market_data.get("equity_volatility", 0.30)
        risk_free_rate = market_data.get("risk_free_rate", 0.05)
        total_liabilities = balance_sheet.get("total_liabilities", 0)
        
        if market_cap is None:
            return {"error": "Market cap required for Merton model"}
        
        if total_liabilities == 0:
            return {"error": "Total liabilities required for Merton model"}
        
        # Simplified Merton model calculation
        # Use iterative approach to solve for asset value and asset volatility
        
        # Initial estimate: asset value = equity + debt
        asset_value = market_cap + total_liabilities
        
        # Estimate asset volatility from equity volatility
        # σ_A ≈ σ_E * (E / V)
        equity_ratio = market_cap / asset_value
        asset_volatility = equity_volatility * equity_ratio
        
        # Time horizon
        T = 1.0  # 1 year
        if self.time_horizon == "3_year":
            T = 3.0
        elif self.time_horizon == "5_year":
            T = 5.0
        
        # Calculate distance to default
        try:
            d1 = (math.log(asset_value / total_liabilities) + 
                  (risk_free_rate + 0.5 * asset_volatility**2) * T) / \
                 (asset_volatility * math.sqrt(T))
            
            d2 = d1 - asset_volatility * math.sqrt(T)
            
            # Distance to Default
            distance_to_default = d2
            
            # Default probability using normal CDF approximation
            default_probability = self._normal_cdf(-distance_to_default)
            
        except (ValueError, ZeroDivisionError) as e:
            return {"error": f"Calculation error: {str(e)}"}
        
        # Map to credit rating
        rating = self._dd_to_rating(distance_to_default)
        
        return {
            "distance_to_default": round(distance_to_default, 4),
            "default_probability": round(default_probability, 6),
            "default_probability_formatted": f"{default_probability * 100:.4f}%",
            "implied_asset_value": round(asset_value, 2),
            "asset_volatility": round(asset_volatility, 4),
            "rating": rating,
            "time_horizon_years": T,
            "inputs": {
                "market_cap": market_cap,
                "total_liabilities": total_liabilities,
                "equity_volatility": equity_volatility,
                "risk_free_rate": risk_free_rate,
            },
            "interpretation": self._interpret_merton(distance_to_default, default_probability),
        }

    def _calculate_creditmetrics(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplified CreditMetrics approach.
        
        Uses transition probabilities and recovery rates to estimate credit risk.
        This is a simplified version that uses financial ratios as inputs.
        """
        income_stmt = financial_data.get("income_statement", {})
        balance_sheet = financial_data.get("balance_sheet", {})
        
        # Calculate key credit metrics
        total_assets = balance_sheet.get("total_assets", 1)
        total_liabilities = balance_sheet.get("total_liabilities", 0)
        total_equity = balance_sheet.get("total_equity", 0)
        ebit = income_stmt.get("ebit", income_stmt.get("operating_income", 0))
        interest_expense = income_stmt.get("interest_expense", 1)
        revenue = income_stmt.get("revenue", 0)
        
        # Calculate credit metrics
        leverage_ratio = total_liabilities / total_assets if total_assets > 0 else 0
        interest_coverage = ebit / interest_expense if interest_expense > 0 else 10
        profit_margin = (ebit / revenue) if revenue > 0 else 0
        
        # Score based on metrics (simplified scoring model)
        score = 0
        
        # Leverage score (lower is better)
        if leverage_ratio < 0.3:
            score += 30
        elif leverage_ratio < 0.5:
            score += 20
        elif leverage_ratio < 0.7:
            score += 10
        
        # Interest coverage score (higher is better)
        if interest_coverage > 5:
            score += 40
        elif interest_coverage > 3:
            score += 30
        elif interest_coverage > 1.5:
            score += 20
        elif interest_coverage > 1:
            score += 10
        
        # Profitability score
        if profit_margin > 0.20:
            score += 30
        elif profit_margin > 0.10:
            score += 20
        elif profit_margin > 0.05:
            score += 15
        elif profit_margin > 0:
            score += 5
        
        # Normalize to 100
        credit_score = min(score, 100)
        
        # Map score to rating
        rating = self._score_to_rating(credit_score)
        
        # Estimate default probability
        default_prob = DEFAULT_PROBABILITIES.get(rating, 0.10)
        
        # Expected loss calculation
        exposure = total_liabilities
        lgd = 0.45  # Typical loss given default
        expected_loss = exposure * default_prob * lgd
        
        return {
            "credit_score": credit_score,
            "rating": rating,
            "default_probability": round(default_prob, 6),
            "default_probability_formatted": f"{default_prob * 100:.4f}%",
            "expected_loss": round(expected_loss, 2),
            "loss_given_default": lgd,
            "metrics": {
                "leverage_ratio": round(leverage_ratio, 4),
                "interest_coverage": round(interest_coverage, 2),
                "profit_margin": round(profit_margin, 4),
            },
            "interpretation": self._interpret_creditmetrics(credit_score, rating),
        }

    def _zscore_to_rating(self, z_score: float) -> str:
        """Map Z-score to credit rating."""
        scale = ZSCORE_TO_RATING.get(self.rating_scale, ZSCORE_TO_RATING["SP"])
        for threshold, rating in scale:
            if z_score >= threshold:
                return rating
        return scale[-1][1]  # Lowest rating

    def _dd_to_rating(self, distance_to_default: float) -> str:
        """Map distance to default to credit rating."""
        # Higher DD = lower default risk = better rating
        if distance_to_default > 4.0:
            return "AAA" if self.rating_scale == "S&P" else "Aaa"
        elif distance_to_default > 3.5:
            return "AA" if self.rating_scale == "S&P" else "Aa"
        elif distance_to_default > 3.0:
            return "A"
        elif distance_to_default > 2.5:
            return "BBB" if self.rating_scale == "S&P" else "Baa"
        elif distance_to_default > 2.0:
            return "BB" if self.rating_scale == "S&P" else "Ba"
        elif distance_to_default > 1.5:
            return "B"
        elif distance_to_default > 1.0:
            return "CCC" if self.rating_scale == "S&P" else "Caa"
        else:
            return "CC" if self.rating_scale == "S&P" else "Ca"

    def _score_to_rating(self, credit_score: float) -> str:
        """Map credit score to rating."""
        if credit_score >= 90:
            return "AAA" if self.rating_scale == "S&P" else "Aaa"
        elif credit_score >= 80:
            return "AA" if self.rating_scale == "S&P" else "Aa"
        elif credit_score >= 70:
            return "A"
        elif credit_score >= 60:
            return "BBB" if self.rating_scale == "S&P" else "Baa"
        elif credit_score >= 50:
            return "BB" if self.rating_scale == "S&P" else "Ba"
        elif credit_score >= 40:
            return "B"
        elif credit_score >= 30:
            return "CCC" if self.rating_scale == "S&P" else "Caa"
        else:
            return "CC" if self.rating_scale == "S&P" else "Ca"

    def _normal_cdf(self, x: float) -> float:
        """Approximate cumulative distribution function of standard normal distribution."""
        # Approximation using error function
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _interpret_zscore(self, z_score: float, classification: str) -> str:
        """Generate interpretation of Z-score result."""
        if classification == "Safe Zone":
            return f"Z-score of {z_score:.2f} indicates low bankruptcy risk. Company is financially stable."
        elif classification == "Grey Zone":
            return f"Z-score of {z_score:.2f} indicates moderate risk. Further analysis recommended."
        else:
            return f"Z-score of {z_score:.2f} indicates elevated bankruptcy risk. Immediate attention required."

    def _interpret_merton(self, dd: float, default_prob: float) -> str:
        """Generate interpretation of Merton model result."""
        if dd > 3:
            return f"Distance to default of {dd:.2f} indicates very low default risk."
        elif dd > 2:
            return f"Distance to default of {dd:.2f} indicates low to moderate default risk."
        elif dd > 1:
            return f"Distance to default of {dd:.2f} indicates elevated default risk. Monitor closely."
        else:
            return f"Distance to default of {dd:.2f} indicates high default risk. Immediate action recommended."

    def _interpret_creditmetrics(self, score: float, rating: str) -> str:
        """Generate interpretation of CreditMetrics result."""
        if score >= 70:
            return f"Credit score of {score} ({rating}) indicates strong creditworthiness."
        elif score >= 50:
            return f"Credit score of {score} ({rating}) indicates adequate credit quality."
        else:
            return f"Credit score of {score} ({rating}) indicates elevated credit risk."

    def _generate_composite_assessment(self, model_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate composite credit assessment from all models."""
        ratings = []
        default_probs = []
        
        for model_name, result in model_results.items():
            if "error" not in result:
                if "rating" in result:
                    ratings.append(result["rating"])
                if "default_probability" in result:
                    default_probs.append(result["default_probability"])
        
        if not ratings:
            return {"error": "No valid model results available"}
        
        # Use the most conservative (worst) rating
        rating_order = ["AAA", "Aaa", "AA", "Aa", "A", "BBB", "Baa", 
                       "BB", "Ba", "B", "CCC", "Caa", "CC", "Ca", "C", "D"]
        
        worst_rating = ratings[0]
        for rating in ratings:
            if rating in rating_order:
                if rating_order.index(rating) > rating_order.index(worst_rating):
                    worst_rating = rating
        
        # Average default probability
        avg_default_prob = sum(default_probs) / len(default_probs) if default_probs else 0
        
        # Risk classification
        if avg_default_prob < 0.01:
            risk_class = "Investment Grade"
        elif avg_default_prob < 0.05:
            risk_class = "Non-Investment Grade"
        else:
            risk_class = "High Yield / Distressed"
        
        return {
            "rating": worst_rating,
            "rating_scale": self.rating_scale,
            "average_default_probability": round(avg_default_prob, 6),
            "default_probability_formatted": f"{avg_default_prob * 100:.4f}%",
            "risk_classification": risk_class,
            "models_aggregated": len(model_results),
            "confidence": "High" if len(model_results) >= 2 else "Medium",
            "recommendation": self._get_credit_recommendation(worst_rating, avg_default_prob),
        }

    def _get_credit_recommendation(self, rating: str, default_prob: float) -> str:
        """Generate credit recommendation."""
        investment_grade = ["AAA", "Aaa", "AA", "Aa", "A", "BBB", "Baa"]
        
        if rating in investment_grade:
            return "Credit risk is within acceptable bounds. Standard monitoring recommended."
        elif default_prob < 0.10:
            return "Elevated credit risk. Enhanced monitoring and possible collateral requirements."
        else:
            return "High credit risk. Consider additional risk mitigation measures or credit enhancement."
