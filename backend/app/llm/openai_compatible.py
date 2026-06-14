"""基于 OpenAI 兼容接口的通用 provider 实现。

豆包(火山方舟)、Qwen(DashScope 兼容模式)、DeepSeek 均提供 OpenAI 兼容的
/chat/completions 接口，故共用同一实现，仅 base_url / api_key / model 不同。
"""
from __future__ import annotations

from openai import OpenAI

from ..config import get_settings
from .base import LLMProvider, Message


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        *,
        name: str,
        label: str,
        base_url: str,
        api_key: str,
        model: str,
        vision_model: str | None = None,
    ) -> None:
        self.name = name
        self.label = label
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.vision_model = vision_model
        self.supports_vision = bool(vision_model)
        self._settings = get_settings()
        # 即使 key 为空也构造 client；调用时才会真正发请求
        self._client = OpenAI(
            api_key=api_key or "EMPTY",
            base_url=base_url,
            timeout=self._settings.llm_timeout,
        )

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[Message]) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=self._settings.llm_temperature,
        )
        return (resp.choices[0].message.content or "").strip()

    def chat_vision(self, prompt: str, image_data_url: str, system: str = "") -> str:
        if not self.supports_vision:
            raise NotImplementedError(f"{self.name} 不支持视觉输入")
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            }
        )
        resp = self._client.chat.completions.create(
            model=self.vision_model,  # type: ignore[arg-type]
            messages=messages,  # type: ignore[arg-type]
            temperature=self._settings.llm_temperature,
        )
        return (resp.choices[0].message.content or "").strip()
