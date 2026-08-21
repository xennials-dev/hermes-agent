"""
Model training, cross-validation, and calibration pipeline.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from ..config import Config
    from ..models.calibration import CalibratedModel
    from ..models.ensemble import EnsembleModel
    from ..models.lgbm_model import LightGBMModel
    from ..models.logistic_model import LogisticModel
    from ..models.xgb_model import XGBoostModel
    from .synthetic_data import generate_training_dataset
except (ImportError, ValueError):
    from hermes_sports.config import Config  # type: ignore
    from hermes_sports.models.calibration import CalibratedModel  # type: ignore
    from hermes_sports.models.ensemble import EnsembleModel  # type: ignore
    from hermes_sports.models.lgbm_model import LightGBMModel  # type: ignore
    from hermes_sports.models.logistic_model import LogisticModel  # type: ignore
    from hermes_sports.models.xgb_model import XGBoostModel  # type: ignore
    from hermes_sports.training.synthetic_data import generate_training_dataset  # type: ignore

logger = logging.getLogger("hermes_sports.training.train")


def _calc_metrics(y_true: List[int], y_pred: List[float]) -> Tuple[float, float, float]:
    """Calculate LogLoss, Brier Score, and Approximate AUC in pure Python."""
    n = len(y_true)
    if n == 0:
        return 0.0, 0.0, 0.5

    # Log Loss
    eps = 1e-6
    log_loss_val = -sum(
        y_true[i] * math.log(max(eps, y_pred[i])) + (1 - y_true[i]) * math.log(max(eps, 1.0 - y_pred[i]))
        for i in range(n)
    ) / n

    # Brier Score
    brier = sum((y_pred[i] - y_true[i]) ** 2 for i in range(n)) / n

    # ROC AUC (Mann-Whitney U statistic)
    pos_scores = [y_pred[i] for i in range(n) if y_true[i] == 1]
    neg_scores = [y_pred[i] for i in range(n) if y_true[i] == 0]
    if not pos_scores or not neg_scores:
        auc = 0.5
    else:
        wins = sum(1.0 if p > q else (0.5 if p == q else 0.0) for p in pos_scores for q in neg_scores)
        auc = wins / (len(pos_scores) * len(neg_scores))

    return log_loss_val, brier, auc


def train_prediction_pipeline(config: Config, sport: str = "basketball_nba") -> Dict[str, Any]:
    """Train, calibrate, evaluate, and save models for a given sport."""
    logger.info(f"Starting model training pipeline for {sport}...")
    X, y, feature_names = generate_training_dataset(sport=sport, n_samples=2500)

    n_samples = len(X)
    n_train = int(n_samples * 0.70)
    n_calib = int(n_samples * 0.15)

    X_train, y_train = X[:n_train], y[:n_train]
    X_calib, y_calib = X[n_train : n_train + n_calib], y[n_train : n_train + n_calib]
    X_test, y_test = X[n_train + n_calib :], y[n_train + n_calib :]

    # Instantiate base estimators
    xgb = XGBoostModel(params=config.model.xgb_params)
    lgbm = LightGBMModel(params=config.model.lgbm_params)
    logreg = LogisticModel()

    ensemble = EnsembleModel(models=[xgb, lgbm, logreg], weights=[0.45, 0.40, 0.15])
    ensemble.train(X_train, y_train, feature_names)

    # Apply probability calibration
    if config.model.use_calibration:
        calibrated = CalibratedModel(ensemble, method=config.model.calibration_method)
        calibrated.fit_calibrator(X_calib, y_calib)
        final_model = calibrated
    else:
        final_model = ensemble

    # Evaluate on holdout test set
    test_preds = []
    for row in X_test:
        f_dict = {name: val for name, val in zip(feature_names, row)}
        test_preds.append(final_model.predict_proba(f_dict))

    loss, brier, auc = _calc_metrics(y_test, test_preds)
    logger.info(f"Model Evaluation for {sport}: LogLoss={loss:.4f}, Brier={brier:.4f}, AUC={auc:.4f}")

    # Save model artifact
    model_save_path = Path(config.model.models_dir) / f"{sport}_{config.model.model_type}.joblib"
    final_model.save(str(model_save_path))
    logger.info(f"Model saved to {model_save_path}")

    return {
        "sport": sport,
        "samples": len(X),
        "log_loss": round(float(loss), 4),
        "brier_score": round(float(brier), 4),
        "roc_auc": round(float(auc), 4),
        "model_path": str(model_save_path),
    }
