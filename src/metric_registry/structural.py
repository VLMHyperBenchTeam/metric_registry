import json
import logging
from typing import Any, Dict, Optional, Type, Union
from pydantic import BaseModel, ValidationError
from .base import BaseMetric, MetricResult
from .registry import register_metric

logger = logging.getLogger(__name__)

@register_metric(name="structural_fidelity", version="1.0.0")
class StructuralFidelityMetric(BaseMetric):
    """
    Metric to validate if the prediction matches a given Pydantic model or JSON schema.
    Returns 1.0 if valid, 0.0 otherwise.
    """
    def __init__(self, name: str = "structural_fidelity", version: str = "1.0.0"):
        super().__init__(name, version)

    def compute(self, prediction: Any, target: Any = None, schema: Optional[Type[BaseModel]] = None, **kwargs) -> MetricResult:
        """
        Args:
            prediction: The string or dict to validate.
            target: Not used for this metric.
            schema: The Pydantic model class to validate against.
        """
        is_valid = 0.0
        error_msg = None
        
        data = prediction
        if isinstance(prediction, str):
            try:
                data = json.loads(prediction)
            except json.JSONDecodeError as e:
                error_msg = f"JSON Decode Error: {e}"
                return MetricResult(
                    value=0.0,
                    name=self.name,
                    version=self.version,
                    metadata={"error": error_msg}
                )

        if schema:
            try:
                schema.model_validate(data)
                is_valid = 1.0
            except ValidationError as e:
                error_msg = str(e)
                is_valid = 0.0
        else:
            # If no schema provided, just check if it's a valid JSON (already done above)
            is_valid = 1.0

        return MetricResult(
            value=is_valid,
            name=self.name,
            version=self.version,
            metadata={"error": error_msg} if error_msg else None
        )