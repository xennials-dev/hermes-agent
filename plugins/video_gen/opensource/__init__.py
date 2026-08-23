"""Open-Source Video Generation Plugin for Hermes Agent.

Provides plug-and-play support for 20+ local and self-hosted open-source AI video models
(Open-Sora, Wan 2.1/2.2, HunyuanVideo, LTX-Video, Mochi-1, CogVideoX, SVD, Ovi, Alice v1,
Bernini, VACE, OpenVideo, Duix-Avatar, and ComfyUI / Diffusers endpoints) without
modifying Hermes core code or invalidating prompt caches.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.video_gen_provider import (
    VideoGenProvider,
    error_response,
    save_bytes_video,
    save_url_video,
    success_response,
)
from .base_adapter import GenerationRequest
from .manager import ModelManager
from .model_registry import ModelRegistry, OPENSOURCE_MODELS_CATALOG
from . import adapters  # Ensures all adapter registrations run

logger = logging.getLogger(__name__)


class OpenSourceVideoGenProvider(VideoGenProvider):
    """Text-to-video and image-to-video provider for open-source AI models."""

    name = "opensource"

    @property
    def display_name(self) -> str:
        return "Open-Source Video Models"

    def is_available(self) -> bool:
        """Provider is always available; individual model loaders handle hardware requirements."""
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        """Return the catalog of 20+ open-source video models for the CLI/UI picker."""
        return ModelRegistry.get_catalog_entries()

    def default_model(self) -> str:
        """Default to wan2_1 if available, otherwise ltx_video."""
        return "wan2_1"

    def capabilities(self) -> Dict[str, Any]:
        return {
            "modalities": ["text", "image"],
            "aspect_ratios": ["16:9", "9:16", "1:1", "4:3", "3:4"],
            "resolutions": ["480p", "540p", "720p", "1080p"],
            "max_duration": 15,
            "min_duration": 1,
            "supports_audio": True,
            "supports_negative_prompt": True,
            "max_reference_images": 5,
        }

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Open-Source Video Models",
            "badge": "local/self-hosted",
            "tag": "Open-Sora, Wan 2.1, Hunyuan, LTX-Video, CogVideoX, Mochi, SVD, ComfyUI",
            "env_vars": [
                {
                    "key": "HERMES_VIDEO_MODEL_DIR",
                    "prompt": "Custom local weights directory (optional)",
                    "url": "https://github.com/NousResearch/hermes-agent",
                },
                {
                    "key": "COMFYUI_URL",
                    "prompt": "ComfyUI base URL if using ComfyUI bridge (default: http://127.0.0.1:8188)",
                    "url": "http://127.0.0.1:8188",
                },
            ],
        }

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        duration: Optional[int] = None,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        negative_prompt: Optional[str] = None,
        audio: Optional[bool] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if not prompt or not prompt.strip():
            return error_response(
                error="Prompt is required for video generation",
                error_type="invalid_request",
                provider=self.name,
            )

        chosen_model = model or self.default_model()
        meta = OPENSOURCE_MODELS_CATALOG.get(chosen_model, {})

        request = GenerationRequest(
            prompt=prompt,
            image_path=image_url,
            reference_images=reference_image_urls,
            duration=duration or meta.get("default_duration", 5),
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            seed=seed,
            custom_params=kwargs,
        )

        manager = ModelManager()
        response = manager.execute_with_fallback(
            primary_model=chosen_model,
            request=request,
            enable_fallback=True,
        )

        if not response.success:
            return error_response(
                error=response.error_message or "Video generation failed",
                error_type="model_execution_error",
                provider=self.name,
                model=chosen_model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )

        resolved_video_ref: str = ""
        if response.output_path and os.path.exists(response.output_path):
            resolved_video_ref = response.output_path
        elif response.output_url:
            try:
                resolved_video_ref = str(save_url_video(response.output_url, prefix=chosen_model))
            except Exception:
                resolved_video_ref = response.output_url
        elif response.raw_bytes:
            resolved_video_ref = str(save_bytes_video(response.raw_bytes, prefix=chosen_model))
        else:
            resolved_video_ref = response.output_path or "video_generated.mp4"

        return success_response(
            video=resolved_video_ref,
            model=response.metadata.get("resolved_model", chosen_model),
            prompt=prompt,
            modality="image" if image_url else "text",
            aspect_ratio=aspect_ratio,
            duration=request.duration or 0,
            provider=self.name,
            extra=response.metadata,
        )


def register(ctx: Any) -> None:
    """Register the OpenSourceVideoGenProvider with the Hermes plugin registry."""
    ctx.register_video_gen_provider(OpenSourceVideoGenProvider())
