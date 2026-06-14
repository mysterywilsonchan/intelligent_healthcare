"""决策大脑：全链路闭环编排器。

数据整合 → 规则风险识别 → 趋势分析 → 分级预警 → LLM 综合生成 → 落库。
"""
from __future__ import annotations

import json
import re

from sqlalchemy.orm import Session

from ..llm.registry import get_provider
from ..models import Assessment, Elder
from . import risk
from .prompts import DECISION_SYSTEM, build_decision_user_prompt


def _gather_context(elder: Elder, risk_result: risk.RiskResult) -> dict:
    """组装结构化证据。"""
    return {
        "档案": {
            "姓名": elder.name,
            "性别": elder.gender,
            "年龄": elder.age,
        },
        "个人疾病史": elder.medical_history or "无记录",
        "用药情况": elder.medications or "无记录",
        "备注": elder.notes or "",
        "生命体征风险分级": risk_result.to_dict(),
        "已解析检查报告": [
            {"文件": r.filename, "解析": r.parsed_text}
            for r in elder.reports
            if r.parsed_text
        ],
    }


def _split_sections(text: str) -> dict[str, str]:
    """从 LLM 输出中按【标题】切分三段。缺失时回退为整体文本。"""
    sections = {"syndrome": "", "risk": "", "plan": ""}
    mapping = {
        "老年综合征筛查": "syndrome",
        "详细风险评估": "risk",
        "个性化干预方案": "plan",
    }
    # 匹配【标题】...直到下一个【或结尾
    pattern = re.compile(r"【(.+?)】(.*?)(?=【|$)", re.S)
    matched = False
    for m in pattern.finditer(text):
        title = m.group(1).strip()
        body = m.group(2).strip()
        for key, slot in mapping.items():
            if key in title:
                sections[slot] = body
                matched = True
    if not matched:
        sections["risk"] = text.strip()
    return sections


def run_assessment(
    db: Session, elder: Elder, provider_name: str | None = None
) -> Assessment:
    """执行一次完整评估并持久化。"""
    # 1+2+3+4：规则引擎完成风险识别、趋势、分级
    risk_result = risk.assess(list(elder.vitals))

    # 5：LLM 综合生成
    context = _gather_context(elder, risk_result)
    provider = get_provider(provider_name)
    messages = [
        {"role": "system", "content": DECISION_SYSTEM},
        {"role": "user", "content": build_decision_user_prompt(context)},
    ]
    try:
        llm_text = provider.chat(messages)
    except Exception as exc:  # noqa: BLE001
        llm_text = (
            f"【详细风险评估】调用大模型失败：{exc}。"
            "已基于规则引擎给出风险分级，请检查 provider 配置或改用 mock。"
        )
    sections = _split_sections(llm_text)

    # 6：落库
    assessment = Assessment(
        elder_id=elder.id,
        risk_level=risk_result.risk_level,
        risk_score=risk_result.risk_score,
        findings_json=json.dumps(risk_result.to_dict(), ensure_ascii=False),
        syndrome_screening=sections["syndrome"],
        risk_assessment=sections["risk"],
        intervention_plan=sections["plan"],
        provider_used=provider.name,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment
