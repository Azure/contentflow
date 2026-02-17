"""Cross-document field aggregator executor for deterministic field aggregation."""

import logging
import statistics
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from agent_framework import WorkflowContext

from .cross_document_executor import CrossDocumentExecutor
from ..models import Content

logger = logging.getLogger("contentflow.executors.cross_document_field_aggregator")


class CrossDocumentFieldAggregatorExecutor(CrossDocumentExecutor):
    """
    Aggregate specific fields across all documents in a set.
    
    Performs deterministic (non-AI) calculations like sum, average, min, max,
    period-over-period deltas, percentage changes, and trend detection across
    documents in a document set.
    
    Configuration (settings dict):
        - aggregations (list[dict]): List of aggregation definitions. Each dict:
            - field_path (str): Dot-separated path to the field in each document
              (e.g., "data.financial_metrics.revenue")
            - operations (list[str]): Operations to perform.
              Options: "sum", "avg", "min", "max", "count",
                       "delta", "pct_change", "trend", "values"
            - output_key (str): Key name for this aggregation's results.
              Default: last segment of field_path
        - output_key (str): Top-level key in Content.data for all aggregation results.
          Default: "field_aggregations"
        
        Also settings from CrossDocumentExecutor and BaseExecutor apply.
    
    Example:
        ```yaml
        - id: aggregate_metrics
          type: cross_document_field_aggregator
          settings:
            aggregations:
              - field_path: "data.financial_metrics.revenue"
                operations: [sum, avg, delta, pct_change, trend]
                output_key: "revenue_analysis"
              - field_path: "data.financial_metrics.net_income"
                operations: [sum, avg, min, max, delta, pct_change]
                output_key: "net_income_analysis"
              - field_path: "data.financial_metrics.profit_margin"
                operations: [avg, min, max, trend]
                output_key: "margin_analysis"
            output_key: "field_aggregations"
        ```
    
    Input:
        Content with consolidated document set data (from DocumentSetCollectorExecutor)
        
    Output:
        Content with data[output_key] containing aggregation results for each
        configured field, with computed metrics and per-document values.
    
    Supported operations:
        - sum: Sum of all numeric values
        - avg: Average of all numeric values
        - min: Minimum value
        - max: Maximum value
        - count: Count of non-None values
        - delta: Period-over-period absolute changes
        - pct_change: Period-over-period percentage changes
        - trend: Linear trend direction ("increasing", "decreasing", "stable", "mixed")
        - values: Raw list of (role, value) pairs
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Override default output_key for aggregator
        if settings and "output_key" not in settings:
            settings["output_key"] = "field_aggregations"
        elif not settings:
            settings = {"output_key": "field_aggregations"}
        
        super().__init__(
            id=id,
            settings=settings,
            **kwargs
        )
        
        self.aggregations = self.get_setting("aggregations", default=[])
        
        if not self.aggregations:
            logger.warning(
                f"{self.id}: No aggregations configured. "
                f"This executor will produce empty results."
            )
        
        # Validate aggregation definitions
        for agg in self.aggregations:
            if not isinstance(agg, dict):
                raise ValueError(
                    f"{self.id}: Each aggregation must be a dict with "
                    f"'field_path' and 'operations' keys"
                )
            if "field_path" not in agg:
                raise ValueError(
                    f"{self.id}: Aggregation missing required 'field_path'"
                )
            if "operations" not in agg:
                raise ValueError(
                    f"{self.id}: Aggregation for '{agg['field_path']}' "
                    f"missing required 'operations'"
                )
            
            valid_ops = {"sum", "avg", "min", "max", "count", "delta", "pct_change", "trend", "values"}
            invalid_ops = set(agg["operations"]) - valid_ops
            if invalid_ops:
                raise ValueError(
                    f"{self.id}: Invalid operations {invalid_ops} for "
                    f"'{agg['field_path']}'. Valid: {valid_ops}"
                )
        
        if self.debug_mode:
            logger.debug(
                f"CrossDocumentFieldAggregatorExecutor {self.id} initialized: "
                f"{len(self.aggregations)} aggregation(s) configured"
            )
    
    async def process_document_set(
        self,
        set_data: Dict[str, Any],
        content: Content,
        ctx: WorkflowContext
    ) -> Content:
        """
        Run deterministic field aggregations across the document set.
        
        Args:
            set_data: Consolidated document set data
            content: Parent Content item
            ctx: Workflow context
            
        Returns:
            Content with aggregation results in data[output_key]
        """
        aggregation_results = {}
        
        for agg_def in self.aggregations:
            field_path = agg_def["field_path"]
            operations = agg_def["operations"]
            output_key = agg_def.get("output_key", field_path.split(".")[-1])
            
            # Extract values across all documents
            values_with_roles = self.extract_field_across_documents(set_data, field_path)
            
            # Compute requested operations
            result = self._compute_aggregations(
                values_with_roles, operations, field_path
            )
            
            aggregation_results[output_key] = result
            
            if self.debug_mode:
                logger.debug(
                    f"{self.id}: Aggregated '{field_path}' -> '{output_key}': "
                    f"{len(values_with_roles)} values, {len(operations)} operations"
                )
        
        # Store results in content
        content.data[self.output_key] = {
            "type": "field_aggregations",
            "set_id": set_data.get("set_id", ""),
            "set_name": set_data.get("set_name", ""),
            "total_documents": set_data.get("total_documents", 0),
            "aggregations": aggregation_results,
            "computed_at": datetime.now().isoformat(),
        }
        
        return content
    
    def _compute_aggregations(
        self,
        values_with_roles: List[Tuple[str, Any]],
        operations: List[str],
        field_path: str
    ) -> Dict[str, Any]:
        """
        Compute the requested aggregation operations on the values.
        
        Args:
            values_with_roles: List of (role, value) tuples
            operations: List of operation names to compute
            field_path: Original field path (for logging)
            
        Returns:
            Dict with operation results
        """
        result = {
            "field_path": field_path,
            "document_count": len(values_with_roles),
        }
        
        # Extract numeric values (filter out None and non-numeric)
        numeric_values = []
        roles_with_values = []
        for role, value in values_with_roles:
            if value is not None:
                try:
                    numeric_val = float(value)
                    numeric_values.append(numeric_val)
                    roles_with_values.append((role, numeric_val))
                except (ValueError, TypeError):
                    logger.warning(
                        f"{self.id}: Non-numeric value for '{field_path}' "
                        f"in document '{role}': {value}"
                    )
        
        if "values" in operations:
            result["values"] = [
                {"role": role, "value": value}
                for role, value in values_with_roles
            ]
        
        if "count" in operations:
            result["count"] = len(numeric_values)
        
        if not numeric_values:
            # No numeric values to aggregate
            for op in operations:
                if op not in ("values", "count"):
                    result[op] = None
            return result
        
        if "sum" in operations:
            result["sum"] = sum(numeric_values)
        
        if "avg" in operations:
            result["avg"] = statistics.mean(numeric_values)
        
        if "min" in operations:
            result["min"] = min(numeric_values)
        
        if "max" in operations:
            result["max"] = max(numeric_values)
        
        if "delta" in operations:
            result["delta"] = self._compute_deltas(roles_with_values)
        
        if "pct_change" in operations:
            result["pct_change"] = self._compute_pct_changes(roles_with_values)
        
        if "trend" in operations:
            result["trend"] = self._detect_trend(numeric_values)
        
        return result
    
    def _compute_deltas(
        self, values: List[Tuple[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        Compute period-over-period absolute changes.
        
        Args:
            values: Ordered list of (role, numeric_value) tuples
            
        Returns:
            List of delta entries between consecutive periods
        """
        deltas = []
        for i in range(1, len(values)):
            prev_role, prev_val = values[i - 1]
            curr_role, curr_val = values[i]
            delta = curr_val - prev_val
            deltas.append({
                "from": prev_role,
                "to": curr_role,
                "delta": delta,
            })
        return deltas
    
    def _compute_pct_changes(
        self, values: List[Tuple[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        Compute period-over-period percentage changes.
        
        Args:
            values: Ordered list of (role, numeric_value) tuples
            
        Returns:
            List of percentage change entries between consecutive periods
        """
        changes = []
        for i in range(1, len(values)):
            prev_role, prev_val = values[i - 1]
            curr_role, curr_val = values[i]
            
            if prev_val != 0:
                pct = ((curr_val - prev_val) / abs(prev_val)) * 100
            else:
                pct = None  # Cannot compute % change from zero
            
            changes.append({
                "from": prev_role,
                "to": curr_role,
                "pct_change": round(pct, 2) if pct is not None else None,
            })
        return changes
    
    def _detect_trend(self, values: List[float]) -> Dict[str, Any]:
        """
        Detect the overall trend direction using simple linear analysis.
        
        Args:
            values: List of numeric values in order
            
        Returns:
            Dict with trend direction and confidence
        """
        if len(values) < 2:
            return {"direction": "insufficient_data", "confidence": 0.0}
        
        # Simple trend: count increases vs decreases
        increases = 0
        decreases = 0
        for i in range(1, len(values)):
            if values[i] > values[i - 1]:
                increases += 1
            elif values[i] < values[i - 1]:
                decreases += 1
        
        total_changes = increases + decreases
        if total_changes == 0:
            return {"direction": "stable", "confidence": 1.0}
        
        # Determine direction
        if increases == total_changes:
            direction = "increasing"
            confidence = 1.0
        elif decreases == total_changes:
            direction = "decreasing"
            confidence = 1.0
        elif increases > decreases:
            direction = "mostly_increasing"
            confidence = round(increases / total_changes, 2)
        elif decreases > increases:
            direction = "mostly_decreasing"
            confidence = round(decreases / total_changes, 2)
        else:
            direction = "mixed"
            confidence = 0.5
        
        # Calculate overall change
        overall_change = values[-1] - values[0]
        overall_pct = (
            round(((values[-1] - values[0]) / abs(values[0])) * 100, 2)
            if values[0] != 0 else None
        )
        
        return {
            "direction": direction,
            "confidence": confidence,
            "overall_change": overall_change,
            "overall_pct_change": overall_pct,
            "periods_analyzed": len(values),
        }
