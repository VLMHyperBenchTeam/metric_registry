import pytest
import json
from typing import Any
from pydantic import BaseModel
from metric_registry import (
    MetricRegistry, 
    BaseMetric, 
    MetricResult, 
    register_metric, 
    default_registry,
    MetricEvaluator,
    StructuralFidelityMetric
)

class MockMetric(BaseMetric):
    def compute(self, prediction: Any, target: Any, **kwargs) -> MetricResult:
        return MetricResult(value=1.0, name=self.name, version=self.version)

def test_registry_registration():
    registry = MetricRegistry()
    
    @registry.register(name="test_metric", version="1.0.0")
    class TestMetric(BaseMetric):
        def compute(self, prediction, target, **kwargs):
            return MetricResult(value=1.0, name="test_metric", version="1.0.0")
            
    assert registry.get("test_metric", "1.0.0") == TestMetric
    assert registry.get("test_metric") == TestMetric

def test_registry_versioning():
    registry = MetricRegistry()
    
    @registry.register(name="v_metric", version="1.0.0")
    class V1(BaseMetric):
        def compute(self, p, t, **kwargs): pass

    @registry.register(name="v_metric", version="2.0.0")
    class V2(BaseMetric):
        def compute(self, p, t, **kwargs): pass
        
    assert registry.get("v_metric", "1.0.0") == V1
    assert registry.get("v_metric", "2.0.0") == V2
    assert registry.get("v_metric") == V2 # Latest

def test_registry_backends():
    registry = MetricRegistry()
    
    @registry.register(name="m", version="1.0.0", backend="b1")
    class M1(BaseMetric):
        def compute(self, p, t, **kwargs): pass

    @registry.register(name="m", version="1.0.0", backend="b2")
    class M2(BaseMetric):
        def compute(self, p, t, **kwargs): pass
        
    assert registry.get("m", backend="b1") == M1
    assert registry.get("m", backend="b2") == M2
    
    # Default backend logic
    @registry.register(name="m", version="1.0.0", backend="native")
    class M_Native(BaseMetric):
        def compute(self, p, t, **kwargs): pass
        
    assert registry.get("m") == M_Native # native is preferred
    
    # Fallback logic
    registry2 = MetricRegistry()
    @registry2.register(name="m", version="1.0.0", backend="custom")
    class M_Custom(BaseMetric):
        def compute(self, p, t, **kwargs): pass
    
    assert registry2.get("m") == M_Custom # only one available

def test_evaluator_with_backend():
    evaluator = MetricEvaluator()
    
    @register_metric(name="multi_b", version="1.0.0", backend="b1")
    class MB1(BaseMetric):
        def __init__(self):
            super().__init__("multi_b", "1.0.0")
        def compute(self, p, t, **kwargs):
            return MetricResult(value=1.0, name="multi_b", version="1.0.0", metadata={"b": "b1"})

    @register_metric(name="multi_b", version="1.0.0", backend="b2")
    class MB2(BaseMetric):
        def __init__(self):
            super().__init__("multi_b", "1.0.0")
        def compute(self, p, t, **kwargs):
            return MetricResult(value=2.0, name="multi_b", version="1.0.0", metadata={"b": "b2"})

    metrics_config = [
        {"name": "multi_b", "backend": "b1"},
        {"name": "multi_b", "backend": "b2"}
    ]
    
    # 1. No filter - compute all
    res_all = evaluator.evaluate_item("p", "t", metrics_config)
    assert len(res_all) == 1 # Overwritten in result dict by name
    
    # 2. Filter by b1
    res_b1 = evaluator.evaluate_item("p", "t", metrics_config, active_backend="b1")
    assert res_b1["multi_b"].metadata["b"] == "b1"
    
    # 3. Filter by b2
    res_b2 = evaluator.evaluate_item("p", "t", metrics_config, active_backend="b2")
    assert res_b2["multi_b"].metadata["b"] == "b2"

def test_structural_fidelity():
    class SimpleModel(BaseModel):
        answer: str
        score: int

    metric = StructuralFidelityMetric()
    
    # Valid JSON string
    res1 = metric.compute(prediction='{"answer": "test", "score": 10}', schema=SimpleModel)
    assert res1.value == 1.0
    
    # Invalid JSON string
    res2 = metric.compute(prediction='{"answer": "test"}', schema=SimpleModel)
    assert res2.value == 0.0
    assert "validation error" in res2.metadata["error"]

    # Not a JSON
    res3 = metric.compute(prediction='not a json', schema=SimpleModel)
    assert res3.value == 0.0
    assert "JSON Decode Error" in res3.metadata["error"]

def test_evaluator():
    evaluator = MetricEvaluator()
    
    # Register a dummy metric in default registry for test
    @register_metric(name="dummy", version="1.0.0")
    class DummyMetric(BaseMetric):
        def compute(self, prediction, target, **kwargs):
            return MetricResult(value=float(prediction == target), name="dummy", version="1.0.0")

    metrics_config = [
        {"name": "dummy", "version": "1.0.0"},
        {"name": "structural_fidelity", "version": "1.0.0"}
    ]
    
    class MyModel(BaseModel):
        text: str

    results = evaluator.evaluate_item(
        prediction='{"text": "hello"}',
        target='{"text": "hello"}', # target is not used by dummy in this way but for demo
        metrics=metrics_config,
        schema=MyModel
    )
    
    assert "dummy" in results
    assert "structural_fidelity" in results
    assert results["structural_fidelity"].value == 1.0