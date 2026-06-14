"""ORM 模型：老人档案、生命体征、报告、评估、对话。"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Elder(Base):
    """老人档案 + 个人疾病数据库。"""

    __tablename__ = "elders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    gender: Mapped[str] = mapped_column(String(8), default="未知")
    age: Mapped[int] = mapped_column(Integer, default=0)
    # 个人疾病史 / 慢性病，逗号或换行分隔的自由文本
    medical_history: Mapped[str] = mapped_column(Text, default="")
    medications: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    vitals: Mapped[list["VitalSign"]] = relationship(
        back_populates="elder", cascade="all, delete-orphan", order_by="VitalSign.measured_at"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="elder", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="elder", cascade="all, delete-orphan"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="elder", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


class VitalSign(Base):
    """单次生命体征测量记录。指标可空，按需填写。"""

    __tablename__ = "vital_signs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    elder_id: Mapped[int] = mapped_column(ForeignKey("elders.id"))
    measured_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    systolic: Mapped[float | None] = mapped_column(Float, nullable=True)   # 收缩压 mmHg
    diastolic: Mapped[float | None] = mapped_column(Float, nullable=True)  # 舒张压 mmHg
    heart_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # 心率 bpm
    blood_glucose: Mapped[float | None] = mapped_column(Float, nullable=True)  # 血糖 mmol/L
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)  # 体温 ℃
    spo2: Mapped[float | None] = mapped_column(Float, nullable=True)  # 血氧 %
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)  # 体重 kg

    elder: Mapped["Elder"] = relationship(back_populates="vitals")


class Report(Base):
    """上传的医疗报告（图片/文档）及其解析结果。"""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    elder_id: Mapped[int] = mapped_column(ForeignKey("elders.id"))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(128), default="")
    stored_path: Mapped[str] = mapped_column(String(512), default="")
    parsed_text: Mapped[str] = mapped_column(Text, default="")  # 解析出的关键信息
    provider_used: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    elder: Mapped["Elder"] = relationship(back_populates="reports")


class Assessment(Base):
    """一次决策大脑评估的输出。"""

    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    elder_id: Mapped[int] = mapped_column(ForeignKey("elders.id"))
    risk_level: Mapped[str] = mapped_column(String(16), default="低")  # 低/中/高/危急
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    # 结构化证据 + LLM 文本，统一以 JSON 字符串存储
    findings_json: Mapped[str] = mapped_column(Text, default="{}")
    syndrome_screening: Mapped[str] = mapped_column(Text, default="")
    risk_assessment: Mapped[str] = mapped_column(Text, default="")
    intervention_plan: Mapped[str] = mapped_column(Text, default="")
    provider_used: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    elder: Mapped["Elder"] = relationship(back_populates="assessments")


class ChatMessage(Base):
    """健康问答对话记录。"""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    elder_id: Mapped[int] = mapped_column(ForeignKey("elders.id"))
    role: Mapped[str] = mapped_column(String(16))  # user / assistant
    content: Mapped[str] = mapped_column(Text)
    provider_used: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    elder: Mapped["Elder"] = relationship(back_populates="messages")
