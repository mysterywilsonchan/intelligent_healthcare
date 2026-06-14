"""决策大脑评估接口 + provider 列表。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..agent.decision_brain import run_assessment
from ..db import get_db
from ..llm.providers import ALL_PROVIDERS, build_provider
from ..llm.registry import default_provider_name
from ..config import get_settings
from ..models import Assessment, Elder
from ..schemas import AssessmentOut, AssessmentRequest, ProviderInfo

router = APIRouter(tags=["assessment"])


@router.post("/api/elders/{elder_id}/assessment", response_model=AssessmentOut)
def create_assessment(
    elder_id: int, payload: AssessmentRequest, db: Session = Depends(get_db)
):
    elder = db.get(Elder, elder_id)
    if not elder:
        raise HTTPException(404, "老人档案不存在")
    return run_assessment(db, elder, payload.provider)


@router.get("/api/elders/{elder_id}/assessments", response_model=list[AssessmentOut])
def list_assessments(elder_id: int, db: Session = Depends(get_db)):
    if not db.get(Elder, elder_id):
        raise HTTPException(404, "老人档案不存在")
    return (
        db.query(Assessment)
        .filter(Assessment.elder_id == elder_id)
        .order_by(Assessment.created_at.desc())
        .all()
    )


@router.get("/api/providers", response_model=list[ProviderInfo])
def list_providers():
    settings = get_settings()
    default = default_provider_name()
    infos: list[ProviderInfo] = []
    for name in ALL_PROVIDERS:
        p = build_provider(name, settings)
        infos.append(
            ProviderInfo(
                name=p.name,
                label=p.label,
                available=p.available,
                supports_vision=p.supports_vision,
                is_default=(name == default),
            )
        )
    return infos
