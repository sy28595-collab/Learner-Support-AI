import streamlit as st
import pandas as pd
import json
import html

from database.db import get_connection
from database.crud import get_thread
from src.search import search_conversations


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------
def show():
    st.markdown("""
    <style>

    /* Main page spacing */
    

    /* Page heading */
    .history-title {
        font-size: 27px;
        font-weight: 700;
        color: #172554;
        margin-bottom: 0px;
    }

    .history-subtitle {
        font-size: 12px;
        color: #64748b;
        margin-top: 2px;
        margin-bottom: 12px;
    }

    /* Metric cards */
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 15px;
        height: 82px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }

    .metric-label {
        font-size: 12px;
        color: #64748b;
    }

    .metric-value {
        font-size: 25px;
        font-weight: 700;
        color: #172554;
        margin-top: 3px;
    }

    /* Section heading */
    .section-heading {
        font-size: 16px;
        font-weight: 700;
        color: #172554;
        margin-bottom: 8px;
    }

    /* Preview cards */
    .preview-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 9px;
        padding: 11px;
        margin-bottom: 8px;
    }

    .preview-label {
        font-size: 11px;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 3px;
    }

    .preview-value {
        font-size: 13px;
        color: #1e293b;
    }

    /* Chat messages */
    .chat-learner {
        background: #f1f5f9;
        padding: 8px 10px;
        border-radius: 9px;
        margin-bottom: 6px;
        font-size: 12px;
        color: #1e293b;
    }

    .chat-agent {
        background: #dcfce7;
        padding: 8px 10px;
        border-radius: 9px;
        margin-bottom: 6px;
        font-size: 12px;
        color: #14532d;
    }

    /* Summary card */
    .summary-box {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 9px;
        padding: 11px;
        margin-top: 7px;
        font-size: 12px;
        color: #1e3a8a;
    }

    /* Compact dividers */
    hr {
        margin-top: 8px !important;
        margin-bottom: 8px !important;
    }

    </style>
    """, unsafe_allow_html=True)


    # --------------------------------------------------
    # 2. DATABASE STATISTICS
    # --------------------------------------------------

    def get_statistics():

        with get_connection() as connection:

            total = connection.execute(
                "SELECT COUNT(*) FROM support_threads"
            ).fetchone()[0]

            open_count = connection.execute(
                """
                SELECT COUNT(*) FROM support_threads
                WHERE LOWER(thread_status) = 'open'
                """
            ).fetchone()[0]

            resolved = connection.execute(
                """
                SELECT COUNT(*) FROM support_threads
                WHERE LOWER(thread_status) = 'resolved'
                """
            ).fetchone()[0]

            closed = connection.execute(
                """
                SELECT COUNT(*) FROM support_threads
                WHERE LOWER(thread_status) = 'closed'
                """
            ).fetchone()[0]

        return total, open_count, resolved, closed


    # --------------------------------------------------
    # 3. GET LATEST SUMMARY
    # --------------------------------------------------

    def get_latest_summary(thread_id):

        with get_connection() as connection:

            summary = connection.execute(
                """
                SELECT *
                FROM handover_summaries
                WHERE thread_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (thread_id,)
            ).fetchone()

        return dict(summary) if summary else None


    # --------------------------------------------------
    # 4. SAFE JSON CONVERSION
    # --------------------------------------------------

    def convert_list(value):

        if not value:
            return []

        try:
            result = json.loads(value)

            if isinstance(result, list):
                return result

            return [str(result)]

        except (json.JSONDecodeError, TypeError):
            return [str(value)]


    # --------------------------------------------------
    # 5. DISPLAY CONVERSATION
    # --------------------------------------------------

    def display_messages(messages, limit=4):

        if not messages:
            st.info("No messages found.")
            return

        recent_messages = messages[-limit:]

        for message in recent_messages:

            sender = message.get("sender", "Unknown")
            content = html.escape(str(message.get("message", "")))

            if sender.lower() == "learner":

                st.markdown(
                    f"""
                    <div class="chat-learner">
                        <b>🎓 Learner</b><br>
                        {content}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    f"""
                    <div class="chat-agent">
                        <b>👨‍💻 Support Agent</b><br>
                        {content}
                    </div>
                    """,
                    unsafe_allow_html=True
                )


    # --------------------------------------------------
    # 6. DISPLAY HANDOVER SUMMARY
    # --------------------------------------------------

    def display_summary(summary):

        if not summary:
            st.info("No AI summary available for this conversation.")
            return

        st.markdown(
            '<div class="section-heading">🤖 AI Handover Summary</div>',
            unsafe_allow_html=True
        )

        issue = summary.get("issue", "Not available")
        status = summary.get("current_status", "Not available")
        next_action = summary.get("next_action", "Not available")

        steps = convert_list(summary.get("steps_tried"))
        questions = convert_list(summary.get("unresolved_questions"))

        st.markdown(
            f"""
            <div class="summary-box">

            <b>Issue</b><br>
            {html.escape(str(issue))}

            <br><br>

            <b>Current Status</b><br>
            {html.escape(str(status))}

            <br><br>

            <b>Next Action</b><br>
            {html.escape(str(next_action))}

            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("View complete AI summary"):

            st.write("**Steps Tried**")

            if steps:
                for step in steps:
                    st.write(f"• {step}")
            else:
                st.write("No steps recorded.")

            st.write("**Unresolved Questions**")

            if questions:
                for question in questions:
                    st.write(f"• {question}")
            else:
                st.write("No unresolved questions.")

            st.caption(
                f"Provider: {summary.get('provider', 'N/A')} | "
                f"Model: {summary.get('model', 'N/A')} | "
                f"Version: {summary.get('version', 'N/A')}"
            )


    # --------------------------------------------------
    # 7. PAGE HEADER
    # --------------------------------------------------

    header_col1, header_col2 = st.columns([5, 1])

    with header_col1:

        st.markdown(
            '<div class="history-title">Conversation History</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="history-subtitle">'
            'Search, review and manage learner support conversations.'
            '</div>',
            unsafe_allow_html=True
        )

    with header_col2:

        st.write("")

        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()


    # --------------------------------------------------
    # 8. METRIC CARDS
    # --------------------------------------------------

    total, open_count, resolved, closed = get_statistics()

    metric_columns = st.columns(4)

    metrics = [
        ("Total Conversations", total, "📁"),
        ("Open Conversations", open_count, "🟠"),
        ("Resolved", resolved, "✅"),
        ("Closed", closed, "🔒")
    ]

    for column, metric in zip(metric_columns, metrics):

        label, value, icon = metric

        with column:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{icon} {label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


    st.write("")


    # --------------------------------------------------
    # 9. SEARCH AND FILTERS
    # --------------------------------------------------

    filter_col1, filter_col2, filter_col3 = st.columns([4, 1.5, 1])

    with filter_col1:

        search_query = st.text_input(
            "Search Conversations",
            placeholder="Search by Thread ID, Learner ID or keyword...",
            label_visibility="collapsed"
        )

    with filter_col2:

        status_filter = st.selectbox(
            "Status",
            ["All", "Open", "Resolved", "Closed"],
            label_visibility="collapsed"
        )

    with filter_col3:

        if st.button("Search", use_container_width=True):
            st.session_state.history_page = 1


    # --------------------------------------------------
    # 10. PAGINATION DATA
    # --------------------------------------------------

    if "history_page" not in st.session_state:
        st.session_state.history_page = 1


    selected_status = (
        None if status_filter == "All"
        else status_filter.lower()
    )

    result = search_conversations(
        query=search_query.strip() or None,
        status=selected_status,
        page=1,
        page_size=max(total,1)
    )

    records = result["records"]
    total_records = result["total_records"]
    total_pages = result["total_pages"]


    # Reset page if filters result in fewer pages
    if total_pages > 0 and st.session_state.history_page > total_pages:

        st.session_state.history_page = total_pages

        st.rerun()


    # --------------------------------------------------
    # 11. MAIN TWO-COLUMN LAYOUT
    # --------------------------------------------------

    left_column, right_column = st.columns(
        [1.25, 1],
        gap="medium"
    )


    # ==================================================
    # LEFT: CONVERSATION LIST
    # ==================================================

    with left_column:

        st.markdown(
            '<div class="section-heading">📋 Conversations</div>',
            unsafe_allow_html=True
        )

        st.caption(f"{total_records} conversations found")

        if records:

            dataframe = pd.DataFrame(records)

            display_columns = [
                "thread_id",
                "learner_id",
                "thread_status",
                "total_messages"
            ]

            dataframe = dataframe[
                [column for column in display_columns
                if column in dataframe.columns]
            ]

            dataframe = dataframe.rename(
                columns={
                    "thread_id": "Thread ID",
                    "learner_id": "Learner ID",
                    "thread_status": "Status",
                    "total_messages": "Messages"
                }
            )

            st.dataframe(
                dataframe,
                use_container_width=True,
                hide_index=True,
                height=420
            )

        else:

            st.info("No conversations found.")


    # ==================================================
    # RIGHT: CONVERSATION PREVIEW
    # ==================================================

    with right_column:

        st.markdown(
            '<div class="section-heading">👁️ Conversation Preview</div>',
            unsafe_allow_html=True
        )

        if records:

            thread_options = [
                record["thread_id"] for record in records
            ]

            selected_thread = st.selectbox(
                "Select Conversation",
                thread_options,
                label_visibility="collapsed"
            )

            thread_data = get_thread(selected_thread)

            if thread_data:

                thread = thread_data.get("thread", {})
                messages = thread_data.get("messages", [])

                info_col1, info_col2 = st.columns(2)

                with info_col1:

                    st.markdown(
                        f"""
                        <div class="preview-card">
                            <div class="preview-label">THREAD ID</div>
                            <div class="preview-value">
                                {html.escape(str(selected_thread))}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with info_col2:

                    st.markdown(
                        f"""
                        <div class="preview-card">
                            <div class="preview-label">STATUS</div>
                            <div class="preview-value">
                                {html.escape(str(thread.get('thread_status', 'N/A')))}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.markdown("**Recent Messages**")

                display_messages(messages, limit=3)

                if len(messages) > 3:

                    with st.expander(
                        f"View all {len(messages)} messages"
                    ):

                        display_messages(
                            messages,
                            limit=len(messages)
                        )

                st.divider()

                summary = get_latest_summary(selected_thread)

                display_summary(summary)

        else:

            st.info("Select a conversation to see its details.")


    # --------------------------------------------------
    # 12. COMPACT PAGINATION
    # --------------------------------------------------

    st.divider()

    page_col1, page_col2, page_col3 = st.columns(
        [2, 2, 2]
    )

    with page_col1:

        st.caption(
            f"Showing {len(records)} of {total_records} conversations"
        )

    with page_col2:

        st.caption(
            f"Page {result['current_page']} of {total_pages}"
            if total_pages > 0
            else "Page 0 of 0"
        )

    with page_col3:

        previous_col, next_col = st.columns(2)

        with previous_col:

            if st.button(
                "← Previous",
                disabled=st.session_state.history_page <= 1,
                use_container_width=True
            ):

                st.session_state.history_page -= 1
                st.rerun()

        with next_col:

            if st.button(
                "Next →",
                disabled=st.session_state.history_page >= total_pages,
                use_container_width=True
            ):

                st.session_state.history_page += 1
                st.rerun()