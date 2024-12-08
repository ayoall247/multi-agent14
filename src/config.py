import os

# Generic LLM Configuration
# Set LLM_API_KEY and LLM_API_BASE in the environment for your chosen platform.
# Adjust the model name to the one provided by Groq:
# e.g., "llama-3.3-70b" if that’s the model name they provide.
# Refer to their docs for the correct model ID.

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_API_BASE = os.environ.get("LLM_API_BASE", "https://api.groq.com/openai/v1/chat/completions")  # default fallback
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE = 0.7

if not LLM_API_KEY:
    raise ValueError("LLM_API_KEY environment variable not set. Please set it before running.")
