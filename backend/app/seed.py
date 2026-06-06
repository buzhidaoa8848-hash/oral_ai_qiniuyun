"""Seed data — 4 built-in SceneCards for demo & development.

Auto-seeded on first startup if the scene_cards table is empty.
"""

from __future__ import annotations

import uuid
from typing import List

from sqlmodel import Session, select, func

from . import models as m

# ── Fixed UUIDs so frontend can reference them if needed ──────
INTERVIEW_ID = uuid.UUID("aaaaaaaa-0001-4000-8000-000000000001")
RESTAURANT_ID = uuid.UUID("aaaaaaaa-0002-4000-8000-000000000002")
MEETING_ID = uuid.UUID("aaaaaaaa-0003-4000-8000-000000000003")
PITCH_ID = uuid.UUID("aaaaaaaa-0004-4000-8000-000000000004")

DEMO_PROFILE_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _builtin_scenes() -> List[m.SceneCard]:
    """Return the 4 built-in SceneCard instances (not persisted)."""
    return [
        # ── 1. Internship Interview ─────────────────────────
        m.SceneCard(
            id=INTERVIEW_ID,
            title="Internship Interview",
            difficulty="B1",
            topic="Career",
            scene_type="interview",
            style="professional",
            ai_role="Hiring Manager at a tech company",
            user_role="University student applying for a summer internship",
            task_goal="Introduce yourself, explain why you want this internship, and answer 2-3 behavioral questions confidently.",
            key_expressions=[
                "I'm passionate about…",
                "One of my strengths is…",
                "I handled that by…",
                "I'm eager to learn…",
                "Could you tell me more about the team?",
            ],
            must_cover_points=[
                "State your name and major",
                "Explain one relevant project or experience",
                "Answer 'Tell me about a challenge you overcame'",
                "Ask one thoughtful question about the role",
            ],
            follow_up_strategy="Push gently on any vague answers — ask for specifics. If the candidate gives a short answer, probe with 'Can you elaborate?' or 'What was the outcome?'",
            evaluation_rubric="Clarity (25%) · Relevance of examples (25%) · Professional tone (20%) · Question-asking (15%) · Fluency (15%)",
            opening_question="Hi there! Thanks for applying for our summer internship. Could you start by telling me a bit about yourself and why you're interested in this role?",
            prompt="You are interviewing for a summer internship at a tech company.",
            character_role="Candidate",
            model_answer="",
            hints=["dress professionally", "maintain eye contact"],
            target_language="en",
            source_language="en",
            tags=["career", "interview", "internship", "professional"],
        ),
        # ── 2. Restaurant Ordering ──────────────────────────
        m.SceneCard(
            id=RESTAURANT_ID,
            title="Restaurant Ordering",
            difficulty="A2",
            topic="Food",
            scene_type="restaurant",
            style="casual",
            ai_role="Waiter at a busy downtown restaurant",
            user_role="Customer ordering dinner with friends",
            task_goal="Ask about the daily special, order your meal with customizations, and handle a minor issue (wrong side dish).",
            key_expressions=[
                "What's the special today?",
                "I'll have the…",
                "Could I get that without…?",
                "I think there's been a mix-up — I ordered…",
                "Can we get the check, please?",
            ],
            must_cover_points=[
                "Ask about the daily special",
                "Order one main course with a customization",
                "Politely correct the wrong side dish",
                "Request the bill",
            ],
            follow_up_strategy="Take the order, confirm it back, then 'deliver' one wrong item. If the user doesn't speak up, gently prompt: 'Is everything okay with your meal?'",
            evaluation_rubric="Clarity of order (30%) · Politeness (25%) · Handling the mistake (25%) · Natural flow (20%)",
            opening_question="Good evening! Welcome to The Grove. Here are your menus. Can I start you off with any drinks while you decide?",
            prompt="You are dining at a restaurant with friends.",
            character_role="Customer",
            model_answer="",
            hints=["use polite language", "don't forget to tip"],
            target_language="en",
            source_language="en",
            tags=["food", "restaurant", "casual", "daily-life"],
        ),
        # ── 3. Work Meeting ─────────────────────────────────
        m.SceneCard(
            id=MEETING_ID,
            title="Work Meeting",
            difficulty="B2",
            topic="Business",
            scene_type="meeting",
            style="semi-formal",
            ai_role="Project Manager leading a weekly stand-up",
            user_role="Software developer giving a status update",
            task_goal="Give a clear status update, flag a blocker that will delay the timeline, and propose a solution.",
            key_expressions=[
                "Here's where we stand on…",
                "I've completed… and I'm currently working on…",
                "We've hit a blocker with…",
                "I'd suggest we…",
                "Happy to dive deeper offline.",
            ],
            must_cover_points=[
                "Report what you completed this week",
                "Report what you're working on now",
                "Flag one blocker with a proposed solution",
                "Respond to a follow-up question from the manager",
            ],
            follow_up_strategy="Ask one clarifying question about the blocker. Probe for timeline impact. If the proposed solution sounds vague, ask for more concrete next steps.",
            evaluation_rubric="Structure (25%) · Clarity of blocker explanation (25%) · Proactiveness (solution-oriented) (25%) · Concision (15%) · Professional tone (10%)",
            opening_question="Alright team, let's go around the room. Alex, can you kick us off? What's the latest on the authentication module?",
            prompt="You are giving a status update in your team's weekly stand-up meeting.",
            character_role="Developer",
            model_answer="",
            hints=["be concise but specific", "come with solutions not just problems"],
            target_language="en",
            source_language="en",
            tags=["business", "meeting", "stand-up", "professional"],
        ),
        # ── 4. Project Pitch Q&A ────────────────────────────
        m.SceneCard(
            id=PITCH_ID,
            title="Project Pitch Q&A",
            difficulty="C1",
            topic="Business",
            scene_type="pitch",
            style="professional",
            ai_role="Senior Investor at a venture capital firm",
            user_role="Startup founder pitching their product for funding",
            task_goal="Deliver a concise pitch, handle tough questions about market and competition, and leave a strong closing impression.",
            key_expressions=[
                "We're solving [problem] by [solution].",
                "Our target market is… and it's growing at…",
                "What sets us apart is…",
                "Our go-to-market strategy is…",
                "We're seeking [amount] to achieve [milestone].",
            ],
            must_cover_points=[
                "State the problem and your solution in 60 seconds",
                "Define the target market and its size",
                "Explain your competitive advantage",
                "Answer a tough question about competitors",
                "Close with a clear ask and use-of-funds",
            ],
            follow_up_strategy="Challenge with 2–3 sharp investor questions: 'How is this defensible?', 'What's stopping a big player from copying this?', 'Walk me through your unit economics.' Push back gently on optimistic numbers.",
            evaluation_rubric="Clarity of value proposition (25%) · Handling tough questions (25%) · Market understanding (20%) · Closing strength (15%) · Delivery & confidence (15%)",
            opening_question="I've got 10 minutes. Impress me. What problem are you solving, and why should I care?",
            prompt="You are pitching your startup to a VC investor.",
            character_role="Founder",
            model_answer="",
            hints=["know your numbers cold", "anticipate objections"],
            target_language="en",
            source_language="en",
            tags=["business", "pitch", "startup", "professional"],
        ),
    ]


def seed_db(session: Session) -> None:
    """Populate with demo profile + 4 built-in scene cards."""
    # Profile
    p = m.Profile(
        id=DEMO_PROFILE_ID,
        name="Demo Learner",
        email="demo@scenetalk.dev",
        source_language="en",
        target_language="en",
        proficiency_level="B1",
    )
    session.add(p)

    # Scene cards
    for sc in _builtin_scenes():
        session.add(sc)

    session.commit()
    print("[OK] Seeded: 1 demo profile + 4 built-in scene cards")


def seed_if_empty(session: Session) -> None:
    """Seed the database only if no scene cards exist yet."""
    count = session.exec(select(func.count()).select_from(m.SceneCard)).one()
    if count == 0:
        seed_db(session)
    else:
        print(f"[INFO] Database already has {count} scene card(s), skipping seed.")
