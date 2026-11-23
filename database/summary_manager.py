import json
from database.db import get_connection


def save_summary(thread_id, summary, provider="openai",
                 model=None, prompt_version="v1"):

    with get_connection() as connection:

        # Check whether conversation exists
        thread = connection.execute(
            "SELECT thread_id FROM support_threads WHERE thread_id = ?",
            (thread_id,)
        ).fetchone()

        if thread is None:
            raise ValueError("Conversation not found.")

        # Find next summary version
        result = connection.execute(
            """
            SELECT COALESCE(MAX(version), 0) + 1
            FROM handover_summaries
            WHERE thread_id = ?
            """,
            (thread_id,)
        ).fetchone()

        version = result[0]

        # Save new summary
        cursor = connection.execute(
            """
            INSERT INTO handover_summaries
            (
                thread_id, version, issue, steps_tried,
                current_status, unresolved_questions,
                next_action, provider, model, prompt_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                thread_id,
                version,
                summary["issue"],
                json.dumps(summary["steps_tried"]),
                summary["current_status"],
                json.dumps(summary["unresolved_questions"]),
                summary["next_action"],
                provider,
                model,
                prompt_version
            )
        )

        summary_id = cursor.lastrowid

    return summary_id, version


def get_summary_versions(thread_id):

    with get_connection() as connection:
        records = connection.execute(
            """
            SELECT *
            FROM handover_summaries
            WHERE thread_id = ?
            ORDER BY version DESC
            """,
            (thread_id,)
        ).fetchall()

    return [dict(row) for row in records]


def get_latest_summary(thread_id):

    with get_connection() as connection:
        record = connection.execute(
            """
            SELECT *
            FROM handover_summaries
            WHERE thread_id = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (thread_id,)
        ).fetchone()

    return dict(record) if record else None