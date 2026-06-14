# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

老年人健康管理系统 · 多模态医疗智能体（决策大脑）— an elderly health-management MVP. A FastAPI backend acts as a "decision brain" that integrates multi-source data (vital signs, medical reports, disease history) and runs a closed loop: rule-based risk identification → graded warning → LLM-generated personalized intervention plan. A Vue3 CDN single-page frontend is served as static files by the same backend.

## Commands

All commands run from `backend/`.

```powershell
pip install -r requirements.txt
copy .env.example .env          # set LLM_PROVIDER=mock for offline (no API key) runs
uvicorn app.main:app --reload   # serves API + frontend at http://127.0.0.1:8000
pytest                          # full suite
pytest tests/test_risk.py::test_critical_bp_triggers_crit   # single test
```

- API docs: `/docs`. Frontend: `/` (mounted last in `main.py` so it never shadows `/api/*`).
- `pytest.ini` sets `pythonpath = .`, so tests import `from app...` — run pytest from `backend/`, not the repo root.

## Architecture

Request → router → (agent | llm) → SQLite. Three layers matter:

**LLM adapter (`app/llm/`)** — the core abstraction. Doubao, Qwen, and DeepSeek are all reached through *one* OpenAI-compatible client (`openai_compatible.py`); only `base_url`/`api_key`/`model` differ, set per provider in `providers.py`. `registry.py` selects the provider (default **doubao**, overridable per-request via the `provider` field) and is the single source of the **vision-fallback rule**: when the chosen provider lacks vision (DeepSeek), `get_vision_provider()` falls back to `VISION_FALLBACK_PROVIDER` and reports `fell_back=True`. `mock.py` is an always-available offline provider that keys off keywords across *all* messages (system + user) — the decision-brain trigger words live in the system prompt, so don't make mock inspect only the last user message.

**Decision brain (`app/agent/`)** — `decision_brain.run_assessment()` is the closed-loop orchestrator: gather context → `risk.assess()` → build prompt (`prompts.py`) → LLM `chat()` → `_split_sections()` parses the `【标题】` blocks into syndrome/risk/plan → persist `Assessment`. `risk.py` is pure rules + simple linear-slope trend (no ML model); it returns deterministic grading independent of any LLM, so risk level is still produced even if the LLM call fails. `multimodal.py` routes report images to a vision provider and decodes text files directly.

**Routers (`app/routers/`)** — thin CRUD/dispatch over SQLAlchemy models (`models.py`). Most endpoints are nested under `/api/elders/{elder_id}/...`. `assessment.py` also hosts `GET /api/providers` (drives the frontend's provider switcher and exposes `available`/`supports_vision`).

## Conventions

- All config flows through `app/config.py` (`pydantic-settings`, reads `backend/.env`, `get_settings()` is `lru_cache`d and creates `data/` + `data/uploads/` on first call). Never read env vars directly elsewhere.
- Providers are also `lru_cache`d in `registry.py` — changing `.env` requires a server restart.
- Structured evidence (risk findings) is stored as a JSON string in `Assessment.findings_json`; the frontend `JSON.parse`s it.
- UI strings, prompts, and risk thresholds are Chinese/domain-specific; keep that style. Risk thresholds in `risk.py` are demo reference ranges, not clinical values.
- `data/` (SQLite db + uploads) is runtime-generated and should stay out of commits.
