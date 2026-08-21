"""
LightGBM model wrapper with fallback to pure-Python tree ensemble.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

try:
    from .base import BaseModel
    from .xgb_model import XGBoostModel
except (ImportError, ValueError):
    from hermes_sports.models.base import BaseModel  # type: ignore
    from hermes_sports.models.xgb_model import XGBoostModel  # type: ignore

logger = logging.getLogger("hermes_sports.models.lgbm")


class LightGBMModel(BaseModel):
    """LightGBM booster with fallback."""

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.params = params or {
            "num_leaves": 20,
            "learning_rate": 0.03,
            "n_estimators": 100,
            "subsample": 0.8,
        }
        self._fallback_model = XGBoostModel(params=self.params)

    def train(self, X: Any, y: Any, feature_names: List[str]):
        self.feature_names = feature_names
        try:
            import lightgbm as lgb  # type: ignore
            import numpy as np  # type: ignore

            clf = lgb.LGBMClassifier(
                num_leaves=self.params.get("num_leaves", 20),
                learning_rate=self.params.get("learning_rate", 0.03),
                n_estimators=self.params.get("n_estimators", 100),
                subsample=self.params.get("subsample", 0.8),
                random_state=42,
                verbosity=-1,
            )
            clf.fit(np.array(X), np.array(y))
            self.model = clf
            logger.info("Trained native LGBMClassifier.")
            return
        except ImportError:
            pass

        # Fallback to pure Python booster
        self._fallback_model.train(X, y, feature_names)
        self.model = self._fallback_model.model

    def predict_proba(self, features: Dict[str, Any]) -> float:
        if not self.model or not self.feature_names:
            return features.get("home_fair_prob", 0.50)

        if hasattr(self.model, "predict_proba"):
            try:
                import numpy as np  # type: ignore
                vec = [float(features.get(name, 0.0)) for name in self.feature_names]
                return float(self.model.predict_proba(np.array([vec]))[0][1])
            except Exception:
                pass

        self._fallback_model.model = self.model
        self._fallback_model.feature_names = self.feature_names
        return self._fallback_model.predict_proba(features)
