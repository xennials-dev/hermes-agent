"""Unit tests for the open-source video generation plugin."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
import pytest

from plugins.video_gen.opensource import OpenSourceVideoGenProvider
from plugins.video_gen.opensource.base_adapter import GenerationRequest, GenerationResponse
from plugins.video_gen.opensource.model_registry import ModelRegistry, OPENSOURCE_MODELS_CATALOG
from plugins.video_gen.opensource.manager import ModelManager


@pytest.fixture(autouse=True)
def _clean_manager(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    manager = ModelManager()
    manager.unload_all()
    yield
    manager.unload_all()


def test_provider_identity_and_catalog():
    """Verify provider identity, availability, and model catalog size."""
    provider = OpenSourceVideoGenProvider()
    assert provider.name == "opensource"
    assert provider.display_name == "Open-Source Video Models"
    assert provider.is_available() is True
    assert provider.default_model() == "wan2_1"

    models = provider.list_models()
    assert len(models) >= 18
    model_ids = {m["id"] for m in models}
    assert "open_sora" in model_ids
    assert "wan2_1" in model_ids
    assert "hunyuan_video" in model_ids
    assert "ltx_video" in model_ids
    assert "cogvideox" in model_ids
    assert "mochi_1" in model_ids
    assert "svd" in model_ids
    assert "comfyui_bridge" in model_ids


def test_model_registry_fallback_resolution():
    """Verify fallback chain for heavy models."""
    wan_meta = OPENSOURCE_MODELS_CATALOG.get("wan2_1", {})
    assert wan_meta.get("fallback") == "ltx_video"

    sora_meta = OPENSOURCE_MODELS_CATALOG.get("open_sora", {})
    assert sora_meta.get("fallback") == "open_sora_plan"


def test_manager_lru_eviction():
    """Verify LRU model eviction when exceeding max_active_models."""
    manager = ModelManager(max_active_models=2)

    mock_adapter_1 = MagicMock()
    mock_adapter_2 = MagicMock()
    mock_adapter_3 = MagicMock()

    with patch.object(ModelRegistry, "get_model_class") as mock_get_class:
        mock_get_class.side_effect = [
            lambda cfg: mock_adapter_1,
            lambda cfg: mock_adapter_2,
            lambda cfg: mock_adapter_3,
        ]

        manager.get_or_load_model("open_sora")
        manager.get_or_load_model("wan2_1")
        assert len(manager.active_models) == 2
        assert "open_sora" in manager.active_models
        assert "wan2_1" in manager.active_models

        # Load 3rd model -> should evict open_sora
        manager.get_or_load_model("mochi_1")
        assert len(manager.active_models) == 2
        assert "open_sora" not in manager.active_models
        assert "wan2_1" in manager.active_models
        assert "mochi_1" in manager.active_models
        mock_adapter_1._unload_model.assert_called_once()


def test_execute_with_fallback_success():
    """Verify fallback activates when primary model fails."""
    manager = ModelManager()

    failing_adapter = MagicMock()
    failing_adapter.generate.return_value = GenerationResponse(
        success=False,
        error_message="CUDA OOM on 14B model",
    )

    success_adapter = MagicMock()
    success_adapter.generate.return_value = GenerationResponse(
        success=True,
        output_path="/tmp/video.mp4",
        metadata={"backend": "diffusers"},
    )

    def fake_get_or_load(name, config=None):
        if name == "wan2_1":
            return failing_adapter
        return success_adapter

    with patch.object(manager, "get_or_load_model", side_effect=fake_get_or_load):
        req = GenerationRequest(prompt="A cinematic drone shot of mountains")
        resp = manager.execute_with_fallback("wan2_1", req, enable_fallback=True)

        assert resp.success is True
        assert resp.output_path == "/tmp/video.mp4"
        assert resp.metadata["resolved_model"] == "ltx_video"


def test_provider_generate_integration(tmp_path):
    """Verify provider.generate() handles response contracts correctly."""
    provider = OpenSourceVideoGenProvider()

    test_video = tmp_path / "rendered.mp4"
    test_video.write_bytes(b"mock_mp4_bytes")

    success_adapter = MagicMock()
    success_adapter.generate.return_value = GenerationResponse(
        success=True,
        output_path=str(test_video),
    )

    manager = ModelManager()
    with patch.object(manager, "get_or_load_model", return_value=success_adapter):
        result = provider.generate(
            prompt="A futuristic neon city at night",
            model="ltx_video",
            duration=5,
            aspect_ratio="16:9",
        )

        assert result["success"] is True
        assert result["model"] == "ltx_video"
        assert result["provider"] == "opensource"
        assert result["duration"] == 5
        assert result["video"] == str(test_video)


def test_plugin_register_contract():
    """Verify register(ctx) registers provider without error."""
    from plugins.video_gen.opensource import register
    ctx = MagicMock()
    register(ctx)
    ctx.register_video_gen_provider.assert_called_once()
