from database.crud import (
    get_thread,
    get_all_threads,
    update_thread_status,
    delete_thread
)


# 1. Read one conversation
thread = get_thread("THREAD_001")

print("READ TEST")

if thread:
    print("Thread ID:", thread["thread"]["thread_id"])
    print("Messages:", len(thread["messages"]))
else:
    print("Thread not found.")


# 2. Read all conversations
print("\nALL THREADS TEST")

threads = get_all_threads()

print("Total threads:", len(threads))


# 3. Update status
print("\nUPDATE TEST")

result = update_thread_status(
    "THREAD_001",
    "resolved"
)

print("Status updated:", result)


# 4. Verify updated status
thread = get_thread("THREAD_001")

print(
    "Current status:",
    thread["thread"]["thread_status"]
)