import uuid
import pytest

from database.db import get_connection
from database.crud import (
    create_thread,
    get_thread,
    get_all_threads,
    update_thread_status,
    delete_thread
)
from database.summary_manager import (
    save_summary,
    get_summary_versions,
    get_latest_summary
)
from database.feedback_manager import (
    submit_feedback,
    get_feedback
)
from database.review_manager import (
    review_summary,
    get_review_status
)
from database.audit_manager import (
    log_action,
    get_audit_logs
)
from src.search import search_conversations
from src.preprocessor import clean_text, preprocess_text
from src.exporter import export_json, export_csv


@pytest.fixture
def test_thread():

    thread_id = "TEST_" + uuid.uuid4().hex[:10]
    learner_id = "LEARNER_" + uuid.uuid4().hex[:10]

    create_thread(
        thread_id,
        learner_id,
        "2026-11-24 10:00:00",
        [
            {
                "sender": "learner",
                "message": "I cannot access my Python course."
            },
            {
                "sender": "agent",
                "message": "Please clear your browser cache."
            }
        ]
    )

    yield thread_id

    # Remove test data after test
    with get_connection() as connection:

        summary_ids = connection.execute(
            """
            SELECT summary_id
            FROM handover_summaries
            WHERE thread_id = ?
            """,
            (thread_id,)
        ).fetchall()

        for row in summary_ids:

            connection.execute(
                "DELETE FROM agent_feedback WHERE summary_id = ?",
                (row["summary_id"],)
            )

        connection.execute(
            "DELETE FROM audit_logs WHERE thread_id = ?",
            (thread_id,)
        )

        connection.execute(
            "DELETE FROM agent_feedback WHERE summary_id IN "
            "(SELECT summary_id FROM handover_summaries WHERE thread_id = ?)",
            (thread_id,)
        )

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

        connection.execute(
            "DELETE FROM support_threads WHERE thread_id = ?",
            (thread_id,)
        )

        connection.execute(
            "DELETE FROM learners WHERE learner_id = ?",
            (learner_id,)
        )


@pytest.fixture
def test_summary(test_thread):

    summary = {
        "issue": "Python course access problem",
        "steps_tried": ["Cleared browser cache"],
        "current_status": "Issue unresolved",
        "unresolved_questions": ["When will access be restored?"],
        "next_action": "Technical team should investigate."
    }

    summary_id, version = save_summary(
        test_thread,
        summary,
        provider="gemini",
        model="gemini-3.6-flash"
    )

    return test_thread, summary_id


# 1. CRUD TESTS

def test_create_and_read_thread(test_thread):

    result = get_thread(test_thread)

    assert result is not None
    assert result["thread"]["thread_id"] == test_thread
    assert len(result["messages"]) == 2


def test_get_all_threads():

    result = get_all_threads()

    assert isinstance(result, list)


def test_update_thread_status(test_thread):

    result = update_thread_status(test_thread, "resolved")

    assert result is True

    thread = get_thread(test_thread)

    assert thread["thread"]["thread_status"] == "resolved"


def test_invalid_thread_status(test_thread):

    with pytest.raises(ValueError):

        update_thread_status(test_thread, "invalid")


# 2. SUMMARY VERSIONING TESTS

def test_save_summary(test_summary):

    thread_id, summary_id = test_summary

    result = get_latest_summary(thread_id)

    assert result is not None
    assert result["summary_id"] == summary_id


def test_summary_versioning(test_summary):

    thread_id, summary_id = test_summary

    summary = {
        "issue": "Updated Python access problem",
        "steps_tried": ["Cleared cache", "Changed browser"],
        "current_status": "Under investigation",
        "unresolved_questions": [],
        "next_action": "Contact technical team."
    }

    new_id, version = save_summary(
        thread_id,
        summary,
        provider="gemini"
    )

    versions = get_summary_versions(thread_id)

    assert version == 2
    assert len(versions) == 2


# 3. FEEDBACK TESTS

def test_submit_feedback(test_summary):

    thread_id, summary_id = test_summary

    feedback_id = submit_feedback(
        summary_id,
        5,
        "Test Agent",
        "Summary is accurate."
    )

    feedback = get_feedback(summary_id)

    assert feedback_id is not None
    assert len(feedback) == 1
    assert feedback[0]["rating"] == 5


def test_invalid_feedback_rating(test_summary):

    thread_id, summary_id = test_summary

    with pytest.raises(ValueError):

        submit_feedback(
            summary_id,
            6,
            "Test Agent"
        )


# 4. REVIEW TESTS

def test_review_summary(test_summary):

    thread_id, summary_id = test_summary

    result = review_summary(
        summary_id,
        "approved",
        "Test Agent",
        "Verified successfully."
    )

    status = get_review_status(summary_id)

    assert result is True
    assert status["review_status"] == "approved"


# 5. AUDIT LOG TESTS

def test_audit_log(test_thread):

    log_action(
        "test_action",
        "Test Agent",
        thread_id=test_thread,
        details="Automated test"
    )

    logs = get_audit_logs(test_thread)

    assert len(logs) >= 1
    assert logs[0]["action"] == "test_action"


# 6. SEARCH TESTS

def test_search_by_thread_id(test_thread):

    result = search_conversations(query=test_thread)

    assert result["total_records"] == 1


def test_search_status_filter(test_thread):

    update_thread_status(test_thread, "resolved")

    result = search_conversations(status="resolved")

    assert result["total_records"] >= 1


def test_invalid_page_number():

    with pytest.raises(ValueError):

        search_conversations(page=0)


# 7. PREPROCESSING TESTS

def test_clean_text():

    result = clean_text(
        "HELLO! Visit https://example.com"
    )

    assert result == "hello visit"


def test_preprocess_text():

    result = preprocess_text(
        "I cannot access my Python course"
    )

    assert "not" in result
    assert "python" in result


# 8. EXPORT TESTS

def test_json_export():

    result = export_json()

    assert isinstance(result, str)
    assert len(result) > 0


def test_csv_export():

    result = export_csv()

    assert isinstance(result, str)
    assert "thread_id" in result
    assert "learner_id" in result