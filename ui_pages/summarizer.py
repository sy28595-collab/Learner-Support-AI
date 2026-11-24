import streamlit as st
import streamlit.components.v1 as components
import html
import logging
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

    .main-heading {
        font-size: 28px;
        font-weight: 800;
        color: #172554;
        margin-bottom: 2px;
    }

    .page-caption {
        color: #64748B;
        font-size: 12px;
        margin-bottom: 12px;
    }

    .section-heading {
        font-size: 18px;
        font-weight: 750;
        color: #172554;
        margin-bottom: 5px;
    }

    .panel-caption {
        color: #64748B;
        font-size: 11px;
        margin-bottom: 8px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 13px;
        border-color: #DCE4F2;
    }

    .stButton button {
        border-radius: 9px;
        font-weight: 650;
        transition: all 0.2s ease;
    }

    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.12);
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 11px;
        padding: 10px;
    }

    .selector-label {
        color: #64748B;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
    }

    .selector-value {
        color: #172554;
        font-size: 14px;
        font-weight: 700;
        overflow-wrap: anywhere;
    }

    @keyframes pageFade {
        from {
            opacity: 0;
            transform: translateY(7px);
        }

        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .main .block-container {
        animation: pageFade 0.35s ease;
        padding-top: 0.55rem !important;
    }

    @media (max-width: 900px) {
        .main-heading {
            font-size: 23px;
        }
    }

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

            .message-row {
                display: flex;
                width: 100%;
                margin-bottom: 12px;
                opacity: 0;
                animation: messageEnter 0.45s ease forwards;
            }

            .learner-row {
                justify-content: flex-start;
            }

            .agent-row {
                justify-content: flex-end;
            }

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

            .learner-bubble {
                background: #FFFFFF;
                color: #172033;
                border-radius: 4px 14px 14px 14px;
            }

            .agent-bubble {
                background: #D9FDD3;
                color: #172033;
                border-radius: 14px 4px 14px 14px;
            }

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

            .message-number {
                text-align: right;
                font-size: 10px;
                color: #94A3B8;
                margin-top: 5px;
            }

            .chat-container::-webkit-scrollbar {
                width: 5px;
            }

            .chat-container::-webkit-scrollbar-thumb {
                background: #B8C2CC;
                border-radius: 10px;
            }

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

        st.markdown(
            "## 🤖",
            text_alignment="center"
        )

        st.markdown(
            "### AI Summary",
            text_alignment="center"
        )

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
        'Select a learner conversation, review messages and generate an AI handover summary.'
        '</div>',
        unsafe_allow_html=True
    )

    # LOAD AVAILABLE CONVERSATIONS

    threads = get_all_threads()

    if not threads:

        st.warning("No conversations available.")

        return

    thread_options = {
        item["thread_id"]: item
        for item in threads
    }

    # THREE SECTION LAYOUT

    selector_col, chat_col, summary_col = st.columns(
        [0.78, 1.25, 1.12],
        gap="small"
    )

    # ==================================================
    # LEFT SECTION - CONVERSATION SELECTOR
    # ==================================================

    with selector_col:

        with st.container(border=True, height=570):

            st.markdown(
                '<div class="section-heading">📂 Select Conversation</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="panel-caption">Choose a thread to view its conversation and summary.</div>',
                unsafe_allow_html=True
            )

            selected_thread = st.selectbox(
                "Conversation",
                options=list(thread_options.keys()),
                format_func=lambda thread_id: (
                    f"{thread_id} | "
                    f"{thread_options[thread_id]['learner_id']}"
                ),
                label_visibility="collapsed",
                key="summarizer_thread_selector"
            )

            thread_data = get_thread(selected_thread)

            if not thread_data:

                st.error("Conversation not found.")

                return

            thread_info = thread_data["thread"]

            messages = thread_data["messages"]

            # CLEAR PREVIOUS SUMMARY WHEN THREAD CHANGES

            if st.session_state.get("active_thread") != selected_thread:

                st.session_state["active_thread"] = selected_thread

                st.session_state.pop(
                    "generated_summary",
                    None
                )

            st.divider()

            st.markdown("**CONVERSATION DETAILS**")

            st.markdown(
                f'''<div class="selector-label">Thread ID</div>
                <div class="selector-value">{html.escape(str(thread_info["thread_id"]))}</div>''',
                unsafe_allow_html=True
            )

            st.write("")

            st.markdown(
                f'''<div class="selector-label">Learner ID</div>
                <div class="selector-value">{html.escape(str(thread_info["learner_id"]))}</div>''',
                unsafe_allow_html=True
            )

            st.write("")

            st.markdown(
                f'''<div class="selector-label">Total Messages</div>
                <div class="selector-value">{len(messages)}</div>''',
                unsafe_allow_html=True
            )

            st.divider()

            st.markdown("**SUPPORT AGENT**")

            agent_name = st.text_input(
                "Agent name",
                value="Support Agent",
                key="summarizer_agent_name",
                label_visibility="collapsed",
                placeholder="Enter support agent name"
            )

            st.caption(
                "This name is recorded in the summary audit log."
            )

            st.divider()

            if st.button(
                "↻ Refresh Conversation",
                width="stretch",
                key="refresh_summarizer_thread"
            ):

                st.rerun()

    # ==================================================
    # CENTER SECTION - CONVERSATION
    # ==================================================

    with chat_col:

        with st.container(border=True, height=570):

            st.markdown(
                '<div class="section-heading">💬 Conversation</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="panel-caption">{len(messages)} messages · {html.escape(str(selected_thread))}</div>',
                unsafe_allow_html=True
            )

            if messages:

                chat_html = create_chat_html(messages)

                components.html(
                    chat_html,
                    height=485,
                    scrolling=True
                )

            else:

                st.info(
                    "No messages available for this conversation."
                )

    # ==================================================
    # RIGHT SECTION - AI HANDOVER SUMMARY
    # ==================================================

    with summary_col:

        with st.container(border=True, height=570):

            st.markdown(
                '<div class="section-heading">✨ AI Handover Summary</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="panel-caption">Powered by Google Gemini · {html.escape(str(MODEL))}</div>',
                unsafe_allow_html=True
            )

            result = st.session_state.get(
                "generated_summary"
            )

            has_current_summary = (
                result is not None
                and result.get("thread_id") == selected_thread
            )

            button_label = (
                "↻ Regenerate Summary"
                if has_current_summary
                else "✨ Generate Summary"
            )

            generate_button = st.button(
                button_label,
                type="primary",
                width="stretch",
                key="generate_handover_summary"
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

                            # GENERATE SUMMARY

                            summary = generate_handover_summary(
                                messages
                            )

                            summary_data = summary.model_dump()

                            # SAVE SUMMARY

                            summary_id, version = save_summary(
                                thread_id=selected_thread,
                                summary=summary_data,
                                provider="gemini",
                                model=MODEL,
                                prompt_version="v1"
                            )

                            # SAVE AUDIT LOG

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

                            # SAVE IN SESSION STATE

                            st.session_state["generated_summary"] = {

                                "summary": summary_data,

                                "thread_id": selected_thread,

                                "summary_id": summary_id,

                                "version": version

                            }

                        st.rerun()

                    except Exception as error:

                        error_message = str(error)

                        if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:

                            st.warning(
                                "⚠️ Gemini Free Tier daily limit has been reached. "
                                "Please try again after your quota resets."
                            )

                        elif "503" in error_message or "UNAVAILABLE" in error_message:

                            st.warning(
                                "⚠️ Gemini is temporarily unavailable due to high demand. "
                                "Please try again later."
                            )
                        elif "401" in error_message or "403" in error_message:

                            st.error(
                                "Gemini API authentication failed. "
                                "Please check your API key."
                            )

                        else:

                            st.error(
                                "Summary generation failed. Please try again later."
                            )

                        logging.error(
                            "Summary generation failed: %s",
                            error_message
                        )

            # DISPLAY CURRENT SUMMARY

            result = st.session_state.get(
                "generated_summary"
            )

            if result and result.get("thread_id") == selected_thread:

                with st.container(
                    height=455,
                    border=False
                ):

                    display_summary(result)

            else:

                with st.container(
                    height=455,
                    border=False
                ):

                    display_empty_summary()