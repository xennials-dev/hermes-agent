"""Base Model Adapter and Request/Response specifications for open-source AI video models."""

from __future__ import annotations

import abc
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union


@dataclass
class GenerationRequest:
    """Standardized request object across all open-source video adapters."""
    prompt: str
    image_path: Optional[str] = None
    reference_images: Optional[List[str]] = None
    audio_path: Optional[str] = None
    duration: Optional[int] = 5
    resolution: Optional[Tuple[int, int]] = (720, 1280)
    aspect_ratio: str = "16:9"
    fps: Optional[int] = 24
    seed: Optional[int] = None
    negative_prompt: Optional[str] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResponse:
    """Standardized response object across all open-source video adapters."""
    success: bool
    output_path: Optional[str] = None
    output_url: Optional[str] = None
    raw_bytes: Optional[bytes] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    generation_time: Optional[float] = None


class BaseModelAdapter(abc.ABC):
    """Abstract base class for open-source video model integrations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config: Dict[str, Any] = config or {}
        self.model: Any = None
        self.device: str = self._setup_device()
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate model-specific configuration. Override in subclass if needed."""
        pass

    def _setup_device(self) -> str:
        """Detect compute device with graceful fallback (cuda -> mps -> cpu)."""
        force_device = self.config.get("device")
        if force_device:
            return force_device

        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"

    @abc.abstractmethod
    def _load_model(self) -> None:
        """Load model weights into compute device or connect to runtime backend."""
        pass

    @abc.abstractmethod
    def _unload_model(self) -> None:
        """Unload model from device memory to free VRAM."""
        pass

    @abc.abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Execute video generation."""
        pass

    def generate_stream(self, request: GenerationRequest) -> Generator[Dict[str, Any], None, None]:
        """Stream generation progress. Default implementation yields initial/done steps."""
        yield {"status": "starting", "progress": 0}
        resp = self.generate(request)
        if resp.success:
            yield {"status": "complete", "progress": 100, "response": resp}
        else:
            yield {"status": "failed", "error": resp.error_message}

    def __enter__(self) -> "BaseModelAdapter":
        self._load_model()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._unload_model()
