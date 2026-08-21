"""
Base Model abstract definition for sports outcome prediction.
"""

from __future__ import annotations

import json
import math
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


class BaseModel(ABC):
    """Abstract base class for all prediction estimators."""

    def __init__(self):
        self.model: Any = None
        self.feature_names: List[str] = []

    @abstractmethod
    def train(self, X: Any, y: Any, feature_names: List[str]):
        """Train the model on feature matrix X and target labels y."""
        pass

    def predict_proba(self, features: Dict[str, Any]) -> float:
        """Predict the probability of a positive outcome (0.0 to 1.0)."""
        if self.model is None or not self.feature_names:
            return features.get("home_fair_prob", 0.50)

        # Standard sklearn-like model object
        if hasattr(self.model, "predict_proba"):
            try:
                import numpy as np
                vec = [float(features.get(name, 0.0)) for name in self.feature_names]
                probs = self.model.predict_proba(np.array([vec]))[0]
                if len(probs) > 1:
                    return float(probs[1])
                return float(probs[0])
            except Exception:
                pass

        # Pure Python dict model fallback
        if isinstance(self.model, dict) and "weights" in self.model:
            weights = self.model["weights"]
            bias = self.model.get("bias", 0.0)
            z = bias + sum(weights.get(name, 0.0) * float(features.get(name, 0.0)) for name in self.feature_names)
            z = max(-20.0, min(20.0, z))
            return 1.0 / (1.0 + math.exp(-z))

        return features.get("home_fair_prob", 0.50)

    def save(self, path: str):
        """Persist model artifacts and feature schema to disk."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            import joblib
            joblib.dump(self.model, str(p))
        except ImportError:
            with open(str(p), "wb") as f:
                pickle.dump(self.model, f)

        with open(str(p) + ".features.json", "w", encoding="utf-8") as f:
            json.dump(self.feature_names, f, indent=2)

    def load(self, path: str):
        """Load model artifacts and feature schema from disk."""
        p = Path(path)
        if p.exists():
            try:
                import joblib
                self.model = joblib.load(str(p))
            except Exception:
                try:
                    with open(str(p), "rb") as f:
                        self.model = pickle.load(f)
                except Exception:
                    pass

            feat_file = Path(str(p) + ".features.json")
            if feat_file.exists():
                with open(feat_file, "r", encoding="utf-8") as f:
                    self.feature_names = json.load(f)
