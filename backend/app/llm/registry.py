"""Provider 选择工厂：默认豆包，支持运行时切换与视觉回退。"""
from __future__ import annotations

from functools import lru_cache

from ..config import get_settings
from .base import LLMProvider
from .providers import ALL_PROVIDERS, build_provider


@lru_cache(maxsize=8)
def _cached_provider(name: str) -> LLMProvider:
    return build_provider(name, get_settings())


def get_provider(name: str | None = None) -> LLMProvider:
    """获取文本对话 provider。

    name 为空时使用配置中的默认 provider（默认豆包）。
    """
    settings = get_settings()
    chosen = (name or settings.llm_provider or "doubao").lower()
    if chosen not in ALL_PROVIDERS:
        chosen = settings.llm_provider or "doubao"
    return _cached_provider(chosen)


def get_vision_provider(name: str | None = None) -> tuple[LLMProvider, bool]:
    """获取支持视觉的 provider。

    若所选 provider 不支持视觉（如 DeepSeek），回退到 VISION_FALLBACK_PROVIDER（默认豆包）。
    返回 (provider, fell_back) —— fell_back 表示是否发生了回退。
    """
    settings = get_settings()
    primary = get_provider(name)
    if primary.supports_vision:
        return primary, False
    fallback = _cached_provider(settings.vision_fallback_provider.lower())
    return fallback, True


def default_provider_name() -> str:
    return (get_settings().llm_provider or "doubao").lower()
