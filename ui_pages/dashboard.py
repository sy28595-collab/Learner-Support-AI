import streamlit as st
import pandas as pd
import plotly.express as px
import json
import html

from textwrap import dedent
from database.db import get_connection


# ==================================================
# 1. HELPER FUNCTIONS
# ==================================================

def parse_list(value):

    if not value:
        return []

    if isinstance(value, list):
        return value

    try:

        result = json.loads(value)

        if isinstance(result, list):
            return result

        return [result]

    except (json.JSONDecodeError, TypeError):

        return [str(value)]


def get_conversation_details(thread_id):

    with get_connection() as connection:

        thread = connection.execute(
            """
            SELECT
                thread_id,
                learner_id,
                thread_status,
                created_at
            FROM support_threads
            WHERE thread_id = ?
            """,
            (thread_id,)
        ).fetchone()

        if not thread:
            return None

        messages = connection.execute(
            """
            SELECT sender, message, message_order, created_at
            FROM support_messages
            WHERE thread_id = ?
            ORDER BY message_order
            """,
            (thread_id,)
        ).fetchall()

        summaries = connection.execute(
            """
            SELECT *
            FROM handover_summaries
            WHERE thread_id = ?
            ORDER BY version DESC
            """,
            (thread_id,)
        ).fetchall()

        feedback = connection.execute(
            """
            SELECT
                f.*,
                s.version
            FROM agent_feedback f
            JOIN handover_summaries s
                ON f.summary_id = s.summary_id
            WHERE s.thread_id = ?
            ORDER BY f.created_at DESC
            """,
            (thread_id,)
        ).fetchall()

    return {
        "thread": dict(thread),
        "messages": [dict(row) for row in messages],
        "summaries": [dict(row) for row in summaries],
        "feedback": [dict(row) for row in feedback]
    }


# ==================================================
# 2. CONVERSATION POPUP
# ==================================================

@st.dialog("Conversation Details", width="large")
def show_conversation_modal(thread_id):

    data = get_conversation_details(thread_id)

    if not data:

        st.error("Conversation not found.")
        return

    thread = data["thread"]
    messages = data["messages"]
    summaries = data["summaries"]
    feedback_records = data["feedback"]

    st.markdown(
        f"### 💬 Conversation — {thread_id}"
    )

    # ----------------------------------------------
    # MODAL CSS
    # ----------------------------------------------

    st.markdown("""
    <style>

    .modal-info-label {
        color: #64748B;
        font-size: 11px;
        font-weight: 650;
        text-transform: uppercase;
    }

    .modal-info-value {
        color: #172554;
        font-size: 14px;
        font-weight: 700;
        margin-top: 3px;
    }

    .message-bubble {
        padding: 12px 15px;
        border-radius: 12px;
        margin-bottom: 9px;
        font-size: 13px;
        line-height: 1.5;
        overflow-wrap: anywhere;
    }

    .learner-message {
        background: #EEF2FF;
        border: 1px solid #DCE4FA;
        margin-right: 35px;
    }

    .agent-message {
        background: #DCFCE7;
        border: 1px solid #BBF7D0;
        margin-left: 35px;
    }

    .message-sender {
        font-weight: 750;
        font-size: 12px;
        margin-bottom: 5px;
        color: #172554;
    }

    .summary-label {
        font-size: 12px;
        font-weight: 700;
        color: #64748B;
        margin-bottom: 4px;
    }

    .summary-value {
        font-size: 13px;
        color: #172554;
        line-height: 1.6;
    }

    </style>
    """, unsafe_allow_html=True)

    # ----------------------------------------------
    # DETAILS PANEL
    # ----------------------------------------------

    detail_col, content_col = st.columns([0.85, 2])

    with detail_col:

        with st.container(border=True):

            st.markdown("### 📋 Conversation Details")

            st.markdown(
                f"""
                <div class="modal-info-label">Learner ID</div>
                <div class="modal-info-value">
                    {html.escape(str(thread['learner_id']))}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write("")

            status = thread["thread_status"].capitalize()

            st.markdown(
                f"""
                <div class="modal-info-label">Status</div>
                <div class="modal-info-value">
                    {html.escape(status)}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write("")

            st.markdown(
                f"""
                <div class="modal-info-label">Created At</div>
                <div class="modal-info-value">
                    {html.escape(str(thread['created_at']))}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write("")

            st.markdown(
                f"""
                <div class="modal-info-label">Total Messages</div>
                <div class="modal-info-value">
                    {len(messages)}
                </div>
                """,
                unsafe_allow_html=True
            )

    # ----------------------------------------------
    # CONTENT TABS
    # ----------------------------------------------

    with content_col:

        conversation_tab, summary_tab, feedback_tab = st.tabs([
            "💬 Conversation",
            "📄 Handover Summary",
            "⭐ Agent Feedback"
        ])

        # ==========================================
        # CONVERSATION TAB
        # ==========================================

        with conversation_tab:

            st.markdown("#### Conversation Messages")

            if messages:

                for item in messages:

                    sender = item["sender"]

                    if sender == "learner":

                        sender_name = "👤 Learner"
                        css_class = "learner-message"

                    else:

                        sender_name = "🎧 Support Agent"
                        css_class = "agent-message"

                    safe_message = html.escape(
                        str(item["message"])
                    )

                    st.markdown(
                        f"""
                        <div class="message-bubble {css_class}">
                            <div class="message-sender">
                                {sender_name}
                            </div>
                            {safe_message}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            else:

                st.info("No messages available.")

        # ==========================================
        # HANDOVER SUMMARY TAB
        # ==========================================

        with summary_tab:

            st.markdown("#### AI Handover Summary")

            if summaries:

                selected_summary = summaries[0]

                st.caption(
                    f"Version {selected_summary['version']} | "
                    f"Provider: {selected_summary['provider'] or 'N/A'} | "
                    f"Model: {selected_summary['model'] or 'N/A'}"
                )

                with st.container(border=True):

                    st.markdown("**Main Issue**")

                    st.write(
                        selected_summary["issue"] or "Not available"
                    )

                    st.divider()

                    st.markdown("**Steps Tried**")

                    steps = parse_list(
                        selected_summary["steps_tried"]
                    )

                    if steps:

                        for step in steps:
                            st.write(f"• {step}")

                    else:

                        st.write("Not available")

                    st.divider()

                    st.markdown("**Current Status**")

                    st.write(
                        selected_summary["current_status"]
                        or "Not available"
                    )

                    st.divider()

                    st.markdown("**Unresolved Questions**")

                    questions = parse_list(
                        selected_summary["unresolved_questions"]
                    )

                    if questions:

                        for question in questions:
                            st.write(f"• {question}")

                    else:

                        st.write("None")

                    st.divider()

                    st.markdown("**Next Action**")

                    st.write(
                        selected_summary["next_action"]
                        or "Not available"
                    )

                    st.divider()

                    st.markdown("**Review Status**")

                    st.write(
                        selected_summary["review_status"].capitalize()
                    )

            else:

                st.info(
                    "No AI summary available for this conversation."
                )

        # ==========================================
        # AGENT FEEDBACK TAB
        # ==========================================

        with feedback_tab:

            st.markdown("#### Agent Feedback")

            if feedback_records:

                for item in feedback_records:

                    with st.container(border=True):

                        st.markdown(
                            f"**Reviewer:** {item['reviewer']}"
                        )

                        st.write(
                            f"Rating: {'⭐' * item['rating']}"
                        )

                        st.write(
                            f"Summary Version: {item['version']}"
                        )

                        st.markdown("**Feedback**")

                        st.write(
                            item["feedback_text"]
                            or "No written feedback."
                        )

                        if item["corrected_summary"]:

                            st.markdown("**Corrected Summary**")

                            st.write(
                                item["corrected_summary"]
                            )

                        st.caption(
                            f"Submitted: {item['created_at']}"
                        )

            else:

                st.info(
                    "No agent feedback available for this conversation."
                )


# ==================================================
# 3. MAIN PAGE
# ==================================================

def show():

    # ==============================================
    # PAGE CSS
    # ==============================================

    st.markdown(
        dedent("""
        <style>

        /* MAIN CONTENT SPACING */

        .main .block-container {
            padding-top: 0.20rem !important;
            padding-bottom: 0.35rem !important;
        }


        /* EQUAL DASHBOARD PANEL HEIGHT */

        .st-key-dashboard_summary_panel,
        .st-key-dashboard_status_panel,
        .st-key-dashboard_overview_panel {
            height: 340px !important;
            min-height: 340px !important;
            box-sizing: border-box !important;
        }

        .st-key-dashboard_summary_panel [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-dashboard_status_panel [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-dashboard_overview_panel [data-testid="stVerticalBlockBorderWrapper"] {
            height: 340px !important;
            min-height: 340px !important;
            box-sizing: border-box !important;
        }


        /* DASHBOARD HEADER */

        .dashboard-header {
            display: flex;
            align-items: center;
            gap: 11px;
            margin-bottom: 8px;
        }

        .dashboard-icon {
            width: 48px;
            height: 48px;
            border-radius: 13px;
            background: linear-gradient(135deg,#A855F7,#6366F1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 5px 15px rgba(99,102,241,0.22);
        }

        .dashboard-heading {
            font-size: 27px;
            font-weight: 800;
            color: #172554;
            line-height: 1.2;
        }

        .dashboard-subtitle {
            font-size: 12px;
            color: #64748B;
            margin-top: 3px;
        }


        /* PANEL HEADINGS */

        .panel-heading {
            font-size: 17px;
            font-weight: 750;
            color: #172554;
            margin-bottom: 10px;
        }


        /* PANEL CONTAINERS */

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255,255,255,0.80);
            border: 1px solid #DCE4FA;
            border-radius: 14px;
            box-shadow: 0 4px 14px rgba(50,60,120,0.05);
        }


        /* METRIC CARDS */

        div[data-testid="stMetric"] {
            background: linear-gradient(145deg,#FFFFFF,#F0F4FF);
            border: 1px solid #E0E7FF;
            border-radius: 12px;
            padding: 11px 12px;
            min-height: 83px;
        }

        div[data-testid="stMetricLabel"] {
            color: #526581 !important;
            font-size: 12px !important;
            font-weight: 650 !important;
        }

        div[data-testid="stMetricValue"] {
            color: #172554 !important;
            font-size: 25px !important;
            font-weight: 800 !important;
        }


        /* CHART SPACING */

        div[data-testid="stPlotlyChart"] {
            margin-top: -5px;
        }


        /* PENDING NOTE */

        .pending-note {
            color: #64748B;
            font-size: 12px;
            padding-top: 5px;
        }


        /* RECENT CONVERSATIONS */

        .recent-caption {
            color: #64748B;
            font-size: 12px;
            margin-top: -5px;
        }


        /* BUTTONS */

        div[data-testid="stButton"] button {
            border-radius: 9px;
            font-weight: 650;
        }

        </style>
        """),
        unsafe_allow_html=True
    )


    # ==============================================
    # DATABASE
    # ==============================================

    with get_connection() as connection:

        total_threads = connection.execute(
            "SELECT COUNT(*) FROM support_threads"
        ).fetchone()[0]

        status_data = connection.execute(
            """
            SELECT thread_status, COUNT(*) AS total
            FROM support_threads
            GROUP BY thread_status
            """
        ).fetchall()

        total_summaries = connection.execute(
            "SELECT COUNT(*) FROM handover_summaries"
        ).fetchone()[0]

        pending_reviews = connection.execute(
            """
            SELECT COUNT(*)
            FROM handover_summaries
            WHERE review_status = 'pending'
            """
        ).fetchone()[0]

        recent_threads = connection.execute(
            """
            SELECT
                t.thread_id,
                t.learner_id,
                t.thread_status,
                t.created_at,
                COUNT(m.message_id) AS total_messages
            FROM support_threads t
            LEFT JOIN support_messages m
                ON t.thread_id = m.thread_id
            GROUP BY t.thread_id
            ORDER BY t.created_at DESC, t.thread_id DESC
            LIMIT 5
            """
        ).fetchall()


    # ==============================================
    # STATUS COUNTS
    # ==============================================

    counts = {
        row["thread_status"]: row["total"]
        for row in status_data
    }

    open_threads = counts.get("open", 0)
    resolved_threads = counts.get("resolved", 0)
    closed_threads = counts.get("closed", 0)


    # ==============================================
    # HEADER
    # ==============================================

    st.markdown(
        """
        <div class="dashboard-header">
            <div class="dashboard-icon">📊</div>
            <div>
                <div class="dashboard-heading">
                    Dashboard Overview
                </div>
                <div class="dashboard-subtitle">
                    Monitor learner conversations, AI summaries and support activity.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    # ==============================================
    # MAIN THREE COLUMN LAYOUT
    # ==============================================

    left_column, center_column, right_column = st.columns(
        [1, 1, 1],
        gap="small"
    )


    # ==============================================
    # LEFT - CONVERSATION SUMMARY
    # ==============================================

    with left_column:

        with st.container(
            key="dashboard_summary_panel",
            border=True
        ):

            st.markdown(
                '<div class="panel-heading">📚 Conversation Summary</div>',
                unsafe_allow_html=True
            )

            row1_col1, row1_col2 = st.columns(2)

            with row1_col1:

                st.metric(
                    "📁 Total Conversations",
                    total_threads
                )

            with row1_col2:

                st.metric(
                    "🟠 Open Issues",
                    open_threads
                )

            row2_col1, row2_col2 = st.columns(2)

            with row2_col1:

                st.metric(
                    "✅ Resolved Issues",
                    resolved_threads
                )

            with row2_col2:

                st.metric(
                    "⚡ AI Summaries",
                    total_summaries
                )

            st.markdown(
                f"""
                <div class="pending-note">
                    📋 Pending Reviews:
                    <b>{pending_reviews}</b>
                </div>
                """,
                unsafe_allow_html=True
            )


    # ==============================================
    # CENTER - CONVERSATION STATUS
    # ==============================================

    with center_column:

        with st.container(
            key="dashboard_status_panel",
            border=True
        ):

            st.markdown(
                '<div class="panel-heading">🥧 Conversation Status</div>',
                unsafe_allow_html=True
            )

            chart_data = pd.DataFrame({
                "Status": ["Open", "Resolved", "Closed"],
                "Total": [
                    open_threads,
                    resolved_threads,
                    closed_threads
                ]
            })

            fig = px.pie(
                chart_data,
                names="Status",
                values="Total",
                hole=0.66,
                color="Status",
                color_discrete_map={
                    "Open": "#3B82F6",
                    "Resolved": "#10B981",
                    "Closed": "#F59E0B"
                }
            )

            fig.update_traces(
                textinfo="percent",
                textposition="inside",
                textfont=dict(
                    size=12,
                    color="white"
                ),
                hovertemplate=(
                    "%{label}<br>"
                    "Conversations: %{value}"
                    "<extra></extra>"
                )
            )

            fig.update_layout(
                height=270,
                margin=dict(t=5, b=5, l=5, r=5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(
                    orientation="h",
                    y=-0.08,
                    x=0.05,
                    font=dict(
                        size=10,
                        color="#172554"
                    )
                ),
                annotations=[
                    dict(
                        text=f"<b>{total_threads}</b><br>Total",
                        x=0.5,
                        y=0.5,
                        showarrow=False,
                        font=dict(
                            size=21,
                            color="#172554"
                        )
                    )
                ]
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False}
            )


    # ==============================================
    # RIGHT - SUPPORT OVERVIEW
    # ==============================================

    with right_column:

        with st.container(
            key="dashboard_overview_panel",
            border=True
        ):

            st.markdown(
                '<div class="panel-heading">📊 Support Overview</div>',
                unsafe_allow_html=True
            )

            overview = pd.DataFrame({
                "Category": ["Open", "Resolved", "Closed"],
                "Conversations": [
                    open_threads,
                    resolved_threads,
                    closed_threads
                ]
            })

            fig = px.bar(
                overview,
                x="Category",
                y="Conversations",
                text="Conversations",
                color="Category",
                color_discrete_map={
                    "Open": "#3B82F6",
                    "Resolved": "#10B981",
                    "Closed": "#F59E0B"
                }
            )

            fig.update_traces(
                textposition="outside",
                textfont=dict(
                    size=12,
                    color="#172554"
                )
            )

            fig.update_layout(
                height=270,
                margin=dict(t=20, b=20, l=10, r=10),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#64748B"),
                xaxis=dict(
                    title=None,
                    showgrid=False
                ),
                yaxis=dict(
                    title=None,
                    gridcolor="#E2E8F0",
                    rangemode="tozero"
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False}
            )


    # ==============================================
    # RECENT CONVERSATIONS
    # ==============================================

    with st.container(border=True):

        title_col, action_col = st.columns([3, 1])

        with title_col:

            st.markdown(
                "### 💬 Recent Conversations"
            )

            st.markdown(
                '<div class="recent-caption">'
                'Click a conversation to view its complete details.'
                '</div>',
                unsafe_allow_html=True
            )

        with action_col:

            st.button(
                "View All Conversations →",
                use_container_width=True,
                on_click=lambda: st.session_state.update({
                    "page_navigation": "Conversation History"
                })
            )


        # ------------------------------------------
        # TABLE HEADER
        # ------------------------------------------

        header_cols = st.columns(
            [1.5, 1.35, 1.1, 1.35, 0.7, 0.45]
        )

        headers = [
            "Thread ID",
            "Learner ID",
            "Status",
            "Created At",
            "Messages",
            "Action"
        ]

        for col, heading in zip(header_cols, headers):

            with col:

                st.markdown(f"**{heading}**")

        st.divider()


        # ------------------------------------------
        # CONVERSATION ROWS
        # ------------------------------------------

        if recent_threads:

            for row in recent_threads:

                thread_id = row["thread_id"]

                learner_id = row["learner_id"]

                status = row["thread_status"].capitalize()

                created_at = row["created_at"]

                total_messages = row["total_messages"]

                cols = st.columns(
                    [1.5, 1.35, 1.1, 1.35, 0.7, 0.45]
                )

                with cols[0]:

                    if st.button(
                        thread_id,
                        key=f"thread_{thread_id}",
                        use_container_width=True
                    ):

                        show_conversation_modal(thread_id)

                with cols[1]:

                    st.write(learner_id)

                with cols[2]:

                    if status == "Open":

                        st.markdown("🔵 Open")

                    elif status == "Resolved":

                        st.markdown("🟢 Resolved")

                    else:

                        st.markdown("🟠 Closed")

                with cols[3]:

                    st.caption(str(created_at))

                with cols[4]:

                    st.write(total_messages)

                with cols[5]:

                    if st.button(
                        "👁️",
                        key=f"view_{thread_id}",
                        help="View conversation",
                        use_container_width=True
                    ):

                        show_conversation_modal(thread_id)

                st.divider()

        else:

            st.info("No conversations available.")