import streamlit as st
import pandas as pd
import json
import io
import zipfile

from datetime import datetime
from database.db import get_connection


# ==================================================
# 1. DATABASE TABLES
# ==================================================

TABLES = [
    "learners",
    "support_threads",
    "support_messages",
    "issue_tags",
    "handover_summaries",
    "agent_feedback",
    "audit_logs"
]


# ==================================================
# 2. FETCH TABLE DATA
# ==================================================

def get_table_data(table_name):

    if table_name not in TABLES:
        raise ValueError("Invalid table name")

    with get_connection() as connection:

        rows = connection.execute(
            f'SELECT * FROM "{table_name}"'
        ).fetchall()

    return [dict(row) for row in rows]


# ==================================================
# 3. FETCH EXPORT DATA
# ==================================================

def get_export_data(category, status="All"):

    if category == "Conversations":

        threads = get_table_data("support_threads")

        if status != "All":

            threads = [
                row for row in threads
                if str(row.get("thread_status", "")).lower()
                == status.lower()
            ]

        thread_ids = {
            row.get("thread_id") for row in threads
        }

        messages = get_table_data("support_messages")

        messages = [
            row for row in messages
            if row.get("thread_id") in thread_ids
        ]

        return {
            "support_threads": threads,
            "support_messages": messages
        }

    elif category == "AI Summaries":

        summaries = get_table_data("handover_summaries")

        threads = get_table_data("support_threads")

        learner_map = {
            row["thread_id"]: row.get("learner_id")
            for row in threads
        }

        for row in summaries:

            row["learner_id"] = learner_map.get(
                row.get("thread_id")
            )

        return {
            "handover_summaries": summaries
        }

    elif category == "Agent Feedback":

        return {
            "agent_feedback": get_table_data("agent_feedback")
        }

    elif category == "Audit Logs":

        return {
            "audit_logs": get_table_data("audit_logs")
        }

    elif category == "Complete Dataset":

        return {
            table: get_table_data(table)
            for table in TABLES
        }

    return {}


# ==================================================
# 4. CONVERT DATA TO JSON
# ==================================================

def create_json(data):

    return json.dumps(
        data,
        indent=4,
        ensure_ascii=False,
        default=str
    ).encode("utf-8")


# ==================================================
# 5. CONVERT DATA TO CSV
# ==================================================

def create_csv(data):

    frames = []

    for table_name, records in data.items():

        if not records:
            continue

        dataframe = pd.DataFrame(records)

        dataframe.insert(
            0,
            "source_table",
            table_name
        )

        frames.append(dataframe)

    if not frames:
        return b""

    combined = pd.concat(
        frames,
        ignore_index=True,
        sort=False
    )

    return combined.to_csv(
        index=False
    ).encode("utf-8-sig")


# ==================================================
# 6. CREATE COMPLETE DATASET ZIP
# ==================================================

def create_zip(data):

    output = io.BytesIO()

    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED
    ) as archive:

        for table_name, records in data.items():

            dataframe = pd.DataFrame(records)

            csv_data = dataframe.to_csv(
                index=False
            ).encode("utf-8-sig")

            archive.writestr(
                f"{table_name}.csv",
                csv_data
            )

    output.seek(0)

    return output.getvalue()


# ==================================================
# 7. DATABASE STATISTICS
# ==================================================

def get_statistics():

    with get_connection() as connection:

        statistics = {}

        for table in TABLES:

            exists = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = ?
                """,
                (table,)
            ).fetchone()

            if exists:

                count = connection.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                ).fetchone()[0]

                statistics[table] = count

            else:

                statistics[table] = 0

    return statistics


# ==================================================
# 8. PAGE CSS
# ==================================================

def load_export_css():

    st.markdown("""
    <style>

    .export-title {
        font-size: 26px;
        font-weight: 750;
        color: #172554;
        margin-bottom: 2px;
    }

    .export-subtitle {
        color: #64748b;
        font-size: 12px;
        margin-bottom: 12px;
    }

    .export-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 11px;
        padding: 13px;
        min-height: 82px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }

    .export-label {
        font-size: 12px;
        color: #64748b;
    }

    .export-value {
        font-size: 24px;
        font-weight: 700;
        color: #172554;
        margin-top: 4px;
    }

    .section-title {
        font-size: 16px;
        font-weight: 700;
        color: #172554;
        margin-bottom: 8px;
    }

    </style>
    """, unsafe_allow_html=True)


# ==================================================
# 9. MAIN EXPORT PAGE
# ==================================================

def show():

    load_export_css()

    # ----------------------------------------------
    # HEADER
    # ----------------------------------------------

    header_col, refresh_col = st.columns([5, 1])

    with header_col:

        st.markdown(
            '<div class="export-title">'
            '📤 Data Export Center'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="export-subtitle">'
            'Export, preview and download your support data.'
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
    # STATISTICS
    # ----------------------------------------------

    stats = get_statistics()

    total_records = sum(stats.values())

    metrics = [
        ("Total Database Records", total_records),
        ("Conversations", stats["support_threads"]),
        ("AI Summaries", stats["handover_summaries"])
    ]

    columns = st.columns(3)

    for column, metric in zip(columns, metrics):

        label, value = metric

        with column:

            st.markdown(
                f"""
                <div class="export-card">
                    <div class="export-label">
                        {label}
                    </div>
                    <div class="export-value">
                        {value:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.write("")

    # ----------------------------------------------
    # EXPORT CONFIGURATION
    # ----------------------------------------------

    st.markdown(
        '<div class="section-title">'
        '⚙️ Export Configuration'
        '</div>',
        unsafe_allow_html=True
    )

    config_col1, config_col2, config_col3 = st.columns(
        [2, 1, 1.5]
    )

    with config_col1:

        category = st.selectbox(
            "Select Data",
            [
                "Conversations",
                "AI Summaries",
                "Agent Feedback",
                "Audit Logs",
                "Complete Dataset"
            ]
        )

    with config_col2:

        file_format = st.selectbox(
            "Export Format",
            ["CSV", "JSON"]
        )

    with config_col3:

        if category == "Conversations":

            status = st.selectbox(
                "Conversation Status",
                ["All", "Open", "Resolved", "Closed"]
            )

        else:

            status = "All"

            st.selectbox(
                "Conversation Status",
                ["Not Applicable"],
                disabled=True
            )

    # ----------------------------------------------
    # GENERATE EXPORT
    # ----------------------------------------------

    generate_col, info_col = st.columns([1, 3])

    with generate_col:

        generate = st.button(
            "📥 Generate Export",
            type="primary",
            use_container_width=True
        )

    with info_col:

        st.caption(
            "Complete Dataset includes all 7 database tables."
        )

    # ----------------------------------------------
    # GENERATE AND STORE EXPORT
    # ----------------------------------------------

    if generate:

        try:

            with st.spinner("Preparing your export..."):

                export_data = get_export_data(
                    category,
                    status
                )

                total_exported = sum(
                    len(records)
                    for records in export_data.values()
                )

                timestamp = datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )

                if category == "Complete Dataset":

                    if file_format == "CSV":

                        file_bytes = create_zip(export_data)

                        file_name = (
                            f"complete_dataset_{timestamp}.zip"
                        )

                        mime_type = "application/zip"

                    else:

                        file_bytes = create_json(export_data)

                        file_name = (
                            f"complete_dataset_{timestamp}.json"
                        )

                        mime_type = "application/json"

                else:

                    if file_format == "CSV":

                        file_bytes = create_csv(export_data)

                        file_name = (
                            f"{category.lower().replace(' ', '_')}"
                            f"_{timestamp}.csv"
                        )

                        mime_type = "text/csv"

                    else:

                        file_bytes = create_json(export_data)

                        file_name = (
                            f"{category.lower().replace(' ', '_')}"
                            f"_{timestamp}.json"
                        )

                        mime_type = "application/json"

                st.session_state["export_result"] = {
                    "data": export_data,
                    "file_bytes": file_bytes,
                    "file_name": file_name,
                    "mime_type": mime_type,
                    "total": total_exported,
                    "format": file_format,
                    "category": category
                }

        except Exception as error:

            st.error(f"Export failed: {error}")

    # ----------------------------------------------
    # EXPORT PREVIEW AND DOWNLOAD
    # ----------------------------------------------

    result = st.session_state.get("export_result")

    if result:

        st.divider()

        st.markdown(
            '<div class="section-title">'
            '📋 Export Preview & Download'
            '</div>',
            unsafe_allow_html=True
        )

        preview_col, download_col = st.columns(
            [1.6, 1],
            gap="medium"
        )

        # PREVIEW
        with preview_col:

            st.markdown("**Export Data Preview**")

            preview_data = result["data"]

            table_options = list(preview_data.keys())

            selected_table = st.selectbox(
                "Preview Table",
                table_options
            )

            preview_records = preview_data[selected_table]

            if preview_records:

                preview_df = pd.DataFrame(
                    preview_records
                )

                st.dataframe(
                    preview_df.head(8),
                    use_container_width=True,
                    hide_index=True,
                    height=235
                )

                st.caption(
                    f"Showing up to 8 of "
                    f"{len(preview_records)} records."
                )

            else:

                st.info("No records available in this table.")

        # DOWNLOAD
        with download_col:

            with st.container(border=True):

                st.markdown("### 📥 Download")

                st.success("Export generated successfully!")

                st.write(
                    f"**File:** {result['file_name']}"
                )

                st.write(
                    f"**Category:** {result['category']}"
                )

                st.write(
                    f"**Format:** {result['format']}"
                )

                st.write(
                    f"**Records:** {result['total']:,}"
                )

                st.write("")

                st.download_button(
                    label="⬇️ Download File",
                    data=result["file_bytes"],
                    file_name=result["file_name"],
                    mime=result["mime_type"],
                    type="primary",
                    use_container_width=True
                )

                st.caption(
                    "Your file will be saved to your computer."
                )

    else:

        st.divider()

        st.info(
            "Select your data and format, then click "
            "'Generate Export' to preview and download."
        )

    # ----------------------------------------------
    # FOOTER
    # ----------------------------------------------

    st.divider()

    st.caption(
        "Data Export Center | SQLite Database | CSV & JSON"
    )