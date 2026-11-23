import os
import logging
import streamlit as st

from dotenv import load_dotenv
from google import genai
from google.genai import types

from models.schemas import HandoverSummary


load_dotenv()

logging.basicConfig(level=logging.INFO)


# ==========================================
# 1. GEMINI CONFIGURATION
# ==========================================

def get_api_key():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass

    return api_key


def get_model():

    model = os.getenv("GEMINI_MODEL")

    if not model:
        try:
            model = st.secrets.get(
                "GEMINI_MODEL",
                "gemini-3.6-flash"
            )
        except Exception:
            model = "gemini-3.6-flash"

    return model


# ==========================================
# 2. GENERATE HANDOVER SUMMARY
# ==========================================

def generate_handover_summary(messages):

    api_key = get_api_key()
    model = get_model()

    if not api_key:
        raise ValueError("Gemini API key is missing.")

    if not messages:
        raise ValueError("Conversation messages cannot be empty.")

    # Convert messages into conversation text
    conversation = "\n".join(
        f"{message['sender']}: {message['message']}"
        for message in messages
    )

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=30000,
            retry_options=types.HttpRetryOptions(
                attempts=1
            )
        )
    )

    system_instruction = """
    You are an experienced learner support assistant.

    Analyze the support conversation and generate
    a concise handover summary.

    Required fields:

    1. issue: Main learner problem.
    2. steps_tried: Troubleshooting already attempted.
    3. current_status: Current issue status.
    4. unresolved_questions: Questions still unanswered.
    5. next_action: Recommended next action.

    Rules:
    - Use only information from the conversation.
    - Never invent facts.
    - Do not assume an issue is resolved.
    - Use simple professional English.
    - If information is missing, clearly mention it.
    - Keep the summary concise.
    """

    response = client.models.generate_content(
        model=model,
        contents=conversation,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=HandoverSummary,
            max_output_tokens=2048
        )
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    # Check whether the response was truncated
    if response.candidates:

        finish_reason = response.candidates[0].finish_reason

        if finish_reason and "MAX_TOKENS" in str(finish_reason):

            raise ValueError(
                "Gemini response was truncated. "
                "Increase output token limit."
            )

    # Validate JSON using Pydantic
    try:

        summary = HandoverSummary.model_validate_json(
            response.text
        )

    except Exception as error:

        logging.error("Invalid Gemini JSON response.")

        raise ValueError(
            "Gemini returned incomplete or invalid JSON."
        ) from error

    logging.info("Gemini summary generated successfully.")

    return summary