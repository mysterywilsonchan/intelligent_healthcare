"""大模型 provider 抽象接口。

所有 provider（豆包/Qwen/DeepSeek/mock）实现统一接口，
对上层 agent 屏蔽厂商差异。
"""
from __future__ import annotations

from abc import ABC, abstractmethod

# 一条消息：{"role": "system|user|assistant", "content": "..."}
Message = dict[str, str]


class LLMProvider(ABC):
    name: str = "base"
    label: str = "Base"
    supports_vision: bool = False

    @property
    @abstractmethod
    def available(self) -> bool:
        """是否可用（已配置 API key）。mock 永远可用。"""

    @abstractmethod
    def chat(self, messages: list[Message]) -> str:
        """纯文本对话补全，返回助手回复文本。"""

    def chat_vision(self, prompt: str, image_data_url: str, system: str = "") -> str:
        """带图片的多模态补全。

        默认不支持；支持视觉的 provider 需重写。
        image_data_url 形如 data:image/png;base64,xxxx
        """
        raise NotImplementedError(f"{self.name} 不支持视觉输入")
