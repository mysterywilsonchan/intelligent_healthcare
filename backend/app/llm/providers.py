"""三家厂商 provider 的构造：base_url / 模型 / key 的差异集中在这里。"""
from __future__ import annotations

from ..config import Settings
from .base import LLMProvider
from .mock import MockProvider
from .openai_compatible import OpenAICompatibleProvider

# 三家 OpenAI 兼容接口的 base_url
DOUBAO_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def build_provider(name: str, settings: Settings) -> LLMProvider:
    """按名称构造 provider 实例。"""
    name = name.lower()
    if name == "doubao":
        return OpenAICompatibleProvider(
            name="doubao",
            label="豆包 / 火山方舟",
            base_url=DOUBAO_BASE_URL,
            api_key=settings.doubao_api_key,
            model=settings.doubao_model,
            vision_model=settings.doubao_vision_model,
        )
    if name == "qwen":
        return OpenAICompatibleProvider(
            name="qwen",
            label="通义千问 Qwen",
            base_url=QWEN_BASE_URL,
            api_key=settings.qwen_api_key,
            model=settings.qwen_model,
            vision_model=settings.qwen_vision_model,
        )
    if name == "deepseek":
        return OpenAICompatibleProvider(
            name="deepseek",
            label="DeepSeek",
            base_url=DEEPSEEK_BASE_URL,
            api_key=settings.deepseek_api_key,
            model=settings.deepseek_model,
            vision_model=None,  # DeepSeek 文本接口暂无视觉
        )
    if name == "mock":
        return MockProvider()
    raise ValueError(f"未知的 provider: {name}")


# 所有已知 provider 名称（用于前端展示）
ALL_PROVIDERS = ["doubao", "qwen", "deepseek", "mock"]
