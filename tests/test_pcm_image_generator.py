import json
import os
from pathlib import Path
import pytest

from tools.registry import registry
from tools.pcm_image_generator import (
    HermesPCMTool,
    HERMES_PCM_TOOL_SCHEMA,
    _handle_generate_pcm_asset,
)


def test_hermes_pcm_tool_initialization(tmp_path):
    tool = HermesPCMTool(output_dir=str(tmp_path / "assets"))
    assert os.path.exists(tool.output_dir)


def test_hermes_pcm_tool_execute(tmp_path):
    tool = HermesPCMTool(output_dir=str(tmp_path / "assets"))
    res = tool.execute(
        prompt="A minimalist developer dashboard wireframe with dark slate theme",
        steps=4,
        resolution_tag="sd15",
        filename="custom_dashboard.png",
    )
    assert res["status"] == "success"
    assert "file_path" in res
    assert Path(res["file_path"]).exists()
    assert res["steps_used"] == 4
    assert res["generation_time_seconds"] >= 0


def test_generate_pcm_asset_registry_registration():
    # Verify the tool is officially registered in registry
    assert "generate_pcm_asset" in registry._tools
    tool_meta = registry._tools["generate_pcm_asset"]
    assert tool_meta.name == "generate_pcm_asset"
    assert tool_meta.toolset == "pcm"
    assert tool_meta.emoji == "⚡"


def test_handle_generate_pcm_asset():
    raw_res = _handle_generate_pcm_asset({
        "prompt": "Futuristic AI code agent flowchart, clean diagram",
        "steps": 8,
        "resolution_tag": "sdxl",
    })
    res = json.loads(raw_res)
    assert res["status"] == "success"
    assert Path(res["file_path"]).exists()
    assert res["steps_used"] == 8
