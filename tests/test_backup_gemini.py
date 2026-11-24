import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_BACKUP_API_KEY")

if not api_key:
    print("Backup API key not found!")
    exit()

client = genai.Client(api_key=api_key)

models_to_test = [
    "gemini-3.5-flash-lite"
]

print("\nBACKUP GEMINI API TEST")
print("-" * 40)

for model in models_to_test:

    print(f"\nTesting: {model}")

    try:
        response = client.models.generate_content(
            model=model,
            contents="Reply with only: API working"
        )

        print("SUCCESS:", response.text)

    except Exception as error:
        print("FAILED:", str(error)[:250])

print("\nTesting completed.")