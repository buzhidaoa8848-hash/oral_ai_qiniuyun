# SceneTalk AI — Product Design

## Vision

SceneTalk AI transforms language learning by replacing rote memorization with **immersive scene-based conversation practice**. Learners step into realistic scenarios — ordering coffee, checking into a hotel, making small talk at a party — and receive AI-powered feedback on every utterance.

## Core Product Principles

1. **Learn by doing**: Practice in context, not in abstract drills.
2. **Immediate, actionable feedback**: Know what to fix and how to fix it, right after you speak.
3. **Progressive difficulty**: Scenes scale from A1 (beginner) to C2 (mastery).
4. **Provider flexibility**: Users choose their AI backend (OpenAI, DashScope, DeepSeek, Azure).

## User Flow

```
Select Scene → Read Prompt → Record Speech → Submit →
  → Receive Transcript + Pronunciation Score + Grammar Feedback →
  → Listen to Model Answer (TTS) → Try Again or Next Scene
```

## Key Screens

### Home / Scene Browser
- Browse scene cards by category, level, and topic.
- Each card shows: title, difficulty badge, topic tag, brief description.
- "Continue Learning" section for in-progress scenes.

### Scene Practice
- Scene context and character role displayed prominently.
- Prompt text and optional hint.
- Record button with waveform visualization.
- Playback and re-record before submitting.

### Feedback View
- Side-by-side: Your transcript vs. model answer.
- Pronunciation score (0–100) with phoneme-level breakdown.
- Grammar and vocabulary suggestions.
- "Try Again" and "Next Scene" actions.

### Progress Dashboard
- Streak and total practice time.
- Per-skill radar chart (pronunciation, fluency, grammar, vocabulary).
- Recent scenes and scores.

## Target Audience

- **Independent learners** who want speaking practice outside a classroom.
- **Language teachers** assigning scenes as homework.
- **Test prep students** (IELTS, TOEFL, HSK) practicing spoken sections.

## Language Support

- Phase 1: English (native) learning Chinese (Mandarin).
- Phase 2: English ↔ Spanish, English ↔ Japanese.
- Phase 3: Any language pair supported by the underlying LLM/STT/TTS providers.
