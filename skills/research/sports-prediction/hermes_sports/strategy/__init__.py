"""
Strategy and staking modules for sports betting.
"""

from __future__ import annotations

from .edge_detector import EdgeDetector  # type: ignore
from .staking import KellyStaking  # type: ignore

__all__ = ["EdgeDetector", "KellyStaking"]
