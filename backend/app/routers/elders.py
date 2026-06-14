"""老人档案 + 个人疾病数据库。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Elder
from ..schemas import ElderCreate, ElderOut

router = APIRouter(prefix="/api/elders", tags=["elders"])


@router.get("", response_model=list[ElderOut])
def list_elders(db: Session = Depends(get_db)):
    return db.query(Elder).order_by(Elder.created_at.desc()).all()


@router.post("", response_model=ElderOut, status_code=201)
def create_elder(payload: ElderCreate, db: Session = Depends(get_db)):
    elder = Elder(**payload.model_dump())
    db.add(elder)
    db.commit()
    db.refresh(elder)
    return elder


@router.get("/{elder_id}", response_model=ElderOut)
def get_elder(elder_id: int, db: Session = Depends(get_db)):
    elder = db.get(Elder, elder_id)
    if not elder:
        raise HTTPException(404, "老人档案不存在")
    return elder


@router.put("/{elder_id}", response_model=ElderOut)
def update_elder(elder_id: int, payload: ElderCreate, db: Session = Depends(get_db)):
    elder = db.get(Elder, elder_id)
    if not elder:
        raise HTTPException(404, "老人档案不存在")
    for k, v in payload.model_dump().items():
        setattr(elder, k, v)
    db.commit()
    db.refresh(elder)
    return elder


@router.delete("/{elder_id}", status_code=204)
def delete_elder(elder_id: int, db: Session = Depends(get_db)):
    elder = db.get(Elder, elder_id)
    if not elder:
        raise HTTPException(404, "老人档案不存在")
    db.delete(elder)
    db.commit()
