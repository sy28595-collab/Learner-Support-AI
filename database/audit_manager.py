from database.db import get_connection


def log_action(
    action,
    performed_by,
    thread_id=None,
    summary_id=None,
    details=None
):
    if not action or not performed_by:
        raise ValueError("Action and performed_by are required.")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO audit_logs
            (
                thread_id, summary_id, action,
                performed_by, details
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                thread_id,
                summary_id,
                action,
                performed_by,
                details
            )
        )

    return cursor.lastrowid


def get_audit_logs(thread_id=None):

    with get_connection() as connection:

        if thread_id:
            records = connection.execute(
                """
                SELECT *
                FROM audit_logs
                WHERE thread_id = ?
                ORDER BY created_at DESC
                """,
                (thread_id,)
            ).fetchall()

        else:
            records = connection.execute(
                """
                SELECT *
                FROM audit_logs
                ORDER BY created_at DESC
                """
            ).fetchall()

    return [dict(row) for row in records]