import re
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

STOP_WORDS = set(stopwords.words("english"))

# Preserve important negation words
STOP_WORDS -= {"no", "not", "nor", "cannot"}


def clean_text(text):

    if not isinstance(text, str):
        raise ValueError("Input must be a string.")

    text = text.lower()
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def preprocess_text(text):

    cleaned_text = clean_text(text)

    tokens = word_tokenize(cleaned_text)

    filtered_tokens = [
        word for word in tokens
        if word not in STOP_WORDS
    ]

    return filtered_tokens