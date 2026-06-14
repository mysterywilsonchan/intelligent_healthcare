"""应用配置：通过环境变量 / .env 注入大模型 provider 与运行参数。"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根：backend/
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR.parent / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
FRONTEND_DIR = BASE_DIR.parent / "frontend"


class Settings(BaseSettings):
    """从 .env 读取的配置。字段名大小写不敏感。"""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # 默认 provider：doubao（豆包）。可选 doubao|qwen|deepseek|mock
    llm_provider: str = "doubao"

    # 豆包 / 火山方舟
    doubao_api_key: str = ""
    doubao_model: str = "doubao-pro-32k"
    doubao_vision_model: str = "doubao-vision-pro-32k"

    # 通义千问 Qwen
    qwen_api_key: str = ""
    qwen_model: str = "qwen-plus"
    qwen_vision_model: str = "qwen-vl-max"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"

    # 视觉任务回退 provider
    vision_fallback_provider: str = "doubao"

    # 通用 LLM 参数
    llm_temperature: float = 0.4
    llm_timeout: int = 60

    # SQLite 数据库路径
    database_url: str = f"sqlite:///{(DATA_DIR / 'healthcare.db').as_posix()}"


@lru_cache
def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
