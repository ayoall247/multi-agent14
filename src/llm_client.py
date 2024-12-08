import requests
from typing import List, Dict
from .config import LLM_API_KEY, LLM_API_BASE, DEFAULT_MODEL, DEFAULT_TEMPERATURE

class LLMClient:
    """
    Generic LLM client assuming an OpenAI-compatible chat completion endpoint.
    """

    def __init__(self, api_key: str = LLM_API_KEY, base_url: str = LLM_API_BASE):
        if not api_key:
            raise ValueError("LLM_API_KEY not set. Please set it in environment.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def chat_completion(self, messages: List[Dict[str, str]], model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE) -> str:
        """
        messages = [
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "Hello!"}
        ]
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        res = response.json()
        return res["choices"][0]["message"]["content"]
