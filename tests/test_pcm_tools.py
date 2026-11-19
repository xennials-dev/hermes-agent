import json
import os
from pathlib import Path
import pytest

from tools.pcm_tools import (
    handle_pcm_generate_mockup,
    handle_pcm_storyboard,
    handle_pcm_component_asset,
    handle_pcm_debug_diagram,
)


def test_pcm_generate_mockup():
    res_str = handle_pcm_generate_mockup({
        "prompt": "Modern SaaS landing page hero section with gradient background",
        "style_preset": "modern_saas",
        "steps": 4,
    })
    data = json.loads(res_str)
    assert data["success"] is True
    assert "mockup_" in data["image_path"]
    assert Path(data["image_path"]).exists()


def test_pcm_storyboard():
    res_str = handle_pcm_storyboard({
        "script_panels": [
            "Agent receives task from user",
            "Agent searches local codebase with ripgrep",
            "Agent compiles code and runs verification tests",
        ],
        "consistency_seed": 100,
        "steps": 4,
    })
    data = json.loads(res_str)
    assert data["success"] is True
    assert data["panels_generated"] == 3
    assert len(data["panels"]) == 3
    for p in data["panels"]:
        assert Path(p["image_path"]).exists()


def test_pcm_component_asset(tmp_path):
    res_str = handle_pcm_component_asset({
        "component_name": "feature_card",
        "prompt": "Futuristic AI chip illustration with glowing circuit traces",
        "theme_context": "dark slate and electric cyan",
        "output_dir": str(tmp_path / "public" / "images"),
        "steps": 4,
    })
    data = json.loads(res_str)
    assert data["success"] is True
    assert "feature_card.png" in data["file_path"]
    assert Path(data["file_path"]).exists()
    assert "<img" in data["jsx_snippet"]


def test_pcm_debug_diagram():
    res_str = handle_pcm_debug_diagram({
        "concept": "FastAPI to Diffusers PCM request dispatching pipeline",
        "architecture_flow": "Client -> FastAPI Gateway -> Scheduler Worker -> Latent Denoise -> Image Output",
        "format": "architecture",
    })
    data = json.loads(res_str)
    assert data["success"] is True
    assert Path(data["diagram_path"]).exists()
    assert "![" in data["markdown_embed"]
