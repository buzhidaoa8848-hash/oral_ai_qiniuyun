# SceneTalk AI — Architecture

## Overview

SceneTalk AI is a language-learning platform that uses AI-generated scene-based conversation cards. Learners practice speaking through structured scenarios, receiving real-time feedback on pronunciation, fluency, and grammar.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ Next.js App  │  │ Scene Card   │  │ Recording /       │   │
│  │ Router       │  │ Renderer     │  │ Playback UI       │   │
│  └─────────────┘  └──────────────┘  └───────────────────┘   │
│                         │                                     │
│                    Tailwind CSS                               │
└─────────────────────────┼───────────────────────────────────┘
                          │ HTTP / WebSocket
┌─────────────────────────┼───────────────────────────────────┐
│                        Backend                               │
│  ┌─────────────┐  ┌─────┴──────┐  ┌───────────────────┐    │
│  │ FastAPI      │  │ Scene      │  │ Evaluation        │    │
│  │ Router       │  │ Generator  │  │ Engine            │    │
│  └─────────────┘  └────────────┘  └───────────────────┘    │
│                         │                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 Provider Adapters                      │   │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────────────┐   │   │
│  │  │ LLM  │  │ STT  │  │ TTS  │  │ Pronunciation    │   │   │
│  │  │      │  │      │  │      │  │ Assessment       │   │   │
│  │  └──────┘  └──────┘  └──────┘  └──────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer        | Technology                                               |
|--------------|----------------------------------------------------------|
| Frontend     | Next.js (App Router), TypeScript, Tailwind CSS           |
| Backend      | FastAPI (Python), Pydantic schemas                       |
| AI Providers | OpenAI, DashScope (Alibaba), DeepSeek, Azure Speech      |
| Dev Tools    | ESLint, Prettier, pytest, tsx                            |

## Key Design Decisions

1. **Provider abstraction**: All AI services (LLM, STT, TTS, pronunciation) are behind provider-agnostic interfaces, allowing swap between OpenAI / DashScope / DeepSeek / Azure via environment variables.

2. **Scene Card as core domain model**: The SceneCard is the central data type, shared between frontend and backend via Pydantic-generated JSON schemas.

3. **Mock-first development**: The backend returns mock data before any AI provider is wired up, enabling frontend development to proceed independently.

4. **Evaluation pipeline**: User audio → STT → transcript → LLM evaluation → score breakdown → TTS feedback → response to frontend.

## Directory Structure

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
```
