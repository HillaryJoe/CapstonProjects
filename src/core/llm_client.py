from dotenv import load_dotenv
import os
from pathlib import Path
from typing import List, Dict

from openai import OpenAI
from google import genai
#from .cost_tracker import calculate_cost

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

import time

# Load .env from project root (works regardless of cwd)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Read configuration from .env file
PROVIDER = os.getenv("PROVIDER", "openai").lower()
MODEL = os.getenv("MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
TIMEOUT = 60

Message = Dict[str, str]


def get_langchain_llm():
    if PROVIDER == "openai":
        return ChatOpenAI(
            model=MODEL,
            temperature=0,
            api_key=OPENAI_API_KEY
        )

    elif PROVIDER == "google":
        return ChatGoogleGenerativeAI(
            model=MODEL,
            temperature=0,
            google_api_key=GOOGLE_API_KEY
        )

    elif PROVIDER == "ollama":
        return Ollama(
            model=MODEL,
            temperature=0,
            base_url=OLLAMA_HOST
        )