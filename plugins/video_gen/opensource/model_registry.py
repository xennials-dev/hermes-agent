"""Model Registry for Open-Source AI Video Generation Models."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type
from .base_adapter import BaseModelAdapter

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model Metadata Catalog (20+ Open-Source Models)
# ---------------------------------------------------------------------------

OPENSOURCE_MODELS_CATALOG: Dict[str, Dict[str, Any]] = {
    "open_sora": {
        "display": "Open-Sora 1.2",
        "description": "High-fidelity open-source text-to-video diffusion transformer.",
        "vram_gb": 32,
        "modalities": ["text", "image"],
        "fallback": "open_sora_plan",
        "default_duration": 4,
        "aspect_ratios": ["16:9", "9:16", "1:1", "4:3"],
        "diffusers_id": "hpcaitech/open-sora",
    },
    "open_sora_plan": {
        "display": "Open-Sora Plan v1.3",
        "description": "Memory-efficient Open-Sora variant with native high dynamic motion.",
        "vram_gb": 24,
        "modalities": ["text", "image"],
        "fallback": "wan2_1",
        "default_duration": 4,
        "aspect_ratios": ["16:9", "9:16", "1:1"],
        "diffusers_id": "LanguageBind/Open-Sora-Plan-v1.3.0",
    },
    "wan2_1": {
        "display": "Wan 2.1 (T2V & I2V)",
        "description": "State-of-the-art open weights video model with 14B & 1.3B variants.",
        "vram_gb": 28,
        "modalities": ["text", "image"],
        "fallback": "ltx_video",
        "default_duration": 5,
        "aspect_ratios": ["16:9", "9:16", "1:1", "4:3"],
        "diffusers_id": "Wan-AI/Wan2.1-T2V-14B",
    },
    "wan2_2": {
        "display": "Wan 2.2",
        "description": "Next-gen Wan architecture optimized for rapid inference and FP8.",
        "vram_gb": 20,
        "modalities": ["text", "image"],
        "fallback": "wan2_1",
        "default_duration": 5,
        "aspect_ratios": ["16:9", "9:16", "1:1"],
        "diffusers_id": "Wan-AI/Wan2.2-T2V",
    },
    "hunyuan_video": {
        "display": "HunyuanVideo",
        "description": "Tencent 13B transformer-based video foundation model.",
        "vram_gb": 16,
        "modalities": ["text", "image"],
        "fallback": "ltx_video",
        "default_duration": 5,
        "aspect_ratios": ["16:9", "9:16", "1:1"],
        "diffusers_id": "tencent/HunyuanVideo",
    },
    "ltx_video": {
        "display": "LTX-Video 2.3",
        "description": "Ultra-fast real-time DiT video generation (Lightricks).",
        "vram_gb": 12,
        "modalities": ["text", "image"],
        "fallback": "cogvideox",
        "default_duration": 5,
        "aspect_ratios": ["16:9", "9:16", "1:1"],
        "diffusers_id": "Lightricks/LTX-Video",
    },
    "mochi_1": {
        "display": "Mochi 1 Preview",
        "description": "Genmo 10B open-weights model with high visual fidelity.",
        "vram_gb": 20,
        "modalities": ["text"],
        "fallback": "hunyuan_video",
        "default_duration": 5,
        "aspect_ratios": ["16:9", "9:16", "1:1"],
        "diffusers_id": "genmo/mochi-1-preview",
    },
    "cogvideox": {
        "display": "CogVideoX-5B / 2B",
        "description": "THUDM 3D VAE + DiT video model with exceptional temporal consistency.",
        "vram_gb": 16,
        "modalities": ["text", "image"],
        "fallback": "svd",
        "default_duration": 6,
        "aspect_ratios": ["16:9", "9:16", "1:1"],
        "diffusers_id": "THUDM/CogVideoX-5b",
    },
    "svd": {
        "display": "Stable Video Diffusion (SVD-XT)",
        "description": "Stability AI standard image-to-video baseline.",
        "vram_gb": 12,
        "modalities": ["image"],
        "fallback": "ltx_video",
        "default_duration": 4,
        "aspect_ratios": ["16:9", "9:16", "1:1"],
        "diffusers_id": "stabilityai/stable-video-diffusion-img2vid-xt",
    },
    "ovi": {
        "display": "Ovi Omni-Video",
        "description": "Unified multimodal video generation architecture with audio synchronization.",
        "vram_gb": 32,
        "modalities": ["text", "image"],
        "fallback": "hunyuan_video",
        "default_duration": 5,
        "aspect_ratios": ["16:9", "9:16"],
        "diffusers_id": "ovi-project/ovi-base",
    },
    "alice_v1": {
        "display": "Alice v1",
        "description": "Controllable character-consistent cinematic video generator.",
        "vram_gb": 28,
        "modalities": ["text", "image"],
        "fallback": "wan2_1",
        "default_duration": 5,
        "aspect_ratios": ["16:9", "9:16", "2.35:1"],
        "diffusers_id": "alice-ai/alice-v1",
    },
    "bernini": {
        "display": "Bernini 3D-Video",
        "description": "Spatial 3D-aware video generation with camera motion controls.",
        "vram_gb": 24,
        "modalities": ["text", "image"],
        "fallback": "ltx_video",
        "default_duration": 4,
        "aspect_ratios": ["16:9", "1:1"],
        "diffusers_id": "bernini-research/bernini-v1",
    },
    "openvideo": {
        "display": "OpenVideo",
        "description": "Community lightweight open weights model suited for edge GPU nodes.",
        "vram_gb": 12,
        "modalities": ["text", "image"],
        "fallback": "cogvideox",
        "default_duration": 4,
        "aspect_ratios": ["16:9", "1:1"],
        "diffusers_id": "openvideo-ai/openvideo-7b",
    },
    "vace": {
        "display": "VACE Visual Action Control",
        "description": "Action-conditioned video generation with trajectory controls.",
        "vram_gb": 20,
        "modalities": ["text", "image"],
        "fallback": "hunyuan_video",
        "default_duration": 4,
        "aspect_ratios": ["16:9", "9:16"],
        "diffusers_id": "vace-team/vace-v1",
    },
    "duix_avatar": {
        "display": "Duix-Avatar",
        "description": "Specialized audio-driven digital avatar and talking face generation.",
        "vram_gb": 8,
        "modalities": ["image"],
        "fallback": "svd",
        "default_duration": 10,
        "aspect_ratios": ["9:16", "1:1"],
        "diffusers_id": "duix/duix-avatar-base",
    },
    "openshorts": {
        "display": "OpenShorts Platform",
        "description": "Automated vertical video pipeline integration.",
        "vram_gb": 16,
        "modalities": ["text", "image"],
        "fallback": "wan2_1",
        "default_duration": 6,
        "aspect_ratios": ["9:16"],
        "diffusers_id": "openshorts/pipeline",
    },
    "wangp": {
        "display": "WanGP Distributed",
        "description": "Distributed multi-GPU pipeline for large batch video generation.",
        "vram_gb": 24,
        "modalities": ["text", "image"],
        "fallback": "wan2_1",
        "default_duration": 5,
        "aspect_ratios": ["16:9", "9:16"],
        "diffusers_id": "wangp/wan-distributed",
    },
    "sogni": {
        "display": "Sogni AI Engine",
        "description": "Local on-device optimized diffusion pipeline (Apple Silicon & RTX).",
        "vram_gb": 12,
        "modalities": ["text", "image"],
        "fallback": "ltx_video",
        "default_duration": 4,
        "aspect_ratios": ["16:9", "9:16", "1:1"],
        "diffusers_id": "sogni/engine",
    },
    "comfyui_bridge": {
        "display": "ComfyUI Bridge",
        "description": "Direct HTTP / WebSocket bridge to any local ComfyUI video workflow.",
        "vram_gb": 8,
        "modalities": ["text", "image"],
        "fallback": "ltx_video",
        "default_duration": 5,
        "aspect_ratios": ["16:9", "9:16", "1:1"],
        "diffusers_id": "comfyui/workflow",
    },
    "diffusers_generic": {
        "display": "Generic HuggingFace Diffusers",
        "description": "Loads any arbitrary video pipeline from Hugging Face Hub.",
        "vram_gb": 16,
        "modalities": ["text", "image"],
        "fallback": "ltx_video",
        "default_duration": 5,
        "aspect_ratios": ["16:9", "9:16", "1:1", "4:3"],
        "diffusers_id": "custom",
    },
}


class ModelRegistry:
    """Central registry for managing available video model adapters."""

    _models: Dict[str, Type[BaseModelAdapter]] = {}
    _configs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        model_class: Optional[Type[BaseModelAdapter]] = None,
        default_config: Optional[Dict[str, Any]] = None,
    ):
        """Register a model adapter class, supporting both function calls and decorators."""
        def decorator(klass: Type[BaseModelAdapter]) -> Type[BaseModelAdapter]:
            cls._models[name] = klass
            base_config = dict(OPENSOURCE_MODELS_CATALOG.get(name, {}))
            if default_config:
                base_config.update(default_config)
            cls._configs[name] = base_config
            return klass

        if model_class is not None:
            return decorator(model_class)
        return decorator

    @classmethod
    def get_model_class(cls, name: str) -> Optional[Type[BaseModelAdapter]]:
        """Retrieve registered model class by name (or fallback to generic adapter)."""
        if name in cls._models:
            return cls._models[name]
        # Fallback to diffusers_generic if registered
        return cls._models.get("diffusers_generic")

    @classmethod
    def get_config(cls, name: str) -> Dict[str, Any]:
        """Get default configuration for model."""
        return cls._configs.get(name, OPENSOURCE_MODELS_CATALOG.get(name, {}))

    @classmethod
    def list_models(cls) -> List[str]:
        """List all known model keys."""
        all_keys = set(cls._models.keys()) | set(OPENSOURCE_MODELS_CATALOG.keys())
        return sorted(list(all_keys))

    @classmethod
    def get_catalog_entries(cls) -> List[Dict[str, Any]]:
        """Return structured catalog for Hermes CLI / tool pickers."""
        entries: List[Dict[str, Any]] = []
        for model_id, meta in OPENSOURCE_MODELS_CATALOG.items():
            entries.append({
                "id": model_id,
                "display": meta["display"],
                "speed": f"~{meta.get('vram_gb', 16)}GB VRAM",
                "strengths": meta["description"],
                "price": "Free / Open-Weights",
                "modalities": meta["modalities"],
            })
        return entries
