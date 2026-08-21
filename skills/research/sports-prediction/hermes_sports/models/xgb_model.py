"""
XGBoost model wrapper with fallback to Scikit-Learn GradientBoosting or Pure Python boosting.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

from .base import BaseModel

logger = logging.getLogger("hermes_sports.models.xgb")


class XGBoostModel(BaseModel):
    """Gradient boosting classifier with native and pure Python fallbacks."""

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.params = params or {
            "max_depth": 4,
            "learning_rate": 0.03,
            "n_estimators": 100,
            "subsample": 0.8,
        }

    def train(self, X: Any, y: Any, feature_names: List[str]):
        self.feature_names = feature_names
        try:
            import xgboost as xgb
            import numpy as np

            clf = xgb.XGBClassifier(
                max_depth=self.params.get("max_depth", 4),
                learning_rate=self.params.get("learning_rate", 0.03),
                n_estimators=self.params.get("n_estimators", 100),
                subsample=self.params.get("subsample", 0.8),
                eval_metric="logloss",
                random_state=42,
            )
            clf.fit(np.array(X), np.array(y))
            self.model = clf
            logger.info("Trained native XGBoostClassifier.")
            return
        except ImportError:
            pass

        try:
            from sklearn.ensemble import HistGradientBoostingClassifier
            import numpy as np

            clf = HistGradientBoostingClassifier(
                max_depth=self.params.get("max_depth", 4),
                learning_rate=self.params.get("learning_rate", 0.03),
                max_iter=self.params.get("n_estimators", 100),
                random_state=42,
            )
            clf.fit(np.array(X), np.array(y))
            self.model = clf
            logger.info("Trained Scikit-Learn HistGradientBoostingClassifier.")
            return
        except ImportError:
            logger.info("Using pure-Python Ensemble Booster.")

        # Pure Python Decision Stump ensemble
        n_samples = len(X)
        n_feats = len(feature_names)
        lr = self.params.get("learning_rate", 0.03)

        # Baseline log-odds
        pos = sum(y)
        bias = math.log(max(pos, 1) / max(n_samples - pos, 1))

        trees = []
        residuals = [y[i] - 1.0 / (1.0 + math.exp(-bias)) for i in range(n_samples)]

        # Train stumps
        for _ in range(min(50, self.params.get("n_estimators", 100))):
            best_feat = 0
            best_thresh = 0.0
            best_gain = -1.0
            best_left_val = 0.0
            best_right_val = 0.0

            # Sample features
            for f_idx in range(n_feats):
                vals = [X[i][f_idx] for i in range(n_samples)]
                thresh = sum(vals) / max(len(vals), 1)

                left_r = [residuals[i] for i in range(n_samples) if X[i][f_idx] <= thresh]
                right_r = [residuals[i] for i in range(n_samples) if X[i][f_idx] > thresh]

                if not left_r or not right_r:
                    continue

                l_val = sum(left_r) / len(left_r)
                r_val = sum(right_r) / len(right_r)
                gain = sum(r**2 for r in left_r) + sum(r**2 for r in right_r)

                if gain > best_gain:
                    best_gain = gain
                    best_feat = f_idx
                    best_thresh = thresh
                    best_left_val = l_val * lr
                    best_right_val = r_val * lr

            trees.append(
                {
                    "feature_name": feature_names[best_feat],
                    "threshold": best_thresh,
                    "left_val": best_left_val,
                    "right_val": best_right_val,
                }
            )

            # Update residuals
            for i in range(n_samples):
                val = best_left_val if X[i][best_feat] <= best_thresh else best_right_val
                residuals[i] -= val

        self.model = {"trees": trees, "bias": bias}

    def predict_proba(self, features: Dict[str, Any]) -> float:
        if not self.model or not self.feature_names:
            return features.get("home_fair_prob", 0.50)

        if hasattr(self.model, "predict_proba"):
            import numpy as np
            vec = [float(features.get(name, 0.0)) for name in self.feature_names]
            return float(self.model.predict_proba(np.array([vec]))[0][1])

        if isinstance(self.model, dict) and "trees" in self.model:
            score = self.model["bias"]
            for tree in self.model["trees"]:
                val = float(features.get(tree["feature_name"], 0.0))
                score += tree["left_val"] if val <= tree["threshold"] else tree["right_val"]
            score = max(-20.0, min(20.0, score))
            return 1.0 / (1.0 + math.exp(-score))

        return features.get("home_fair_prob", 0.50)
