"""Mock LLM provider — returns deterministic scene cards based on scene_type.

Used when MOCK_MODE=true or no real provider is configured.
"""

from __future__ import annotations

import uuid
from typing import Any

from .base import BaseLLMProvider

# ── Scene templates keyed by scene_type ────────────────────────
_TEMPLATES: dict[str, dict[str, Any]] = {
    "interview": {
        "title": "Mock Interview",
        "difficulty": "B1",
        "topic": "Career",
        "scene_type": "interview",
        "style": "professional",
        "ai_role": "Hiring Manager",
        "user_role": "Candidate",
        "task_goal": "Introduce yourself and answer behavioral questions confidently.",
        "key_expressions": [
            "I'm passionate about…",
            "One of my strengths is…",
            "I handled that by…",
        ],
        "must_cover_points": [
            "State your name and background",
            "Share one relevant accomplishment",
            "Answer a challenge question",
        ],
        "follow_up_strategy": "Ask for specifics on any vague answers. Probe with 'Can you elaborate?'",
        "evaluation_rubric": "Clarity (30%) · Relevance (30%) · Professional tone (20%) · Fluency (20%)",
        "opening_question": "Tell me about yourself and why you're interested in this role.",
        "prompt": "You are interviewing for a position.",
        "character_role": "Candidate",
        "model_answer": "",
        "hints": ["be specific", "use examples"],
        "tags": ["mock", "interview"],
    },
    "restaurant": {
        "title": "Mock Restaurant",
        "difficulty": "A2",
        "topic": "Food",
        "scene_type": "restaurant",
        "style": "casual",
        "ai_role": "Waiter",
        "user_role": "Customer",
        "task_goal": "Order a meal with customizations and handle one issue.",
        "key_expressions": [
            "I'll have the…",
            "Could I get that without…?",
            "Can we get the check?",
        ],
        "must_cover_points": [
            "Ask about the daily special",
            "Order a main course with a customization",
            "Request the bill",
        ],
        "follow_up_strategy": "Confirm the order back, then 'deliver' one wrong item.",
        "evaluation_rubric": "Clarity (30%) · Politeness (25%) · Handling issues (25%) · Flow (20%)",
        "opening_question": "Good evening! Welcome. Can I start you off with any drinks?",
        "prompt": "You are dining at a restaurant.",
        "character_role": "Customer",
        "model_answer": "",
        "hints": ["be polite", "speak clearly"],
        "tags": ["mock", "restaurant"],
    },
    "meeting": {
        "title": "Mock Meeting",
        "difficulty": "B2",
        "topic": "Business",
        "scene_type": "meeting",
        "style": "semi-formal",
        "ai_role": "Project Manager",
        "user_role": "Team Member",
        "task_goal": "Give a clear status update, flag one blocker, and propose a solution.",
        "key_expressions": [
            "Here's where we stand on…",
            "We've hit a blocker with…",
            "I'd suggest we…",
        ],
        "must_cover_points": [
            "Report completed tasks",
            "Report current work",
            "Flag a blocker with proposed solution",
        ],
        "follow_up_strategy": "Ask one clarifying question about the blocker.",
        "evaluation_rubric": "Structure (25%) · Clarity (25%) · Proactiveness (25%) · Concision (15%) · Tone (10%)",
        "opening_question": "Alright team, Alex — what's the latest on the auth module?",
        "prompt": "You are giving a status update in a stand-up meeting.",
        "character_role": "Team Member",
        "model_answer": "",
        "hints": ["be concise", "come with solutions"],
        "tags": ["mock", "meeting"],
    },
    "pitch": {
        "title": "Mock Pitch",
        "difficulty": "C1",
        "topic": "Business",
        "scene_type": "pitch",
        "style": "professional",
        "ai_role": "Investor",
        "user_role": "Founder",
        "task_goal": "Deliver a concise pitch and handle tough questions.",
        "key_expressions": [
            "We're solving [problem] by [solution].",
            "What sets us apart is…",
            "We're seeking [amount] to achieve [milestone].",
        ],
        "must_cover_points": [
            "State problem and solution in 60s",
            "Define market size",
            "Answer a competitor question",
            "Close with a clear ask",
        ],
        "follow_up_strategy": "Challenge with sharp questions: defensibility, competition, unit economics.",
        "evaluation_rubric": "Value prop (25%) · Tough Qs (25%) · Market (20%) · Close (15%) · Delivery (15%)",
        "opening_question": "I've got 10 minutes. What problem are you solving, and why should I care?",
        "prompt": "You are pitching your startup to a VC.",
        "character_role": "Founder",
        "model_answer": "",
        "hints": ["know your numbers", "anticipate objections"],
        "tags": ["mock", "pitch"],
    },
    "conversation": {
        "title": "Mock Conversation",
        "difficulty": "B1",
        "topic": "Daily Life",
        "scene_type": "conversation",
        "style": "casual",
        "ai_role": "Friendly Stranger",
        "user_role": "Traveler",
        "task_goal": "Make small talk and ask for a local recommendation.",
        "key_expressions": [
            "Excuse me, could you…?",
            "I'm new here, what do you recommend?",
            "That sounds great, thanks!",
        ],
        "must_cover_points": [
            "Start the conversation politely",
            "Ask for one recommendation",
            "End the conversation naturally",
        ],
        "follow_up_strategy": "Be warm and helpful. Offer one recommendation and ask a follow-up question.",
        "evaluation_rubric": "Politeness (30%) · Clarity (25%) · Natural flow (25%) · Task completion (20%)",
        "opening_question": "Hi! Lovely day, isn't it? Are you visiting the area?",
        "prompt": "You are making small talk with a local.",
        "character_role": "Traveler",
        "model_answer": "",
        "hints": ["smile", "be friendly"],
        "tags": ["mock", "conversation"],
    },
}


class MockProvider(BaseLLMProvider):
    """Returns deterministic scene templates — always succeeds."""

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        # Pick template based on scene_type mentioned in the prompt
        for stype in ("interview", "restaurant", "meeting", "pitch", "conversation"):
            if stype in prompt.lower():
                return dict(_TEMPLATES[stype])
        return dict(_TEMPLATES["conversation"])
