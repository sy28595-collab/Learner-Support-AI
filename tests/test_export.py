import json

from src.exporter import export_json, export_csv


# JSON Export Test
json_data = export_json()

parsed_data = json.loads(json_data)

print("JSON EXPORT")
print("Total conversations:", len(parsed_data))

if parsed_data:
    print("First thread:", parsed_data[0]["thread_id"])
    print("Messages:", len(parsed_data[0]["messages"]))


# CSV Export Test
csv_data = export_csv()

print("\nCSV EXPORT")
print("CSV characters:", len(csv_data))
print("CSV header:", csv_data.splitlines()[0])


print("\nExport testing completed!")