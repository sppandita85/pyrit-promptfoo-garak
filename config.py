"""Settings for the banking RAG app, read from environment variables / .env."""
import os

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5436"))
DB_NAME = os.getenv("DB_NAME", "bankrag")
DB_USER = os.getenv("DB_USER", "bank")
DB_PASSWORD = os.getenv("DB_PASSWORD", "bank")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.1:8b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# Default guardrails mode. Each request can override it with the X-Guardrails header.
GUARDRAILS_DEFAULT = os.getenv("GUARDRAILS", "off").lower() == "on"

API_URL = os.getenv("API_URL", "http://localhost:8001")

TOP_K = 4  # number of chunks retrieved per question
