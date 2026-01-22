from typing import Any, Dict, Optional
from .base import BaseMetric, MetricResult
from .registry import register_metric

@register_metric(name="latency", version="1.0.0")
class LatencyMetric(BaseMetric):
    """
    Metric for measuring latency (total time).
    Usually prediction contains the measurement.
    """
    def __init__(self, name: str = "latency", version: str = "1.0.0"):
        super().__init__(name, version)

    def compute(self, prediction: Any, target: Any = None, **kwargs) -> MetricResult:
        # Expecting prediction to be the latency value (float)
        try:
            val = float(prediction)
            return MetricResult(value=val, name=self.name, version=self.version)
        except (TypeError, ValueError):
            return MetricResult(value=0.0, name=self.name, version=self.version, metadata={"error": "Invalid latency value"})

@register_metric(name="peak_memory", version="1.0.0")
class PeakMemoryMetric(BaseMetric):
    """
    Metric for peak VRAM/RAM consumption.
    """
    def __init__(self, name: str = "peak_memory", version: str = "1.0.0"):
        super().__init__(name, version)

    def compute(self, prediction: Any, target: Any = None, **kwargs) -> MetricResult:
        try:
            val = float(prediction)
            return MetricResult(value=val, name=self.name, version=self.version)
        except (TypeError, ValueError):
            return MetricResult(value=0.0, name=self.name, version=self.version, metadata={"error": "Invalid memory value"})