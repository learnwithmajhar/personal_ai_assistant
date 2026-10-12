from sqlalchemy.orm import Session

from backend.database.models import (
    Conversation,
    Message,
    ConversationSummary,
    PersonalMemory
)


def create_conversation(
    db: Session,
    title: str = "New Conversation"
):

    conversation = Conversation(
        title=title
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


def save_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str
):

    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


def get_conversation_messages(
    db: Session,
    conversation_id: int
):

    return (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation_id
        )
        .order_by(Message.created_at.asc())
        .all()
    )


def get_conversation_summary(
    db: Session,
    conversation_id: int
):

    return (
        db.query(ConversationSummary)
        .filter(
            ConversationSummary.conversation_id
            == conversation_id
        )
        .first()
    )



def save_conversation_summary(
    db: Session,
    conversation_id: int,
    summary_text: str,
    message_count: int = 0
):
    existing_summary = get_conversation_summary(
        db=db,
        conversation_id=conversation_id
    )

    if existing_summary:
        existing_summary.summary = summary_text
        existing_summary.last_summarized_message_count = message_count
    else:
        existing_summary = ConversationSummary(
            conversation_id=conversation_id,
            summary=summary_text,
            last_summarized_message_count=message_count
        )
        db.add(existing_summary)

    db.commit()
    db.refresh(existing_summary)

    return existing_summary



# ==================================================
# PERSONAL MEMORY FUNCTIONS
# ==================================================


def create_memory(
    db: Session,
    memory_type: str,
    content: str,
    source_message_id: int | None = None,
    confidence: float | None = None
):

    memory = PersonalMemory(
        memory_type=memory_type,
        content=content,
        status="pending",
        source_message_id=source_message_id,
        confidence=confidence
    )

    db.add(memory)
    db.commit()
    db.refresh(memory)

    return memory


def get_pending_memories(
    db: Session
):

    return (
        db.query(PersonalMemory)
        .filter(
            PersonalMemory.status == "pending"
        )
        .order_by(
            PersonalMemory.created_at.desc()
        )
        .all()
    )


def get_approved_memories(
    db: Session
):

    return (
        db.query(PersonalMemory)
        .filter(
            PersonalMemory.status == "approved"
        )
        .order_by(
            PersonalMemory.created_at.desc()
        )
        .all()
    )


def get_memory_by_id(
    db: Session,
    memory_id: int
):

    return (
        db.query(PersonalMemory)
        .filter(
            PersonalMemory.id == memory_id
        )
        .first()
    )


def update_memory_status(
    db: Session,
    memory_id: int,
    status: str
):

    memory = get_memory_by_id(
        db=db,
        memory_id=memory_id
    )

    if memory is None:
        return None

    memory.status = status

    db.commit()
    db.refresh(memory)

    return memory


def update_memory_content(
    db: Session,
    memory_id: int,
    content: str
):

    memory = get_memory_by_id(
        db=db,
        memory_id=memory_id
    )

    if memory is None:
        return None

    memory.content = content

    db.commit()
    db.refresh(memory)

    return memory


def delete_memory(
    db: Session,
    memory_id: int
):

    memory = get_memory_by_id(
        db=db,
        memory_id=memory_id
    )

    if memory is None:
        return False

    db.delete(memory)
    db.commit()

    return True

    # ==================================================
# CONVERSATION HISTORY FUNCTIONS
# ==================================================


def get_all_conversations(
    db: Session
):

    return (
        db.query(Conversation)
        .order_by(
            Conversation.created_at.desc()
        )
        .all()
    )


def get_conversation_by_id(
    db: Session,
    conversation_id: int
):

    return (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id
        )
        .first()
    )
