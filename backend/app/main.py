"""FastAPI 入口：挂载 API 路由 + 静态前端。"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import FRONTEND_DIR
from .db import init_db
from .routers import assessment, chat, consult, elders, reports, vitals


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="老年人健康管理系统 · 多模态医疗智能体", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(elders.router)
app.include_router(vitals.router)
app.include_router(reports.router)
app.include_router(chat.router)
app.include_router(consult.router)
app.include_router(assessment.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# 静态前端（放最后，避免覆盖 /api）
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
