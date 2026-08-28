import os
import pytest
from providers import get_provider_profile


def test_nvidia_nim_provider_registration():
    provider = get_provider_profile("nvidia-nim")
    assert provider is not None
    assert provider.name == "nvidia-nim"
    assert "nvidia/llama-3.1-nemotron-70b-instruct" in provider.fallback_models
    assert provider.supports_health_check is True
    assert provider.supports_vision is True


def test_nvidia_nim_endpoint_discovery(monkeypatch):
    monkeypatch.setenv("NVIDIA_NIM_BASE_URL", "http://my-nim-cluster:8000/v1")
    # Discover and verify
    provider = get_provider_profile("nvidia-nim")
    assert provider.resolve_base_url() == "http://my-nim-cluster:8000/v1"
