"""
Regularized Logistic Regression baseline estimator with pure-Python fallback.
"""

from __future__ import annotations

import logging
import math
from typing import Any, List

from .base import BaseModel

logger = logging.getLogger("hermes_sports.models.logistic")


class LogisticModel(BaseModel):
    """Linear baseline model with standardization and L2 regularization."""

    def __init__(self, learning_rate: float = 0.05, epochs: int = 200, l2_reg: float = 0.01):
        super().__init__()
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.l2_reg = l2_reg

    def train(self, X: Any, y: Any, feature_names: List[str]):
        self.feature_names = feature_names

        try:
            import numpy as np
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(np.array(X))
            clf = LogisticRegression(C=1.0 / max(self.l2_reg, 1e-4), max_iter=self.epochs, random_state=42)
            clf.fit(X_scaled, np.array(y))
            self.model = {"scaler": scaler, "clf": clf}
            logger.info("Trained Scikit-Learn LogisticRegression.")
            return
        except ImportError:
            logger.info("Scikit-Learn not found; using pure-Python Logistic Regression.")

        # Pure Python Implementation
        n_samples = len(X)
        n_feats = len(feature_names)
        weights = [0.0] * n_feats
        bias = 0.0

        # Mean and Std for scaling
        means = [sum(X[i][j] for i in range(n_samples)) / max(n_samples, 1) for j in range(n_feats)]
        stds = [
            math.sqrt(sum((X[i][j] - means[j]) ** 2 for i in range(n_samples)) / max(n_samples, 1)) or 1.0
            for j in range(n_feats)
        ]

        # Standardize X
        X_norm = [
            [(X[i][j] - means[j]) / stds[j] for j in range(n_feats)]
            for i in range(n_samples)
        ]

        # Mini-batch gradient descent
        for _ in range(self.epochs):
            for i in range(n_samples):
                xi = X_norm[i]
                yi = y[i]
                z = bias + sum(w * x for w, x in zip(weights, xi))
                z = max(-20.0, min(20.0, z))
                p = 1.0 / (1.0 + math.exp(-z))
                err = p - yi

                bias -= self.learning_rate * err
                for j in range(n_feats):
                    weights[j] -= self.learning_rate * (err * xi[j] + self.l2_reg * weights[j])

        # Store weights mapped back to original scale
        raw_weights = {name: (weights[j] / stds[j]) for j, name in enumerate(feature_names)}
        raw_bias = bias - sum((weights[j] * means[j]) / stds[j] for j in range(n_feats))

        self.model = {"weights": raw_weights, "bias": raw_bias}

    def predict_proba(self, features) -> float:
        if not self.model or not self.feature_names:
            return features.get("home_fair_prob", 0.50)

        if isinstance(self.model, dict) and "clf" in self.model:
            import numpy as np
            vec = [float(features.get(name, 0.0)) for name in self.feature_names]
            X = np.array([vec])
            X_scaled = self.model["scaler"].transform(X)
            return float(self.model["clf"].predict_proba(X_scaled)[0][1])

        if isinstance(self.model, dict) and "weights" in self.model:
            weights = self.model["weights"]
            bias = self.model.get("bias", 0.0)
            z = bias + sum(weights.get(name, 0.0) * float(features.get(name, 0.0)) for name in self.feature_names)
            z = max(-20.0, min(20.0, z))
            return 1.0 / (1.0 + math.exp(-z))

        return features.get("home_fair_prob", 0.50)
