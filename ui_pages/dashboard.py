import streamlit as st
import pandas as pd
import plotly.express as px
from textwrap import dedent

from database.db import get_connection


def show():

    # ==========================================
    # DASHBOARD CSS
    # ==========================================

    st.markdown(
        dedent("""
        <style>

        /* Compact page spacing */

        .main .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
        }

        /* Dashboard heading */

        .dashboard-header {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 14px;
        }

        .dashboard-icon {
            width: 52px;
            height: 52px;
            border-radius: 14px;
            background: linear-gradient(135deg,#A855F7,#6366F1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 25px;
            box-shadow: 0 5px 15px rgba(99,102,241,0.25);
        }

        .dashboard-heading {
            font-size: 27px;
            font-weight: 800;
            color: #172554;
            line-height: 1.2;
        }

        .dashboard-subtitle {
            font-size: 13px;
            color: #64748B;
            margin-top: 4px;
        }

        /* Metric cards */

        div[data-testid="stMetric"] {
            background: linear-gradient(145deg,#FFFFFF,#F0F4FF);
            border: 1px solid #DCE4FA;
            border-radius: 13px;
            padding: 10px 12px;
            min-height: 75px;
            box-shadow: 0 4px 12px rgba(50,60,120,0.06);
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

        /* Chart containers */

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255,255,255,0.82);
            border: 1px solid #DCE4FA;
            border-radius: 15px;
            box-shadow: 0 5px 16px rgba(50,60,120,0.06);
        }

        /* Section headings */

        .chart-heading {
            font-size: 18px;
            font-weight: 750;
            color: #172554;
            margin-bottom: 4px;
        }

        /* Reduce chart spacing */

        div[data-testid="stPlotlyChart"] {
            margin-top: -5px;
        }

        </style>
        """),
        unsafe_allow_html=True
    )

    # ==========================================
    # DATABASE
    # ==========================================

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
            ORDER BY t.created_at DESC
            LIMIT 5
            """
        ).fetchall()

    # ==========================================
    # STATUS COUNTS
    # ==========================================

    counts = {
        row["thread_status"]: row["total"]
        for row in status_data
    }

    open_threads = counts.get("open", 0)
    resolved_threads = counts.get("resolved", 0)
    closed_threads = counts.get("closed", 0)

    # ==========================================
    # HEADER
    # ==========================================

    st.markdown(
        dedent("""
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
        """),
        unsafe_allow_html=True
    )

    # ==========================================
    # MAIN THREE COLUMN LAYOUT
    # ==========================================

    left_column, center_column, right_column = st.columns(
        [0.95, 1.15, 1.15],
        gap="small"
    )

    # ==========================================
    # LEFT - KPI CARDS
    # ==========================================

    with left_column:

        with st.container(border=True):
            st.markdown("💬 **Total Conversations**")
            st.metric(
                label="Total",
                value=total_threads,
                label_visibility="collapsed"
            )

        with st.container(border=True):
            st.markdown("🔵 **Open Issues**")
            st.metric(
                label="Open",
                value=open_threads,
                label_visibility="collapsed"
            )

        with st.container(border=True):
            st.markdown("✅ **Resolved Issues**")
            st.metric(
                label="Resolved",
                value=resolved_threads,
                label_visibility="collapsed"
            )

        with st.container(border=True):
            st.markdown("📚 **AI Summaries**")
            st.metric(
                label="Summaries",
                value=total_summaries,
                label_visibility="collapsed"
            )

        with st.container(border=True):
            st.markdown("📋 **Pending Reviews**")
            st.metric(
                label="Pending",
                value=pending_reviews,
                label_visibility="collapsed"
            )

    # ==========================================
    # CENTER - DONUT CHART
    # ==========================================

    with center_column:

        with st.container(border=True):

            st.markdown(
                '<div class="chart-heading">🥧 Conversation Status</div>',
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
                height=310,
                margin=dict(t=12, b=12, l=5, r=5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(
                    orientation="h",
                    y=-0.08,
                    x=0.05,
                    font=dict(size=10, color="#172554")
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

    # ==========================================
    # RIGHT - BAR CHART
    # ==========================================

    with right_column:

        with st.container(border=True):

            st.markdown(
                '<div class="chart-heading">📊 Support Overview</div>',
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
                height=310,
                margin=dict(t=25, b=25, l=10, r=10),
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

    # ==========================================
    # RECENT CONVERSATIONS
    # ==========================================

    st.markdown("")

    with st.container(border=True):

        st.markdown("### 📋 Recent Conversations")

        recent_df = pd.DataFrame(
            [dict(row) for row in recent_threads]
        )

        if not recent_df.empty:

            recent_df.columns = [
                "Thread ID",
                "Learner ID",
                "Status",
                "Created At",
                "Messages"
            ]

            st.dataframe(
                recent_df,
                use_container_width=True,
                hide_index=True,
                height=190
            )

        else:
            st.info("No conversations available.")