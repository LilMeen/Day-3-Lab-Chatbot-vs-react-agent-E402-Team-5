import os
from pathlib import Path
from dotenv import load_dotenv

_BASE_DIR = Path(__file__).resolve().parent
_ENV_PATH = _BASE_DIR / ".env"

# Force loading ai-services/.env and override inherited shell/system env values.
load_dotenv(dotenv_path=_ENV_PATH, override=True)

def _normalized_provider(raw_provider: str) -> str:
	value = (raw_provider or "").strip().lower()
	if value in {"openai", "gemini"}:
		return value
	return "openai"

# LLM Provider: "openai" or "gemini"
LLM_PROVIDER = _normalized_provider(os.getenv("LLM_PROVIDER", "openai"))

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Google Gemini settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Google Custom Search API (for compare_ticket_prices across cinemas)
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")