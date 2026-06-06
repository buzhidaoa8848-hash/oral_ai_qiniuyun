"""ConversationAgent — drives the AI side of a practice conversation.

Input:  SceneCard + style constraints + conversation history + user utterance
Output: Typed JSON — see ConversationResponse schema.

Uses the LLM provider (mock by default) for generation, then StyleAgent for enforcement.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlmodel import Session, select

from . import models as m
from .providers import get_provider, MockProvider
from .style_agent import StyleAgent, StyleConstraints


# ── Mock conversation responses ─────────────────────────────────
# Keyed by scene_type, cycled by turn index.
_MOCK_REPLIES: dict[str, list[dict[str, Any]]] = {
    "interview": [
        {
            "reply": "That's a strong start! Can you tell me more about a specific project where you took initiative?",
            "intent": "probe_for_specifics",
            "based_on_user_point": "user_introduction",
            "next_goal": "get_concrete_example",
            "should_interrupt": False,
        },
        {
            "reply": "Interesting. What was the biggest challenge you faced, and how did you handle it?",
            "intent": "test_problem_solving",
            "based_on_user_point": "project_experience",
            "next_goal": "evaluate_challenge_response",
            "should_interrupt": False,
        },
        {
            "reply": "Good answer. Now, why do you want to work with us specifically? What drew you to this role?",
            "intent": "test_motivation",
            "based_on_user_point": "challenge_handling",
            "next_goal": "assess_cultural_fit",
            "should_interrupt": False,
        },
        {
            "reply": "Thanks for sharing that. I appreciate your time today — any questions for me before we wrap up?",
            "intent": "invite_questions",
            "based_on_user_point": "motivation",
            "next_goal": "close_interview",
            "should_interrupt": False,
        },
    ],
    "restaurant": [
        {
            "reply": "Sure! Our special today is grilled salmon with roasted vegetables. Would you like to try that, or do you need a moment?",
            "intent": "present_special",
            "based_on_user_point": "user_inquiry",
            "next_goal": "take_order",
            "should_interrupt": False,
        },
        {
            "reply": "Great choice. Would you like any sides or drinks with that?",
            "intent": "upsell",
            "based_on_user_point": "order_selection",
            "next_goal": "complete_order",
            "should_interrupt": False,
        },
        {
            "reply": "Oh, I'm sorry — I brought you fries instead of the salad. Let me fix that right away. Is everything else okay?",
            "intent": "correct_mistake",
            "based_on_user_point": "side_dish_issue",
            "next_goal": "ensure_satisfaction",
            "should_interrupt": False,
        },
        {
            "reply": "Of course! Here's your check. Thank you for dining with us — have a wonderful evening!",
            "intent": "close_interaction",
            "based_on_user_point": "bill_request",
            "next_goal": "end_service",
            "should_interrupt": False,
        },
    ],
    "meeting": [
        {
            "reply": "Thanks for the update, Alex. That's good progress. Could you elaborate a bit more on the timeline for the authentication module?",
            "intent": "probe_timeline",
            "based_on_user_point": "status_update",
            "next_goal": "clarify_deliverables",
            "should_interrupt": False,
        },
        {
            "reply": "I see. And what's your plan to mitigate the risk you mentioned with the API integration?",
            "intent": "test_planning",
            "based_on_user_point": "blocker_description",
            "next_goal": "evaluate_solution",
            "should_interrupt": False,
        },
        {
            "reply": "That sounds reasonable. Can you send a quick summary to the team by end of day so everyone is aligned?",
            "intent": "delegate",
            "based_on_user_point": "solution_proposal",
            "next_goal": "close_standup",
            "should_interrupt": False,
        },
        {
            "reply": "Perfect. Thanks everyone — let's regroup same time next week. Alex, great job on the update!",
            "intent": "close_meeting",
            "based_on_user_point": "summary",
            "next_goal": "end_session",
            "should_interrupt": False,
        },
    ],
    "pitch": [
        {
            "reply": "Interesting problem space. But I've seen a dozen startups in this area — what specifically makes your approach defensible?",
            "intent": "challenge_defensibility",
            "based_on_user_point": "problem_statement",
            "next_goal": "test_unique_value",
            "should_interrupt": False,
        },
        {
            "reply": "Fair point. Let's talk numbers — what's your current traction, and what are your unit economics looking like?",
            "intent": "probe_metrics",
            "based_on_user_point": "defensibility_answer",
            "next_goal": "evaluate_business_model",
            "should_interrupt": False,
        },
        {
            "reply": "Okay, I see the potential. What's stopping a big player like Google from building this in six months?",
            "intent": "stress_test",
            "based_on_user_point": "traction_data",
            "next_goal": "assess_competitive_moat",
            "should_interrupt": False,
        },
        {
            "reply": "You've made a compelling case. Let's set up a follow-up meeting — I'd like to bring in our technical partner.",
            "intent": "advance_deal",
            "based_on_user_point": "competitive_response",
            "next_goal": "schedule_followup",
            "should_interrupt": False,
        },
    ],
    "conversation": [
        {
            "reply": "That's really interesting! Tell me more about that — I'm curious what brought you here.",
            "intent": "show_interest",
            "based_on_user_point": "user_intro",
            "next_goal": "deepen_conversation",
            "should_interrupt": False,
        },
        {
            "reply": "I see! And have you had a chance to explore the area yet? There's a great spot nearby I'd recommend.",
            "intent": "offer_recommendation",
            "based_on_user_point": "user_background",
            "next_goal": "share_local_knowledge",
            "should_interrupt": False,
        },
        {
            "reply": "Absolutely, it's one of my favorites. What kind of things do you enjoy doing in your free time?",
            "intent": "build_rapport",
            "based_on_user_point": "recommendation_response",
            "next_goal": "find_common_ground",
            "should_interrupt": False,
        },
        {
            "reply": "That's great to hear. It was so nice chatting with you — I hope you enjoy the rest of your day!",
            "intent": "close_conversation",
            "based_on_user_point": "shared_interests",
            "next_goal": "end_on_positive_note",
            "should_interrupt": False,
        },
    ],
}


class ConversationAgent:
    """Orchestrates: get AI reply → style enforcement → typed output."""

    def __init__(self) -> None:
        self._style = StyleAgent()
        self._provider = get_provider()

    def reply(
        self,
        *,
        scene: dict[str, Any],
        history: list[dict[str, Any]],
        user_utterance: str,
    ) -> dict[str, Any]:
        """Generate the next AI turn."""
        scene_type = scene.get("scene_type", "conversation")
        constraints = StyleConstraints(scene)
        turn_count = len(history)

        # ── Check for conversation end ───────────────────────
        user_said_goodbye = any(
            w in user_utterance.lower()
            for w in ("goodbye", "bye", "thank you", "thanks for", "that's all")
        )
        all_covered = _all_points_covered(history, scene.get("must_cover_points") or [])
        is_final = self._style.should_end_conversation(turn_count, user_said_goodbye, all_covered)

        if is_final:
            closing = self._style.closing_message(constraints)
            return {
                "reply": closing,
                "intent": "close_session",
                "based_on_user_point": "user_input",
                "next_goal": "end",
                "should_interrupt": False,
            }

        # ── Generate via provider ────────────────────────────
        if isinstance(self._provider, MockProvider):
            raw = self._mock_reply(scene_type, turn_count)
        else:
            raw = self._llm_reply(scene, history, user_utterance)

        # ── Style enforcement ────────────────────────────────
        raw["reply"] = self._style.enforce(
            raw.get("reply", ""),
            constraints,
            turn_count,
            is_final=False,
        )

        return raw

    def summarize_turn(
        self,
        *,
        user_message: str,
        ai_reply: dict[str, Any],
        turn_index: int,
        session_id: uuid.UUID,
    ) -> tuple[m.ConversationTurn, m.ConversationTurn]:
        """Create the user and AI ConversationTurn model instances (not persisted)."""
        user_turn = m.ConversationTurn(
            session_id=session_id,
            turn_index=turn_index,
            role="user",
            message=user_message,
        )
        ai_turn = m.ConversationTurn(
            session_id=session_id,
            turn_index=turn_index + 1,
            role="ai",
            message=ai_reply.get("reply", ""),
            intent=ai_reply.get("intent"),
            based_on_user_point=ai_reply.get("based_on_user_point"),
            next_goal=ai_reply.get("next_goal"),
            should_interrupt=ai_reply.get("should_interrupt", False),
        )
        return user_turn, ai_turn

    # ── Private helpers ──────────────────────────────────────

    def _mock_reply(self, scene_type: str, turn_count: int) -> dict[str, Any]:
        replies = _MOCK_REPLIES.get(scene_type, _MOCK_REPLIES["conversation"])
        idx = min(turn_count // 2, len(replies) - 1)
        return dict(replies[idx])

    def _llm_reply(
        self, scene: dict[str, Any], history: list[dict[str, Any]], utterance: str
    ) -> dict[str, Any]:
        prompt = _build_conversation_prompt(scene, history, utterance)
        raw = self._provider.generate_json(prompt, {})
        return {
            "reply": raw.get("reply", "That's interesting — can you tell me more?"),
            "intent": raw.get("intent", "follow_up"),
            "based_on_user_point": raw.get("based_on_user_point", "user_input"),
            "next_goal": raw.get("next_goal", "continue_conversation"),
            "should_interrupt": raw.get("should_interrupt", False),
        }


# ── Helpers ────────────────────────────────────────────────────

def _all_points_covered(history: list[dict[str, Any]], must_cover: list[str]) -> bool:
    """Heuristic: check if all must-cover points appear in conversation."""
    if not must_cover:
        return False
    all_text = " ".join(
        t.get("message", "") for t in history if t.get("role") == "user"
    ).lower()
    covered = 0
    for point in must_cover:
        # Simple keyword matching
        keywords = point.lower().split()[:3]  # first 3 words
        if any(kw in all_text for kw in keywords if len(kw) > 3):
            covered += 1
    return covered >= len(must_cover)


def _build_conversation_prompt(
    scene: dict[str, Any], history: list[dict[str, Any]], utterance: str
) -> str:
    """Build an LLM prompt for conversation continuation."""
    hist_str = "\n".join(
        f"{t['role'].upper()}: {t.get('message', '')}"
        for t in history[-6:]  # last 6 turns for context
    )
    return f"""You are role-playing as: {scene.get('ai_role', 'AI Assistant')}
The user is: {scene.get('user_role', 'User')}
Scene: {scene.get('title', '')}
Task goal: {scene.get('task_goal', '')}
Style: {scene.get('style', 'casual')}
Opening: {scene.get('opening_question', '')}
Follow-up strategy: {scene.get('follow_up_strategy', '')}

Conversation so far:
{hist_str}
USER: {utterance}

Respond as the AI role. Rules:
- Max 3 sentences
- End with a clear question (unless the user is saying goodbye)
- Stay in character
- Push the conversation toward the task goal

Output JSON with keys: reply, intent, based_on_user_point, next_goal, should_interrupt"""
