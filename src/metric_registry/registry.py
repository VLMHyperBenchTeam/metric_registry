import importlib
from typing import Any, Dict, List

class MetricRegistry:
    """
    Registry for metrics. Supports dynamic loading of metric classes.
    """
    def __init__(self):
        self._metrics = {}

    def register(self, name: str, metric_cls: Any):
        self._metrics[name] = metric_cls

    def get(self, name: str) -> Any:
        """
        Retrieves a metric class by name. 
        Supports dynamic loading if name is a full path (e.g., 'my_pkg.MyMetric').
        """
        if "." in name and name not in self._metrics:
            try:
                module_name, class_name = name.rsplit(".", 1)
                module = importlib.import_module(module_name)
                cls = getattr(module, class_name)
                return cls
            except (ImportError, AttributeError) as e:
                raise ValueError(f"Could not dynamically load metric {name}: {e}")

        if name not in self._metrics:
            raise ValueError(f"Metric {name} not found in registry")
        return self._metrics[name]

    def list_metrics(self) -> List[str]:
        return list(self._metrics.keys())
