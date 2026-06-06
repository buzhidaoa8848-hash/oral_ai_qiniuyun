"""Test that all models can be created and persisted."""

import uuid
from sqlmodel import Session

from app.models import (
    Profile,
    Material,
    SceneCard,
    PracticeSession,
    ConversationTurn,
    EvaluationResult,
    CorrectionItem,
    LatencyMetric,
    PersonalExpressionReport,
)


def test_create_profile(session: Session):
    p = Profile(name="Test User", email="test@example.com")
    session.add(p)
    session.commit()
    session.refresh(p)
    assert isinstance(p.id, uuid.UUID)
    assert p.name == "Test User"
    assert p.proficiency_level == "A1"


def test_create_material(session: Session):
    m = Material(title="Greetings", content="你好 = Hello", material_type="vocabulary")
    session.add(m)
    session.commit()
    session.refresh(m)
    assert isinstance(m.id, uuid.UUID)
    assert m.title == "Greetings"


def test_create_scene_card(session: Session):
    sc = SceneCard(
        title="At the Restaurant",
        difficulty="A2",
        topic="Food",
        prompt="Order a meal at a Chinese restaurant.",
        character_role="Customer",
        model_answer="我要一份宫保鸡丁。",
        hints=["宫保鸡丁 = Kung Pao chicken"],
        tags=["restaurant", "food"],
    )
    session.add(sc)
    session.commit()
    session.refresh(sc)
    assert isinstance(sc.id, uuid.UUID)
    assert sc.title == "At the Restaurant"
    assert sc.hints == ["宫保鸡丁 = Kung Pao chicken"]
    assert sc.tags == ["restaurant", "food"]


def test_create_practice_session(session: Session):
    p = Profile(name="Learner")
    sc = SceneCard(
        title="Test Scene",
        difficulty="A1",
        topic="Test",
        prompt="Say hello.",
        character_role="Speaker",
        model_answer="你好",
    )
    session.add_all([p, sc])
    session.commit()

    ps = PracticeSession(profile_id=p.id, scene_card_id=sc.id)
    session.add(ps)
    session.commit()
    session.refresh(ps)
    assert ps.status == "in_progress"
    assert ps.profile_id == p.id


def test_create_conversation_turn(session: Session):
    p = Profile(name="Learner")
    sc = SceneCard(
        title="Test Scene",
        difficulty="A1",
        topic="Test",
        prompt="Say hello.",
        character_role="Speaker",
        model_answer="你好",
    )
    ps = PracticeSession(profile_id=p.id, scene_card_id=sc.id)
    session.add_all([p, sc, ps])
    session.commit()

    turn = ConversationTurn(session_id=ps.id, turn_index=0, transcript="你好")
    session.add(turn)
    session.commit()
    session.refresh(turn)
    assert turn.turn_index == 0
    assert turn.transcript == "你好"


def test_create_evaluation_result(session: Session):
    p = Profile(name="Learner")
    sc = SceneCard(
        title="Test Scene",
        difficulty="A1",
        topic="Test",
        prompt="Say hello.",
        character_role="Speaker",
        model_answer="你好",
    )
    ps = PracticeSession(profile_id=p.id, scene_card_id=sc.id)
    turn = ConversationTurn(session_id=ps.id, turn_index=0)
    session.add_all([p, sc, ps, turn])
    session.commit()

    ev = EvaluationResult(
        turn_id=turn.id,
        pronunciation_score=85.0,
        fluency_score=90.0,
        grammar_score=78.0,
        vocabulary_score=88.0,
        overall_score=85.0,
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)
    assert ev.overall_score == 85.0


def test_create_correction_item(session: Session):
    p = Profile(name="Learner")
    sc = SceneCard(
        title="Test Scene",
        difficulty="A1",
        topic="Test",
        prompt="Say hello.",
        character_role="Speaker",
        model_answer="你好",
    )
    ps = PracticeSession(profile_id=p.id, scene_card_id=sc.id)
    turn = ConversationTurn(session_id=ps.id, turn_index=0)
    ev = EvaluationResult(turn_id=turn.id, overall_score=80.0)
    session.add_all([p, sc, ps, turn, ev])
    session.commit()

    ci = CorrectionItem(
        evaluation_id=ev.id,
        error_text="泥好",
        correction="你好",
        explanation="Tone error: ní vs nǐ",
        category="pronunciation",
    )
    session.add(ci)
    session.commit()
    session.refresh(ci)
    assert ci.category == "pronunciation"


def test_create_latency_metric(session: Session):
    lm = LatencyMetric(provider="mock", capability="llm", duration_ms=150)
    session.add(lm)
    session.commit()
    session.refresh(lm)
    assert lm.provider == "mock"
    assert lm.duration_ms == 150


def test_create_personal_expression_report(session: Session):
    p = Profile(name="Learner")
    session.add(p)
    session.commit()

    report = PersonalExpressionReport(
        profile_id=p.id,
        report_type="session",
        expression_count=12,
        summary="Good progress on tones.",
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    assert report.report_type == "session"
    assert report.expression_count == 12
