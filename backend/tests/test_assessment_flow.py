"""端到端集成测试：用 mock provider 跑通 档案→体征→评估→对话 闭环。

使用独立的内存 SQLite，避免污染开发库。
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

# 内存数据库（StaticPool 让多线程共享同一连接）
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db
client = TestClient(app)


def test_providers_endpoint_lists_four():
    r = client.get("/api/providers")
    assert r.status_code == 200
    names = {p["name"] for p in r.json()}
    assert {"doubao", "qwen", "deepseek", "mock"} == names
    # 默认应为豆包
    assert any(p["is_default"] and p["name"] == "doubao" for p in r.json())


def test_full_closed_loop_with_mock():
    # 1. 建档
    e = client.post("/api/elders", json={
        "name": "测试老人", "gender": "男", "age": 75,
        "medical_history": "高血压", "medications": "缬沙坦",
    }).json()
    eid = e["id"]

    # 2. 录入体征（偏高血压 + 高血糖）
    client.post(f"/api/elders/{eid}/vitals", json={
        "systolic": 155, "diastolic": 96, "heart_rate": 80,
        "blood_glucose": 8.5, "temperature": 36.6, "spo2": 97,
    })

    # 3. 规则风险
    risk = client.get(f"/api/elders/{eid}/vitals/risk").json()
    assert risk["risk_level"] in ("中", "高", "危急")

    # 4. 决策大脑评估（强制 mock）
    a = client.post(f"/api/elders/{eid}/assessment", json={"provider": "mock"}).json()
    assert a["provider_used"] == "mock"
    assert a["risk_level"] in ("低", "中", "高", "危急")
    assert a["intervention_plan"]  # mock 返回了干预方案

    # 5. 健康问答
    msg = client.post(f"/api/elders/{eid}/chat",
                      json={"message": "我血压有点高怎么办？", "provider": "mock"}).json()
    assert msg["role"] == "assistant"
    assert msg["content"]
