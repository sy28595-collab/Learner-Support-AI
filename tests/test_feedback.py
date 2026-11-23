from database.summary_manager import save_summary
from database.feedback_manager import submit_feedback, get_feedback
from database.audit_manager import get_audit_logs

thread_id = "THREAD_001"

summary = {
    "issue": "Course access problem",
    "steps_tried": ["Login attempted"],
    "current_status": "Issue unresolved",
    "unresolved_questions": ["Is access activated?"],
    "next_action": "Check account access"
}

# Create a summary for testing
summary_id, version = save_summary(thread_id, summary)

# Submit agent feedback
feedback_id = submit_feedback(
    summary_id=summary_id,
    rating=5,
    reviewer="Support Agent",
    feedback_text="Summary is clear and useful.",
    corrected_summary="Course access issue requires account verification."
)

print("Feedback ID:", feedback_id)

# Read feedback
feedback = get_feedback(summary_id)

print("\nFeedback records:", len(feedback))
print("Rating:", feedback[0]["rating"])
print("Reviewer:", feedback[0]["reviewer"])

# Check audit logs
logs = get_audit_logs(thread_id)

print("\nAudit logs:", len(logs))

for log in logs:
    print(log["action"], "-", log["performed_by"])

print("\nFeedback testing completed!")