import json
import logging
from pathlib import Path

from database.db import get_connection
from models.schemas import Conversation


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = BASE_DIR / "data" / "raw" / "sample_conversations.json"


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


def load_conversations():

    if not DATA_PATH.exists():
        raise FileNotFoundError("Conversation dataset not found.")

    with open(DATA_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Dataset must contain a list of conversations.")

    # Validate all records before database insertion
    conversations = [
        Conversation.model_validate(item)
        for item in data
    ]

    return conversations


def import_conversations():

    conversations = load_conversations()

    with get_connection() as connection:

        for conversation in conversations:

            # 1. Insert learner
            connection.execute(
                """
                INSERT INTO learners (learner_id)
                VALUES (?)
                ON CONFLICT(learner_id) DO NOTHING
                """,
                (conversation.learner_id,)
            )

            # 2. Insert or update support thread
            connection.execute(
                """
                INSERT INTO support_threads
                (thread_id, learner_id, created_at)
                VALUES (?, ?, ?)

                ON CONFLICT(thread_id) DO UPDATE SET
                    learner_id = excluded.learner_id,
                    created_at = excluded.created_at
                """,
                (
                    conversation.thread_id,
                    conversation.learner_id,
                    conversation.created_at
                )
            )

            # 3. Refresh messages for this thread
            connection.execute(
                """
                DELETE FROM support_messages
                WHERE thread_id = ?
                """,
                (conversation.thread_id,)
            )

            # 4. Insert messages
            message_records = [
                (
                    conversation.thread_id,
                    message.sender,
                    message.message,
                    index
                )
                for index, message in enumerate(
                    conversation.messages, start=1
                )
            ]

            connection.executemany(
                """
                INSERT INTO support_messages
                (thread_id, sender, message, message_order)
                VALUES (?, ?, ?, ?)
                """,
                message_records
            )

    logging.info(
        "%s conversations imported successfully.",
        len(conversations)
    )


if __name__ == "__main__":

    try:
        import_conversations()

    except Exception:
        logging.exception("Conversation import failed.")
        raise