import streamlit as st
import streamlit.components.v1 as components
import html

from database.crud import get_thread, get_all_threads
from database.summary_manager import save_summary
from database.audit_manager import log_action

from src.gemini_client import generate_handover_summary, MODEL


# ==================================================
# 1. PAGE CSS
# ==================================================

def load_page_css():

    st.markdown("""
    <style>

    /* Page heading */

    .main-heading {
        font-size: 30px;
        font-weight: 750;
        color: #172033;
        margin-bottom: 3px;
    }

    .page-caption {
        color: #64748B;
        font-size: 13px;
        margin-bottom: 12px;
    }

    /* Section heading */

    .section-heading {
        font-size: 22px;
        font-weight: 700;
        color: #172033;
    }

    /* Summary cards */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 11px;
        transition: all 0.25s ease;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #BFDBFE;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
    }

    /* Buttons */

    .stButton button {
        border-radius: 9px;
        font-weight: 600;
        transition: all 0.25s ease;
    }

    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 12px rgba(37, 99, 235, 0.15);
    }

    /* Metric cards */

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 12px;
        transition: all 0.25s ease;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: #BFDBFE;
    }

    /* Page animation */

    @keyframes pageFade {

        from {
            opacity: 0;
            transform: translateY(10px);
        }

        to {
            opacity: 1;
            transform: translateY(0);
        }

    }

    .main .block-container {
        animation: pageFade 0.5s ease;
    }

    /* Accessibility */

    @media (prefers-reduced-motion: reduce) {

        *,
        *::before,
        *::after {
            animation-duration: 0.01ms !important;
            animation-delay: 0ms !important;
            transition-duration: 0.01ms !important;
        }

    }

    </style>
    """, unsafe_allow_html=True)


# ==================================================
# 2. WHATSAPP STYLE CHAT
# ==================================================

def create_chat_html(messages):

    chat_html = """
    <!DOCTYPE html>
    <html>

    <head>

        <meta name="viewport" content="width=device-width, initial-scale=1">

        <style>

            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background: #E9EDF2;
            }

            .chat-container {
                width: 100%;
                height: 100%;
                padding: 14px;
                overflow-y: auto;
                background: #E9EDF2;
                border-radius: 12px;
            }

            /* Message rows */

            .message-row {
                display: flex;
                width: 100%;
                margin-bottom: 12px;
                opacity: 0;
                animation: messageEnter 0.45s ease forwards;
            }

            /* Learner left */

            .learner-row {
                justify-content: flex-start;
            }

            /* Agent right */

            .agent-row {
                justify-content: flex-end;
            }

            /* Sequential animation */

            @keyframes messageEnter {

                from {
                    opacity: 0;
                    transform: translateY(14px);
                }

                to {
                    opacity: 1;
                    transform: translateY(0);
                }

            }

            /* Message bubble */

            .message-bubble {
                max-width: 82%;
                min-width: 100px;
                padding: 10px 13px;
                font-size: 13px;
                line-height: 1.55;
                overflow-wrap: anywhere;
                box-shadow: 0 2px 5px rgba(0,0,0,0.07);
                transition: transform 0.2s ease;
            }

            .message-bubble:hover {
                transform: translateY(-2px);
            }

            /* Learner bubble */

            .learner-bubble {
                background: #FFFFFF;
                color: #172033;
                border-radius: 4px 14px 14px 14px;
            }

            /* Agent bubble */

            .agent-bubble {
                background: #D9FDD3;
                color: #172033;
                border-radius: 14px 4px 14px 14px;
            }

            /* Sender */

            .sender {
                font-size: 11px;
                font-weight: 700;
                margin-bottom: 5px;
            }

            .learner-sender {
                color: #2563EB;
            }

            .agent-sender {
                color: #15803D;
            }

            /* Message number */

            .message-number {
                text-align: right;
                font-size: 10px;
                color: #94A3B8;
                margin-top: 5px;
            }

            /* Scrollbar */

            .chat-container::-webkit-scrollbar {
                width: 5px;
            }

            .chat-container::-webkit-scrollbar-thumb {
                background: #B8C2CC;
                border-radius: 10px;
            }

            /* Accessibility */

            @media (prefers-reduced-motion: reduce) {

                .message-row {
                    animation: none;
                    opacity: 1;
                }

            }

        </style>

    </head>

    <body>

        <div class="chat-container">

    """

    # Generate messages

    for index, message in enumerate(messages, start=1):

        sender = message["sender"]

        message_text = html.escape(
            str(message["message"])
        ).replace("\n", "<br>")

        # Each message appears one by one

        delay = min((index - 1) * 0.15, 4)

        if sender == "learner":

            chat_html += f"""

                <div class="message-row learner-row"
                     style="animation-delay:{delay}s;">

                    <div class="message-bubble learner-bubble">

                        <div class="sender learner-sender">
                            👤 Learner
                        </div>

                        <div>
                            {message_text}
                        </div>

                        <div class="message-number">
                            Message {index}
                        </div>

                    </div>

                </div>

            """

        else:

            chat_html += f"""

                <div class="message-row agent-row"
                     style="animation-delay:{delay}s;">

                    <div class="message-bubble agent-bubble">

                        <div class="sender agent-sender">
                            🎧 Support Agent
                        </div>

                        <div>
                            {message_text}
                        </div>

                        <div class="message-number">
                            Message {index}
                        </div>

                    </div>

                </div>

            """

    chat_html += """

        </div>

    </body>
    </html>

    """

    return chat_html


# ==================================================
# 3. SUMMARY DISPLAY
# ==================================================

def display_summary(result):

    summary = result["summary"]

    st.success(
        f"Version {result['version']} | "
        f"Summary ID: {result['summary_id']}"
    )

    # MAIN ISSUE

    with st.container(border=True):

        st.markdown("**🔴 MAIN ISSUE**")

        st.write(
            summary.get("issue", "Not available")
        )

    # STEPS TRIED

    with st.container(border=True):

        st.markdown("**🛠️ STEPS TRIED**")

        steps = summary.get("steps_tried", [])

        if steps:

            for step in steps:
                st.markdown(f"- {step}")

        else:

            st.write("No steps identified.")

    # CURRENT STATUS

    with st.container(border=True):

        st.markdown("**📌 CURRENT STATUS**")

        st.write(
            summary.get("current_status", "Not available")
        )

    # UNRESOLVED QUESTIONS

    with st.container(border=True):

        st.markdown("**❓ UNRESOLVED QUESTIONS**")

        questions = summary.get("unresolved_questions", [])

        if questions:

            for question in questions:
                st.markdown(f"- {question}")

        else:

            st.write("No unresolved questions.")

    # NEXT ACTION

    with st.container(border=True):

        st.markdown("**➡️ RECOMMENDED NEXT ACTION**")

        st.write(
            summary.get("next_action", "Not available")
        )

    st.warning(
        "Human review required. Verify this AI-generated "
        "summary before using it."
    )


# ==================================================
# 4. EMPTY SUMMARY STATE
# ==================================================

def display_empty_summary():

    with st.container(border=True):

        st.write("")

        # Robot icon

        st.markdown(
            "## 🤖",
            text_alignment="center"
        )

        # Heading

        st.markdown(
            "### AI Summary",
            text_alignment="center"
        )

        # Description

        st.caption(
            "Your handover summary will appear here "
            "after Gemini analyzes the conversation.",
            text_alignment="center"
        )

        st.write("")


# ==================================================
# 5. MAIN SUMMARIZER PAGE
# ==================================================

def show():

    load_page_css()

    # PAGE HEADER

    st.markdown(
        '<div class="main-heading">AI Conversation Summarizer</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="page-caption">'
        'Review learner conversations and generate AI-powered handover summaries.'
        '</div>',
        unsafe_allow_html=True
    )

    # FETCH CONVERSATIONS

    threads = get_all_threads()

    if not threads:

        st.warning("No conversations available.")

        return

    thread_options = {
        item["thread_id"]: item
        for item in threads
    }

    # CONVERSATION SELECTION

    col1, col2 = st.columns([3, 2])

    with col1:

        selected_thread = st.selectbox(
            "Select Conversation",
            options=list(thread_options.keys()),
            format_func=lambda thread_id: (
                f"{thread_id} | "
                f"{thread_options[thread_id]['learner_id']}"
            )
        )

    with col2:

        agent_name = st.text_input(
            "Support Agent",
            value="Support Agent"
        )

    # LOAD CONVERSATION

    thread_data = get_thread(selected_thread)

    if not thread_data:

        st.error("Conversation not found.")

        return

    thread_info = thread_data["thread"]

    messages = thread_data["messages"]

    # CLEAR OLD SUMMARY WHEN THREAD CHANGES

    if st.session_state.get("active_thread") != selected_thread:

        st.session_state["active_thread"] = selected_thread

        st.session_state.pop(
            "generated_summary",
            None
        )

    # CONVERSATION INFORMATION

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Thread ID",
        thread_info["thread_id"]
    )

    col2.metric(
        "Learner ID",
        thread_info["learner_id"]
    )

    col3.metric(
        "Total Messages",
        len(messages)
    )

    st.divider()

    # TWO COLUMN LAYOUT

    chat_col, summary_col = st.columns(
        [1.2, 0.8],
        gap="small"
    )

    # ==================================================
    # LEFT SIDE - CONVERSATION
    # ==================================================

    with chat_col:

        st.markdown(
            '<div class="section-heading">💬 Conversation</div>',
            unsafe_allow_html=True
        )

        if messages:

            chat_html = create_chat_html(messages)

            chat_height = min(
                max(350, len(messages) * 85),
                500
            )

            components.html(
                chat_html,
                height=chat_height,
                scrolling=True
            )

        else:

            st.info("No messages available.")

    # ==================================================
    # RIGHT SIDE - AI SUMMARY
    # ==================================================

    with summary_col:

        st.markdown(
            '<div class="section-heading">✨ AI Handover Summary</div>',
            unsafe_allow_html=True
        )

        st.caption(
            f"Powered by Google Gemini | {MODEL}"
        )

        # GENERATE BUTTON

        generate_button = st.button(
            "✨ Generate Summary",
            type="primary",
            width="stretch"
        )

        if generate_button:

            if not agent_name.strip():

                st.error(
                    "Please enter the support agent name."
                )

            elif not messages:

                st.warning(
                    "No conversation messages available."
                )

            else:

                try:

                    with st.spinner(
                        "Gemini is analyzing the conversation..."
                    ):

                        # Generate summary

                        summary = generate_handover_summary(
                            messages
                        )

                        # Convert Pydantic response

                        summary_data = summary.model_dump()

                        # Save summary

                        summary_id, version = save_summary(
                            thread_id=selected_thread,
                            summary=summary_data,
                            provider="gemini",
                            model=MODEL,
                            prompt_version="v1"
                        )

                        # Save audit log

                        log_action(
                            action="summary_generated",
                            performed_by=agent_name.strip(),
                            thread_id=selected_thread,
                            summary_id=summary_id,
                            details=(
                                f"Gemini generated summary "
                                f"version {version}."
                            )
                        )

                        # Save in session state

                        st.session_state["generated_summary"] = {

                            "summary": summary_data,

                            "thread_id": selected_thread,

                            "summary_id": summary_id,

                            "version": version

                        }

                    st.success(
                        "Summary generated successfully!"
                    )

                except Exception as error:

                    st.error(
                        "Summary generation failed."
                    )

                    st.exception(error)

        # DISPLAY SUMMARY

        result = st.session_state.get(
            "generated_summary"
        )

        if result and result["thread_id"] == selected_thread:

            st.divider()

            display_summary(result)

        else:

            display_empty_summary()