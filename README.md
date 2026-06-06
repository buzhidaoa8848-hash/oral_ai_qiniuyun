# SceneTalk AI

**AI-powered language learning through scene-based conversation practice.**

Practice speaking a new language by stepping into realistic scenes — ordering coffee, checking into a hotel, making small talk. Record yourself, get AI feedback on pronunciation, fluency, and grammar, then listen to a native-level model answer.

## Architecture

```
┌──────────────────────┐     ┌──────────────────────────────────┐
│   Frontend           │     │   Backend                        │
│   Next.js + TS       │────▶│   FastAPI + Python               │
│   Tailwind CSS       │     │                                  │
│                      │     │   ┌────────────────────────────┐ │
│   Scene Browser      │     │   │  Provider Adapters         │ │
│   Recording UI       │     │   │  LLM │ STT │ TTS │ Pron.   │ │
│   Feedback View      │     │   │  (OpenAI / DashScope /     │ │
│   Progress Dashboard │     │   │   DeepSeek / Azure)        │ │
└──────────────────────┘     │   └────────────────────────────┘ │
                             └──────────────────────────────────┘
```

- **Scene Cards** are the core domain model — structured conversation prompts at CEFR levels A1–C2.
- **Provider abstraction** lets you swap AI backends via environment variables — no code changes needed.
- **Mock-first development**: The backend returns mock data out of the box, so you can build the frontend without API keys.

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- npm

### 1. Clone & install

```bash
# Frontend
cd frontend
npm install

# Backend
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env to set your provider keys, or leave as "mock" for demo mode
```

### 3. Start

```bash
# Terminal 1 — Backend (http://localhost:8000)
cd backend
uvicorn app.main:app --reload

# Terminal 2 — Frontend (http://localhost:3000)
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Mock-First Development Mode

When `.env` has all providers set to `mock`, the backend returns realistic but static data — no API keys required. This mode is designed for:

- **Frontend development**: Build the UI without waiting for AI integrations.
- **Design reviews**: Click through the full user flow with sample data.
- **CI/testing**: Run integration tests without hitting paid APIs.

To switch a provider to live mode, set it to `openai`, `dashscope`, `deepseek`, or `azure` and fill in the corresponding API key.

## Project Structure

```
scenetalk-ai/
├── frontend/                  # Next.js app
│   ├── src/
│   │   ├── app/               # App Router pages
│   │   ├── components/        # React components
│   │   └── lib/               # API client, types, utils
│   ├── public/
│   └── package.json
├── backend/                   # FastAPI app
│   ├── app/
│   │   ├── main.py            # App entry point
│   │   ├── routers/           # API route handlers
│   │   ├── models/            # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── providers/         # AI provider adapters
│   └── requirements.txt
└── docs/                      # Project documentation
    ├── architecture.md
    ├── product-design.md
    ├── scene-card-schema.md
    ├── evaluation-rubric.md
    └── pr-plan.md
```

## Documentation

| Document                                              | Content                                         |
|-------------------------------------------------------|-------------------------------------------------|
| [architecture.md](docs/architecture.md)               | System architecture and tech stack              |
| [product-design.md](docs/product-design.md)           | Product vision, user flows, target audience     |
| [scene-card-schema.md](docs/scene-card-schema.md)      | Core data model and JSON schema                 |
| [evaluation-rubric.md](docs/evaluation-rubric.md)      | Scoring dimensions and feedback format          |
| [pr-plan.md](docs/pr-plan.md)                         | Launch strategy and outreach plan               |

## License

MIT
