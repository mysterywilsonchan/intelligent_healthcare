"""离线 Mock provider：无 API key 时返回结构化模拟结果，保证演示与测试可跑通。

它会读取最后一条 user 消息里的关键词，给出合理的中文模拟输出，
让整个决策大脑闭环在没有真实大模型的情况下也能演示。
"""
from __future__ import annotations

from .base import LLMProvider, Message


class MockProvider(LLMProvider):
    name = "mock"
    label = "离线模拟 (Mock)"
    supports_vision = True  # 模拟视觉，返回占位解析

    @property
    def available(self) -> bool:
        return True

    def chat(self, messages: list[Message]) -> str:
        # 合并所有消息内容判断意图（决策大脑的触发词在 system 提示中）
        text = " ".join(
            m.get("content", "") for m in messages if isinstance(m.get("content"), str)
        )

        # 决策大脑综合评估请求
        if "干预方案" in text or "风险评估" in text or "综合征" in text:
            return (
                "【老年综合征筛查】\n"
                "- 跌倒风险：中等，建议进行步态与平衡评估。\n"
                "- 多重用药：存在，需药师复核相互作用。\n"
                "- 营养与认知：暂未见明显异常，建议定期随访。\n\n"
                "【详细风险评估】\n"
                "结合血压、血糖趋势与既往病史，当前以心血管与代谢风险为主，"
                "短期内需重点关注血压波动。\n\n"
                "【个性化干预方案】\n"
                "1. 监测：每日早晚各测一次血压并记录；每周空腹血糖 2 次。\n"
                "2. 用药：遵医嘱规律服药，避免自行增减。\n"
                "3. 生活方式：低盐低脂饮食，每日适度活动 30 分钟。\n"
                "4. 随访：2 周后复诊评估血压控制情况。\n\n"
                "（注：本结果由离线 Mock 模型生成，仅用于演示，不构成医疗建议。）"
            )
        # 普通健康问答
        return (
            "您好，我是您的健康管理助手（离线模拟）。根据您描述的情况，"
            "建议保持规律作息、均衡饮食，并按时监测血压血糖。如有持续不适，"
            "请及时就医。（本回复由 Mock 模型生成，仅供演示。）"
        )

    def chat_vision(self, prompt: str, image_data_url: str, system: str = "") -> str:
        return (
            "【报告解析-模拟】检测到一张医疗报告图片。模拟提取关键指标：\n"
            "- 血常规：白细胞 6.2×10^9/L（正常）；血红蛋白 118 g/L（偏低）。\n"
            "- 血脂：低密度脂蛋白 3.6 mmol/L（偏高）。\n"
            "结论：建议关注贫血与血脂偏高，复查并调整饮食。\n"
            "（离线 Mock 解析，仅供演示。）"
        )
