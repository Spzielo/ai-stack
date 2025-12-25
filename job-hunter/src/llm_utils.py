import os
from openai import OpenAI
from typing import Optional, Dict, Any
import json

class LLMService:
    def __init__(self):
        # We assume OPENAI_API_KEY is compatible with whatever provider is used (Ollama/OpenAI)
        # If using Ollama, we might need base_url
        self.base_url = os.getenv("LLM_BASE_URL", "http://host.docker.internal:11434/v1") 
        self.api_key = os.getenv("LLM_API_KEY", "ollama")
        self.model = os.getenv("LLM_MODEL", "llama3.2")
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def extract_json(self, system_prompt: str, user_text: str, model_class: Any = None) -> Dict[str, Any]:
        """
        Extracts structured JSON from text using the LLM.
        If model_class is provided (Pydantic), it can be used for schema validation (if supported by provider)
        or just to guide the prompt.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt + "\nRespond ONLY with valid JSON."},
                    {"role": "user", "content": user_text}
                ],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {}
