"""NVIDIA NIM dedicated provider with local microservice auto-discovery and health probing."""

import os
import urllib.request
import json
import logging
from providers import register_provider
from providers.base import ProviderProfile

logger = logging.getLogger(__name__)


def discover_nim_endpoint() -> str:
    """Auto-discover active NVIDIA NIM endpoint (local container vs cloud API)."""
    # 1. User specified explicit NIM URL
    explicit_url = os.getenv("NVIDIA_NIM_BASE_URL") or os.getenv("NIM_BASE_URL")
    if explicit_url:
        return explicit_url.rstrip("/")

    # 2. Probe local NIM microservice container (default port 8000)
    local_url = "http://localhost:8000/v1"
    try:
        req = urllib.request.Request(
            f"{local_url}/models",
            headers={"User-Agent": "hermes-agent"},
        )
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            if resp.status == 200:
                logger.info("Auto-discovered local NVIDIA NIM microservice at %s", local_url)
                return local_url
    except Exception:
        pass

    # 3. Default to NVIDIA Hosted Cloud API
    return "https://integrate.api.nvidia.com/v1"


class NvidiaNimProviderProfile(ProviderProfile):
    """Custom ProviderProfile with dynamic endpoint resolution and model probing."""

    def resolve_base_url(self) -> str:
        return discover_nim_endpoint()

    def fetch_models(self, api_key: str = "") -> list:
        """Fetch available models from the active NIM endpoint."""
        url = f"{self.resolve_base_url()}/models"
        headers = {"User-Agent": "hermes-agent"}
        key = api_key or os.getenv("NVIDIA_API_KEY") or os.getenv("NGC_API_KEY", "")
        if key:
            headers["Authorization"] = f"Bearer {key}"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                    if models:
                        return models
        except Exception as e:
            logger.debug("Failed to fetch NVIDIA NIM models from %s: %s", url, e)

        return list(self.fallback_models)


nvidia_nim = NvidiaNimProviderProfile(
    name="nvidia-nim",
    aliases=("nim", "nvidia_nim"),
    env_vars=("NVIDIA_API_KEY", "NGC_API_KEY"),
    display_name="NVIDIA NIM (Microservices & Cloud)",
    description="NVIDIA NIM — GPU-accelerated microservices and Nemotron models with auto-discovery",
    signup_url="https://build.nvidia.com/",
    fallback_models=(
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "nvidia/nemotron-4-340b-instruct",
        "meta/llama-3.3-70b-instruct",
        "deepseek-ai/deepseek-r1",
    ),
    base_url="https://integrate.api.nvidia.com/v1",
    default_max_tokens=16384,
    supports_health_check=True,
    supports_vision=True,
)

register_provider(nvidia_nim)
