from database.db import get_connection


def submit_feedback(
    summary_id,
    rating,
    reviewer,
    feedback_text=None,
    corrected_summary=None
):
    if not 1 <= rating <= 5:
        raise ValueError("Rating must be between 1 and 5.")

    if not reviewer or not reviewer.strip():
        raise ValueError("Reviewer name is required.")

    with get_connection() as connection:

        # Check whether summary exists
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

        # Save feedback
        cursor = connection.execute(
            """
            INSERT INTO agent_feedback
            (
                summary_id, rating, feedback_text,
                corrected_summary, reviewer
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                summary_id,
                rating,
                feedback_text,
                corrected_summary,
                reviewer
            )
        )

        feedback_id = cursor.lastrowid

        # Record action in audit logs
        connection.execute(
            """
            INSERT INTO audit_logs
            (thread_id, summary_id, action, performed_by, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                summary["thread_id"],
                summary_id,
                "feedback_submitted",
                reviewer,
                f"Rating: {rating}"
            )
        )

    return feedback_id


def get_feedback(summary_id):

    with get_connection() as connection:
        records = connection.execute(
            """
            SELECT *
            FROM agent_feedback
            WHERE summary_id = ?
            ORDER BY created_at DESC
            """,
            (summary_id,)
        ).fetchall()

    return [dict(row) for row in records]