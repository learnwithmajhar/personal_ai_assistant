from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import (
    engine,
    Base,
    SessionLocal
)

from backend.database import models

from backend.services.llm_service import (
    get_ai_response,
    generate_conversation_summary,
    detect_memory_candidate
)

from backend.services.conversation_service import (
    create_conversation,
    save_message,
    get_conversation_messages,
    get_conversation_summary,
    save_conversation_summary,
    create_memory as save_memory,
    get_pending_memories,
    get_approved_memories,
    get_memory_by_id,
    update_memory_status,
    update_memory_content,
    delete_memory,
    get_all_conversations,
    get_conversation_by_id
)

from backend.services.memory_service import (
    get_relevant_memories,
    is_explicit_memory_request,
    find_duplicate_memory
)


app = FastAPI(
    title="Personal AI Assistant"
)


# ==================================================
# DATABASE
# ==================================================

Base.metadata.create_all(
    bind=engine
)


def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()


# ==================================================
# REQUEST MODELS
# ==================================================

class ChatRequest(BaseModel):

    message: str

    conversation_id: int | None = None


class MemoryCreateRequest(BaseModel):

    memory_type: str

    content: str

    source_message_id: int | None = None

    confidence: float | None = None


class MemoryStatusRequest(BaseModel):

    status: str


class MemoryUpdateRequest(BaseModel):

    content: str


class DuplicateCheckRequest(BaseModel):

    memory_type: str

    content: str

# ==================================================
# DUPLICATE MEMORY CHECK
# ==================================================

@app.post("/memories/check-duplicate")
def check_duplicate_memory(
    request: DuplicateCheckRequest,
    db: Session = Depends(get_db)
):

    duplicate_result = find_duplicate_memory(
        db=db,
        memory_type=request.memory_type,
        content=request.content
    )

    if duplicate_result is None:

        return {
            "is_duplicate": False,
            "similarity": 0.0,
            "existing_memory_id": None,
            "existing_memory_content": None
        }

    existing_memory = duplicate_result["memory"]

    return {
        "is_duplicate": True,
        "similarity": round(
            duplicate_result["score"],
            2
        ),
        "existing_memory_id": existing_memory.id,
        "existing_memory_content": (
            existing_memory.content
        )
    }


# ==================================================
# HOME
# ==================================================

@app.get("/")
def home():

    return {
        "message":
        "Personal AI Assistant API is running"
    }


# ==================================================
# CHAT
# ==================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):

    # ------------------------------------------------
    # STEP 1
    # Create conversation
    # ------------------------------------------------

    if request.conversation_id is None:

        conversation = create_conversation(

            db=db,

            title=request.message[:50]
        )

        conversation_id = conversation.id

    else:

        conversation_id = (
            request.conversation_id
        )


    # ------------------------------------------------
    # STEP 2
    # Check whether user explicitly requested memory
    # ------------------------------------------------

    memory_request = is_explicit_memory_request(
        request.message
    )


    # ------------------------------------------------
    # STEP 3
    # Get conversation summary
    # ------------------------------------------------

    summary_record = get_conversation_summary(

        db=db,

        conversation_id=conversation_id
    )


    conversation_summary = None


    if summary_record:

        conversation_summary = (
            summary_record.summary
        )


    # ------------------------------------------------
    # STEP 4
    # Get previous conversation messages
    # ------------------------------------------------

    previous_messages = (
        get_conversation_messages(

            db=db,

            conversation_id=conversation_id
        )
    )


    conversation_history = [

        {
            "role": msg.role,

            "content": msg.content
        }

        for msg in previous_messages
    ]


    # ------------------------------------------------
    # STEP 5
    # Recent messages
    # ------------------------------------------------

    recent_messages = (
        conversation_history[-10:]
    )


    # ------------------------------------------------
    # STEP 6
    # Retrieve relevant approved memories
    # ------------------------------------------------

    relevant_memories = (
        get_relevant_memories(

            db=db,

            query=request.message,

            limit=5
        )
    )


    personal_memory_context = [

        {
            "memory_type":
                memory.memory_type,

            "content":
                memory.content
        }

        for memory in relevant_memories
    ]


    # ------------------------------------------------
    # STEP 7
    # Generate AI response
    # ------------------------------------------------

    ai_response = get_ai_response(

        message=request.message,

        conversation_history=recent_messages,

        conversation_summary=conversation_summary,

        personal_memories=personal_memory_context
    )


    # ------------------------------------------------
    # STEP 8
    # Save user message
    # ------------------------------------------------

    user_message = save_message(

        db=db,

        conversation_id=conversation_id,

        role="user",

        content=request.message
    )


    # ==================================================
    # EXPLICIT MEMORY PROCESSING
    # ==================================================

    if memory_request:

        memory_candidate = (
            detect_memory_candidate(
                request.message
            )
        )


        if memory_candidate:

            duplicate_result = find_duplicate_memory(
                db=db,
                memory_type=(
                    memory_candidate["memory_type"]
                ),
                content=(
                    memory_candidate["content"]
                )
            )

            if duplicate_result is not None:

                existing_memory = duplicate_result["memory"]

                ai_response = (
                    "A matching personal memory already exists:\n\n"
                    f"â€¢ {existing_memory.content}\n\n"
                    "No new memory was created."
                )

            else:

                memory = save_memory(

                    db=db,

                    memory_type=(
                        memory_candidate["memory_type"]
                    ),

                    content=(
                        memory_candidate["content"]
                    ),

                    source_message_id=user_message.id,

                    confidence=(
                        memory_candidate["confidence"]
                    )
                )

                ai_response = (
                    "I found a memory you explicitly "
                    "asked me to remember:\n\n"
                    f"â€¢ {memory.content}\n\n"
                    "It is currently marked as PENDING. "
                    "Please review and approve it before "
                    "I use it as permanent personal memory."
                )

    # Save exactly one assistant response, whether this was a
    # normal chat response or an explicit memory response.
    save_message(

        db=db,

        conversation_id=conversation_id,

        role="assistant",

        content=ai_response
    )





    # ------------------------------------------------
    # STEP 10
    # Conversation summary
    # ------------------------------------------------

    all_messages = get_conversation_messages(
        db=db,
        conversation_id=conversation_id
    )

    total_messages = len(all_messages)

    summary_record = get_conversation_summary(
        db=db,
        conversation_id=conversation_id
    )

    last_summarized_count = (
        summary_record.last_summarized_message_count
        if summary_record
        else 0
    )

    new_message_count = total_messages - last_summarized_count

    should_update_summary = (
        total_messages >= 6
        and (
            summary_record is None
            or new_message_count >= 6
        )
    )

    if should_update_summary:
        messages_for_summary = [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in all_messages
        ]

        try:
            updated_summary = generate_conversation_summary(
                messages=messages_for_summary,
                existing_summary=conversation_summary
            )

            save_conversation_summary(
                db=db,
                conversation_id=conversation_id,
                summary_text=updated_summary,
                message_count=total_messages
            )

        except Exception as exc:
            print(f"Conversation summary update failed: {exc}")


    # ------------------------------------------------
    # RESPONSE
    # ------------------------------------------------

    return {

        "conversation_id":
            conversation_id,

        "response":
            ai_response,

        "memory_request":
            memory_request
    }
# ==================================================
# CONVERSATION HISTORY
# ==================================================

@app.get("/conversations")
def list_conversations(db: Session = Depends(get_db)):
    conversations = get_all_conversations(db=db)

    return {
        "count": len(conversations),
        "conversations": [
            {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at
            }
            for conversation in conversations
        ]
    }


@app.get("/conversations/{conversation_id}/messages")
def list_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    conversation = get_conversation_by_id(
        db=db,
        conversation_id=conversation_id
    )

    if conversation is None:
        return {
            "error": "Conversation not found"
        }

    messages = get_conversation_messages(
        db=db,
        conversation_id=conversation_id
    )

    return {
        "conversation_id": conversation_id,
        "count": len(messages),
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at
            }
            for message in messages
        ]
    }

# ==================================================
# CREATE MEMORY
# ==================================================

@app.post("/memories")
def create_memory(
    request: MemoryCreateRequest,
    db: Session = Depends(get_db)
):

    # 1. Check whether the same memory already exists
    duplicate_result = find_duplicate_memory(
        db=db,
        memory_type=request.memory_type,
        content=request.content
    )

    # 2. If duplicate exists, do not create a new memory
    if duplicate_result is not None:

        existing_memory = duplicate_result["memory"]

        return {
            "message": "Duplicate memory already exists",
            "is_duplicate": True,
            "existing_memory_id": existing_memory.id,
            "existing_memory_content": existing_memory.content,
            "similarity": round(
                duplicate_result["score"],
                2
            )
        }

    # 3. Create a new pending memory
    new_memory = models.PersonalMemory(
        memory_type=request.memory_type,
        content=request.content,
        status="pending",
        source_message_id=request.source_message_id,
        confidence=(
            request.confidence
            if request.confidence is not None
            else 1.0
        )
    )

    # 4. Save the new memory
    db.add(new_memory)
    db.commit()
    db.refresh(new_memory)

    # 5. Return created memory details
    return {
        "message": "Memory created successfully",
        "is_duplicate": False,
        "memory": {
            "id": new_memory.id,
            "memory_type": new_memory.memory_type,
            "content": new_memory.content,
            "status": new_memory.status,
            "confidence": new_memory.confidence,
            "source_message_id": new_memory.source_message_id
        }
    }

@app.get("/memories/pending")
def get_pending_memory_list(
    db: Session = Depends(get_db)
):

    memories = get_pending_memories(
        db=db
    )


    return {

        "count":
            len(memories),

        "memories": [

            {
                "id":
                    memory.id,

                "memory_type":
                    memory.memory_type,

                "content":
                    memory.content,

                "status":
                    memory.status,

                "confidence":
                    memory.confidence,

                "source_message_id":
                    memory.source_message_id,

                "created_at":
                    memory.created_at
            }

            for memory in memories
        ]
    }


@app.get("/memories/approved")
def get_approved_memory_list(
    db: Session = Depends(get_db)
):

    memories = get_approved_memories(
        db=db
    )


    return {

        "count":
            len(memories),

        "memories": [

            {
                "id":
                    memory.id,

                "memory_type":
                    memory.memory_type,

                "content":
                    memory.content,

                "status":
                    memory.status,

                "confidence":
                    memory.confidence,

                "source_message_id":
                    memory.source_message_id,

                "created_at":
                    memory.created_at,

                "updated_at":
                    memory.updated_at
            }

            for memory in memories
        ]
    }


@app.get("/memories/{memory_id}")
def get_single_memory(
    memory_id: int,
    db: Session = Depends(get_db)
):

    memory = get_memory_by_id(

        db=db,

        memory_id=memory_id
    )


    if memory is None:

        return {
            "error":
                "Memory not found"
        }


    return {

        "id":
            memory.id,

        "memory_type":
            memory.memory_type,

        "content":
            memory.content,

        "status":
            memory.status,

        "confidence":
            memory.confidence,

        "source_message_id":
            memory.source_message_id,

        "created_at":
            memory.created_at,

        "updated_at":
            memory.updated_at
    }


@app.patch("/memories/{memory_id}/status")
def change_memory_status(
    memory_id: int,
    request: MemoryStatusRequest,
    db: Session = Depends(get_db)
):

    allowed_statuses = [
        "approved",
        "rejected"
    ]


    if request.status not in allowed_statuses:

        return {

            "error":
                "Status must be either "
                "'approved' or 'rejected'"
        }


    memory = update_memory_status(

        db=db,

        memory_id=memory_id,

        status=request.status
    )


    if memory is None:

        return {
            "error":
                "Memory not found"
        }


    return {

        "message":
            f"Memory {request.status} successfully",

        "memory": {

            "id":
                memory.id,

            "memory_type":
                memory.memory_type,

            "content":
                memory.content,

            "status":
                memory.status,

            "confidence":
                memory.confidence
        }
    }


@app.patch("/memories/{memory_id}")
def edit_memory(
    memory_id: int,
    request: MemoryUpdateRequest,
    db: Session = Depends(get_db)
):

    if not request.content.strip():

        return {
            "error":
                "Memory content cannot be empty"
        }


    memory = update_memory_content(

        db=db,

        memory_id=memory_id,

        content=request.content.strip()
    )


    if memory is None:

        return {
            "error":
                "Memory not found"
        }


    return {

        "message":
            "Memory updated successfully",

        "memory": {

            "id":
                memory.id,

            "memory_type":
                memory.memory_type,

            "content":
                memory.content,

            "status":
                memory.status,

            "confidence":
                memory.confidence
        }
    }


@app.delete("/memories/{memory_id}")
def remove_memory(
    memory_id: int,
    db: Session = Depends(get_db)
):

    deleted = delete_memory(

        db=db,

        memory_id=memory_id
    )


    if not deleted:

        return {
            "error":
                "Memory not found"
        }


    return {

        "message":
            "Memory permanently deleted",

        "memory_id":
            memory_id
    }
