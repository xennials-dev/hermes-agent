"""Unified Hugging Face Diffusers adapter for local open-source video generation."""

from __future__ import annotations

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from ..base_adapter import BaseModelAdapter, GenerationRequest, GenerationResponse
from ..model_registry import ModelRegistry

logger = logging.getLogger(__name__)


@ModelRegistry.register("diffusers_generic")
class GenericDiffusersAdapter(BaseModelAdapter):
    """Generic Diffusers pipeline loader for text-to-video and image-to-video."""

    def _load_model(self) -> None:
        model_id = self.config.get("diffusers_id") or self.config.get("model_path")
        if not model_id:
            raise ValueError(f"No diffusers_id or model_path configured for {self.config.get('display', 'diffusers')}")

        try:
            import torch
            from diffusers import AutoPipelineForText2Video, AutoPipelineForImage2Video
        except ImportError as exc:
            raise ImportError(
                "torch and diffusers are required for local model execution. "
                "Install with: pip install torch diffusers transformers accelerate imageio[ffmpeg]"
            ) from exc

        dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16

        logger.info("Loading Diffusers video pipeline from '%s' on %s (%s)...", model_id, self.device, dtype)
        try:
            # Try auto pipeline
            self.model = AutoPipelineForText2Video.from_pretrained(
                model_id,
                torch_dtype=dtype,
                trust_remote_code=True,
            )
        except Exception:
            try:
                from diffusers import DiffusionPipeline
                self.model = DiffusionPipeline.from_pretrained(
                    model_id,
                    torch_dtype=dtype,
                    trust_remote_code=True,
                )
            except Exception as e:
                raise RuntimeError(f"Failed to load pipeline for {model_id}: {e}") from e

        if self.device == "cuda":
            if hasattr(self.model, "enable_model_cpu_offload"):
                self.model.enable_model_cpu_offload()
            else:
                self.model.to("cuda")
            if hasattr(self.model, "enable_vae_slicing"):
                self.model.enable_vae_slicing()
        else:
            self.model.to(self.device)

    def _unload_model(self) -> None:
        if self.model is not None:
            del self.model
            self.model = None

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        start_time = time.time()
        if self.model is None:
            try:
                self._load_model()
            except Exception as exc:
                return GenerationResponse(
                    success=False,
                    error_message=f"Model loading failed: {exc}",
                    generation_time=time.time() - start_time,
                )

        try:
            import torch
            from diffusers.utils import export_to_video
            from PIL import Image

            num_frames = max(16, int((request.duration or 4) * (request.fps or 16)))
            generator = None
            if request.seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(request.seed)

            call_kwargs: Dict[str, Any] = {
                "prompt": request.prompt,
                "num_frames": min(num_frames, 64),
            }
            if request.negative_prompt:
                call_kwargs["negative_prompt"] = request.negative_prompt
            if generator:
                call_kwargs["generator"] = generator

            # Image-to-video branch
            if request.image_path and os.path.exists(request.image_path):
                img = Image.open(request.image_path).convert("RGB")
                call_kwargs["image"] = img

            # Run inference
            output = self.model(**call_kwargs)
            frames = output.frames[0]

            temp_output = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            temp_output.close()
            output_path = export_to_video(frames, temp_output.name, fps=request.fps or 16)

            return GenerationResponse(
                success=True,
                output_path=output_path,
                generation_time=time.time() - start_time,
                metadata={"num_frames": len(frames), "fps": request.fps or 16},
            )
        except Exception as exc:
            logger.exception("Inference failed for %s", self.config.get("display"))
            return GenerationResponse(
                success=False,
                error_message=str(exc),
                generation_time=time.time() - start_time,
            )


# Concrete model bindings for top open-source families
@ModelRegistry.register("open_sora")
class OpenSoraAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("open_sora_plan")
class OpenSoraPlanAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("wan2_1")
@ModelRegistry.register("wan2_2")
class WanAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("hunyuan_video")
class HunyuanAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("ltx_video")
class LTXVideoAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("cogvideox")
class CogVideoAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("mochi_1")
class MochiAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("svd")
class SVDAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("ovi")
class OviAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("alice_v1")
class AliceAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("bernini")
class BerniniAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("openvideo")
class OpenVideoAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("vace")
class VACEAdapter(GenericDiffusersAdapter):
    pass

@ModelRegistry.register("duix_avatar")
class DuixAvatarAdapter(GenericDiffusersAdapter):
    pass
