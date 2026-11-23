from src.search import search_conversations


# 1. Search by Thread ID
print("THREAD SEARCH")

result = search_conversations(
    query="THREAD_001"
)

print("Records:", result["total_records"])


# 2. Search by Learner ID
print("\nLEARNER SEARCH")

result = search_conversations(
    query="LEARNER_005"
)

print("Records:", result["total_records"])


# 3. Search by Keyword
print("\nKEYWORD SEARCH")

result = search_conversations(
    query="Python"
)

print("Records:", result["total_records"])


# 4. Filter by Status
print("\nSTATUS FILTER")

result = search_conversations(
    status="open"
)

print("Open conversations:", result["total_records"])


# 5. Pagination
print("\nPAGINATION")

result = search_conversations(
    page=1,
    page_size=10
)

print("Current page:", result["current_page"])
print("Total pages:", result["total_pages"])
print("Records on page:", len(result["records"]))


print("\nSearch testing completed!")