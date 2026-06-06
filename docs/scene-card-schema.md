# Scene Card Schema

The SceneCard is the core domain model. Every scene is represented by a card containing all the information needed for a practice session.

## JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SceneCard",
  "type": "object",
  "required": ["id", "title", "difficulty", "topic", "prompt", "characterRole", "modelAnswer"],
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique identifier (UUID v4)"
    },
    "title": {
      "type": "string",
      "description": "Short, descriptive scene title",
      "examples": ["At the Coffee Shop", "Hotel Check-In"]
    },
    "difficulty": {
      "type": "string",
      "enum": ["A1", "A2", "B1", "B2", "C1", "C2"],
      "description": "CEFR difficulty level"
    },
    "topic": {
      "type": "string",
      "description": "Topic category",
      "examples": ["Travel", "Food", "Business", "Daily Life", "Social"]
    },
    "prompt": {
      "type": "string",
      "description": "The scenario instruction shown to the learner"
    },
    "characterRole": {
      "type": "string",
      "description": "Who the learner is playing in this scene",
      "examples": ["Customer", "Guest", "Interviewer", "Friend"]
    },
    "modelAnswer": {
      "type": "string",
      "description": "A native-level reference answer for comparison and TTS playback"
    },
    "hints": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Optional vocabulary or grammar hints"
    },
    "targetLanguage": {
      "type": "string",
      "description": "Language the learner should speak (ISO 639-1 code)",
      "default": "zh"
    },
    "sourceLanguage": {
      "type": "string",
      "description": "Language of instructions and UI (ISO 639-1 code)",
      "default": "en"
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Searchable tags"
    },
    "createdAt": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

## Example Scene Card

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Ordering Coffee",
  "difficulty": "A2",
  "topic": "Food",
  "prompt": "You are at a café in Beijing. Order a latte, ask about the price, and say you'll drink it there.",
  "characterRole": "Customer",
  "modelAnswer": "你好，我要一杯拿铁。多少钱？在这里喝。",
  "hints": ["拿铁 (nǎtiě) = latte", "多少钱 (duōshao qián) = how much"],
  "targetLanguage": "zh",
  "sourceLanguage": "en",
  "tags": ["café", "ordering", "beginner", "daily-life"],
  "createdAt": "2026-06-05T00:00:00Z"
}
```

## Related Types

### EvaluationResult

Returned after a learner submits their recording:

```json
{
  "sceneCardId": "string",
  "transcript": "string (STT output of learner's speech)",
  "pronunciationScore": "number (0–100)",
  "fluencyScore": "number (0–100)",
  "grammarScore": "number (0–100)",
  "overallScore": "number (0–100)",
  "phonemeFeedback": [
    { "phoneme": "string", "score": "number", "suggestion": "string" }
  ],
  "grammarNotes": ["string"],
  "modelAudioUrl": "string (TTS-generated model answer audio)"
}
```
