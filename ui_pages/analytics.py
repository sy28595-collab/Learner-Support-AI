import streamlit as st
import pandas as pd
import plotly.express as px

from database.db import get_connection


# ==================================================
# 1. ANALYTICS DATA
# ==================================================

def get_analytics_data():

    with get_connection() as connection:

        # KPI DATA
        total_threads = connection.execute(
            "SELECT COUNT(*) FROM support_threads"
        ).fetchone()[0]

        total_messages = connection.execute(
            "SELECT COUNT(*) FROM support_messages"
        ).fetchone()[0]

        total_summaries = connection.execute(
            "SELECT COUNT(*) FROM handover_summaries"
        ).fetchone()[0]

        pending_reviews = connection.execute(
            """
            SELECT COUNT(*)
            FROM handover_summaries
            WHERE LOWER(review_status) = 'pending'
            """
        ).fetchone()[0]

        # CONVERSATION STATUS
        status_data = pd.read_sql_query(
            """
            SELECT
                thread_status AS status,
                COUNT(*) AS total
            FROM support_threads
            GROUP BY thread_status
            """,
            connection
        )

        # MONTHLY CONVERSATION TREND
        monthly_data = pd.read_sql_query(
            """
            SELECT
                strftime('%Y-%m', created_at) AS month,
                COUNT(*) AS conversations
            FROM support_threads
            WHERE created_at IS NOT NULL
            GROUP BY month
            ORDER BY month
            """,
            connection
        )

        # SUMMARY REVIEW STATUS
        review_data = pd.read_sql_query(
            """
            SELECT
                review_status AS status,
                COUNT(*) AS total
            FROM handover_summaries
            GROUP BY review_status
            """,
            connection
        )

    return {
        "total_threads": total_threads,
        "total_messages": total_messages,
        "total_summaries": total_summaries,
        "pending_reviews": pending_reviews,
        "status_data": status_data,
        "monthly_data": monthly_data,
        "review_data": review_data
    }


# ==================================================
# 2. PAGE CSS
# ==================================================

def load_analytics_css():

    st.markdown("""
    <style>

    /* ANALYTICS PAGE SPACING */

    

    /* PAGE HEADER */

    .analytics-title {
        font-size: 25px;
        font-weight: 750;
        color: #172554;
        margin-bottom: 1px;
    }

    .analytics-subtitle {
        font-size: 12px;
        color: #64748b;
        margin-bottom: 8px;
    }

    /* KPI CARDS */

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 10px 13px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        min-height: 82px;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 12px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 25px;
        color: #172554;
        font-weight: 700;
    }

    /* CHART HEADINGS */

    .chart-heading {
        font-size: 14px;
        font-weight: 700;
        color: #172554;
        margin-bottom: 3px;
    }

    /* REDUCE EMPTY SPACE */

    div[data-testid="stVerticalBlock"] {
        gap: 0.55rem;
    }

    hr {
        margin-top: 5px !important;
        margin-bottom: 5px !important;
    }

    </style>
    """, unsafe_allow_html=True)


# ==================================================
# 3. MAIN PAGE
# ==================================================

def show():

    load_analytics_css()

    try:

        data = get_analytics_data()

    except Exception as error:

        st.error(f"Unable to load analytics: {error}")
        return

    # ----------------------------------------------
    # HEADER
    # ----------------------------------------------

    header_col, refresh_col = st.columns([5, 1])

    with header_col:

        st.markdown(
            '<div class="analytics-title">'
            'Analytics Dashboard'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="analytics-subtitle">'
            'Monitor conversations, AI summaries and support operations.'
            '</div>',
            unsafe_allow_html=True
        )

    with refresh_col:

        if st.button(
            "🔄 Refresh",
            use_container_width=True
        ):
            st.rerun()

    # ----------------------------------------------
    # KPI CARDS
    # ----------------------------------------------

    metric_columns = st.columns(4, gap="small")

    metrics = [
        ("📁 Total Conversations", data["total_threads"]),
        ("💬 Total Messages", data["total_messages"]),
        ("🤖 AI Summaries", data["total_summaries"]),
        ("⏳ Pending Reviews", data["pending_reviews"])
    ]

    for column, metric in zip(metric_columns, metrics):

        label, value = metric

        with column:

            st.metric(
                label=label,
                value=f"{value:,}"
            )

    # ----------------------------------------------
    # CHART CONFIGURATION
    # ----------------------------------------------

    chart_config = {
        "displayModeBar": False,
        "responsive": True
    }

    chart_height = 340

    # ----------------------------------------------
    # THREE CHARTS IN ONE ROW
    # ----------------------------------------------

    left_chart, center_chart, right_chart = st.columns(
        [1, 1, 1],
        gap="small"
    )

    # ==============================================
    # LEFT CHART - CONVERSATION STATUS
    # ==============================================

    with left_chart:

        st.markdown(
            '<div class="chart-heading">'
            '📊 Conversation Status'
            '</div>',
            unsafe_allow_html=True
        )

        status_data = data["status_data"]

        if not status_data.empty:

            fig_status = px.pie(
                status_data,
                names="status",
                values="total",
                hole=0.58
            )

            fig_status.update_layout(
                height=chart_height,
                margin=dict(l=5, r=5, t=20, b=5),
                legend=dict(
                    orientation="h",
                    y=-0.12,
                    font=dict(size=10)
                ),
                font=dict(size=11)
            )

            fig_status.update_traces(
                textposition="inside",
                textinfo="percent+label"
            )

            st.plotly_chart(
                fig_status,
                use_container_width=True,
                config=chart_config
            )

        else:

            st.info("No conversation data available.")

    # ==============================================
    # CENTER CHART - MONTHLY TREND
    # ==============================================

    with center_chart:

        st.markdown(
            '<div class="chart-heading">'
            '📈 Monthly Conversation Trend'
            '</div>',
            unsafe_allow_html=True
        )

        monthly_data = data["monthly_data"].copy()

        if not monthly_data.empty:

            monthly_data["month"] = pd.to_datetime(
                monthly_data["month"],
                format="%Y-%m",
                errors="coerce"
            )

            monthly_data = monthly_data.dropna(
                subset=["month"]
            )

            if not monthly_data.empty:

                fig_monthly = px.line(
                    monthly_data,
                    x="month",
                    y="conversations",
                    markers=True
                )

                fig_monthly.update_layout(
                    height=chart_height,
                    margin=dict(l=5, r=5, t=20, b=5),
                    xaxis_title="Month",
                    yaxis_title="Conversations",
                    font=dict(size=10)
                )

                fig_monthly.update_traces(
                    line=dict(width=3),
                    marker=dict(size=7)
                )

                st.plotly_chart(
                    fig_monthly,
                    use_container_width=True,
                    config=chart_config
                )

            else:

                st.info("No valid monthly data available.")

        else:

            st.info("No monthly data available.")

    # ==============================================
    # RIGHT CHART - SUMMARY REVIEW STATUS
    # ==============================================

    with right_chart:

        st.markdown(
            '<div class="chart-heading">'
            '✅ AI Summary Review Status'
            '</div>',
            unsafe_allow_html=True
        )

        review_data = data["review_data"]

        if not review_data.empty:

            fig_review = px.bar(
                review_data,
                x="status",
                y="total",
                text="total"
            )

            fig_review.update_layout(
                height=chart_height,
                margin=dict(l=5, r=5, t=20, b=5),
                xaxis_title="Review Status",
                yaxis_title="Summaries",
                font=dict(size=10)
            )

            fig_review.update_traces(
                textposition="outside"
            )

            st.plotly_chart(
                fig_review,
                use_container_width=True,
                config=chart_config
            )

        else:

            st.info("No review data available.")

    # ----------------------------------------------
    # FOOTER
    # ----------------------------------------------

    st.caption(
        "Analytics Dashboard | Live SQLite Database Data"
    )