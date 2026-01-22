import importlib
import functools
import logging
from typing import Any, Dict, List, Optional, Type, Union, Callable
from .base import BaseMetric

class MetricRegistry:
    """
    Registry for metrics. Supports dynamic loading, versioning and backends (namespaces).
    """
    def __init__(self):
        # Structure: {metric_name: {backend: {version: metric_cls}}}
        self._metrics: Dict[str, Dict[str, Dict[str, Type[BaseMetric]]]] = {}
        # Structure: {backend_name: {"dependencies": [str], ...}}
        self._backend_metadata: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, version: str, backend: str = "native"):
        """
        Decorator to register a metric class.
        """
        def decorator(cls: Type[BaseMetric]):
            if name not in self._metrics:
                self._metrics[name] = {}
            if backend not in self._metrics[name]:
                self._metrics[name][backend] = {}
            self._metrics[name][backend][version] = cls
            return cls
        return decorator

    def register_backend(self, name: str, dependencies: Optional[List[str]] = None, **metadata):
        """
        Register metadata for a backend (e.g., dependencies).
        """
        self._backend_metadata[name] = {
            "dependencies": dependencies or [],
            **metadata
        }

    def get_backend_info(self, name: str) -> Dict[str, Any]:
        return self._backend_metadata.get(name, {"dependencies": []})

    def get(self, name: str, version: Optional[str] = None, backend: Optional[str] = None) -> Type[BaseMetric]:
        """
        Retrieves a metric class by name, version and backend.
        If backend is not provided, tries 'native', then any available.
        If version is not provided, returns the latest registered version.
        Supports dynamic loading if name is a full path.
        """
        if "." in name and name not in self._metrics:
            return self._dynamic_load(name)

        if name not in self._metrics:
            raise ValueError(f"Metric '{name}' not found in registry")

        backends = self._metrics[name]
        
        # Select backend
        selected_backend = backend
        if not selected_backend:
            if "native" in backends:
                selected_backend = "native"
            else:
                # Fallback to the first available backend
                selected_backend = next(iter(backends.keys()))
        
        if selected_backend not in backends:
            raise ValueError(f"Backend '{selected_backend}' for metric '{name}' not found. Available: {list(backends.keys())}")

        versions = backends[selected_backend]
        if version:
            if version not in versions:
                raise ValueError(f"Version '{version}' for metric '{name}' (backend: {selected_backend}) not found. Available: {list(versions.keys())}")
            return versions[version]
        
        # Return latest version (lexicographical sort as fallback)
        latest_version = sorted(versions.keys())[-1]
        return versions[latest_version]

    def _dynamic_load(self, path: str) -> Type[BaseMetric]:
        try:
            module_name, class_name = path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
            return cls
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Could not dynamically load metric from {path}: {e}")

    def list_metrics(self) -> List[str]:
        result = []
        for name, backends in self._metrics.items():
            for backend, versions in backends.items():
                for version in versions.keys():
                    result.append(f"{name} [{backend}] (v{version})")
        return result

# Global registry instance
default_registry = MetricRegistry()

def register_metric(name: str, version: str, backend: str = "native"):
    return default_registry.register(name, version, backend)

def register_backend(name: str, dependencies: Optional[List[str]] = None, **metadata):
    return default_registry.register_backend(name, dependencies, **metadata)