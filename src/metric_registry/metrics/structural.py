import json
from typing import Any, Dict
from ..base import BaseMetric, MetricResult

class StructuralFidelity(BaseMetric):
    """
    Metric to check if the output is valid JSON and matches the expected structure.
    """
    def __init__(self, name: str = "structural_fidelity", version: str = "0.1.0"):
        super().__init__(name, version)

    def compute(self, prediction: Any, target: Any, **kwargs) -> MetricResult:
        """
        Computes structural fidelity.
        
        Args:
            prediction: The raw string output from the model.
            target: The expected JSON object (dict).
        
        Returns:
            MetricResult with value 1.0 if valid and matches structure, else < 1.0.
        """
        try:
            # Try to parse prediction as JSON
            # Handle potential markdown code blocks
            clean_prediction = str(prediction).strip()
            if clean_prediction.startswith("```json"):
                clean_prediction = clean_prediction[7:]
            if clean_prediction.endswith("```"):
                clean_prediction = clean_prediction[:-3]
            
            pred_json = json.loads(clean_prediction.strip())
            
            # Basic validation: is it a dict?
            if not isinstance(pred_json, dict):
                return MetricResult(value=0.0, name=self.name, version=self.version, metadata={"error": "Not a dict"})
            
            # Check fields
            if "fields" not in target:
                 return MetricResult(value=1.0, name=self.name, version=self.version, metadata={"info": "No fields in target"})

            target_fields = target.get("fields", {}).keys()
            pred_fields = pred_json.get("fields", {}).keys() if "fields" in pred_json else pred_json.keys()
            
            # Jaccard index of keys
            intersection = len(set(target_fields).intersection(set(pred_fields)))
            union = len(set(target_fields).union(set(pred_fields)))
            
            score = intersection / union if union > 0 else 0.0
            
            return MetricResult(value=score, name=self.name, version=self.version, metadata={"parsed": True})

        except json.JSONDecodeError as e:
            return MetricResult(value=0.0, name=self.name, version=self.version, metadata={"error": f"JSON Decode Error: {str(e)}"})
        except Exception as e:
            return MetricResult(value=0.0, name=self.name, version=self.version, metadata={"error": f"Unknown Error: {str(e)}"})

class FieldAccuracy(BaseMetric):
    """
    Metric to check accuracy of extracted field values.
    """
    def __init__(self, name: str = "field_accuracy", version: str = "0.1.0"):
        super().__init__(name, version)

    def compute(self, prediction: Any, target: Any, **kwargs) -> MetricResult:
        try:
            clean_prediction = str(prediction).strip()
            if clean_prediction.startswith("```json"):
                clean_prediction = clean_prediction[7:]
            if clean_prediction.endswith("```"):
                clean_prediction = clean_prediction[:-3]
            
            pred_json = json.loads(clean_prediction.strip())
            
            target_fields = target.get("fields", {})
            # Support both flat structure and nested "fields" key
            pred_fields = pred_json.get("fields", pred_json)
            
            if not isinstance(target_fields, dict) or not isinstance(pred_fields, dict):
                 return MetricResult(value=0.0, name=self.name, version=self.version, metadata={"error": "Invalid fields structure"})

            total_fields = len(target_fields)
            if total_fields == 0:
                return MetricResult(value=1.0, name=self.name, version=self.version)

            correct_fields = 0
            details = {}
            
            for key, target_val_obj in target_fields.items():
                # target_val_obj is like {"value": "...", "bboxes": ...}
                target_val = target_val_obj.get("value", "") if isinstance(target_val_obj, dict) else str(target_val_obj)
                
                pred_val_obj = pred_fields.get(key)
                pred_val = pred_val_obj.get("value", "") if isinstance(pred_val_obj, dict) else str(pred_val_obj) if pred_val_obj is not None else ""
                
                # Simple exact match for now (can be improved with Levenshtein)
                if str(target_val).strip() == str(pred_val).strip():
                    correct_fields += 1
                    details[key] = True
                else:
                    details[key] = False
            
            score = correct_fields / total_fields
            return MetricResult(value=score, name=self.name, version=self.version, metadata={"details": details})

        except Exception:
            return MetricResult(value=0.0, name=self.name, version=self.version)