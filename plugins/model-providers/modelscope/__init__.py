"""ModelScope Inference API provider profile."""

from providers import register_provider
from providers.base import ProviderProfile

modelscope = ProviderProfile(
    name="modelscope",
    aliases=("ms", "modelscope-api", "modelscope-hub"),
    env_vars=("MODELSCOPE_API_KEY", "MODELSCOPE_TOKEN", "MODELSCOPE_API_TOKEN"),
    display_name="ModelScope",
    description="ModelScope Inference API (Free Tier & Serverless)",
    signup_url="https://modelscope.cn/my/myaccesstoken",
    fallback_models=(
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        "deepseek-ai/DeepSeek-V3",
        "deepseek-ai/DeepSeek-R1",
    ),
    base_url="https://api-inference.modelscope.cn/v1",
)

register_provider(modelscope)
