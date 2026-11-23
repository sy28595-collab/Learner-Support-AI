from database.db import get_connection


def review_summary(summary_id, status, reviewed_by, feedback=None):

    allowed_statuses = ["pending", "approved", "rejected"]

    if status not in allowed_statuses:
        raise ValueError("Invalid review status.")

    if not reviewed_by or not reviewed_by.strip():
        raise ValueError("Reviewer name is required.")

    with get_connection() as connection:

        # Check summary
        summary = connection.execute(
            """
            SELECT thread_id
            FROM handover_summaries
            WHERE summary_id = ?
            """,
            (summary_id,)
        ).fetchone()

        if summary is None:
            raise ValueError("Summary not found.")

        # Update review status
        connection.execute(
            """
            UPDATE handover_summaries
            SET review_status = ?,
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                feedback = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE summary_id = ?
            """,
            (status, reviewed_by, feedback, summary_id)
        )

        # Save audit log
        connection.execute(
            """
            INSERT INTO audit_logs
            (thread_id, summary_id, action, performed_by, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                summary["thread_id"],
                summary_id,
                f"summary_{status}",
                reviewed_by,
                feedback
            )
        )

    return True


def get_review_status(summary_id):

    with get_connection() as connection:
        record = connection.execute(
            """
            SELECT review_status, reviewed_by,
                   reviewed_at, feedback
            FROM handover_summaries
            WHERE summary_id = ?
            """,
            (summary_id,)
        ).fetchone()

    return dict(record) if record else None