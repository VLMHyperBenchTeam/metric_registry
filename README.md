# Metric Registry

[English](README.md) | [Русский](README.ru.md)

Dynamic metric registry for VLMHyperBench. Supports dot notation for loading custom metrics.

## Installation

```bash
pip install metric_registry
```

## Usage

```python
from metric_registry.registry import MetricRegistry

registry = MetricRegistry()
# Dynamic load
metric_cls = registry.get("my_custom_package.MyMetric")
```
