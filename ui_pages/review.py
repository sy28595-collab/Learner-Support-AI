
import json
import streamlit as st

from database.db import get_connection
from database.summary_manager import save_summary
from database.audit_manager import log_action


# ==================================================
# 1. HELPER FUNCTIONS
# ==================================================

def parse_list(value):

    if not value:
        return []

    if isinstance(value, list):
        return value

    try:
        return json.loads(value)

    except (json.JSONDecodeError, TypeError):
        return []


def get_summaries(status=None):

    with get_connection() as connection:

        query = """
            SELECT
                s.*,
                t.learner_id,
                t.thread_status
            FROM handover_summaries s
            JOIN support_threads t
                ON s.thread_id = t.thread_id
        """

        params = []

        if status and status != "All":
            query += " WHERE s.review_status = ?"
            params.append(status.lower())

        query += """
            ORDER BY s.created_at DESC, s.summary_id DESC
        """

        rows = connection.execute(
            query, params
        ).fetchall()

    return [dict(row) for row in rows]


def get_summary(summary_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                hs.*,
                st.learner_id,
                st.thread_status
            FROM handover_summaries hs
            JOIN support_threads st
                ON hs.thread_id = st.thread_id
            WHERE hs.summary_id = ?
            """,
            (summary_id,)
        ).fetchone()

    return dict(row) if row else None


def get_versions(thread_id):

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                summary_id,
                version,
                provider,
                model,
                review_status,
                created_at
            FROM handover_summaries
            WHERE thread_id = ?
            ORDER BY version DESC
            """,
            (thread_id,)
        ).fetchall()

    return [dict(row) for row in rows]


def save_feedback(
    summary_id,
    rating,
    feedback_text,
    reviewer,
    corrected_summary
):

    with get_connection() as connection:

        connection.execute(
            """
            INSERT INTO agent_feedback
            (
                summary_id,
                rating,
                feedback_text,
                corrected_summary,
                reviewer
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                summary_id,
                rating,
                feedback_text,
                json.dumps(corrected_summary),
                reviewer
            )
        )


def update_review_status(
    summary_id,
    status,
    reviewer,
    feedback_text
):

    with get_connection() as connection:

        cursor = connection.execute(
            """
            UPDATE handover_summaries
            SET
                review_status = ?,
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                feedback = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE summary_id = ?
            """,
            (
                status,
                reviewer,
                feedback_text,
                summary_id
            )
        )

    return cursor.rowcount > 0


# ==================================================
# 2. MAIN PAGE
# ==================================================

def show():

    st.title("Handover Review")

    st.caption(
        "Review, correct and approve AI-generated learner support summaries."
    )

    st.divider()

    # ==================================================
    # 2.1 SAVE CONFIRMATION
    # ==================================================

    if "review_flash" in st.session_state:

        message = st.session_state.pop("review_flash")

        st.success(message)

        st.toast(
            "Review saved successfully!",
            icon="✅"
        )

    # ==================================================
    # 3. REVIEW STATISTICS
    # ==================================================

    with get_connection() as connection:

        total = connection.execute(
            "SELECT COUNT(*) FROM handover_summaries"
        ).fetchone()[0]

        pending = connection.execute(
            """
            SELECT COUNT(*)
            FROM handover_summaries
            WHERE review_status = 'pending'
            """
        ).fetchone()[0]

        approved = connection.execute(
            """
            SELECT COUNT(*)
            FROM handover_summaries
            WHERE review_status = 'approved'
            """
        ).fetchone()[0]

        rejected = connection.execute(
            """
            SELECT COUNT(*)
            FROM handover_summaries
            WHERE review_status = 'rejected'
            """
        ).fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Summaries", total)
    col2.metric("Pending Reviews", pending)
    col3.metric("Approved", approved)
    col4.metric("Rejected", rejected)

    st.divider()

    # ==================================================
    # 4. FILTER SUMMARIES
    # ==================================================

    st.subheader("Summary Management")

    filter_col, search_col = st.columns([1, 2])

    with filter_col:

        selected_status = st.selectbox(
            "Filter by Status",
            ["All", "Pending", "Approved", "Rejected"]
        )

    with search_col:

        search_query = st.text_input(
            "Search",
            placeholder="Search Thread ID or Learner ID..."
        )

    summaries = get_summaries(selected_status)

    if search_query.strip():

        query = search_query.strip().lower()

        summaries = [
            item for item in summaries
            if query in item["thread_id"].lower()
            or query in item["learner_id"].lower()
        ]

    if not summaries:

        st.info(
            "No summaries found for the selected filter."
        )

        return

    # ==================================================
    # 5. SELECT SUMMARY
    # ==================================================

    summary_options = {
        (
            f"Summary #{item['summary_id']} | "
            f"{item['thread_id']} | "
            f"Version {item['version']} | "
            f"{item['review_status'].title()}"
        ): item["summary_id"]
        for item in summaries
    }

    selected_label = st.selectbox(
        "Select Summary",
        list(summary_options.keys())
    )

    summary_id = summary_options[selected_label]

    summary = get_summary(summary_id)

    if not summary:

        st.error("Summary not found.")

        return

    st.divider()

    # ==================================================
    # 6. SUMMARY INFORMATION
    # ==================================================

    st.subheader("Summary Information")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Summary ID",
        summary["summary_id"]
    )

    col2.metric(
        "Version",
        summary["version"]
    )

    col3.metric(
        "Status",
        summary["review_status"].title()
    )

    st.write("**Thread ID:**", summary["thread_id"])

    st.write("**Learner ID:**", summary.get("learner_id", "Not available"))

    st.write("**Provider:**", summary["provider"])

    st.write(
        "**Model:**",
        summary["model"] or "Not available"
    )

    st.write("**Created At:**", summary["created_at"])

    if summary["reviewed_by"]:

        st.write(
            "**Last Reviewed By:**",
            summary["reviewed_by"]
        )

        st.write(
            "**Reviewed At:**",
            summary["reviewed_at"]
        )

    st.divider()

    # ==================================================
    # 7. SUMMARY VERSION HISTORY
    # ==================================================

    with st.expander("🕘 View Previous Versions"):

        versions = get_versions(summary["thread_id"])

        if versions:

            st.dataframe(
                versions,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No previous versions available.")

    # ==================================================
    # 8. SUMMARY EDITOR
    # ==================================================

    st.subheader("Review and Edit Summary")

    steps = parse_list(summary["steps_tried"])

    questions = parse_list(
        summary["unresolved_questions"]
    )

    with st.form("review_summary_form"):

        issue = st.text_area(
            "Main Issue",
            value=summary["issue"] or "",
            height=100
        )

        steps_text = st.text_area(
            "Steps Tried",
            value="\n".join(steps),
            height=120,
            help="Enter one step per line."
        )

        current_status = st.text_area(
            "Current Status",
            value=summary["current_status"] or "",
            height=100
        )

        questions_text = st.text_area(
            "Unresolved Questions",
            value="\n".join(questions),
            height=120,
            help="Enter one question per line."
        )

        next_action = st.text_area(
            "Recommended Next Action",
            value=summary["next_action"] or "",
            height=100
        )

        st.divider()

        # Agent Details

        reviewer = st.text_input(
            "Reviewer Name",
            value="Support Agent"
        )

        rating = st.slider(
            "AI Summary Rating",
            min_value=1,
            max_value=5,
            value=4
        )

        feedback_text = st.text_area(
            "Agent Feedback / Comments",
            placeholder="Write feedback or corrections..."
        )

        decision = st.radio(
            "Review Decision",
            ["Pending", "Approve", "Reject"],
            horizontal=True
        )

        submitted = st.form_submit_button(
            "💾 Save Review",
            type="primary",
            use_container_width=True
        )

    # ==================================================
    # 9. SAVE REVIEW
    # ==================================================

    if submitted:

        if not reviewer.strip():

            st.error("Please enter reviewer name.")

            return

        if not issue.strip() or not next_action.strip():

            st.error(
                "Main Issue and Next Action cannot be empty."
            )

            return

        corrected_summary = {

            "issue": issue.strip(),

            "steps_tried": [
                item.strip()
                for item in steps_text.splitlines()
                if item.strip()
            ],

            "current_status": current_status.strip(),

            "unresolved_questions": [
                item.strip()
                for item in questions_text.splitlines()
                if item.strip()
            ],

            "next_action": next_action.strip()
        }

        try:

            original_summary = {

                "issue": summary["issue"],

                "steps_tried": steps,

                "current_status": summary["current_status"],

                "unresolved_questions": questions,

                "next_action": summary["next_action"]
            }

            # Check whether content changed

            content_changed = (
                corrected_summary != original_summary
            )

            target_summary_id = summary_id

            new_version = None

            # Create new version if edited

            if content_changed:

                target_summary_id, new_version = save_summary(
                    thread_id=summary["thread_id"],
                    summary=corrected_summary,
                    provider=summary["provider"],
                    model=summary["model"],
                    prompt_version=summary["prompt_version"]
                )

            # Save agent feedback against the
            # summary version being reviewed

            save_feedback(
                summary_id=target_summary_id,
                rating=rating,
                feedback_text=feedback_text,
                reviewer=reviewer.strip(),
                corrected_summary=corrected_summary
            )

            # Update review decision

            status_map = {
                "Pending": "pending",
                "Approve": "approved",
                "Reject": "rejected"
            }

            final_status = status_map[decision]

            updated = update_review_status(
                summary_id=target_summary_id,
                status=final_status,
                reviewer=reviewer.strip(),
                feedback_text=feedback_text
            )

            if not updated:

                raise ValueError(
                    "Summary review status could not be updated."
                )

            # Save audit log

            log_action(
                action=f"summary_{final_status}",
                performed_by=reviewer.strip(),
                thread_id=summary["thread_id"],
                summary_id=target_summary_id,
                details=(
                    f"Review completed. Rating: {rating}/5. "
                    f"Content changed: {content_changed}."
                )
            )

            # Prepare success message

            success_message = (
                f"Review saved successfully! "
                f"Summary ID: {target_summary_id}. "
                f"Status: {final_status.title()}."
            )

            if content_changed:

                success_message += (
                    f" New version {new_version} created."
                )

            # Store confirmation before refresh

            st.session_state["review_flash"] = (
                success_message
            )

            # Refresh page

            st.rerun()

        except Exception as error:

            st.error("Unable to save review.")

            st.exception(error)