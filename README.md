# SceneTalk AI

> **不只是 AI 口语陪练。是一个围绕"怎么让用户真正提升口语表达能力"这个命题，做了一系列产品和技术判断的完整系统。**

AI 英语口语练习工具 — 支持场景选择、语音对话、发音评测、多 Agent 语法/表达纠错、个人表达反馈与课后总结报告。

---

## 为什么做这个

市面上的 AI 口语工具大多是这样的：

```
选场景 → ChatGPT 对话 → 简单打分 → 结束
```

但这不能真正帮人提升口语。口语能力的本质不只是"发音准、语法对"，而是**在特定场景下，用英语表达出你自己**。

所以 SceneTalk AI 做的不一样：

```
身份/水平 → 场景/材料 → 风格选择 → 语音+文字双模式练习
    → 6 个 Agent 并行评估（发音/语法/表达/自然度/任务/个人表达）
    → 4 级纠正时机策略 → "If I were you" 模型级反馈
    → 报告：radar chart + 延迟分析 + 对话回放 + 下一步计划
```

**核心理念**：语法纠错只能告诉用户"你错了"，不能告诉用户"怎么说得更好"。我们衡量的不只是语言质量，更是**你有没有表达出你自己**。

---

## 产品亮点

### 1. 不只是场景对话，是完整的练习闭环

| 环节 | 做了什么 |
|------|---------|
| 练习前 | 身份选择 + CEFR 水平映射（支持 IELTS/TOEFL/CET/高考/中考自动估算） |
| 练习中 | 场景卡片 + 风格控制（友好/专业/严格/高压/刻薄专业/鼓励） + 语音或文字输入 |
| 练习后 | 6 维评估报告 + 延迟分析 + 纠正统计 + 对话回放 + 下一步练习建议 |

### 2. 场景自定义 — 把任何材料变成口语练习

用户可粘贴**面试脚本、YouTube 字幕、小红书笔记、课程资料**，系统自动生成定制场景卡片。不是死记硬背，是用真实材料练习。

### 3. 6 种教练风格

```
friendly          → 温暖支持型
professional      → 正式结构化
strict            → 高标准严要求
high_pressure     → 高压快节奏
harsh_but_professional → 投行面试官式：尖锐但不人身攻击
encouraging       → 积极鼓励型
```

每种风格有明确的 tone、challenge_level、allowed_behaviors 和 forbidden_behaviors 约束，确保 AI 有边界。

---

## 多 Agent 评估体系

这是 SceneTalk AI 最核心的差异化设计。不使用单一 prompt 出分，而是 **6 个独立 Agent 并行评估**，每个有独立 schema 和评估视角：

```
用户回答 + 场景上下文
        │
        ├── GrammarAgent        → 语法准确性、错误检测与纠正建议
        ├── ExpressionAgent     → 词汇丰富度、表达质量、场景适配度
        ├── NaturalnessAgent    → 对话自然度、上下文连贯性、角色一致性
        ├── TaskCompletionAgent → 任务完成度、must-cover 覆盖追踪
        ├── ProfileAgent        → 个人表达度、证据密度、主动性、原创思考
        └── ReportAgent         → 会话级汇总、趋势分析、弱项识别
```

### 为什么用多 Agent 而不是一个 prompt？

- **独立视角**：grammar 和 expression 是不同的能力维度，需要不同的评估标准
- **可扩展**：新增评估维度不影响现有 Agent
- **可解释**：每个分数有来源，不是黑盒
- **并行执行**：6 个 Agent 同时运行，不增加用户等待时间

---

## 纠正时机策略

纠正不是越及时越好。错误的纠正时机会打断思维、降低自信。我们设计了 4 级策略：

| 情况 | 策略 | 时机 |
|------|------|------|
| 错误不影响理解 | 记录，不打断 | post_session |
| 轻微影响自然度 | 用正确表达复述 (light_recast) | 下一轮对话 |
| 影响任务完成 | 追问澄清 (clarification) | 即时 |
| 用户卡住 | 给句型支架 (scaffold) | 即时 |
| 严格模式开启 | 允许即时纠错 (immediate) | 即时 |

---

## 语音端到端管道

```
[浏览器]                              [后端]                    [AI 服务]
MediaRecorder → webm/opus
     ↓
AudioContext → 解码 → 重采样 16kHz
     ↓
encode WAV/PCM ──────────────────→  voice-turn API
                                      ├─ STT (Qwen/OpenAI/Mock)
                                      │   └─ 失败 → 自动降级 mock，对话继续
                                      ├─ Pronunciation (Fallback/Azure)
                                      ├─ ConversationAgent → LLM 生成回复
                                      ├─ EvaluationPipeline → 6 Agent 并行
                                      └─ 延迟追踪 (STT/LLM/TTS/Pron/E2E)
                                              ↓
                                    [前端] ← JSON response
                                      ├─ 延迟面板实时展示
                                      ├─ 纠正提示悬浮栏
                                      └─ TTS 朗读 AI 回复
```

### 延迟度量

每一轮语音对话记录 5 项延迟指标：

```
STT Latency  │ 语音转写耗时
LLM Latency  │ AI 回复生成耗时
TTS Latency  │ 文本转语音耗时（浏览器端）
Pron Latency │ 发音评估耗时
E2E Latency  │ 用户说完到 AI 开始朗读的总延迟
```

**设计决策**：不做 streaming。72 小时内 streaming 的稳定性风险大于体验收益。用 typing indicator + 延迟面板透明化等待时间，效果更好。

---

## 个人表达评估 — "If I were you"

这是 SceneTalk AI 最具区分度的功能。传统口语评估只关注"你说得对不对"，我们更关注**"你有没有表达出你自己"**。

### 5 个个人表达维度

| 指标 | 衡量什么 |
|------|---------|
| **Profile Coverage** | 有没有提到与个人画像相关的经历、项目、目标 |
| **Evidence Density** | 有没有用具体项目、数据、例子支撑 |
| **Agency** | 有没有体现"我做了什么"，而不是泛泛说"我们做了什么" |
| **Original Thinking** | 有没有表达你的判断、观点、取舍 |
| **Position Fit** | 有没有把自己和当前场景/岗位/任务连接起来 |

### 不只是打分，是模型级反馈

```
"If I were you, I'd approach it this way:
 I'd use 'I led' or 'I built' to show personal ownership.
 I'd elaborate with a concrete example or data point.
 When asked about your motivation, I'd structure my answer:
 (1) context, (2) my specific role, (3) concrete result, (4) what I learned."
```

---

## 架构设计

```
┌──────────────────────┐     ┌──────────────────────────────────────┐
│   Frontend           │     │   Backend                             │
│   Next.js 16 + TS    │────▶│   FastAPI + Python                    │
│   Tailwind CSS       │     │                                        │
│                      │     │   ┌────────────────────────────────┐  │
│   Scene Browser      │     │   │  Provider Adapters             │  │
│   Voice Recorder     │     │   │  LLM │ STT │ TTS │ Pron        │  │
│   Latency Panel      │     │   │  (可替换，env 切换)             │  │
│   Report Dashboard   │     │   └────────────────────────────────┘  │
└──────────────────────┘     │                                        │
                              │   ┌────────────────────────────────┐  │
                              │   │  Multi-Agent Pipeline           │  │
                              │   │  Grammar │ Expression │ Task    │  │
                              │   │  Naturalness │ Profile │ Report │  │
                              │   └────────────────────────────────┘  │
                              └──────────────────────────────────────┘
```

### 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| Provider 抽象层 | 所有 AI 服务可替换 | 不绑定单一供应商；mock mode 零依赖开发 |
| 多 Agent vs 单 prompt | 6 个独立 Agent | 独立视角、可扩展、可解释 |
| Turn-based vs Streaming | Turn-based + typing indicator | 72h 内稳定性优先；typing indicator 缓解等待焦虑 |
| 发音评估 | Fallback (WPM/填充词) + Azure 预留 | 先有可用的评估，再迭代精度 |
| 前端 WAV 转换 | AudioContext 浏览器端转码 | 消除服务端 ffmpeg 依赖 |
| STT 降级 | 失败自动切 mock | 语音流程永不崩溃 |
| 错误处理 | 全链路 try/except + 中文提示 | 用户永远知道发生了什么、怎么处理 |

---

## 技术栈

| 层 | 技术 |
|----|------|
| **前端** | Next.js 16 (App Router), TypeScript, Tailwind CSS |
| **后端** | FastAPI (Python 3.11+), SQLModel, Pydantic v2 |
| **数据库** | SQLite (开发) / PostgreSQL (生产就绪) |
| **LLM** | DeepSeek (默认) / OpenAI / Qwen (百炼) — OpenAI-compatible 接口 |
| **STT** | Qwen Paraformer / OpenAI Whisper — 支持直接文件上传 |
| **发音** | Fallback (WPM/填充词/重复词) + Azure Pronunciation 预留接口 |
| **图表** | Recharts (Radar Chart, Score Rings) |
| **测试** | pytest (20 tests, 3 层覆盖) |

---

## 快速启动

### 前置条件

- Node.js 18+
- Python 3.11+
- npm

### 1. 安装依赖

```bash
# 前端
cd frontend && npm install

# 后端
cd backend && pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env，设置 provider 和 API key
# 或者保持 mock mode，零依赖运行
```

### 3. 启动

```bash
# 终端 1 — 后端 (http://localhost:8000)
cd backend && uvicorn app.main:app --reload

# 终端 2 — 前端 (http://localhost:3000)
cd frontend && npm run dev
```

### Mock Mode（零 API Key）

当 `.env` 中所有 provider 设为 `mock` 时，系统返回逼真的模拟数据 — 无需任何 API Key 即可体验完整流程。适合开发、Demo、CI。

```env
MOCK_MODE=true
LLM_PROVIDER=mock
STT_PROVIDER=mock
```

要启用真实 AI 服务，设置对应 provider 和 API key：

```env
MOCK_MODE=false
LLM_PROVIDER=deepseek
STT_PROVIDER=qwen
DEEPSEEK_API_KEY=sk-xxx
DASHSCOPE_API_KEY=sk-xxx
```

---

## 项目结构

```
scenetalk-ai/
├── frontend/                          # Next.js 16 前端
│   └── src/
│       ├── app/                       # App Router 页面
│       │   ├── page.tsx               # 首页 — 身份/水平/场景选择
│       │   ├── practice/[sessionId]/  # 练习页 — 语音+文字双模式
│       │   └── report/[sessionId]/    # 报告页 — 多维评估+对话回放
│       ├── components/                # React 组件
│       │   ├── VoiceRecorder.tsx      # 录音 + WAV 转换
│       │   ├── LiveLatencyPanel.tsx   # 延迟实时面板
│       │   └── CorrectionHintPanel.tsx # 纠正提示
│       └── lib/                       # API 客户端 + 类型 + 工具
│           ├── api.ts                 # 类型化 API 请求 + 错误处理
│           ├── types.ts               # TypeScript 类型定义
│           └── audio-utils.ts         # 浏览器端 WAV 转换
├── backend/                           # FastAPI 后端
│   ├── app/
│   │   ├── agents/                    # 多 Agent 评估管道
│   │   │   ├── pipeline.py            # 编排器
│   │   │   ├── grammar_agent.py
│   │   │   ├── expression_agent.py
│   │   │   ├── naturalness_agent.py
│   │   │   ├── task_completion.py
│   │   │   ├── profile_agent.py       # 个人表达评估
│   │   │   ├── report_agent.py        # 会话汇总
│   │   │   └── correction_policy.py   # 纠正时机策略
│   │   ├── providers/                 # AI 服务抽象层
│   │   │   ├── llm/                   # DeepSeek, OpenAI, Qwen, Mock
│   │   │   ├── stt/                   # Qwen, OpenAI Whisper, Mock
│   │   │   └── pronunciation/         # Fallback, Azure
│   │   ├── routers/                   # API 路由
│   │   ├── models.py                  # SQLModel 数据模型
│   │   ├── schemas.py                 # Pydantic schema
│   │   └── services.py                # 业务逻辑层
│   └── tests/                         # 20 个测试 (API + Models + Voice)
└── docs/                              # 产品/架构文档
```

---

## 测试

```bash
cd backend && python -m pytest tests/ -v
```

```
20 passed
├── test_api.py      (6) — 健康检查、CRUD、404
├── test_models.py   (9) — 所有数据模型创建
└── test_voice.py    (5) — 404/空音频/静音/正常/webm 格式
```

---

## 开发过程

15 个语义化 commit，从 scaffold → data → routes → agents → providers → frontend → tests → polish：

```
a9f6e65 chore: project scaffold — FastAPI + Next.js 16 with Tailwind
70862ce feat: data models — SceneCard, PracticeSession, Profile, Evaluation
3d15177 feat: business services + seed data — 4 built-in scene cards
2346fc6 feat: API routes — scenes, profiles, sessions, materials, health
e8faf95 feat: conversation agent — multi-scene dialogue with style enforcement
35c5a20 feat: AI provider abstraction — LLM, STT, pronunciation
32b2776 feat: multi-agent evaluation pipeline — 6 assessment dimensions
f435083 feat: voice-turn endpoint + session report API
45b8664 feat: frontend core — home launch flow with identity and level
1e387b8 feat: practice page — voice recorder + latency panel + correction hints
8a0565f feat: report page — radar chart, score rings, conversation replay
d6bc852 feat: browser-side WAV conversion for STT compatibility
f35881b test: add voice-turn endpoint tests — 5 edge cases
cee6624 chore: add .editorconfig and .prettierrc for consistent code style
778c8d3 chore: add favicon and update gitignore for generated files
```

---

## 设计文档

| 文档 | 内容 |
|------|------|
| [product-design.md](docs/product-design.md) | 产品愿景、用户流程、目标受众 |
| [architecture.md](docs/architecture.md) | 系统架构、技术选型、设计决策 |
| [scene-card-schema.md](docs/scene-card-schema.md) | 核心数据模型与 JSON Schema |
| [evaluation-rubric.md](docs/evaluation-rubric.md) | 评分维度与反馈格式 |

---

## Demo 视频

**SceneTalk AI 中文旁白 Demo**（在线观看，无需下载）

<video src="https://raw.githubusercontent.com/buzhidaoa8848-hash/oral_ai_qiniuyun/main/media/scenetalk_ai_demo_v2_zh_no_subtitles.mp4" width="100%" controls></video>

> 如果视频无法加载，点击 [这里直接观看](https://github.com/buzhidaoa8848-hash/oral_ai_qiniuyun/blob/main/media/scenetalk_ai_demo_v2_zh_no_subtitles.mp4)

- 时长：2:58
- 格式：16:9 横屏，1920×1080
- 旁白稿：[demo_v2_voiceover_zh.txt](media/demo_v2_voiceover_zh.txt)

---

## 原创声明

本项目为 2026 年七牛云 XEngineer 暑期实训营参赛作品，72 小时内独立完成设计与开发。

所有代码、架构设计、多 Agent 评估方案、个人表达评估体系、"If I were you" 反馈机制均为原创。

第三方依赖：
- AI 模型：DeepSeek / Qwen (阿里百炼) / OpenAI（通过 provider 抽象层调用）
- 前端框架：Next.js, Tailwind CSS, Recharts
- 后端框架：FastAPI, SQLModel, httpx

---

## License

MIT
