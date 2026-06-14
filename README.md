# 老年人健康管理系统 · 多模态医疗智能体（决策大脑）

依据《多模态医疗智能体》设计的老年人健康管理 MVP。系统作为"决策大脑"，整合
**生命体征、医疗报告、个人疾病史** 等多源数据，完成
**风险精准识别 → 分级预警 → 个性化干预方案自动生成** 的全链路闭环智能决策。

前端分两个视图：**智能咨询**（面向客户的医疗智能体对话，落地默认页）与
**健康管理**（老人档案 + 体征 + 报告 + 决策评估）。

## 核心能力
- 💬 **智能咨询**：面向老人及家属的医疗智能体对话，咨询各类老年健康问题（含建议问题、语音输入）
- 👵 **个人疾病数据库**：老人档案、疾病史、用药管理
- ❤️ **生命体征 + 趋势**：血压/心率/血糖/体温/血氧录入，规则化分级与时序趋势分析
- 📄 **多模态报告解析**：上传检查报告图片走视觉模型提取关键指标
- 🧠 **决策大脑**：综合证据，生成老年综合征筛查、详细风险评估、个性化干预方案

## 大模型适配（核心）
统一接入 **豆包 / 通义千问 Qwen / DeepSeek**，三者均为 OpenAI 兼容接口，**默认豆包**。
所用 provider **仅通过配置文件 `.env` 的 `LLM_PROVIDER` 指定**，前端不提供厂商切换入口。

| Provider | 视觉 | 说明 |
|---|---|---|
| 豆包（默认） | ✅ | 火山方舟 Ark |
| Qwen | ✅ | DashScope 兼容模式，qwen-vl 视觉 |
| DeepSeek | ❌ | 文本接口无视觉，**上传图片自动回退到豆包视觉** |
| mock | ✅ | 离线模拟，无需任何 key，用于演示/测试 |

## 快速开始

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 配置（可选）：复制 .env.example 为 .env 并填入 key
copy .env.example .env
# 无 key 时，把 LLM_PROVIDER 设为 mock 即可离线演示

uvicorn app.main:app --reload
```

浏览器打开 http://127.0.0.1:8000 即为前端仪表盘；API 文档见 http://127.0.0.1:8000/docs 。

### 离线演示（无 API key）
将 `.env` 中 `LLM_PROVIDER=mock`，重启服务。
即可走通 智能咨询 + 建档 → 录体征 → 传报告 → 一键评估 全流程。

### 切换为真实大模型
在 `.env` 设 `LLM_PROVIDER=doubao|qwen|deepseek` 并填入对应 key（如 `DOUBAO_API_KEY`、
`DOUBAO_MODEL`），重启服务即可。切换 provider 只改配置文件，无需改动前端。
DeepSeek 下上传图片会自动回退到豆包视觉并标注。

## 测试
```powershell
cd backend
pytest
```
覆盖：风险分级规则、provider 选择与视觉回退、mock 端到端闭环。

## 目录结构
```
backend/app/
  config.py            # provider 与运行配置（默认豆包）
  db.py models.py schemas.py
  llm/                 # 大模型适配层（base / openai_compatible / providers / registry / mock）
  agent/               # risk(规则分级+趋势) / multimodal / prompts / decision_brain(闭环)
  routers/             # elders / vitals / reports / chat / assessment
frontend/              # Vue3(CDN) 单页仪表盘
data/                  # healthcare.db + uploads/（运行时生成）
```

## 范围与免责声明
本项目为可演示 MVP。幻灯片提到的"分类/回归/聚类"以规则分级、时序趋势、风险画像实现，
不引入重训练模型。所有输出仅为健康管理建议，**不构成医疗诊断，请以医生面诊为准**。
