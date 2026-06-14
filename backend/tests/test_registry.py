"""Provider 选择与视觉回退测试。"""
from app.llm.registry import get_provider, get_vision_provider


def test_deepseek_has_no_vision():
    p = get_provider("deepseek")
    assert p.name == "deepseek"
    assert p.supports_vision is False


def test_vision_falls_back_for_deepseek():
    provider, fell_back = get_vision_provider("deepseek")
    assert fell_back is True
    assert provider.supports_vision is True
    # 默认回退到豆包
    assert provider.name == "doubao"


def test_vision_no_fallback_for_doubao():
    provider, fell_back = get_vision_provider("doubao")
    assert fell_back is False
    assert provider.name == "doubao"


def test_mock_always_available():
    p = get_provider("mock")
    assert p.available is True
    assert p.supports_vision is True
