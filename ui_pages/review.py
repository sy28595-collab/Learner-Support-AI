import json
import textwrap
import streamlit as st

from database.db import get_connection
from database.summary_manager import save_summary
from database.audit_manager import log_action


# ==========================================================
# 1. HELPER FUNCTIONS
# ==========================================================

def parse_list(value):

    if not value:
        return []

    if isinstance(value, list):
        return value

    try:
        result = json.loads(value)

        if isinstance(result, list):
            return result

        return []

    except (json.JSONDecodeError, TypeError):
        return []


# ==========================================================
# 2. FETCH SUMMARIES
# ==========================================================

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
            query,
            params
        ).fetchall()

    return [dict(row) for row in rows]


# ==========================================================
# 3. FETCH SINGLE SUMMARY
# ==========================================================

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


# ==========================================================
# 4. FETCH VERSION HISTORY
# ==========================================================

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


def delete_summary(summary_id, performed_by="Support Agent"):
    """Delete one summary version and preserve its audit history."""
    with get_connection() as connection:
        record = connection.execute(
            """
            SELECT summary_id, thread_id, version
            FROM handover_summaries
            WHERE summary_id = ?
            """,
            (summary_id,)
        ).fetchone()

        if record is None:
            return False, None

        thread_id = record["thread_id"]
        version = record["version"]

        connection.execute(
            "DELETE FROM agent_feedback WHERE summary_id = ?",
            (summary_id,)
        )
        connection.execute(
            "UPDATE audit_logs SET summary_id = NULL WHERE summary_id = ?",
            (summary_id,)
        )
        connection.execute(
            "DELETE FROM handover_summaries WHERE summary_id = ?",
            (summary_id,)
        )

    log_action(
        action="summary_deleted",
        performed_by=performed_by,
        thread_id=thread_id,
        summary_id=None,
        details=f"Deleted summary version {version} (summary ID {summary_id})."
    )
    return True, thread_id


# ==========================================================
# 5. SAVE FEEDBACK
# ==========================================================

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


# ==========================================================
# 6. UPDATE REVIEW STATUS
# ==========================================================

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


# ==========================================================
# 7. PAGE CSS
# ==========================================================

def load_review_css():

    st.markdown(
        textwrap.dedent("""
        <style>

        /* MAIN PAGE */

        .main .block-container {
            padding-top: 0.65rem !important;
            padding-bottom: 1rem !important;
        }


        /* PAGE HEADER */

        .review-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 5px;
        }

        .review-icon {
            width: 44px;
            height: 44px;
            min-width: 44px;
            border-radius: 12px;

            background: linear-gradient(
                135deg,
                #6366F1,
                #7C3AED
            );

            display: flex;
            align-items: center;
            justify-content: center;

            font-size: 22px;

            box-shadow:
                0 4px 12px rgba(99,102,241,0.20);
        }

        .review-title {
            font-size: 27px;
            font-weight: 800;
            color: #172554;
            line-height: 1.2;
        }

        .review-subtitle {
            color: #64748B;
            font-size: 12px;
            margin-top: 4px;
        }


        /* SECTION HEADINGS */

        .section-title {
            font-size: 17px;
            font-weight: 750;
            color: #172554;
            margin-bottom: 4px;
        }

        .section-caption {
            font-size: 11px;
            color: #64748B;
            margin-bottom: 12px;
        }


        /* PANEL CARDS */

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #DCE4F2;
            border-radius: 13px;
            background: rgba(255,255,255,0.55);
        }


        /* METRIC CARDS */

        div[data-testid="stMetric"] {
            background: linear-gradient(
                135deg,
                #FFFFFF,
                #F5F7FF
            );

            border: 1px solid #E0E7FF;
            border-radius: 12px;
            padding: 12px 14px;
            min-height: 88px;

            box-shadow:
                0 3px 10px rgba(30,64,175,0.04);
        }

        div[data-testid="stMetricLabel"] {
            font-size: 11px;
            color: #64748B;
        }

        div[data-testid="stMetricValue"] {
            font-size: 25px;
            font-weight: 800;
            color: #1E3A8A;
        }


        /* BUTTONS */

        .stButton button,
        .stFormSubmitButton button {
            border-radius: 9px;
            font-weight: 650;
            min-height: 38px;
            transition: all 0.2s ease;
        }

        .stButton button:hover,
        .stFormSubmitButton button:hover {
            transform: translateY(-1px);

            box-shadow:
                0 4px 10px rgba(37,99,235,0.12);
        }


        /* INPUTS */

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div {
            border-radius: 8px;
        }


        /* FORM */

        div[data-testid="stForm"] {
            border: none;
            padding: 0;
        }


        /* STATUS BADGES */

        .status-pending {
            display: inline-block;
            color: #B45309;
            background: #FEF3C7;
            padding: 5px 9px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
        }

        .status-approved {
            display: inline-block;
            color: #047857;
            background: #D1FAE5;
            padding: 5px 9px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
        }

        .status-rejected {
            display: inline-block;
            color: #B91C1C;
            background: #FEE2E2;
            padding: 5px 9px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
        }


        /* DIVIDERS */

        hr {
            margin-top: 12px;
            margin-bottom: 12px;
            border-color: #E2E8F0;
        }


        /* RESPONSIVE */

        @media (max-width: 900px) {

            .review-title {
                font-size: 22px;
            }

        }


        @media (prefers-reduced-motion: reduce) {

            *,
            *::before,
            *::after {
                animation-duration: 0.01ms !important;
                transition-duration: 0.01ms !important;
            }

        }

        </style>
        """),
        unsafe_allow_html=True
    )


# ==========================================================
# 8. STATUS BADGE
# ==========================================================

def status_badge(status):

    status = (status or "pending").lower()

    if status == "approved":

        return """
        <span class="status-approved">
            ● Approved
        </span>
        """

    elif status == "rejected":

        return """
        <span class="status-rejected">
            ● Rejected
        </span>
        """

    return """
    <span class="status-pending">
        ● Pending
    </span>
    """


# ==========================================================
# 9. REVIEW STATISTICS
# ==========================================================

def get_review_statistics():

    with get_connection() as connection:

        total = connection.execute(
            """
            SELECT COUNT(*)
            FROM handover_summaries
            """
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

    return total, pending, approved, rejected


# ==========================================================
# 10. SUMMARY INFORMATION
# ==========================================================

def display_summary_information(summary):

    st.markdown(
        '<div class="section-title">📋 Summary Information</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        textwrap.dedent("""
        <div class="section-caption">
            Details of the selected AI summary.
        </div>
        """),
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Summary ID",
            summary["summary_id"]
        )

    with col2:

        st.metric(
            "Version",
            summary["version"]
        )

    st.markdown(
        f"**Thread ID:** `{summary['thread_id']}`"
    )

    st.markdown(
        f"**Learner ID:** `{summary.get('learner_id', 'Not available')}`"
    )

    st.markdown(
        f"**Conversation Status:** {summary.get('thread_status', 'Not available')}"
    )

    st.markdown(
        f"**Provider:** {summary.get('provider', 'Not available')}"
    )

    st.markdown(
        f"**Model:** {summary.get('model') or 'Not available'}"
    )

    st.markdown(
        f"**Created At:** {summary.get('created_at', 'Not available')}"
    )

    st.markdown("**Review Status:**")

    st.markdown(
        status_badge(summary.get("review_status")),
        unsafe_allow_html=True
    )

    if summary.get("reviewed_by"):

        st.divider()

        st.markdown(
            f"**Last Reviewed By:** {summary['reviewed_by']}"
        )

        st.markdown(
            f"**Reviewed At:** {summary.get('reviewed_at', 'Not available')}"
        )

    if summary.get("feedback"):

        st.divider()

        st.markdown("**Previous Feedback**")

        st.info(summary["feedback"])


# ==========================================================
# 11. VERSION HISTORY
# ==========================================================

def display_version_history(summary):

    st.markdown(
        '<div class="section-title">🕘 Version History</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        textwrap.dedent("""
        <div class="section-caption">
            Open an earlier version or delete an unwanted version.
        </div>
        """),
        unsafe_allow_html=True
    )

    versions = get_versions(summary["thread_id"])

    if not versions:
        st.info("No previous versions available.")
        return

    for version in versions:
        version_id = version["summary_id"]
        is_current = version_id == summary["summary_id"]
        confirm_id = st.session_state.get("confirm_delete_summary_id")

        with st.container(border=True):
            top_col, badge_col = st.columns([1.15, 0.85])

            with top_col:
                st.markdown(f"**Version {version['version']}**")
                st.caption(f"Summary #{version_id}")

            with badge_col:
                st.markdown(
                    status_badge(version["review_status"]),
                    unsafe_allow_html=True
                )

            st.caption(f"Provider: {version.get('provider') or 'Not available'}")
            st.caption(f"Created: {version.get('created_at') or 'Not available'}")

            if is_current:
                st.success("Currently selected")

            action_open, action_delete = st.columns([1.35, 0.85])

            with action_open:
                if st.button(
                    "Open Version" if not is_current else "Selected",
                    key=f"open_version_{version_id}",
                    width="stretch",
                    disabled=is_current
                ):
                    # A fresh widget key prevents the old selectbox value
                    # from overwriting the selected historical version.
                    st.session_state["selected_review_summary"] = version_id
                    st.session_state["review_status_value"] = "All"
                    st.session_state["review_selector_revision"] = (
                        st.session_state.get("review_selector_revision", 0) + 1
                    )
                    st.rerun()

            with action_delete:
                if st.button(
                    "🗑 Delete",
                    key=f"delete_version_{version_id}",
                    width="stretch"
                ):
                    st.session_state["confirm_delete_summary_id"] = version_id
                    st.rerun()

            if confirm_id == version_id:
                st.warning(
                    f"Delete Version {version['version']} permanently? "
                    "Its agent feedback will also be deleted."
                )
                confirm_col, cancel_col = st.columns(2)

                with confirm_col:
                    if st.button(
                        "Confirm Delete",
                        key=f"confirm_delete_{version_id}",
                        type="primary",
                        width="stretch"
                    ):
                        try:
                            deleted, deleted_thread_id = delete_summary(
                                version_id,
                                performed_by="Support Agent"
                            )
                            st.session_state.pop("confirm_delete_summary_id", None)

                            if deleted:
                                remaining = get_versions(deleted_thread_id)
                                if st.session_state.get("selected_review_summary") == version_id:
                                    if remaining:
                                        st.session_state["selected_review_summary"] = remaining[0]["summary_id"]
                                    else:
                                        st.session_state.pop("selected_review_summary", None)

                                st.session_state["review_status_value"] = "All"
                                st.session_state["review_selector_revision"] = (
                                    st.session_state.get("review_selector_revision", 0) + 1
                                )
                                st.session_state["review_flash"] = (
                                    f"Summary version {version['version']} deleted successfully."
                                )
                                st.session_state["review_flash_type"] = "delete"
                            else:
                                st.session_state["review_flash"] = "This summary was already deleted."
                                st.session_state["review_flash_type"] = "warning"
                            st.rerun()
                        except Exception as error:
                            st.error("Could not delete this summary version.")
                            st.exception(error)

                with cancel_col:
                    if st.button(
                        "Cancel",
                        key=f"cancel_delete_{version_id}",
                        width="stretch"
                    ):
                        st.session_state.pop("confirm_delete_summary_id", None)
                        st.rerun()


# ==========================================================
# 12. SUMMARY EDITOR
# ==========================================================

def display_summary_editor(summary):

    st.markdown(
        '<div class="section-title">✏️ Review & Edit Summary</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        textwrap.dedent("""
        <div class="section-caption">
            Edit AI-generated content and complete the review.
        </div>
        """),
        unsafe_allow_html=True
    )

    steps = parse_list(
        summary.get("steps_tried")
    )

    questions = parse_list(
        summary.get("unresolved_questions")
    )

    with st.form(
        key=f"review_summary_form_{summary['summary_id']}"
    ):

        issue = st.text_area(
            "🔴 Main Issue",
            value=summary.get("issue") or "",
            height=85,
            placeholder="Describe the learner's main issue..."
        )

        steps_text = st.text_area(
            "🛠️ Steps Tried",
            value="\n".join(steps),
            height=100,
            help="Enter one step per line."
        )

        current_status = st.text_area(
            "📌 Current Status",
            value=summary.get("current_status") or "",
            height=75
        )

        questions_text = st.text_area(
            "❓ Unresolved Questions",
            value="\n".join(questions),
            height=90,
            help="Enter one question per line."
        )

        next_action = st.text_area(
            "➡️ Recommended Next Action",
            value=summary.get("next_action") or "",
            height=80
        )

        st.divider()

        st.markdown("**👤 Reviewer Details**")

        reviewer = st.text_input(
            "Reviewer Name",
            value="Support Agent",
            placeholder="Enter reviewer name"
        )

        rating = st.slider(
            "AI Summary Rating",
            min_value=1,
            max_value=5,
            value=4
        )

        feedback_text = st.text_area(
            "Agent Feedback / Comments",
            placeholder="Write feedback or corrections...",
            height=75
        )

        decision = st.radio(
            "Review Decision",
            ["Pending", "Approve", "Reject"],
            horizontal=True
        )

        submitted = st.form_submit_button(
            "💾 Save Review",
            type="primary",
            width="stretch"
        )

    return {
        "submitted": submitted,
        "issue": issue,
        "steps_text": steps_text,
        "current_status": current_status,
        "questions_text": questions_text,
        "next_action": next_action,
        "reviewer": reviewer,
        "rating": rating,
        "feedback_text": feedback_text,
        "decision": decision
    }


# ==========================================================
# 13. SAVE REVIEW
# ==========================================================

def process_review(summary, form_data):

    if not form_data["reviewer"].strip():

        st.error("Please enter reviewer name.")

        return

    if not form_data["issue"].strip():

        st.error("Main Issue cannot be empty.")

        return

    if not form_data["next_action"].strip():

        st.error("Recommended Next Action cannot be empty.")

        return

    corrected_summary = {

        "issue": form_data["issue"].strip(),

        "steps_tried": [
            item.strip()
            for item in form_data["steps_text"].splitlines()
            if item.strip()
        ],

        "current_status": form_data["current_status"].strip(),

        "unresolved_questions": [
            item.strip()
            for item in form_data["questions_text"].splitlines()
            if item.strip()
        ],

        "next_action": form_data["next_action"].strip()

    }

    try:

        original_summary = {

            "issue": summary["issue"],

            "steps_tried": parse_list(
                summary["steps_tried"]
            ),

            "current_status": summary["current_status"],

            "unresolved_questions": parse_list(
                summary["unresolved_questions"]
            ),

            "next_action": summary["next_action"]

        }

        content_changed = (
            corrected_summary != original_summary
        )

        target_summary_id = summary["summary_id"]

        new_version = None

        # Create a new version if content changed

        if content_changed:

            target_summary_id, new_version = save_summary(
                thread_id=summary["thread_id"],
                summary=corrected_summary,
                provider=summary["provider"],
                model=summary["model"],
                prompt_version=summary["prompt_version"]
            )

        status_map = {
            "Pending": "pending",
            "Approve": "approved",
            "Reject": "rejected"
        }

        final_status = status_map[
            form_data["decision"]
        ]

        # Save feedback

        save_feedback(
            summary_id=target_summary_id,
            rating=form_data["rating"],
            feedback_text=form_data["feedback_text"],
            reviewer=form_data["reviewer"].strip(),
            corrected_summary=corrected_summary
        )

        # Update status

        updated = update_review_status(
            summary_id=target_summary_id,
            status=final_status,
            reviewer=form_data["reviewer"].strip(),
            feedback_text=form_data["feedback_text"]
        )

        if not updated:

            raise ValueError(
                "Summary review status could not be updated."
            )

        # Audit log

        log_action(
            action=f"summary_{final_status}",
            performed_by=form_data["reviewer"].strip(),
            thread_id=summary["thread_id"],
            summary_id=target_summary_id,
            details=(
                f"Review completed. "
                f"Rating: {form_data['rating']}/5. "
                f"Content changed: {content_changed}."
            )
        )

        success_message = (
            f"Review saved successfully! "
            f"Summary ID: {target_summary_id}. "
            f"Status: {final_status.title()}."
        )

        if content_changed:

            success_message += (
                f" New version {new_version} created."
            )

        st.session_state["review_flash"] = success_message
        st.session_state["review_flash_type"] = "review"

        st.session_state["selected_review_summary"] = (
            target_summary_id
        )

        st.rerun()

    except Exception as error:

        st.error("Unable to save review.")

        st.exception(error)


# ==========================================================
# 14. MAIN PAGE
# ==========================================================

def show():

    load_review_css()

    # ======================================================
    # PAGE HEADER - NATIVE STREAMLIT (NO RAW HTML)
    # ======================================================

    header_icon, header_text = st.columns(
        [0.07, 0.93],
        vertical_alignment="center"
    )

    with header_icon:
        st.markdown("## 📋")

    with header_text:
        st.markdown(
            "<h2 style='margin:0; padding:0; color:#172554;'>"
            "Handover Review</h2>",
            unsafe_allow_html=True
        )
        st.caption(
            "Review, edit and approve AI-generated learner support summaries."
        )

    st.write("")

    # ======================================================
    # SUCCESS MESSAGE
    # ======================================================

    if "review_flash" in st.session_state:

        message = st.session_state.pop("review_flash")
        flash_type = st.session_state.pop("review_flash_type", "review")

        if flash_type == "delete":
            st.success(message)
            st.toast("Version deleted successfully.", icon="🗑️")

        elif flash_type == "warning":
            st.warning(message)

        else:
            st.success(message)
            st.toast("Review saved successfully!", icon="✅")

    # ======================================================
    # REVIEW STATISTICS
    # ======================================================

    total, pending, approved, rejected = (
        get_review_statistics()
    )

    stats_col, management_col = st.columns(
        [1.05, 1.65],
        gap="medium"
    )

    # ======================================================
    # TOP LEFT - 2 x 2 STATISTICS
    # ======================================================

    with stats_col:

        with st.container(border=True):

            st.markdown(
                '<div class="section-title">📊 Review Statistics</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                textwrap.dedent("""
                <div class="section-caption">
                    Overview of generated summaries.
                </div>
                """),
                unsafe_allow_html=True
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "Total Summaries",
                total
            )

            col2.metric(
                "Pending Reviews",
                pending
            )

            col3, col4 = st.columns(2)

            col3.metric(
                "Approved",
                approved
            )

            col4.metric(
                "Rejected",
                rejected
            )

    # ======================================================
    # TOP RIGHT - SUMMARY MANAGEMENT
    # ======================================================

    with management_col:

        with st.container(border=True):

            st.markdown(
                '<div class="section-title">🔎 Summary Management</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                textwrap.dedent("""
                <div class="section-caption">
                    Find and select a conversation summary.
                </div>
                """),
                unsafe_allow_html=True
            )

            filter_col, search_col = st.columns(
                [1, 1.5]
            )

            with filter_col:

                status_options = ["Pending", "All", "Approved", "Rejected"]
                selector_revision = st.session_state.get("review_selector_revision", 0)
                preferred_status = st.session_state.get("review_status_value", "Pending")
                if preferred_status not in status_options:
                    preferred_status = "Pending"

                selected_status = st.selectbox(
                    "Filter by Status",
                    status_options,
                    index=status_options.index(preferred_status),
                    key=f"review_status_filter_{selector_revision}"
                )
                st.session_state["review_status_value"] = selected_status

            with search_col:

                search_query = st.text_input(
                    "Search Summary",
                    placeholder="Thread ID or Learner ID...",
                    key="review_search"
                )

            summaries = get_summaries(
                selected_status
            )

            # SEARCH FILTER

            if search_query.strip():

                query = search_query.strip().lower()

                summaries = [
                    item for item in summaries
                    if query in str(item["thread_id"]).lower()
                    or query in str(item["learner_id"]).lower()
                ]

            if not summaries:

                st.warning(
                    "No summaries found for the selected filter."
                )

                return

            # SUMMARY OPTIONS

            summary_options = {
                (
                    f"#{item['summary_id']} | "
                    f"{item['thread_id']} | "
                    f"V{item['version']} | "
                    f"{item['review_status'].title()}"
                ): item["summary_id"]

                for item in summaries
            }

            labels = list(summary_options.keys())

            previous_selection = st.session_state.get(
                "selected_review_summary"
            )

            default_index = 0

            if previous_selection:

                for index, label in enumerate(labels):

                    if summary_options[label] == previous_selection:

                        default_index = index

                        break

            selector_revision = st.session_state.get("review_selector_revision", 0)
            selector_key = f"review_summary_selector_{selector_revision}"

            selected_label = st.selectbox(
                "Select Summary",
                labels,
                index=default_index,
                key=selector_key
            )

            selected_summary_id = summary_options[
                selected_label
            ]

            st.session_state["selected_review_summary"] = (
                selected_summary_id
            )

            selected_item = next(
                (
                    item for item in summaries
                    if item["summary_id"] == selected_summary_id
                ),
                None
            )

            if selected_item:

                st.markdown(
                    f"""
                    **Selected Thread:** `{selected_item['thread_id']}`

                    **Learner:** `{selected_item['learner_id']}`

                    **Status:** {selected_item['review_status'].title()}
                    """
                )

    # ======================================================
    # LOAD SELECTED SUMMARY
    # ======================================================

    selected_id = st.session_state.get(
        "selected_review_summary"
    )

    if selected_id is None:

        return

    summary = get_summary(selected_id)

    if not summary:

        st.error(
            "Selected summary could not be loaded."
        )

        return

    st.write("")

    # ======================================================
    # BOTTOM SECTION - THREE PANELS
    # ======================================================

    info_col, editor_col, history_col = st.columns(
        [0.95, 1.55, 0.95],
        gap="medium"
    )

    # ======================================================
    # BOTTOM LEFT - SUMMARY INFORMATION
    # ======================================================

    with info_col:

        with st.container(border=True):

            display_summary_information(summary)

    # ======================================================
    # BOTTOM CENTER - REVIEW AND EDIT
    # ======================================================

    with editor_col:

        with st.container(border=True):

            form_data = display_summary_editor(
                summary
            )

            if form_data["submitted"]:

                process_review(
                    summary,
                    form_data
                )

    # ======================================================
    # BOTTOM RIGHT - VERSION HISTORY
    # ======================================================

    with history_col:

        with st.container(border=True):

            display_version_history(summary)