import streamlit as st
import uuid

from datetime import datetime
from database.db import get_connection


# =====================================
# 1. MAIN PAGE
# =====================================

def show():

    # =====================================
    # PAGE CSS
    # =====================================

    st.markdown("""
    <style>

    /* Compact page layout */

    .main .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 0.4rem !important;
    }

    /* Page heading */

    .page-title {
        font-size: 27px;
        font-weight: 800;
        color: #172554;
        margin-bottom: 0;
        line-height: 1.3;
    }

    .page-subtitle {
        color: #64748B;
        font-size: 12px;
        margin-top: 2px;
        margin-bottom: 5px;
    }

    /* Section headings */

    .section-title {
        font-size: 18px;
        font-weight: 750;
        color: #172554;
        margin-bottom: 5px;
    }

    /* Containers */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 11px;
        border-color: #DCE5F2;
    }

    /* Reduce vertical gaps */

    div[data-testid="stVerticalBlock"] {
        gap: 0.45rem;
    }

    /* Input fields */

    .stTextInput,
    .stDateInput,
    .stSelectbox {
        margin-bottom: 0 !important;
    }

    /* Message text area */

    .stTextArea textarea {
        min-height: 65px !important;
    }

    /* Buttons */

    .stButton button,
    .stFormSubmitButton button {
        border-radius: 9px;
        font-weight: 650;
        min-height: 36px;
    }

    /* Divider */

    hr {
        margin-top: 8px !important;
        margin-bottom: 8px !important;
    }

    </style>
    """, unsafe_allow_html=True)


    # =====================================
    # 2. SESSION STATE
    # =====================================

    if "new_messages" not in st.session_state:
        st.session_state["new_messages"] = []

    if "message_counter" not in st.session_state:
        st.session_state["message_counter"] = 0


    # =====================================
    # 3. PAGE HEADER
    # =====================================

    st.markdown(
        '<div class="page-title">➕ New Conversation</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="page-subtitle">'
        'Add and manage a new learner support conversation.'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()


    # =====================================
    # 4. LEARNER INFORMATION
    # =====================================

    with st.container(border=True):

        st.markdown(
            '<div class="section-title">'
            '👤 Learner Information'
            '</div>',
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        with col1:

            learner_id = st.text_input(
                "Learner ID",
                placeholder="Example: LEARNER_021"
            )

        with col2:

            conversation_date = st.date_input(
                "Conversation Date",
                value=datetime.now().date()
            )


    # =====================================
    # 5. ADD NEW MESSAGE
    # =====================================

    with st.container(border=True):

        st.markdown(
            '<div class="section-title">'
            '💬 Add New Message'
            '</div>',
            unsafe_allow_html=True
        )

        counter = st.session_state["message_counter"]

        with st.form("add_message_form"):

            col1, col2 = st.columns([1, 2])

            with col1:

                sender = st.selectbox(
                    "Message Sender",
                    ["learner", "agent"],
                    format_func=lambda x: (
                        "👤 Learner"
                        if x == "learner"
                        else "🎧 Support Agent"
                    ),
                    key=f"sender_{counter}"
                )

            with col2:

                message = st.text_area(
                    "Message Text",
                    placeholder="Enter conversation message...",
                    height=65,
                    key=f"message_{counter}"
                )

            add_message = st.form_submit_button(
                "➕ Add Message",
                width="stretch"
            )

        if add_message:

            if not message.strip():

                st.warning("Please enter a message.")

            else:

                st.session_state["new_messages"].append({
                    "sender": sender,
                    "message": message.strip()
                })

                st.session_state["message_counter"] += 1

                st.rerun()


    # =====================================
    # 6. CONVERSATION PREVIEW
    # =====================================

    messages = st.session_state["new_messages"]

    if messages:

        with st.container(border=True):

            st.markdown(
                '<div class="section-title">'
                '📨 Conversation Preview'
                '</div>',
                unsafe_allow_html=True
            )

            for index, item in enumerate(messages, start=1):

                if item["sender"] == "learner":
                    label = "👤 Learner"
                else:
                    label = "🎧 Support Agent"

                with st.container(border=True):

                    st.markdown(
                        f"**Message {index} | {label}**"
                    )

                    st.write(item["message"])

            col1, col2 = st.columns([3, 1])

            with col1:

                st.caption(
                    f"Total Messages: {len(messages)}"
                )

            with col2:

                if st.button(
                    "🗑️ Clear Messages",
                    width="stretch"
                ):

                    st.session_state["new_messages"] = []

                    st.session_state["message_counter"] = 0

                    st.rerun()


    # =====================================
    # 7. SAVE CONVERSATION
    # =====================================

    if st.button(
        "💾 Save Conversation",
        type="primary",
        width="stretch"
    ):

        if not learner_id.strip():

            st.error("Please enter Learner ID.")

        elif not messages:

            st.error("Please add at least one message.")

        else:

            thread_id = (
                "THREAD_"
                + uuid.uuid4().hex[:8].upper()
            )

            created_at = conversation_date.isoformat()

            try:

                with get_connection() as connection:

                    # Create learner if not exists

                    connection.execute(
                        """
                        INSERT INTO learners (learner_id)
                        VALUES (?)
                        ON CONFLICT(learner_id) DO NOTHING
                        """,
                        (learner_id.strip(),)
                    )

                    # Create support thread

                    connection.execute(
                        """
                        INSERT INTO support_threads
                        (thread_id, learner_id, source, created_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            thread_id,
                            learner_id.strip(),
                            "manual_entry",
                            created_at
                        )
                    )

                    # Save conversation messages

                    records = [
                        (
                            thread_id,
                            item["sender"],
                            item["message"],
                            index
                        )
                        for index, item in enumerate(
                            messages,
                            start=1
                        )
                    ]

                    connection.executemany(
                        """
                        INSERT INTO support_messages
                        (thread_id, sender, message, message_order)
                        VALUES (?, ?, ?, ?)
                        """,
                        records
                    )

                st.success(
                    "Conversation saved successfully!"
                )

                st.info(
                    f"Generated Thread ID: {thread_id}"
                )

                # Clear form data

                st.session_state["new_messages"] = []

                st.session_state["message_counter"] = 0

            except Exception as error:

                st.error(
                    "Unable to save conversation."
                )

                st.exception(error)