import os
import json

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


api_key = os.getenv("OPENAI_API_KEY")


if not api_key:

    raise ValueError(
        "OPENAI_API_KEY is not configured."
    )


client = OpenAI(
    api_key=api_key
)


MODEL_NAME = "gpt-5.6-luna"


# ==================================================
# NORMAL AI RESPONSE
# ==================================================

def get_ai_response(
    message: str,
    conversation_history: list[dict] | None = None,
    conversation_summary: str | None = None,
    personal_memories: list[dict] | None = None
) -> str:

    conversation_history = (
        conversation_history or []
    )

    personal_memories = (
        personal_memories or []
    )


    input_messages = []


    # ------------------------------------------------
    # APPROVED PERSONAL MEMORIES
    # ------------------------------------------------

    if personal_memories:

        memory_text = ""


        for memory in personal_memories:

            memory_text += (
                f"- {memory['content']}\n"
            )


        input_messages.append(
            {
                "role": "developer",
                "content": (
                    "The following information consists "
                    "ONLY of user-approved personal memories. "
                    "Use it when relevant. "
                    "Do not invent additional personal "
                    "information.\n\n"
                    "Approved Personal Memories:\n"
                    f"{memory_text}"
                )
            }
        )


    # ------------------------------------------------
    # CONVERSATION SUMMARY
    # ------------------------------------------------

    if conversation_summary:

        input_messages.append(
            {
                "role": "developer",
                "content": (
                    "Here is a summary of the earlier "
                    "conversation. Use it when relevant.\n\n"
                    f"Conversation Summary:\n"
                    f"{conversation_summary}"
                )
            }
        )


    # ------------------------------------------------
    # RECENT CONVERSATION
    # ------------------------------------------------

    for item in conversation_history:

        input_messages.append(
            {
                "role": item["role"],
                "content": item["content"]
            }
        )


    # ------------------------------------------------
    # CURRENT MESSAGE
    # ------------------------------------------------

    input_messages.append(
        {
            "role": "user",
            "content": message
        }
    )


    # ------------------------------------------------
    # LLM
    # ------------------------------------------------

    response = client.responses.create(
        model=MODEL_NAME,
        input=input_messages
    )


    return response.output_text


# ==================================================
# CONVERSATION SUMMARY
# ==================================================

def generate_conversation_summary(
    messages: list[dict],
    existing_summary: str | None = None
) -> str:

    conversation_text = ""


    for message in messages:

        role = message["role"]

        content = message["content"]

        conversation_text += (
            f"{role.upper()}: {content}\n"
        )


    previous_summary_text = ""


    if existing_summary:

        previous_summary_text = f"""
Previous conversation summary:

{existing_summary}

Update this summary using the new conversation.
"""


    summary_prompt = f"""
You are a conversation summarization component
for a Personal AI Assistant.

Create a concise factual summary.

Focus on:
- Important facts explicitly stated by the user
- User goals
- User preferences explicitly stated
- Decisions already made
- Important tasks or plans
- Important context needed for future conversation

Do NOT:
- Invent facts
- Guess personal information
- Treat assumptions as facts
- Include unnecessary small talk
- Create permanent personal memories

The summary is NOT a personal memory.

{previous_summary_text}

Conversation:

{conversation_text}

Return only the updated summary.
"""


    response = client.responses.create(
        model=MODEL_NAME,
        input=summary_prompt
    )


    return response.output_text.strip()


# ==================================================
# MEMORY CANDIDATE EXTRACTION
# ==================================================

def detect_memory_candidate(
    message: str
) -> dict | None:

    prompt = f"""
Category rules:

identity:
- name
- age
- personal identity details

education:
- degree
- college
- university
- formal education
- academic qualification

career:
- career direction
- desired job
- career plans

skills:
- programming languages
- technical skills
- technologies being learned
- tools/frameworks the user knows or is learning

projects:
- personal or professional projects

goals:
- future goals
- targets
- things the user wants to achieve

preferences:
- likes
- dislikes
- preferred choices

work:
- current work
- workplace
- professional responsibilities

lifestyle:
- daily habits
- routines
- lifestyle preferences

location:
- city
- country
- places where the user lives

deen:
- explicitly stated religious/deen-related preferences or practices

other:
- factual personal information that does not fit above categories

Examples:

"I am learning Generative AI" -> "skills"

"I know Python" -> "skills"

"I completed Mechanical Engineering" -> "education"

"My goal is to become an AI Engineer" -> "goals"

"I prefer Python for programming" -> "preferences"

"I work as an AI Consultant" -> "work"

The memory_type MUST be exactly one
of the allowed categories.

Do not create your own category.

Return JSON only.

If no valid memory can be extracted, return:

null

Otherwise return:

{{
    "memory_type": "one allowed category",
    "content": "clear factual memory statement",
    "confidence": 0.0
}}

User request:

{message}
"""

    response = client.responses.create(
        model=MODEL_NAME,
        input=prompt
    )

    result = response.output_text.strip()

    if result.lower() == "null":
        return None

    try:

        memory = json.loads(result)

        if not isinstance(
            memory,
            dict
        ):
            return None

        required_fields = [
            "memory_type",
            "content",
            "confidence"
        ]

        for field in required_fields:

            if field not in memory:
                return None

        # ------------------------------------------
        # VALIDATE MEMORY CATEGORY
        # ------------------------------------------

        allowed_types = {
            "identity",
            "education",
            "career",
            "skills",
            "projects",
            "goals",
            "preferences",
            "work",
            "lifestyle",
            "location",
            "deen",
            "other"
        }

        memory_type = str(
            memory["memory_type"]
        ).strip().lower()

        if memory_type not in allowed_types:

            memory_type = "other"

        # ------------------------------------------
        # VALIDATE CONFIDENCE
        # ------------------------------------------

        confidence = float(
            memory["confidence"]
        )

        confidence = max(
            0.0,
            min(1.0, confidence)
        )

        # ------------------------------------------
        # RETURN CLEAN MEMORY
        # ------------------------------------------

        return {
            "memory_type": memory_type,
            "content": str(
                memory["content"]
            ),
            "confidence": confidence
        }

    except (
        json.JSONDecodeError,
        ValueError,
        TypeError
    ):
        return None