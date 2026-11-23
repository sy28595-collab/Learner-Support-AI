import os
import logging

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


def test_gemini_connection():

    if not API_KEY:
        print("ERROR: Gemini API key missing.")
        return

    print("\nTesting Gemini API Connection...")
    print("Model:", MODEL)

    try:

        client = genai.Client(
            api_key=API_KEY,
            http_options=types.HttpOptions(
                timeout=120000
            )
        )

        response = client.models.generate_content(
            model=MODEL,
            contents="Reply with only: Gemini API is working."
        )

        if response.text:
            print("\nSUCCESS!")
            print("Gemini Response:", response.text)
        else:
            print("\nERROR: Empty response received.")

    except Exception as error:

        print("\nGEMINI CONNECTION FAILED")
        print("Error:", error)


if __name__ == "__main__":
    test_gemini_connection()