import os
from dotenv import load_dotenv

load_dotenv()

# LLM Provider: "openai" or "gemini"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Google Gemini settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")