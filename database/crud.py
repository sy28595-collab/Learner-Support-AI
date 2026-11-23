from database.db import get_connection


# 1. CREATE - New conversation
def create_thread(thread_id, learner_id, created_at, messages):

    with get_connection() as connection:

        connection.execute(
            """
            INSERT INTO learners (learner_id)
            VALUES (?)
            ON CONFLICT(learner_id) DO NOTHING
            """,
            (learner_id,)
        )

        connection.execute(
            """
            INSERT INTO support_threads
            (thread_id, learner_id, created_at)
            VALUES (?, ?, ?)
            """,
            (thread_id, learner_id, created_at)
        )

        records = [
            (thread_id, msg["sender"], msg["message"], index)
            for index, msg in enumerate(messages, start=1)
        ]

        connection.executemany(
            """
            INSERT INTO support_messages
            (thread_id, sender, message, message_order)
            VALUES (?, ?, ?, ?)
            """,
            records
        )

    return True


# 2. READ - Get conversation
def get_thread(thread_id):

    with get_connection() as connection:

        thread = connection.execute(
            """
            SELECT *
            FROM support_threads
            WHERE thread_id = ?
            """,
            (thread_id,)
        ).fetchone()

        if thread is None:
            return None

        messages = connection.execute(
            """
            SELECT sender, message, message_order
            FROM support_messages
            WHERE thread_id = ?
            ORDER BY message_order
            """,
            (thread_id,)
        ).fetchall()

    return {
        "thread": dict(thread),
        "messages": [dict(message) for message in messages]
    }


# 3. READ - Get all conversations
def get_all_threads():

    with get_connection() as connection:

        records = connection.execute(
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
            """
        ).fetchall()

    return [dict(row) for row in records]


# 4. UPDATE - Update conversation status
def update_thread_status(thread_id, status):

    allowed_statuses = ["open", "resolved", "closed"]

    if status not in allowed_statuses:
        raise ValueError("Invalid thread status.")

    with get_connection() as connection:

        cursor = connection.execute(
            """
            UPDATE support_threads
            SET thread_status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE thread_id = ?
            """,
            (status, thread_id)
        )

    return cursor.rowcount > 0


# 5. DELETE - Delete conversation
def delete_thread(thread_id):

    with get_connection() as connection:

        connection.execute(
            "DELETE FROM handover_summaries WHERE thread_id = ?",
            (thread_id,)
        )

        connection.execute(
            "DELETE FROM issue_tags WHERE thread_id = ?",
            (thread_id,)
        )

        connection.execute(
            "DELETE FROM support_messages WHERE thread_id = ?",
            (thread_id,)
        )

        cursor = connection.execute(
            "DELETE FROM support_threads WHERE thread_id = ?",
            (thread_id,)
        )

    return cursor.rowcount > 0