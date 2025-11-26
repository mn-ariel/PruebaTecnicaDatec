import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

_client: OpenAI | None = None

load_dotenv()

def get_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        msg = "OPENAI_API_KEY is not set in environment."
        logger.error(msg)
        raise RuntimeError(msg)

    _client = OpenAI(api_key=api_key)
    logger.info("OpenAI client initialized.")
    return _client
