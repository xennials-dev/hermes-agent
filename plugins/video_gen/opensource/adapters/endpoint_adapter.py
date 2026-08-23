"""Remote and local API endpoint adapters for open-source video backends (ComfyUI, OpenShorts, WanGP, Sogni)."""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, Optional

from ..base_adapter import BaseModelAdapter, GenerationRequest, GenerationResponse
from ..model_registry import ModelRegistry

logger = logging.getLogger(__name__)


@ModelRegistry.register("comfyui_bridge")
class ComfyUIAdapter(BaseModelAdapter):
    """Bridge to a local or remote ComfyUI instance running video generation nodes."""

    def _load_model(self) -> None:
        self.base_url = self.config.get("url") or os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")

    def _unload_model(self) -> None:
        pass

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        start_time = time.time()
        url = getattr(self, "base_url", "http://127.0.0.1:8188")
        try:
            req = urllib.request.Request(f"{url}/system_stats", method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status != 200:
                    return GenerationResponse(
                        success=False,
                        error_message=f"ComfyUI server returned HTTP {resp.status}",
                        generation_time=time.time() - start_time,
                    )

            prompt_payload = json.dumps({
                "prompt": {
                    "3": {
                        "class_type": "KSampler",
                        "inputs": {"seed": request.seed or 42, "steps": 25, "cfg": 7.0}
                    },
                    "6": {
                        "class_type": "CLIPTextEncode",
                        "inputs": {"text": request.prompt}
                    }
                }
            }).encode("utf-8")

            post_req = urllib.request.Request(
                f"{url}/prompt",
                data=prompt_payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(post_req, timeout=10.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                prompt_id = data.get("prompt_id")

            time.sleep(1.0)
            return GenerationResponse(
                success=True,
                metadata={"prompt_id": prompt_id, "backend": "comfyui"},
                generation_time=time.time() - start_time,
            )
        except Exception as exc:
            return GenerationResponse(
                success=False,
                error_message=f"ComfyUI execution error: {exc}",
                generation_time=time.time() - start_time,
            )


@ModelRegistry.register("openshorts")
@ModelRegistry.register("wangp")
@ModelRegistry.register("sogni")
class RemoteEndpointAdapter(BaseModelAdapter):
    """Generic remote endpoint adapter for specialized open-source platform runners."""

    def _load_model(self) -> None:
        self.endpoint = self.config.get("endpoint") or os.environ.get("VIDEO_MODEL_ENDPOINT", "http://127.0.0.1:8000/v1/generate")

    def _unload_model(self) -> None:
        pass

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        start_time = time.time()
        try:
            payload = json.dumps({
                "prompt": request.prompt,
                "duration": request.duration,
                "aspect_ratio": request.aspect_ratio,
                "fps": request.fps,
                "seed": request.seed,
            }).encode("utf-8")

            req = urllib.request.Request(
                self.endpoint,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return GenerationResponse(
                    success=True,
                    output_url=data.get("video_url"),
                    output_path=data.get("output_path"),
                    generation_time=time.time() - start_time,
                    metadata=data.get("metadata", {}),
                )
        except Exception as exc:
            return GenerationResponse(
                success=False,
                error_message=f"Remote video server connection failed: {exc}",
                generation_time=time.time() - start_time,
            )
