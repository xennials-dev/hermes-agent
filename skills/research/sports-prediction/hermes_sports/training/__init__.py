"""
Training and evaluation modules for sports prediction models.
"""

from __future__ import annotations

from .synthetic_data import generate_training_dataset  # type: ignore
from .train import train_prediction_pipeline  # type: ignore

__all__ = ["generate_training_dataset", "train_prediction_pipeline"]
