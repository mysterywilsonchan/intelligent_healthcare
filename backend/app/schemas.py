"""Pydantic 请求/响应模型。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------- Elder ----------
class ElderCreate(BaseModel):
    name: str
    gender: str = "未知"
    age: int = 0
    medical_history: str = ""
    medications: str = ""
    notes: str = ""


class ElderOut(ElderCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- VitalSign ----------
class VitalSignCreate(BaseModel):
    systolic: float | None = None
    diastolic: float | None = None
    heart_rate: float | None = None
    blood_glucose: float | None = None
    temperature: float | None = None
    spo2: float | None = None
    weight: float | None = None
    measured_at: datetime | None = None


class VitalSignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    measured_at: datetime
    systolic: float | None
    diastolic: float | None
    heart_rate: float | None
    blood_glucose: float | None
    temperature: float | None
    spo2: float | None
    weight: float | None


# ---------- Report ----------
class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    content_type: str
    parsed_text: str
    provider_used: str
    created_at: datetime


# ---------- Chat ----------
class ChatRequest(BaseModel):
    message: str
    provider: str | None = None  # 可覆盖默认 provider


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    content: str
    provider_used: str
    created_at: datetime


# ---------- Consult (面向客户的通用咨询，无状态) ----------
class ConsultTurn(BaseModel):
    role: str  # user / assistant
    content: str


class ConsultRequest(BaseModel):
    message: str
    history: list[ConsultTurn] = []


class ConsultReply(BaseModel):
    role: str = "assistant"
    content: str
    provider_used: str


# ---------- Assessment ----------
class AssessmentRequest(BaseModel):
    provider: str | None = None


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    risk_level: str
    risk_score: int
    findings_json: str
    syndrome_screening: str
    risk_assessment: str
    intervention_plan: str
    provider_used: str
    created_at: datetime


# ---------- Providers ----------
class ProviderInfo(BaseModel):
    name: str
    label: str
    available: bool       # 是否配置了 API key（mock 永远可用）
    supports_vision: bool
    is_default: bool
