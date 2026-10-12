import streamlit as st
import requests

st.set_page_config(
    page_title="My Personal AI Assistant",
    page_icon="🧠",
    layout="wide"
)

# ==================================================
# CONFIGURATION
# ==================================================

BASE_URL = "http://127.0.0.1:8000"

CHAT_URL = f"{BASE_URL}/chat"
CONVERSATIONS_URL = f"{BASE_URL}/conversations"

PENDING_MEMORIES_URL = (
    f"{BASE_URL}/memories/pending"
)

APPROVED_MEMORIES_URL = (
    f"{BASE_URL}/memories/approved"
)

# ==================================================
# COMPLETE CUSTOM UI DESIGN
# ==================================================

st.markdown(
    """
    <style>

    /* ==================================================
       GLOBAL APPLICATION DESIGN
       ================================================== */

    .stApp {
        background: #f5f7fb;
    }

    .main .block-container {
        max-width: 1180px;
        padding-top: 2.5rem;
        padding-bottom: 6rem;
    }

    h1 {
        color: #172554 !important;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        letter-spacing: -1px;
    }

    h2,
    h3,
    h4 {
        color: #1e3a8a !important;
        font-weight: 700 !important;
    }

    p {
        line-height: 1.6;
    }

    /* ==================================================
       SIDEBAR BACKGROUND
       ================================================== */

    section[data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #111827 0%,
            #1e293b 100%
        ) !important;
        border-right: 1px solid #334155;
    }

    section[data-testid="stSidebar"] > div {
        background: transparent !important;
    }

    /* Sidebar headings */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {
        color: #ffffff !important;
    }

    /* Sidebar normal text only */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: #e2e8f0 !important;
    }

    /* Sidebar captions */
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #cbd5e1 !important;
    }

    /* ==================================================
       SIDEBAR DIVIDERS
       ================================================== */

    section[data-testid="stSidebar"] hr {
        border-color: #475569 !important;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    /* ==================================================
       SIDEBAR BUTTONS
       ================================================== */

    section[data-testid="stSidebar"] button {
        background: #263852 !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
        min-height: 42px;
        transition: all 0.2s ease-in-out;
    }

    section[data-testid="stSidebar"] button p,
    section[data-testid="stSidebar"] button span {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] button:hover {
        background: #3b82f6 !important;
        border-color: #93c5fd !important;
        color: #ffffff !important;
    }

    /* ==================================================
       SIDEBAR EXPANDERS
       ================================================== */

    section[data-testid="stSidebar"] div[data-testid="stExpander"] {
        background: #243b5a !important;
        border: 1px solid #64748b !important;
        border-radius: 12px !important;
        margin-bottom: 12px;
        overflow: hidden;
    }

    /* Expander header */
    section[data-testid="stSidebar"]
    div[data-testid="stExpander"] summary {
        background: #e2e8f0 !important;
        color: #111827 !important;
        border-radius: 10px !important;
    }

    section[data-testid="stSidebar"]
    div[data-testid="stExpander"] summary p,
    section[data-testid="stSidebar"]
    div[data-testid="stExpander"] summary span {
        color: #111827 !important;
        font-weight: 600 !important;
    }

    /* Expander body */
    section[data-testid="stSidebar"]
    div[data-testid="stExpander"] > details > div {
        background: #243b5a !important;
    }

    section[data-testid="stSidebar"]
    div[data-testid="stExpander"] p,
    section[data-testid="stSidebar"]
    div[data-testid="stExpander"] label {
        color: #ffffff !important;
    }

    /* ==================================================
       MEMORY CONTENT BOX
       ================================================== */

    section[data-testid="stSidebar"]
    div[data-testid="stAlert"] {
        background: #344f73 !important;
        border: 1px solid #7188a5 !important;
        border-radius: 8px !important;
    }

    section[data-testid="stSidebar"]
    div[data-testid="stAlert"] p {
        color: #ffffff !important;
        font-weight: 500 !important;
    }

    /* ==================================================
       MEMORY TEXTAREA
       ================================================== */

    section[data-testid="stSidebar"] textarea {
        background: #ffffff !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        caret-color: #111827 !important;
        border: 1px solid #94a3b8 !important;
        border-radius: 8px !important;
    }

    section[data-testid="stSidebar"] textarea::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
    }

    section[data-testid="stSidebar"] textarea:focus {
        border: 2px solid #60a5fa !important;
        box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2) !important;
    }

    /* ==================================================
       MAIN CHAT HEADER
       ================================================== */

    .assistant-caption {
        color: #64748b;
        font-size: 15px;
        margin-top: -12px;
        margin-bottom: 24px;
    }

    .conversation-title {
        background: #ffffff;
        border: 1px solid #dbeafe;
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 22px;
        color: #334155;
        font-weight: 600;
    }

    /* ==================================================
       CHAT MESSAGE CARDS
       ================================================== */

    div[data-testid="stChatMessage"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 14px 18px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }

    div[data-testid="stChatMessage"] p {
        color: #1e293b !important;
    }

    /* User message */
    div[data-testid="stChatMessage"]:has(
        div[data-testid="chatAvatarIcon-user"]
    ) {
        background: #eff6ff !important;
        border-color: #bfdbfe !important;
    }

    /* Assistant message */
    div[data-testid="stChatMessage"]:has(
        div[data-testid="chatAvatarIcon-assistant"]
    ) {
        background: #ffffff !important;
        border-color: #e2e8f0 !important;
    }

    /* ==================================================
       CHAT INPUT
       ================================================== */

    div[data-testid="stChatInput"] {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.08);
    }

    div[data-testid="stChatInput"] textarea {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        background: #ffffff !important;
    }

    div[data-testid="stChatInput"] textarea::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
    }

    /* ==================================================
       NORMAL INPUTS AND TEXTAREAS
       ================================================== */

    input,
    textarea {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
    }

    /* ==================================================
       GENERAL EXPANDERS
       ================================================== */

    div[data-testid="stExpander"] {
        border-radius: 12px !important;
        border: 1px solid #dbeafe !important;
        background: #ffffff !important;
    }

    /* ==================================================
       SUCCESS / INFO / WARNING BOXES
       ================================================== */

    div[data-testid="stAlert"] {
        border-radius: 10px !important;
    }

    /* ==================================================
       SCROLLBAR
       ================================================== */

    section[data-testid="stSidebar"]::-webkit-scrollbar {
        width: 8px;
    }

    section[data-testid="stSidebar"]::-webkit-scrollbar-track {
        background: #111827;
    }

    section[data-testid="stSidebar"]::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 10px;
    }

    section[data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover {
        background: #64748b;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# SESSION STATE
# ==================================================

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_loaded" not in st.session_state:
    st.session_state.conversation_loaded = False


# ==================================================
# API FUNCTIONS
# ==================================================
def get_conversations():
    try:
        response = requests.get(
            CONVERSATIONS_URL,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return data.get("conversations", [])

    except requests.RequestException as e:
        st.error(f"Could not load conversations: {e}")
        return []


def get_conversation_messages(conversation_id):
    try:
        response = requests.get(
            f"{CONVERSATIONS_URL}/{conversation_id}/messages",
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return data.get("messages", [])

    except requests.RequestException as e:
        st.error(f"Could not load conversation messages: {e}")
        return []
def restore_latest_conversation():
    conversations = get_conversations()

    if not conversations:
        return

    latest_conversation = conversations[0]
    latest_id = latest_conversation.get("id")

    if latest_id is None:
        return

    st.session_state.conversation_id = latest_id
    st.session_state.messages = get_conversation_messages(
        latest_id
    )
def get_pending_memories():

    try:

        response = requests.get(
            PENDING_MEMORIES_URL,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        # Backend returns:
        #
        # {
        #     "count": 0,
        #     "memories": []
        # }

        return data.get(
            "memories",
            []
        )

    except requests.RequestException as e:

        st.error(
            f"Could not load pending memories: {e}"
        )

        return []


def get_approved_memories():

    try:

        response = requests.get(
            APPROVED_MEMORIES_URL,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        # Backend returns:
        #
        # {
        #     "count": 2,
        #     "memories": [...]
        # }

        return data.get(
            "memories",
            []
        )

    except requests.RequestException as e:

        st.error(
            f"Could not load approved memories: {e}"
        )

        return []


def update_memory_status(
    memory_id,
    status
):

    try:

        response = requests.patch(
            f"{BASE_URL}/memories/{memory_id}/status",
            json={
                "status": status
            },
            timeout=10
        )

        response.raise_for_status()

        return True

    except requests.RequestException as e:

        st.error(
            f"Memory status update failed: {e}"
        )

        return False


def update_memory_content(
    memory_id,
    content
):

    try:

        response = requests.patch(
            f"{BASE_URL}/memories/{memory_id}",
            json={
                "content": content
            },
            timeout=10
        )

        response.raise_for_status()

        return True

    except requests.RequestException as e:

        st.error(
            f"Memory edit failed: {e}"
        )

        return False


def delete_memory(
    memory_id
):

    try:

        response = requests.delete(
            f"{BASE_URL}/memories/{memory_id}",
            timeout=10
        )

        response.raise_for_status()

        return True

    except requests.RequestException as e:

        st.error(
            f"Memory delete failed: {e}"
        )

        return False
# ==================================================
# RESTORE LATEST CONVERSATION
# ==================================================

if not st.session_state.conversation_loaded:
    restore_latest_conversation()
    st.session_state.conversation_loaded = True


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    # ==================================================
    # SIDEBAR HEADER
    # ==================================================

    st.markdown("## 🧠 Personal AI")

    st.caption(
        "Your private AI companion"
    )

    st.divider()

    # ==================================================
    # NEW CONVERSATION
    # ==================================================

    if st.button(
        "➕ New Conversation",
        use_container_width=True
    ):

        st.session_state.conversation_id = None
        st.session_state.messages = []

        # Prevent automatic restoration of the previous conversation
        st.session_state.conversation_loaded = True

        st.rerun()

    st.divider()

    # ==================================================
    # CONVERSATION HISTORY
    # ==================================================

    with st.expander(
        "💬 Conversation History",
        expanded=False
    ):

        conversations = get_conversations()

        if not conversations:

            st.caption(
                "No previous conversations."
            )

        else:

            for conversation in conversations:

                conversation_id = conversation["id"]

                conversation_title = conversation.get(
                    "title",
                    f"Conversation #{conversation_id}"
                )

                short_title = conversation_title[:32]

                if len(conversation_title) > 32:
                    short_title += "..."

                if st.button(
                    f"💬 {short_title}",
                    key=f"conversation_{conversation_id}",
                    use_container_width=True
                ):

                    loaded_messages = (
                        get_conversation_messages(
                            conversation_id
                        )
                    )

                    st.session_state.conversation_id = (
                        conversation_id
                    )

                    st.session_state.messages = [
                        {
                            "role": message["role"],
                            "content": message["content"]
                        }
                        for message in loaded_messages
                    ]

                    st.rerun()

    # ==================================================
    # PENDING MEMORIES
    # ==================================================

    st.subheader("🧠 Memory Center")

    memory_summary_col1, memory_summary_col2 = st.columns(2)

    with memory_summary_col1:
        st.metric(
            "Pending Memories",
            len(get_pending_memories())
        )

    with memory_summary_col2:
        st.metric(
            "Approved Memories",
            len(get_approved_memories())
        )
    
    with st.expander(
        "⏳ Pending Memories",
        expanded=False
    ):

        pending_memories = get_pending_memories()

        if not pending_memories:

            st.info(
                "No pending memories."
            )

        else:

            st.write(
                f"Found {len(pending_memories)} "
                "pending memory/memories."
            )
            st.caption(
                "Review these memories before approving them. "
                "Similar memories may already exist in Approved Memories."
            )

            for memory in pending_memories:

                memory_id = memory["id"]

                memory_type = memory.get(
                    "memory_type",
                    "Unknown"
                )

                memory_content = memory.get(
                    "content",
                    ""
                )

                confidence = memory.get(
                    "confidence",
                    None
                )

                with st.expander(
                    f"🧠 Memory #{memory_id}",
                    expanded=False
                ):

                    st.write(
                        f"**Type:** {memory_type}"
                    )

                    if confidence is not None:

                        st.write(
                            f"**Confidence:** "
                            f"{confidence:.2f}"
                        )

                    st.write(
                        "**Content:**"
                    )

                    st.info(
                        memory_content
                    )

                    col1, col2 = st.columns(2)

                    # ------------------------------------------
                    # APPROVE MEMORY
                    # ------------------------------------------

                    with col1:

                        if st.button(
                            "✅ Approve",
                            key=f"approve_{memory_id}",
                            use_container_width=True
                        ):

                            success = update_memory_status(
                                memory_id,
                                "approved"
                            )

                            if success:

                                st.success(
                                    "Memory approved."
                                )

                                st.rerun()

                    # ------------------------------------------
                    # REJECT MEMORY
                    # ------------------------------------------

                    with col2:

                        if st.button(
                            "❌ Reject",
                            key=f"reject_{memory_id}",
                            use_container_width=True
                        ):

                            success = update_memory_status(
                                memory_id,
                                "rejected"
                            )

                            if success:

                                st.success(
                                    "Memory rejected."
                                )

                                st.rerun()

    # ==================================================
    # APPROVED MEMORIES
    # ==================================================

    with st.expander(
        "✅ Approved Memories",
        expanded=False
    ):

        approved_memories = get_approved_memories()

        search_term = st.text_input(
            "🔎 Search approved memories",
            placeholder="Search by content or memory type...",
            key="approved_memory_search"
        )

        if search_term.strip():

            search_lower = search_term.strip().lower()

            approved_memories = [
                memory
                for memory in approved_memories
                if (
                    search_lower in memory.get(
                        "content",
                        ""
                    ).lower()
                    or
                    search_lower in memory.get(
                        "memory_type",
                        ""
                    ).lower()
                )
            ]

        if not approved_memories:

            st.info(
                "No approved memories."
            )

        else:

            st.write(
                f"{len(approved_memories)} "
                "approved memory/memories."
            )

            for memory in approved_memories:

                memory_id = memory["id"]

                memory_type = memory.get(
                    "memory_type",
                    "Unknown"
                )

                memory_content = memory.get(
                    "content",
                    ""
                )

                confidence = memory.get(
                    "confidence",
                    None
                )

                with st.expander(
                    f"📌 Memory #{memory_id}",
                    expanded=False
                ):

                    st.write(
                        f"**Type:** {memory_type}"
                    )

                    if confidence is not None:

                        st.write(
                            f"**Confidence:** "
                            f"{confidence:.2f}"
                        )

                    st.write(
                        "**Current content:**"
                    )

                    st.info(
                        memory_content
                    )

                    st.write(
                        "**Edit memory:**"
                    )

                    edited_content = st.text_area(
                        "Memory content",
                        value=memory_content,
                        key=f"edit_text_{memory_id}"
                    )

                    # ------------------------------------------
                    # UPDATE MEMORY
                    # ------------------------------------------

                    if st.button(
                        "💾 Update",
                        key=f"update_{memory_id}",
                        use_container_width=True
                    ):

                        cleaned_content = edited_content.strip()

                        if not cleaned_content:

                            st.warning(
                                "Memory cannot be empty."
                            )

                        elif len(cleaned_content) < 5:

                            st.warning(
                                "Memory must contain at least 5 characters."
                            )

                        elif len(cleaned_content) > 500:

                            st.warning(
                                "Memory cannot exceed 500 characters."
                            )

                        elif cleaned_content == memory_content.strip():

                            st.info(
                                "No changes detected."
                            )

                        else:

                            success = update_memory_content(
                                memory_id,
                                cleaned_content
                            )

                            if success:

                                st.success(
                                    "Memory updated successfully."
                                )

                                st.rerun()

                    # ------------------------------------------
                    # DELETE MEMORY
                    # ------------------------------------------

                    if st.button(
                        "🗑️ Delete Memory",
                        key=f"delete_{memory_id}",
                        use_container_width=True
                    ):

                        st.session_state[
                            f"confirm_delete_{memory_id}"
                        ] = True

                    if st.session_state.get(
                        f"confirm_delete_{memory_id}",
                        False
                    ):

                        st.warning(
                            "Are you sure you want to delete this memory?"
                        )

                        confirm_col1, confirm_col2 = st.columns(2)

                        with confirm_col1:

                            if st.button(
                                "Yes, Delete",
                                key=f"confirm_yes_{memory_id}",
                                use_container_width=True
                            ):

                                success = delete_memory(
                                    memory_id
                                )

                                if success:

                                    st.session_state[
                                        f"confirm_delete_{memory_id}"
                                    ] = False

                                    st.success(
                                        "Memory deleted successfully."
                                    )

                                    st.rerun()

                        with confirm_col2:

                            if st.button(
                                "Cancel",
                                key=f"confirm_no_{memory_id}",
                                use_container_width=True
                            ):

                                st.session_state[
                                    f"confirm_delete_{memory_id}"
                                ] = False

                                st.rerun()

    st.divider()



# ==================================================
# MAIN CHAT AREA
# ==================================================

st.title(
    "🧠 My Personal AI Assistant"
)

st.caption(
    "Your private AI companion"
)


# ==================================================
# CONVERSATION INFORMATION
# ==================================================

if st.session_state.conversation_id:

    st.caption(
        f"Conversation ID: "
        f"{st.session_state.conversation_id}"
    )

else:

    st.caption(
        "New conversation"
    )


# ==================================================
# DISPLAY CHAT HISTORY
# ==================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.write(
            message["content"]
        )


# ==================================================
# CHAT INPUT
# ==================================================

user_message = st.chat_input(
    "Type your message..."
)


if user_message:

    # ==================================================
    # DISPLAY USER MESSAGE
    # ==================================================

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    with st.chat_message("user"):

        st.write(
            user_message
        )

    # ==================================================
    # REQUEST DATA
    # ==================================================

    request_data = {

        "message": user_message,

        "conversation_id":
            st.session_state.conversation_id
    }

    # ==================================================
    # CALL BACKEND
    # ==================================================

    try:

        response = requests.post(
            CHAT_URL,
            json=request_data,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        # ----------------------------------------------
        # SAVE CONVERSATION ID
        # ----------------------------------------------

        st.session_state.conversation_id = (
            data["conversation_id"]
        )

        ai_response = data["response"]

    except requests.RequestException as e:

        ai_response = (
            f"Backend error: {e}"
        )

    # ==================================================
    # DISPLAY AI RESPONSE
    # ==================================================

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": ai_response
        }
    )

    with st.chat_message("assistant"):

        st.write(
            ai_response
        )