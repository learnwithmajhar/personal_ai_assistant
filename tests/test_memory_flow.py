import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import database
from backend.database.database import Base
from backend.database.models import (
    ConversationSummary,
    Message,
    PersonalMemory,
)
from backend.services.memory_service import (
    find_duplicate_memory,
    normalize_text,
)


TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

database.engine = TEST_ENGINE

from backend import main  # noqa: E402


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=TEST_ENGINE)
    testing_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=TEST_ENGINE,
    )
    session = testing_session()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def client(db_session, monkeypatch):
    def override_get_db():
        yield db_session

    main.app.dependency_overrides[main.get_db] = override_get_db
    monkeypatch.setattr(
        main,
        "get_ai_response",
        lambda **kwargs: "normal mocked response",
    )
    monkeypatch.setattr(
        main,
        "generate_conversation_summary",
        lambda **kwargs: "mocked summary",
    )

    with TestClient(main.app) as test_client:
        yield test_client

    main.app.dependency_overrides.clear()


def test_normalize_text_returns_normalized_words():
    result = normalize_text("  I am learning Generative AI, in Python! ")

    assert result == "learning generative ai python"


def test_duplicate_detection_identifies_identical_content(db_session):
    memory = PersonalMemory(
        memory_type="skills",
        content="I know Python",
        status="approved",
    )
    db_session.add(memory)
    db_session.commit()

    result = find_duplicate_memory(
        db_session,
        memory_type="skills",
        content="I know Python",
    )

    assert result is not None
    assert result["memory"].id == memory.id
    assert result["score"] == 1.0


def test_duplicate_detection_handles_word_form_variations(db_session):
    memory = PersonalMemory(
        memory_type="preferences",
        content="The user prefers Python for programming.",
        status="approved",
    )
    db_session.add(memory)
    db_session.commit()

    result = find_duplicate_memory(
        db_session,
        memory_type="preferences",
        content="I prefer Python for programming.",
    )

    assert result is not None
    assert result["memory"].id == memory.id
    assert result["score"] == 1.0



def test_duplicate_detection_identifies_similar_word_content(db_session):
    memory = PersonalMemory(
        memory_type="skills",
        content="Python machine learning",
        status="approved",
    )
    db_session.add(memory)
    db_session.commit()

    result = find_duplicate_memory(
        db_session,
        memory_type="skills",
        content="Python machine learning projects",
    )

    assert result is not None
    assert result["memory"].id == memory.id
    assert result["score"] == pytest.approx(0.75)


@pytest.mark.parametrize("status", ["approved", "pending"])
def test_duplicate_detection_checks_approved_and_pending(
    db_session,
    status,
):
    memory = PersonalMemory(
        memory_type="goals",
        content="Become an AI engineer",
        status=status,
    )
    db_session.add(memory)
    db_session.commit()

    result = find_duplicate_memory(
        db_session,
        memory_type="goals",
        content="Become an AI engineer",
    )

    assert result is not None
    assert result["memory"].id == memory.id


def test_unique_memory_is_not_a_duplicate(db_session):
    db_session.add(
        PersonalMemory(
            memory_type="skills",
            content="I know Python",
            status="approved",
        )
    )
    db_session.commit()

    result = find_duplicate_memory(
        db_session,
        memory_type="goals",
        content="I want to travel to Japan",
    )

    assert result is None


def configure_memory_candidate(monkeypatch):
    monkeypatch.setattr(
        main,
        "detect_memory_candidate",
        lambda message: {
            "memory_type": "skills",
            "content": "The user knows Python",
            "confidence": 0.95,
        },
    )


def test_repeated_explicit_chat_request_does_not_create_duplicate(
    client,
    db_session,
    monkeypatch,
):
    configure_memory_candidate(monkeypatch)
    request = {"message": "Please remember that I know Python"}

    first_response = client.post("/chat", json=request)
    second_response = client.post(
        "/chat",
        json={
            **request,
            "conversation_id": first_response.json()["conversation_id"],
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert "already exists" in second_response.json()["response"]
    assert db_session.query(PersonalMemory).count() == 1


def test_new_explicit_chat_request_creates_one_pending_memory(
    client,
    db_session,
    monkeypatch,
):
    configure_memory_candidate(monkeypatch)

    response = client.post(
        "/chat",
        json={"message": "Please remember that I know Python"},
    )

    memories = db_session.query(PersonalMemory).all()

    assert response.status_code == 200
    assert len(memories) == 1
    assert memories[0].status == "pending"
    assert memories[0].content == "The user knows Python"
    assert "PENDING" in response.json()["response"]



def test_explicit_memory_response_is_saved_once(
    client,
    db_session,
    monkeypatch,
):
    configure_memory_candidate(monkeypatch)

    response = client.post(
        "/chat",
        json={"message": "Please remember that I know Python"},
    )
    conversation_id = response.json()["conversation_id"]
    assistant_messages = (
        db_session.query(Message)
        .filter(
            Message.conversation_id == conversation_id,
            Message.role == "assistant",
        )
        .all()
    )

    assert response.status_code == 200
    assert len(assistant_messages) == 1
    assert assistant_messages[0].content == response.json()["response"]
    assert "PENDING" in assistant_messages[0].content



def test_summary_not_generated_before_six_messages(client, monkeypatch):
    from backend import main

    summary_calls = []
    monkeypatch.setattr(
        main,
        "generate_conversation_summary",
        lambda **kwargs: summary_calls.append(kwargs) or "mocked summary",
    )

    conversation_id = None

    for message in ["Hello", "How are you?"]:
        response = client.post(
            "/chat",
            json={"message": message, "conversation_id": conversation_id},
        )
        assert response.status_code == 200
        conversation_id = response.json()["conversation_id"]

    assert summary_calls == []


def test_summary_generated_after_six_messages(client, monkeypatch):
    from backend import main

    summary_calls = []
    monkeypatch.setattr(
        main,
        "generate_conversation_summary",
        lambda **kwargs: summary_calls.append(kwargs) or "mocked summary",
    )

    conversation_id = None

    for message in ["Hello", "How are you?", "Tell me about Python"]:
        response = client.post(
            "/chat",
            json={"message": message, "conversation_id": conversation_id},
        )
        assert response.status_code == 200
        conversation_id = response.json()["conversation_id"]

    assert len(summary_calls) == 1

def test_summary_saves_message_count(client):
    conversation_id = None

    for message in [
        "Hello",
        "How are you?",
        "Tell me about Python",
    ]:
        response = client.post(
            "/chat",
            json={
                "message": message,
                "conversation_id": conversation_id,
            },
        )
        assert response.status_code == 200
        conversation_id = response.json()["conversation_id"]

    from backend.database.models import ConversationSummary
    from backend import main

    db_generator = main.get_db()
    db = next(db_generator)

    try:
        summary = (
            db.query(ConversationSummary)
            .filter(
                ConversationSummary.conversation_id == conversation_id
            )
            .first()
        )

        assert summary is not None
        assert summary.last_summarized_message_count == 6
    finally:
        db.close()
        db_generator.close()



def test_summary_saves_message_count(client, db_session):
    conversation_id = None

    for message in [
        "Hello",
        "How are you?",
        "Tell me about Python",
    ]:
        response = client.post(
            "/chat",
            json={
                "message": message,
                "conversation_id": conversation_id,
            },
        )

        assert response.status_code == 200
        conversation_id = response.json()["conversation_id"]

    from backend.database.models import ConversationSummary

    summary = (
        db_session.query(ConversationSummary)
        .filter(
            ConversationSummary.conversation_id == conversation_id
        )
        .first()
    )

    assert summary is not None
    assert summary.last_summarized_message_count == 6

def test_summary_not_repeated_without_six_new_messages(
    client, monkeypatch
):
    from backend import main

    calls = []

    monkeypatch.setattr(
        main,
        "generate_conversation_summary",
        lambda **kwargs: calls.append(kwargs) or "mocked summary",
    )

    conversation_id = None

    for message in [
        "Hello",
        "How are you?",
        "Tell me about Python",
    ]:
        response = client.post(
            "/chat",
            json={
                "message": message,
                "conversation_id": conversation_id,
            },
        )

        assert response.status_code == 200
        conversation_id = response.json()["conversation_id"]

    assert len(calls) == 1

    response = client.post(
        "/chat",
        json={
            "message": "Tell me more",
            "conversation_id": conversation_id,
        },
    )

    assert response.status_code == 200
    assert len(calls) == 1

def test_summary_updates_after_six_new_messages(
    client, db_session, monkeypatch
):
    from backend import main
    from backend.database.models import ConversationSummary

    summary_calls = []

    def fake_summary(**kwargs):
        summary_calls.append(kwargs)
        return f"summary version {len(summary_calls)}"

    monkeypatch.setattr(
        main,
        "generate_conversation_summary",
        fake_summary,
    )

    conversation_id = None

    # First 3 turns = 6 messages; create initial summary.
    for message in ["Hello", "How are you?", "Tell me about Python"]:
        response = client.post(
            "/chat",
            json={
                "message": message,
                "conversation_id": conversation_id,
            },
        )
        assert response.status_code == 200
        conversation_id = response.json()["conversation_id"]

    assert len(summary_calls) == 1

    # Next 3 turns = 6 more messages; update the summary.
    for message in [
        "Explain functions",
        "Explain classes",
        "Explain inheritance",
    ]:
        response = client.post(
            "/chat",
            json={
                "message": message,
                "conversation_id": conversation_id,
            },
        )
        assert response.status_code == 200

    assert len(summary_calls) == 2

    summary = (
        db_session.query(ConversationSummary)
        .filter(
            ConversationSummary.conversation_id == conversation_id
        )
        .first()
    )

    assert summary is not None
    assert summary.last_summarized_message_count == 12
    assert summary.summary == "summary version 2"

def test_summary_update_receives_existing_summary(
    client, monkeypatch
):
    from backend import main

    received_summaries = []

    def fake_summary(**kwargs):
        received_summaries.append(kwargs.get("existing_summary"))
        return f"summary version {len(received_summaries)}"

    monkeypatch.setattr(
        main,
        "generate_conversation_summary",
        fake_summary,
    )

    conversation_id = None

    for message in [
        "Hello",
        "How are you?",
        "Tell me about Python",
        "Explain functions",
        "Explain classes",
        "Explain inheritance",
    ]:
        response = client.post(
            "/chat",
            json={
                "message": message,
                "conversation_id": conversation_id,
            },
        )
        assert response.status_code == 200
        conversation_id = response.json()["conversation_id"]

    assert len(received_summaries) == 2
    assert received_summaries[0] is None
    assert received_summaries[1] == "summary version 1"



def test_summary_failure_does_not_advance_message_count(
    client, db_session, monkeypatch
):
    from backend import main
    from backend.database.models import ConversationSummary

    calls = []

    def fail_summary(**kwargs):
        calls.append(kwargs)
        raise RuntimeError("Simulated summary failure")

    monkeypatch.setattr(
        main,
        "generate_conversation_summary",
        fail_summary,
    )

    conversation_id = None

    for message in ["Hello", "How are you?", "Tell me about Python"]:
        response = client.post(
            "/chat",
            json={
                "message": message,
                "conversation_id": conversation_id,
            },
        )

        assert response.status_code == 200
        conversation_id = response.json()["conversation_id"]

    # Summary generation should be attempted only once.
    assert len(calls) == 1

    summary = (
        db_session.query(ConversationSummary)
        .filter(
            ConversationSummary.conversation_id == conversation_id
        )
        .first()
    )

    # Failed generation must not save a summary or advance its count.
    assert summary is None
