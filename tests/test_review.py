from database.summary_manager import save_summary
from database.review_manager import review_summary, get_review_status

# Create test summary
summary = {
    "issue": "Login problem",
    "steps_tried": ["Password reset attempted"],
    "current_status": "Issue unresolved",
    "unresolved_questions": ["Is the account active?"],
    "next_action": "Verify learner account"
}

summary_id, version = save_summary("THREAD_001", summary)

print("Summary ID:", summary_id)

# Approve summary
result = review_summary(
    summary_id=summary_id,
    status="approved",
    reviewed_by="Support Agent",
    feedback="Summary verified successfully."
)

print("Review completed:", result)

# Check review status
status = get_review_status(summary_id)

print("\nReview Status:", status["review_status"])
print("Reviewed By:", status["reviewed_by"])
print("Feedback:", status["feedback"])