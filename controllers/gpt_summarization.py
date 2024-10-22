import openai
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("API key not found. Set the OPENAI_API_KEY environment variable.")


def openai_summarizer(text, max_tokens=150, temperature=0.5):
    if not text:
        raise ValueError("Input text cannot be empty.")

    try:
        logging.info("Starting summarization for text of length %d", len(text))
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes text.",
                },
                {"role": "user", "content": text},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if response.choices:
            summary = response.choices[0].message["content"].strip()
            logging.info("Summarization completed successfully.")
            return summary
        else:
            raise ValueError("No choices found in the response.")
    except Exception as e:
        logging.error("Error occurred during summarization: %s", str(e))
        raise RuntimeError(f"Error occurred during summarization: {str(e)}")
