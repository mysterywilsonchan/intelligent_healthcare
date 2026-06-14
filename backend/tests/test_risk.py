"""风险引擎分级规则测试。"""
from dataclasses import dataclass

from app.agent import risk


@dataclass
class FakeVital:
    systolic: float | None = None
    diastolic: float | None = None
    heart_rate: float | None = None
    blood_glucose: float | None = None
    temperature: float | None = None
    spo2: float | None = None
    weight: float | None = None


def test_no_vitals_is_low():
    r = risk.assess([])
    assert r.risk_level == "低"


def test_normal_vitals_low():
    r = risk.assess([FakeVital(systolic=120, diastolic=78, heart_rate=72,
                               blood_glucose=5.5, temperature=36.6, spo2=98)])
    assert r.risk_level == "低"
    assert all(i.status in ("正常", "无数据") for i in r.indicators)


def test_critical_bp_triggers_crit():
    r = risk.assess([FakeVital(systolic=190, diastolic=115)])
    assert r.risk_level == "危急"


def test_high_glucose_and_bp_raises_level():
    r = risk.assess([FakeVital(systolic=150, diastolic=95, blood_glucose=9.0)])
    assert r.risk_level in ("中", "高")
    assert r.risk_score >= 2


def test_trend_detected_upward():
    series = [FakeVital(systolic=v) for v in (120, 130, 140, 150, 160)]
    r = risk.assess(series)
    bp = next(i for i in r.indicators if i.name == "血压")
    assert bp.trend == "上升"
