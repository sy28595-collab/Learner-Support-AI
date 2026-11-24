import os
import logging
import streamlit as st

from dotenv import load_dotenv
from google import genai
from google.genai import types

from models.schemas import HandoverSummary


load_dotenv()

logging.basicConfig(level=logging.INFO)
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# ==========================================
# 1. GEMINI CONFIGURATION
# ==========================================

def get_config(key, default=None):

    value = os.getenv(key)

    if not value:
        try:
            value = st.secrets.get(key, default)
        except Exception:
            value = default

    return value


def get_api_key():
    return get_config("GEMINI_API_KEY")


def get_backup_api_key():
    return get_config("GEMINI_BACKUP_API_KEY")


def get_model():
    return get_config(
        "GEMINI_MODEL",
        "gemini-3.6-flash"
    )


def get_backup_model():
    return get_config(
        "GEMINI_BACKUP_MODEL",
        "gemini-3.5-flash"
    )


def create_client(api_key):

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=60000,
            retry_options=types.HttpRetryOptions(
                attempts=3,
                initial_delay=2.0,
                max_delay=10.0,
                exp_base=2.0,
                jitter=1.0,
                http_status_codes=[408, 500, 502, 503, 504]
            )
        )
    )


# ==========================================
# 2. GEMINI API REQUEST
# ==========================================

def request_summary(api_key, model, conversation, system_instruction):

    client = create_client(api_key)

    return client.models.generate_content(
        model=model,
        contents=conversation,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=HandoverSummary,
            max_output_tokens=2048
        )
    )


# ==========================================
# 3. GENERATE HANDOVER SUMMARY
# ==========================================

def generate_handover_summary(messages):

    primary_key = get_api_key()
    backup_key = get_backup_api_key()

    primary_model = get_model()
    backup_model = get_backup_model()

    if not primary_key:
        raise ValueError(
            "Gemini primary API key is missing."
        )

    if not messages:
        raise ValueError(
            "Conversation messages cannot be empty."
        )

    conversation = "\n".join(
        f"{message['sender']}: {message['message']}"
        for message in messages
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

    # ======================================
    # PRIMARY API
    # ======================================

    try:

        logging.info(
            "Trying primary Gemini API: %s",
            primary_model
        )

        response = request_summary(
            primary_key,
            primary_model,
            conversation,
            system_instruction
        )

    except Exception as primary_error:

        error_text = str(primary_error).upper()

        quota_exceeded = (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
        )

        if not quota_exceeded:
            raise

        logging.warning(
            "Primary Gemini quota exhausted."
        )

        # ==================================
        # BACKUP API
        # ==================================

        if not backup_key:

            raise ValueError(
                "Gemini daily quota has been reached. "
                "No backup API key is configured."
            ) from primary_error

        try:

            logging.info(
                "Trying backup Gemini API: %s",
                backup_model
            )

            response = request_summary(
                backup_key,
                backup_model,
                conversation,
                system_instruction
            )

        except Exception as backup_error:

            logging.error(
                "Backup Gemini API also failed: %s",
                backup_error
            )

            backup_error_text = str(backup_error).upper()

            if (
                "429" in backup_error_text
                or "RESOURCE_EXHAUSTED" in backup_error_text
            ):
                raise ValueError(
                    "Both Gemini API quotas are exhausted. "
                    "Please try again after the quota resets."
                ) from backup_error

            elif (
                "503" in backup_error_text
                or "UNAVAILABLE" in backup_error_text
            ):
                raise ValueError(
                    "Gemini backup model is temporarily unavailable. "
                    "Please try again later."
                ) from backup_error

            else:
                raise ValueError(
                    "Backup Gemini API failed. "
                    "Please check the API configuration."
                ) from backup_error

    # ======================================
    # VALIDATE RESPONSE
    # ======================================

    if not response.text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    if response.candidates:

        finish_reason = response.candidates[0].finish_reason

        if finish_reason and "MAX_TOKENS" in str(finish_reason):

            raise ValueError(
                "Gemini response was truncated."
            )

    try:

        summary = HandoverSummary.model_validate_json(
            response.text
        )

    except Exception as error:

        logging.error(
            "Invalid Gemini JSON response: %s",
            error
        )

        raise ValueError(
            "Gemini returned incomplete or invalid JSON."
        ) from error

    logging.info(
        "Gemini summary generated successfully."
    )

    return summary