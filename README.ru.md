# Metric Registry

[English](README.md) | [Русский](README.ru.md)

Динамический реестр метрик для VLMHyperBench. Поддерживает dot notation для загрузки пользовательских метрик.

## Установка

```bash
pip install metric_registry
```

## Использование

```python
from metric_registry.registry import MetricRegistry

registry = MetricRegistry()
# Динамическая загрузка
metric_cls = registry.get("my_custom_package.MyMetric")
```
