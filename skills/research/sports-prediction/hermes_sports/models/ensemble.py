"""
Ensemble model blending multiple estimators (GBM, Logistic, Forest).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

try:
    from .base import BaseModel  # type: ignore
except (ImportError, ValueError):
    from hermes_sports.models.base import BaseModel  # type: ignore

logger = logging.getLogger("hermes_sports.models.ensemble")


class EnsembleModel(BaseModel):
    """Weighted average ensemble over multiple baseline estimators."""

    def __init__(self, models: Optional[List[BaseModel]] = None, weights: Optional[List[float]] = None):
        super().__init__()
        self.models = models or []
        self.weights = weights or ([1.0 / len(self.models)] * len(self.models) if self.models else [])

    def train(self, X: Any, y: Any, feature_names: List[str]):
        self.feature_names = feature_names
        for m in self.models:
            m.train(X, y, feature_names)
        if not self.weights:
            self.weights = [1.0 / len(self.models)] * len(self.models)
        self.model = {"models": self.models, "weights": self.weights}
        logger.info(f"Trained ensemble of {len(self.models)} models.")

    def predict_proba(self, features: Dict[str, Any]) -> float:
        if not self.models:
            if isinstance(self.model, dict) and "models" in self.model:
                self.models = self.model["models"]
                self.weights = self.model.get("weights", [1.0 / len(self.models)] * len(self.models))
            else:
                return features.get("home_fair_prob", 0.50)

        probs = [m.predict_proba(features) for m in self.models]
        weighted_sum = sum(p * w for p, w in zip(probs, self.weights))
        total_weight = sum(self.weights)
        return float(weighted_sum / max(total_weight, 1e-6))
