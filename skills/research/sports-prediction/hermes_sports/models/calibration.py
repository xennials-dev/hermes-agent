"""
Probability calibration via Platt Scaling (Logistic) and Isotonic Regression.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List

try:
    from .base import BaseModel
except (ImportError, ValueError):
    from hermes_sports.models.base import BaseModel  # type: ignore

logger = logging.getLogger("hermes_sports.models.calibration")


class CalibratedModel(BaseModel):
    """Wraps a base model and calibrates its raw probability predictions."""

    def __init__(self, base_model: BaseModel, method: str = "isotonic"):
        super().__init__()
        self.base_model = base_model
        self.method = method
        self.calibrator: Any = None
        self.feature_names = base_model.feature_names

    def train(self, X: Any, y: Any, feature_names: List[str]):
        self.feature_names = feature_names

    def fit_calibrator(self, X_calib: Any, y_calib: Any):
        """Fit calibration curve on holdout predictions."""
        raw_probs = []
        for row in X_calib:
            feat_dict = {name: val for name, val in zip(self.feature_names, row)}
            raw_probs.append(self.base_model.predict_proba(feat_dict))

        try:
            import numpy as np  # type: ignore
            if self.method == "isotonic":
                from sklearn.isotonic import IsotonicRegression  # type: ignore

                self.calibrator = IsotonicRegression(out_of_bounds="clip")
                self.calibrator.fit(np.array(raw_probs), np.array(y_calib))
                logger.info("Fitted Scikit-Learn Isotonic Regression calibrator.")
                return
            else:
                from sklearn.linear_model import LogisticRegression  # type: ignore

                self.calibrator = LogisticRegression(C=1.0)
                self.calibrator.fit(np.array(raw_probs).reshape(-1, 1), np.array(y_calib))
                logger.info("Fitted Scikit-Learn Platt Scaling calibrator.")
                return
        except ImportError:
            pass

        # Pure Python Platt Scaling (A * logit + B)
        logits = [math.log(max(1e-4, p) / max(1e-4, 1.0 - p)) for p in raw_probs]
        mean_l = sum(logits) / max(len(logits), 1)
        mean_y = sum(y_calib) / max(len(y_calib), 1)

        numer = sum((logits[i] - mean_l) * (y_calib[i] - mean_y) for i in range(len(logits)))
        denom = sum((logits[i] - mean_l) ** 2 for i in range(len(logits))) or 1.0
        slope = numer / denom
        intercept = mean_y - slope * mean_l

        self.calibrator = {"slope": slope, "intercept": intercept}
        logger.info("Fitted pure-Python Platt calibrator.")

    def predict_proba(self, features: Dict[str, Any]) -> float:
        raw_p = self.base_model.predict_proba(features)
        if self.calibrator is None:
            return raw_p

        if hasattr(self.calibrator, "predict"):
            return float(self.calibrator.predict([raw_p])[0])
        elif hasattr(self.calibrator, "predict_proba"):
            return float(self.calibrator.predict_proba([[raw_p]])[0][1])
        elif isinstance(self.calibrator, dict):
            logit = math.log(max(1e-4, raw_p) / max(1e-4, 1.0 - raw_p))
            scaled = self.calibrator["intercept"] + self.calibrator["slope"] * logit
            return max(0.01, min(0.99, scaled))

        return raw_p
