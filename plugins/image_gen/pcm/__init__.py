"""Phased Consistency Model (PCM) rapid generation backend.
Sub-second visual prototyping, UI wireframing, storyboard generation, and design loops.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_b64_image,
    save_url_image,
    success_response,
)
from plugins.image_gen._common import (
    StaticImageGenProvider,
    error_factory,
    load_image_gen_config,
    prompt_required_error,
    resolve_static_model,
)

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://127.0.0.1:8188"

PCM_MODELS: Dict[str, Dict[str, Any]] = {
    "pcm-sd15-4step": {
        "display": "PCM SD15 (4-Step Fast Wireframe)",
        "speed": "~0.4s",
        "strengths": "Instant UI wireframing, rapid multi-step prototypes, agent feedback loops",
        "steps": 4,
        "base_model": "sd15",
    },
    "pcm-sd15-2step": {
        "display": "PCM SD15 (2-Step Ultra Fast Draft)",
        "speed": "~0.2s",
        "strengths": "Exploratory drafts, visual concept check, minimal compute",
        "steps": 2,
        "base_model": "sd15",
    },
    "pcm-sdxl-8step": {
        "display": "PCM SDXL (8-Step HD Asset)",
        "speed": "~1.5s",
        "strengths": "Production UI mockups, marketing hero assets, detailed illustrations",
        "steps": 8,
        "base_model": "sdxl",
    },
    "pcm-sd3-4step": {
        "display": "PCM SD3 (4-Step Flow Match)",
        "speed": "~1.2s",
        "strengths": "Flow-matching consistency, high prompt adherence, clean composition",
        "steps": 4,
        "base_model": "sd3",
    },
}

DEFAULT_MODEL = "pcm-sd15-4step"


def _resolve_base_url() -> str:
    cfg = load_image_gen_config("pcm")
    return os.getenv("PCM_API_BASE_URL") or cfg.get("base_url") or DEFAULT_BASE_URL


def _resolve_model(model_name: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    if model_name and model_name in PCM_MODELS:
        return model_name, PCM_MODELS[model_name]
    return resolve_static_model(
        PCM_MODELS, DEFAULT_MODEL, env_var="PCM_IMAGE_MODEL", config_key="pcm", passthrough=False
    )


class PCMProvider(ImageGenProvider):
    name = "pcm"

    def capabilities(self) -> Dict[str, Any]:
        return {"modalities": ["text", "image"], "max_reference_images": 4}

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {"id": key, "name": meta["display"], "speed": meta["speed"], "strengths": meta["strengths"]}
            for key, meta in PCM_MODELS.items()
        ]

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        *,
        model: Optional[str] = None,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        steps: Optional[int] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        cleaned_prompt = (prompt or "").strip()
        if not cleaned_prompt:
            return prompt_required_error("pcm", model or DEFAULT_MODEL)

        resolved_model, model_meta = _resolve_model(model)
        aspect = resolve_aspect_ratio(aspect_ratio)
        inference_steps = steps or model_meta.get("steps", 4)
        base_url = _resolve_base_url()

        # Try calling the local PCM microservice endpoint if alive
        try:
            resp = requests.post(
                f"{base_url.rstrip('/')}/v1/images/generations",
                json={
                    "prompt": cleaned_prompt,
                    "model": resolved_model,
                    "aspect_ratio": aspect,
                    "steps": inference_steps,
                    "seed": seed or 42,
                    "image_url": image_url,
                    "reference_images": reference_image_urls or [],
                },
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                img_data = data.get("data", [{}])[0]
                if "b64_json" in img_data:
                    local_path = save_b64_image(img_data["b64_json"], prefix="pcm")
                    return success_response(
                        image=local_path,
                        model=resolved_model,
                        prompt=cleaned_prompt,
                        aspect_ratio=aspect,
                        provider="pcm",
                        extra={"steps": inference_steps, "base_model": model_meta["base_model"]},
                    )
                elif "url" in img_data:
                    local_path = save_url_image(img_data["url"], prefix="pcm")
                    return success_response(
                        image=local_path,
                        model=resolved_model,
                        prompt=cleaned_prompt,
                        aspect_ratio=aspect,
                        provider="pcm",
                        extra={"steps": inference_steps, "base_model": model_meta["base_model"]},
                    )
        except Exception as exc:
            logger.debug("PCM microservice not reachable at %s: %s. Falling back to local runner.", base_url, exc)

        # Standalone fallback: execute local runner script in PCM virtual environment
        pcm_repo = Path("C:/Users/tee/.gemini/antigravity-ide/scratch/Phased-Consistency-Model")
        venv_python = pcm_repo / ".venv" / "Scripts" / "python.exe"
        runner_script = pcm_repo / "run_local_inference.py"

        if venv_python.exists() and runner_script.exists():
            out_file = Path(os.getenv("HERMES_HOME", os.path.expanduser("~/.hermes"))) / "cache" / "images" / f"pcm_{int(time.time())}.png"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                str(venv_python),
                str(runner_script),
                "--prompt", cleaned_prompt,
                "--steps", str(inference_steps),
                "--output", str(out_file),
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=str(pcm_repo))
                if proc.returncode == 0 and out_file.exists():
                    return success_response(
                        image=out_file,
                        model=resolved_model,
                        prompt=cleaned_prompt,
                        aspect_ratio=aspect,
                        provider="pcm",
                        extra={"steps": inference_steps, "mode": "local_process"},
                    )
                else:
                    logger.warning("Local PCM execution non-zero exit: %s", proc.stderr)
            except Exception as e:
                logger.error("Failed running local PCM subprocess: %s", e)

        return error_response(
            "pcm",
            resolved_model,
            f"PCM backend service is not running at {base_url} and local execution failed. "
            "Please ensure the PCM microservice is started or dependencies are loaded.",
            error_type="backend_unavailable",
        )
