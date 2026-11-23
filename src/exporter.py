import csv
import io
import json

from database.db import get_connection


def get_export_data():

    with get_connection() as connection:

        threads = connection.execute(
            """
            SELECT *
            FROM support_threads
            ORDER BY created_at DESC
            """
        ).fetchall()

        export_data = []

        for thread in threads:

            thread_data = dict(thread)

            # Get conversation messages
            messages = connection.execute(
                """
                SELECT sender, message, message_order
                FROM support_messages
                WHERE thread_id = ?
                ORDER BY message_order
                """,
                (thread["thread_id"],)
            ).fetchall()

            # Get all summary versions
            summaries = connection.execute(
                """
                SELECT *
                FROM handover_summaries
                WHERE thread_id = ?
                ORDER BY version DESC
                """,
                (thread["thread_id"],)
            ).fetchall()

            thread_data["messages"] = [
                dict(message) for message in messages
            ]

            thread_data["summaries"] = [
                dict(summary) for summary in summaries
            ]

            export_data.append(thread_data)

    return export_data


def export_json():

    data = get_export_data()

    return json.dumps(
        data,
        indent=4,
        ensure_ascii=False
    )


def export_csv():

    data = get_export_data()

    output = io.StringIO()

    fieldnames = [
        "thread_id",
        "learner_id",
        "thread_status",
        "created_at",
        "messages",
        "latest_summary"
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for thread in data:

        latest_summary = (
            thread["summaries"][0]
            if thread["summaries"]
            else {}
        )

        writer.writerow({
            "thread_id": thread["thread_id"],
            "learner_id": thread["learner_id"],
            "thread_status": thread["thread_status"],
            "created_at": thread["created_at"],
            "messages": json.dumps(
                thread["messages"],
                ensure_ascii=False
            ),
            "latest_summary": json.dumps(
                latest_summary,
                ensure_ascii=False
            )
        })

    return output.getvalue()