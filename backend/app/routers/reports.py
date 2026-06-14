"""医疗报告上传与多模态解析。"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..agent.multimodal import parse_report
from ..config import get_settings
from ..db import get_db
from ..models import Elder, Report
from ..schemas import ReportOut

router = APIRouter(prefix="/api/elders/{elder_id}/reports", tags=["reports"])
settings = get_settings()


@router.get("", response_model=list[ReportOut])
def list_reports(elder_id: int, db: Session = Depends(get_db)):
    if not db.get(Elder, elder_id):
        raise HTTPException(404, "老人档案不存在")
    return (
        db.query(Report)
        .filter(Report.elder_id == elder_id)
        .order_by(Report.created_at.desc())
        .all()
    )


@router.post("", response_model=ReportOut, status_code=201)
async def upload_report(
    elder_id: int,
    file: UploadFile = File(...),
    provider: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if not db.get(Elder, elder_id):
        raise HTTPException(404, "老人档案不存在")

    raw = await file.read()
    if not raw:
        raise HTTPException(400, "空文件")

    # 保存原文件
    ext = (file.filename or "report").split(".")[-1]
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    stored_path = settings_upload_path(stored_name)
    stored_path.write_bytes(raw)

    # 多模态解析
    parsed_text, provider_used = parse_report(
        raw, file.filename or stored_name, file.content_type or "", provider
    )

    report = Report(
        elder_id=elder_id,
        filename=file.filename or stored_name,
        content_type=file.content_type or "",
        stored_path=str(stored_path),
        parsed_text=parsed_text,
        provider_used=provider_used,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def settings_upload_path(name: str):
    from ..config import UPLOAD_DIR

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR / name
