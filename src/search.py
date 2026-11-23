from database.db import get_connection


def search_conversations(
    query=None,
    status=None,
    issue_type=None,
    page=1,
    page_size=10
):

    # Validate pagination
    if page < 1:
        raise ValueError("Page must be at least 1.")

    if page_size not in [10, 20, 50]:
        raise ValueError("Page size must be 10, 20 or 50.")

    # Validate status
    allowed_statuses = ["open", "resolved", "closed"]

    if status and status not in allowed_statuses:
        raise ValueError("Invalid conversation status.")

    conditions = []
    params = []

    # Search by Thread ID, Learner ID or Message
    if query and query.strip():

        conditions.append("""
            (
                t.thread_id LIKE ?
                OR t.learner_id LIKE ?
                OR EXISTS (
                    SELECT 1
                    FROM support_messages m
                    WHERE m.thread_id = t.thread_id
                    AND m.message LIKE ?
                )
            )
        """)

        search_value = f"%{query.strip()}%"

        params.extend([
            search_value,
            search_value,
            search_value
        ])

    # Filter by status
    if status:
        conditions.append("t.thread_status = ?")
        params.append(status)

    # Filter by issue type
    if issue_type:
        conditions.append("""
            EXISTS (
                SELECT 1
                FROM issue_tags it
                WHERE it.thread_id = t.thread_id
                AND it.issue_type = ?
            )
        """)

        params.append(issue_type)

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    with get_connection() as connection:

        # Total matching records
        count_query = f"""
            SELECT COUNT(*)
            FROM support_threads t
            {where_clause}
        """

        total_records = connection.execute(
            count_query,
            params
        ).fetchone()[0]

        # Calculate pagination
        total_pages = (
            total_records + page_size - 1
        ) // page_size

        offset = (page - 1) * page_size

        # Fetch matching conversations
        data_query = f"""
            SELECT
                t.thread_id,
                t.learner_id,
                t.thread_status,
                t.created_at,
                COUNT(m.message_id) AS total_messages

            FROM support_threads t

            LEFT JOIN support_messages m
            ON t.thread_id = m.thread_id

            {where_clause}

            GROUP BY t.thread_id

            ORDER BY t.created_at DESC, t.thread_id

            LIMIT ? OFFSET ?
        """

        records = connection.execute(
            data_query,
            params + [page_size, offset]
        ).fetchall()

    return {
        "records": [dict(row) for row in records],
        "total_records": total_records,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size
    }