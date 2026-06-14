"""多模态归一：把报告图片/文档解析为文本，供决策大脑使用。"""
from __future__ import annotations

import base64
import mimetypes

from .prompts import REPORT_VISION_PROMPT
from ..llm.registry import get_vision_provider

# 视为图片的内容类型前缀
_IMAGE_PREFIX = "image/"
# 直接按文本读取的类型
_TEXT_TYPES = {"text/plain", "application/json", "text/csv", "text/markdown"}


def _to_data_url(raw: bytes, content_type: str) -> str:
    b64 = base64.b64encode(raw).decode("ascii")
    ct = content_type or "image/png"
    return f"data:{ct};base64,{b64}"


def parse_report(
    raw: bytes,
    filename: str,
    content_type: str,
    provider_name: str | None = None,
) -> tuple[str, str]:
    """解析一份报告，返回 (解析文本, 实际使用的 provider 名)。

    - 图片：走视觉模型（不支持视觉的 provider 自动回退到默认视觉 provider）。
    - 纯文本/CSV/JSON：直接解码。
    - 其他（如 PDF）：MVP 暂提示需要文本化，返回占位说明。
    """
    guessed = content_type or mimetypes.guess_type(filename)[0] or ""

    if guessed.startswith(_IMAGE_PREFIX):
        provider, fell_back = get_vision_provider(provider_name)
        data_url = _to_data_url(raw, guessed)
        text = provider.chat_vision(REPORT_VISION_PROMPT, data_url)
        used = provider.name + ("(视觉回退)" if fell_back else "")
        return text, used

    if guessed in _TEXT_TYPES or filename.lower().endswith((".txt", ".csv", ".md", ".json")):
        try:
            return raw.decode("utf-8", errors="ignore").strip(), "本地文本解析"
        except Exception:  # noqa: BLE001
            return "（文本解析失败）", "本地文本解析"

    return (
        f"已上传文件 {filename}（类型 {guessed or '未知'}）。"
        "当前 MVP 暂不支持该格式的自动解析，请上传图片或文本格式的报告。",
        "未解析",
    )
