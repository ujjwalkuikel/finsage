from abc import ABC, abstractmethod
import json
import httpx
from app.core import config

class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, json_mode: bool = False, system_instruction: str = None) -> str:
        """Generates a text completion from the LLM."""
        pass
        
    @abstractmethod
    def get_embedding(self, text: str) -> list[float]:
        """Generates a vector embedding for the input text."""
        pass


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def generate(self, prompt: str, json_mode: bool = False, system_instruction: str = None) -> str:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        params = {"key": self.api_key}
        
        system_instruction_part = {}
        if system_instruction:
            system_instruction_part = {
                "system_instruction": {
                    "parts": [{"text": system_instruction}]
                }
            }
            
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            **system_instruction_part
        }
        
        if json_mode:
            payload["generationConfig"] = {"responseMimeType": "application/json"}
            
        headers = {"Content-Type": "application/json"}
        
        response = httpx.post(url, params=params, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        
        res_json = response.json()
        try:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected response structure from Gemini: {res_json}") from e
            
    def get_embedding(self, text: str) -> list[float]:
        url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
        params = {"key": self.api_key}
        payload = {
            "model": "models/text-embedding-004",
            "content": {
                "parts": [{"text": text}]
            }
        }
        headers = {"Content-Type": "application/json"}
        
        response = httpx.post(url, params=params, json=payload, headers=headers, timeout=20.0)
        response.raise_for_status()
        
        res_json = response.json()
        try:
            return res_json["embedding"]["values"]
        except (KeyError, TypeError) as e:
            raise ValueError(f"Unexpected response structure from Gemini Embedding: {res_json}") from e


class GroqClient(BaseLLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def generate(self, prompt: str, json_mode: bool = False, system_instruction: str = None) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "llama3-70b-8192",
            "messages": messages,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
            
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        
        res_json = response.json()
        return res_json["choices"][0]["message"]["content"]
        
    def get_embedding(self, text: str) -> list[float]:
        raise NotImplementedError("Embeddings are not supported by the Groq client.")


class CerebrasClient(BaseLLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def generate(self, prompt: str, json_mode: bool = False, system_instruction: str = None) -> str:
        url = "https://api.cerebras.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "llama3.1-70b",
            "messages": messages,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
            
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        
        res_json = response.json()
        return res_json["choices"][0]["message"]["content"]
        
    def get_embedding(self, text: str) -> list[float]:
        raise NotImplementedError("Embeddings are not supported by the Cerebras client.")


def get_llm_client() -> BaseLLMClient:
    """Factory to retrieve the appropriate LLM client based on configuration."""
    if config.GEMINI_API_KEY:
        return GeminiClient(config.GEMINI_API_KEY)
    elif config.GROQ_API_KEY:
        return GroqClient(config.GROQ_API_KEY)
    elif config.CEREBRAS_API_KEY:
        return CerebrasClient(config.CEREBRAS_API_KEY)
    else:
        raise ValueError("No LLM API keys configured (GEMINI_API_KEY, GROQ_API_KEY, or CEREBRAS_API_KEY must be set).")


def call_llm(prompt: str, json_mode: bool = False, system_instruction: str = None) -> str:
    """Helper function for backward compatibility."""
    client = get_llm_client()
    return client.generate(prompt, json_mode, system_instruction)
