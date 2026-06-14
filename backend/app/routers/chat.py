"""健康问答对话（文本 / 前端语音转写后的文本）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..agent.prompts import CHAT_SYSTEM
from ..db import get_db
from ..llm.registry import get_provider
from ..models import ChatMessage, Elder
from ..schemas import ChatMessageOut, ChatRequest

router = APIRouter(prefix="/api/elders/{elder_id}/chat", tags=["chat"])


def _elder_context(elder: Elder) -> str:
    return (
        f"【当前老人档案】姓名:{elder.name} 性别:{elder.gender} 年龄:{elder.age}; "
        f"疾病史:{elder.medical_history or '无'}; 用药:{elder.medications or '无'}。"
    )


@router.get("", response_model=list[ChatMessageOut])
def history(elder_id: int, db: Session = Depends(get_db)):
    if not db.get(Elder, elder_id):
        raise HTTPException(404, "老人档案不存在")
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.elder_id == elder_id)
        .order_by(ChatMessage.created_at)
        .all()
    )


@router.post("", response_model=ChatMessageOut)
def send(elder_id: int, payload: ChatRequest, db: Session = Depends(get_db)):
    elder = db.get(Elder, elder_id)
    if not elder:
        raise HTTPException(404, "老人档案不存在")
    if not payload.message.strip():
        raise HTTPException(400, "消息不能为空")

    # 存用户消息
    db.add(ChatMessage(elder_id=elder_id, role="user", content=payload.message))
    db.commit()

    # 组装上下文：系统提示 + 老人档案 + 最近若干轮历史
    recent = (
        db.query(ChatMessage)
        .filter(ChatMessage.elder_id == elder_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
        .all()
    )
    recent = list(reversed(recent))
    messages = [
        {"role": "system", "content": CHAT_SYSTEM + "\n" + _elder_context(elder)},
    ]
    for m in recent:
        messages.append({"role": m.role, "content": m.content})

    provider = get_provider(payload.provider)
    try:
        reply = provider.chat(messages)
    except Exception as exc:  # noqa: BLE001
        reply = f"（调用大模型失败：{exc}，请检查 provider 配置或改用 mock）"

    assistant = ChatMessage(
        elder_id=elder_id, role="assistant", content=reply, provider_used=provider.name
    )
    db.add(assistant)
    db.commit()
    db.refresh(assistant)
    return assistant
