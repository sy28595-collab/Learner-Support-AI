from database.summary_manager import (
    save_summary,
    get_summary_versions,
    get_latest_summary
)

thread_id = "THREAD_001"

summary = {
    "issue": "Course access problem",
    "steps_tried": [
        "Checked internet connection",
        "Tried logging in again"
    ],
    "current_status": "Issue still unresolved",
    "unresolved_questions": [
        "Is the course access activated?"
    ],
    "next_action": "Check learner account access"
}

# Save first version
summary_id, version = save_summary(thread_id, summary)

print("First summary saved:", summary_id)
print("Version:", version)

# Save second version
summary["current_status"] = "Access restored"

summary_id, version = save_summary(thread_id, summary)

print("\nSecond summary saved:", summary_id)
print("Version:", version)

# Get all versions
versions = get_summary_versions(thread_id)

print("\nTotal versions:", len(versions))

for item in versions:
    print(
        "Version:", item["version"],
        "| Status:", item["current_status"]
    )

# Get latest version
latest = get_latest_summary(thread_id)

print("\nLatest summary:")
print(latest["current_status"])