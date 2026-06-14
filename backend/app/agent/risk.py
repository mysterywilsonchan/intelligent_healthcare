"""规则化风险引擎：逐指标分级 + 时序趋势 + 整体分级预警。

对应幻灯片的"分类 / 回归"：
- 分类 = 按老年人医学参考区间对每个指标判级（正常/偏高/偏低/危急）。
- 回归 = 对时序生命体征做简单线性斜率，识别恶化趋势。
说明：MVP 使用规则与简单统计，不引入重训练模型；阈值参考常见老年人参考范围，仅用于演示。
"""
from __future__ import annotations

from dataclasses import dataclass, field

# 风险等级与权重分
LEVELS = ["低", "中", "高", "危急"]
_LEVEL_SCORE = {"正常": 0, "偏低": 1, "偏高": 1, "中": 1, "高": 2, "危急": 3}


@dataclass
class IndicatorResult:
    name: str
    value: float | None
    unit: str
    status: str          # 正常/偏高/偏低/危急/无数据
    detail: str = ""
    trend: str = ""      # 上升/下降/平稳/数据不足


@dataclass
class RiskResult:
    risk_level: str = "低"
    risk_score: int = 0
    indicators: list[IndicatorResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "indicators": [vars(i) for i in self.indicators],
        }


def _grade_bp(systolic: float | None, diastolic: float | None) -> IndicatorResult:
    if systolic is None and diastolic is None:
        return IndicatorResult("血压", None, "mmHg", "无数据")
    s = systolic or 0
    d = diastolic or 0
    if s >= 180 or d >= 110:
        status, detail = "危急", "达到高血压危象阈值，需紧急处理"
    elif s >= 140 or d >= 90:
        status, detail = "偏高", "高于老年人推荐控制目标"
    elif s < 90 or d < 60:
        status, detail = "偏低", "血压偏低，注意体位性低血压"
    else:
        status, detail = "正常", "处于合理范围"
    return IndicatorResult("血压", s, "mmHg", status, detail)


def _grade_simple(
    name: str,
    value: float | None,
    unit: str,
    *,
    low: float,
    high: float,
    crit_high: float | None = None,
    crit_low: float | None = None,
) -> IndicatorResult:
    if value is None:
        return IndicatorResult(name, None, unit, "无数据")
    if crit_high is not None and value >= crit_high:
        return IndicatorResult(name, value, unit, "危急", f"{name}严重偏高")
    if crit_low is not None and value <= crit_low:
        return IndicatorResult(name, value, unit, "危急", f"{name}严重偏低")
    if value > high:
        return IndicatorResult(name, value, unit, "偏高", f"高于参考范围 {low}-{high}")
    if value < low:
        return IndicatorResult(name, value, unit, "偏低", f"低于参考范围 {low}-{high}")
    return IndicatorResult(name, value, unit, "正常", f"参考范围 {low}-{high}")


def _trend(values: list[float]) -> str:
    """对一组按时间排序的值做简单斜率判断（轻量回归）。"""
    pts = [v for v in values if v is not None]
    if len(pts) < 3:
        return "数据不足"
    n = len(pts)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(pts) / n
    denom = sum((x - mean_x) ** 2 for x in xs) or 1
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, pts)) / denom
    # 以均值的 2% 作为变化阈值
    thresh = abs(mean_y) * 0.02 or 0.01
    if slope > thresh:
        return "上升"
    if slope < -thresh:
        return "下降"
    return "平稳"


def assess(vitals: list) -> RiskResult:
    """vitals: 按时间升序的 VitalSign ORM 列表（或具同名属性的对象）。"""
    result = RiskResult()
    if not vitals:
        result.indicators.append(IndicatorResult("生命体征", None, "", "无数据"))
        return result

    latest = vitals[-1]

    indicators = [
        _grade_bp(latest.systolic, latest.diastolic),
        _grade_simple("心率", latest.heart_rate, "bpm", low=60, high=100,
                      crit_high=130, crit_low=40),
        _grade_simple("空腹血糖", latest.blood_glucose, "mmol/L", low=3.9, high=7.0,
                      crit_high=16.7, crit_low=2.8),
        _grade_simple("体温", latest.temperature, "℃", low=36.0, high=37.2,
                      crit_high=39.5, crit_low=35.0),
        _grade_simple("血氧", latest.spo2, "%", low=95, high=100, crit_low=90),
    ]

    # 趋势：基于历史序列
    series = {
        "血压": [v.systolic for v in vitals],
        "心率": [v.heart_rate for v in vitals],
        "空腹血糖": [v.blood_glucose for v in vitals],
        "体温": [v.temperature for v in vitals],
        "血氧": [v.spo2 for v in vitals],
    }
    for ind in indicators:
        if ind.name in series:
            ind.trend = _trend([s for s in series[ind.name] if s is not None])

    result.indicators = indicators
    result.risk_score = sum(_LEVEL_SCORE.get(i.status, 0) for i in indicators)

    # 分级预警：任一危急 -> 危急；否则按累计分映射
    if any(i.status == "危急" for i in indicators):
        result.risk_level = "危急"
    elif result.risk_score >= 4:
        result.risk_level = "高"
    elif result.risk_score >= 2:
        result.risk_level = "中"
    else:
        result.risk_level = "低"
    return result
