from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float
)

from sqlalchemy.orm import relationship

from backend.database.database import Base


class Conversation(Base):

    __tablename__ = "conversations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(200),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    summary = relationship(
        "ConversationSummary",
        back_populates="conversation",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Message(Base):

    __tablename__ = "messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False
    )

    role = Column(
        String(20),
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    conversation = relationship(
        "Conversation",
        back_populates="messages"
    )


class ConversationSummary(Base):

    __tablename__ = "conversation_summaries"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        unique=True,
        nullable=False
    )

    summary = Column(
        Text,
        nullable=False
    )


    last_summarized_message_count = Column(
        Integer,
        nullable=False,
        default=0
    )


    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    conversation = relationship(
        "Conversation",
        back_populates="summary"
    )


class PersonalMemory(Base):

    __tablename__ = "personal_memories"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    memory_type = Column(
        String(50),
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="pending"
    )

    confidence = Column(
        Float,
        nullable=True
    )

    source_message_id = Column(
        Integer,
        ForeignKey("messages.id"),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
