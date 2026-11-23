import logging

from database.crud import get_thread
from src.gemini_client import generate_handover_summary
from database.summary_manager import save_summary


def main():

    logging.basicConfig(level=logging.INFO)

    print("Sending conversation to Gemini...")

    thread = get_thread("THREAD_001")

    if not thread:
        print("Conversation not found.")
        return

    summary = generate_handover_summary(thread["messages"])

    summary_id, version = save_summary(
        "THREAD_001",
        summary.model_dump(),
        provider="gemini",
        model="gemini-3.6-flash"
    )

    print("\nSummary saved to database!")
    print("Summary ID:", summary_id)
    print("Version:", version)

    print("\nGEMINI GENERATED SUMMARY")
    print("------------------------")

    print("Issue:", summary.issue)
    print("Steps Tried:", summary.steps_tried)
    print("Current Status:", summary.current_status)
    print("Unresolved Questions:", summary.unresolved_questions)
    print("Next Action:", summary.next_action)

    print("\nGemini API test successful!")


if __name__ == "__main__":
    main()