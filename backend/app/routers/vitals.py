"""生命体征录入与查询（含规则风险分级）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..agent import risk
from ..db import get_db
from ..models import Elder, VitalSign
from ..schemas import VitalSignCreate, VitalSignOut

router = APIRouter(prefix="/api/elders/{elder_id}/vitals", tags=["vitals"])


def _get_elder(elder_id: int, db: Session) -> Elder:
    elder = db.get(Elder, elder_id)
    if not elder:
        raise HTTPException(404, "老人档案不存在")
    return elder


@router.get("", response_model=list[VitalSignOut])
def list_vitals(elder_id: int, db: Session = Depends(get_db)):
    _get_elder(elder_id, db)
    return (
        db.query(VitalSign)
        .filter(VitalSign.elder_id == elder_id)
        .order_by(VitalSign.measured_at)
        .all()
    )


@router.post("", response_model=VitalSignOut, status_code=201)
def add_vital(elder_id: int, payload: VitalSignCreate, db: Session = Depends(get_db)):
    _get_elder(elder_id, db)
    data = payload.model_dump(exclude_none=False)
    measured_at = data.pop("measured_at", None)
    vital = VitalSign(elder_id=elder_id, **data)
    if measured_at:
        vital.measured_at = measured_at
    db.add(vital)
    db.commit()
    db.refresh(vital)
    return vital


@router.get("/risk")
def vitals_risk(elder_id: int, db: Session = Depends(get_db)):
    """返回当前规则化风险分级（不调用大模型）。"""
    elder = _get_elder(elder_id, db)
    return risk.assess(list(elder.vitals)).to_dict()
