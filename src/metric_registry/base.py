from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

class MetricResult(BaseModel):
    """
    Standard structure for metric results.
    """
    value: float
    name: str
    version: str
    metadata: Optional[Dict[str, Any]] = None

class BaseMetric(ABC):
    """
    Abstract base class for all metrics.
    """
    def __init__(self, name: str = "base", version: str = "0.1.0"):
        self.name = name
        self.version = version

    @abstractmethod
    def compute(self, prediction: Any, target: Any, **kwargs) -> MetricResult:
        """
        Compute the metric value.
        """
        pass