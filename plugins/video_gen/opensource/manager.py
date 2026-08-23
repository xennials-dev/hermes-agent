"""Resource, Memory & Lifecycle Manager for Open-Source Video Models."""

from __future__ import annotations

import gc
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from .base_adapter import BaseModelAdapter, GenerationRequest, GenerationResponse
from .model_registry import ModelRegistry, OPENSOURCE_MODELS_CATALOG

logger = logging.getLogger(__name__)


class GPUMemoryMonitor:
    """Monitors GPU/System memory to prevent OOM errors."""

    def __init__(self):
        self._has_cuda = False
        try:
            import torch
            self._has_cuda = torch.cuda.is_available()
        except ImportError:
            pass

    def get_free_memory_gb(self) -> float:
        """Return estimated free VRAM in Gigabytes."""
        if not self._has_cuda:
            return 64.0  # CPU / Endpoint fallback assumption
        try:
            import torch
            free_bytes, _ = torch.cuda.mem_get_info()
            return free_bytes / (1024 ** 3)
        except Exception:
            return 16.0

    def can_fit_model(self, required_gb: float) -> bool:
        """Check if required VRAM is available before loading weights."""
        free_gb = self.get_free_memory_gb()
        # Allow if at least 75% of required VRAM is free (offloading/fp8 can fit)
        return free_gb >= (required_gb * 0.75)


class ModelManager:
    """Thread-safe lifecycle manager for loading, caching, and unloading video models."""

    _instance: Optional["ModelManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "ModelManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, max_active_models: int = 1, memory_limit_gb: float = 24.0):
        if getattr(self, "_initialized", False):
            return
        self.max_active_models = max_active_models
        self.memory_limit_gb = memory_limit_gb
        self.active_models: Dict[str, BaseModelAdapter] = {}
        self.model_queue: List[str] = []
        self.lock = threading.Lock()
        self.memory_monitor = GPUMemoryMonitor()
        self._initialized = True

    def get_or_load_model(self, model_name: str, config_override: Optional[Dict[str, Any]] = None) -> BaseModelAdapter:
        """Retrieve an already loaded model or instantiate and load it with LRU eviction."""
        with self.lock:
            if model_name in self.active_models:
                # Refresh queue order
                if model_name in self.model_queue:
                    self.model_queue.remove(model_name)
                self.model_queue.append(model_name)
                return self.active_models[model_name]

            # Evict oldest loaded model if at capacity
            while len(self.active_models) >= self.max_active_models:
                self._unload_oldest_model()

            model_class = ModelRegistry.get_model_class(model_name)
            if not model_class:
                # Try generic adapter
                model_class = ModelRegistry.get_model_class("diffusers_generic")
            if not model_class:
                raise RuntimeError(f"No adapter found for video model '{model_name}'")

            merged_config = dict(ModelRegistry.get_config(model_name))
            if config_override:
                merged_config.update(config_override)

            adapter = model_class(merged_config)
            adapter._load_model()

            self.active_models[model_name] = adapter
            self.model_queue.append(model_name)
            return adapter

    def _unload_oldest_model(self) -> None:
        """Evict the least recently used model and trigger garbage collection."""
        if not self.model_queue:
            return
        oldest_name = self.model_queue.pop(0)
        adapter = self.active_models.pop(oldest_name, None)
        if adapter:
            try:
                adapter._unload_model()
            except Exception as exc:
                logger.debug("Error during unloading %s: %s", oldest_name, exc)

        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
        except ImportError:
            pass
        gc.collect()

    def unload_all(self) -> None:
        """Unload all active models."""
        with self.lock:
            while self.model_queue:
                self._unload_oldest_model()
            self.active_models.clear()

    def execute_with_fallback(
        self,
        primary_model: str,
        request: GenerationRequest,
        enable_fallback: bool = True,
    ) -> GenerationResponse:
        """Execute video generation with automatic fallback to secondary models if primary fails."""
        candidates = [primary_model]
        if enable_fallback:
            curr = primary_model
            for _ in range(3):
                meta = OPENSOURCE_MODELS_CATALOG.get(curr, {})
                fb = meta.get("fallback")
                if fb and fb not in candidates:
                    candidates.append(fb)
                    curr = fb
                else:
                    break

        last_error = "Unknown error"
        for model_name in candidates:
            try:
                logger.info("Attempting video generation using model '%s'...", model_name)
                adapter = self.get_or_load_model(model_name)
                response = adapter.generate(request)
                if response.success:
                    response.metadata["resolved_model"] = model_name
                    return response
                last_error = response.error_message or "Model returned failure"
                logger.warning("Model '%s' failed: %s. Trying next candidate...", model_name, last_error)
            except Exception as exc:
                last_error = str(exc)
                logger.warning("Exception running '%s': %s", model_name, exc)

        return GenerationResponse(
            success=False,
            error_message=f"All candidate models failed ({candidates}). Last error: {last_error}",
        )
