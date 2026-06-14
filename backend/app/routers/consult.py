"""面向客户的通用老年健康咨询（无状态，不绑定具体老人档案）。

会话历史由前端维护并随请求带上，服务端只负责调用大模型。
provider 固定取配置默认值，不接受前端指定。
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..agent.prompts import CONSULT_SYSTEM
from ..llm.registry import get_provider
from ..schemas import ConsultReply, ConsultRequest

router = APIRouter(prefix="/api/consult", tags=["consult"])

# 仅携带最近若干轮历史，控制上下文长度
_MAX_HISTORY = 12


@router.post("", response_model=ConsultReply)
def consult(payload: ConsultRequest):
    if not payload.message.strip():
        raise HTTPException(400, "请输入您的问题")

    messages = [{"role": "system", "content": CONSULT_SYSTEM}]
    for turn in payload.history[-_MAX_HISTORY:]:
        if turn.role in ("user", "assistant") and turn.content.strip():
            messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": payload.message})

    provider = get_provider()  # 使用配置默认 provider
    try:
        reply = provider.chat(messages)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"智能体暂时无法回应：{exc}")

    return ConsultReply(content=reply, provider_used=provider.name)
