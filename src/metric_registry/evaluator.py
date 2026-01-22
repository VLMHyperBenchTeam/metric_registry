from typing import Any, Dict, List, Optional, Type
import pandas as pd
from .registry import default_registry, MetricRegistry
from .base import BaseMetric, MetricResult
from pydantic import BaseModel

class MetricEvaluator:
    """
    Orchestrates the evaluation process using registered metrics.
    """
    def __init__(self, registry: MetricRegistry = default_registry):
        self.registry = registry

    def evaluate_item(
        self,
        prediction: Any,
        target: Any,
        metrics: List[Dict[str, Any]],
        schema: Optional[Type[BaseModel]] = None,
        active_backend: Optional[str] = None
    ) -> Dict[str, MetricResult]:
        """
        Evaluate a single item against multiple metrics.
        metrics format: [{"name": "anls", "version": "1.0.0", "backend": "evalscope", "params": {}}, ...]
        
        Args:
            prediction: Model output.
            target: Ground truth.
            metrics: List of metric configurations.
            schema: Pydantic model for structural validation.
            active_backend: If set, only metrics from this backend will be computed.
        """
        results = {}
        
        # Check structural fidelity first if requested
        structural_metric_config = next((m for m in metrics if m["name"] == "structural_fidelity"), None)
        if structural_metric_config:
            # Filter by backend if active_backend is set
            config_backend = structural_metric_config.get("backend")
            if not active_backend or not config_backend or config_backend == active_backend:
                sf_metric_cls = self.registry.get(
                    "structural_fidelity",
                    structural_metric_config.get("version"),
                    backend=config_backend
                )
                sf_metric = sf_metric_cls()
                sf_result = sf_metric.compute(prediction, target, schema=schema)
                results["structural_fidelity"] = sf_result

        for m_config in metrics:
            name = m_config["name"]
            if name == "structural_fidelity":
                continue
            
            config_backend = m_config.get("backend")
            
            # Skip if we are filtering by backend and this metric doesn't match
            if active_backend and config_backend and config_backend != active_backend:
                continue
                
            version = m_config.get("version")
            params = m_config.get("params", {})
            
            try:
                metric_cls = self.registry.get(name, version, backend=config_backend)
                metric_instance = metric_cls()
                result = metric_instance.compute(prediction, target, **params)
                results[name] = result
            except Exception as e:
                # Log error and provide a failed metric result
                results[name] = MetricResult(
                    value=0.0,
                    name=name,
                    version=version or "unknown",
                    metadata={"error": str(e)}
                )
        
        return results

    def aggregate_results(self, results: List[Dict[str, MetricResult]], strategy: str = "general") -> Dict[str, float]:
        """
        Aggregate results from multiple items.
        Strategies: general (mean)
        """
        if not results:
            return {}

        df = pd.DataFrame([{k: v.value for k, v in item.items()} for item in results])
        
        if strategy == "general":
            return df.mean().to_dict()
        
        return {}