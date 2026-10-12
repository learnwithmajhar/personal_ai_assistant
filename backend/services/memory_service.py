import re

from sqlalchemy.orm import Session

from backend.database.models import PersonalMemory


# ==================================================
# ALLOWED MEMORY CATEGORIES
# ==================================================

ALLOWED_MEMORY_TYPES = {
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


# ==================================================
# STOP WORDS
# ==================================================

STOP_WORDS = {
    "what",
    "what's",
    "is",
    "are",
    "am",
    "i",
    "my",
    "me",
    "the",
    "a",
    "an",
    "and",
    "or",
    "do",
    "does",
    "did",
    "how",
    "why",
    "where",
    "when",
    "who",
    "can",
    "you",
    "tell",
    "about",
    "please",
    "to",
    "of",
    "in",
    "on",
    "for",
    "that",
    "user",
    "users"
}


# ==================================================
# TEXT NORMALIZATION
# ==================================================

def normalize_text(text: str) -> str:
    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        "",
        text
    )

    stop_words = {
        "the", "a", "an", "user", "users",
        "that", "is", "am", "are", "i",
        "me", "my", "to", "for", "and",
        "of", "in"
    }

    words = text.split()

    filtered_words = [
        word
        for word in words
        if word not in stop_words
    ]

    return " ".join(filtered_words)



    
def normalize_duplicate_words(text: str) -> set[str]:
    words = normalize_text(text).split()
    normalized = set()

    for word in words:
        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("s") and len(word) > 3 and not word.endswith(
            ("ss", "us", "is")
        ):
            word = word[:-1]

        if word.endswith("ing") and len(word) > 5:
            word = word[:-3]
            if len(word) >= 2 and word[-1] == word[-2]:
                word = word[:-1]
        elif word.endswith("ed") and len(word) > 5:
            word = word[:-2]
            if len(word) >= 2 and word[-1] == word[-2]:
                word = word[:-1]

        normalized.add(word)

    return normalized


# ==================================================
# MEMORY TYPE NORMALIZATION
# ==================================================

def normalize_memory_type(
    memory_type: str
) -> str:

    if not memory_type:

        return "other"

    normalized = (
        memory_type
        .strip()
        .lower()
    )

    if normalized in ALLOWED_MEMORY_TYPES:

        return normalized

    return "other"


# ==================================================
# RELEVANT MEMORY RETRIEVAL
# ==================================================

def get_relevant_memories(
    db: Session,
    query: str,
    limit: int = 5
):

    approved_memories = (
        db.query(PersonalMemory)
        .filter(
            PersonalMemory.status == "approved"
        )
        .all()
    )

    if not approved_memories:

        return []

    query_words = set(
    normalize_text(query).split()
    )

    scored_memories = []

    for memory in approved_memories:

        content_words = set(
            normalize_text(memory.content).split()
            )

        memory_type_words = set(
            normalize_text(memory.memory_type)
        )

        content_score = len(
            query_words.intersection(
                content_words
            )
        )

        type_score = len(
            query_words.intersection(
                memory_type_words
            )
        )

        total_score = (
            content_score +
            type_score
        )

        if total_score > 0:

            scored_memories.append(
                (
                    total_score,
                    memory
                )
            )

    scored_memories.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        memory
        for score, memory in scored_memories[:limit]
    ]


# ==================================================
# DUPLICATE MEMORY DETECTION
# ==================================================

def find_duplicate_memory(
    db: Session,
    memory_type: str,
    content: str,
    threshold: float = 0.60
):

    # Check approved and pending memories
    existing_memories = (
        db.query(PersonalMemory)
        .filter(
            PersonalMemory.status.in_(
                ["approved", "pending"]
            )
        )
        .all()
    )

    if not existing_memories:
        return None

    new_words = normalize_duplicate_words(content)

    if not new_words:
        return None

    requested_type = (
        memory_type.strip().lower()
    )

    best_match = None
    best_score = 0.0

    for memory in existing_memories:

        existing_words = normalize_duplicate_words(memory.content)

        if not existing_words:
            continue

        # Calculate Jaccard similarity
        intersection = (
            new_words.intersection(
                existing_words
            )
        )

        union = (
            new_words.union(
                existing_words
            )
        )

        if not union:
            continue

        similarity_score = (
            len(intersection) / len(union)
        )

        existing_type = (
            memory.memory_type.strip().lower()
            if memory.memory_type
            else ""
        )

        # Same type gets priority
        if existing_type == requested_type:
            adjusted_score = similarity_score + 0.10
        else:
            adjusted_score = similarity_score

        if adjusted_score > best_score:

            best_score = adjusted_score
            best_match = memory

    if best_match is not None:

        # Return original similarity without type bonus
        original_words = normalize_duplicate_words(best_match.content)

        intersection = (
            new_words.intersection(
                original_words
            )
        )

        union = (
            new_words.union(
                original_words
            )
        )

        original_score = (
            len(intersection) / len(union)
            if union
            else 0.0
        )

        if original_score >= threshold:

            return {
                "memory": best_match,
                "score": original_score
            }

    return None

    # ==================================================
# EXPLICIT MEMORY REQUEST DETECTION
# ==================================================

def is_explicit_memory_request(
    message: str
) -> bool:

    text = message.lower().strip()

    memory_phrases = [
        "remember that",
        "remember this",
        "please remember",
        "save this",
        "save that",
        "keep this in memory",
        "keep that in memory",
        "store this",
        "store that",
        "don't forget that",
        "dont forget that",
        "yaad rakho",
        "yaad rakhna",
        "yaad rakh"
    ]

    for phrase in memory_phrases:

        if phrase in text:
            return True

    return False