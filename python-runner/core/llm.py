"""
LLM Client Wrapper
core/llm.py

Handles interaction with OpenAI API.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self._api_key = os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            logger.warning("OPENAI_API_KEY not found. LLM features disabled.")
            self._client = None
        else:
            self._client = OpenAI(api_key=self._api_key)
            
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def is_ready(self) -> bool:
        return self._client is not None

    def classify(self, text: str, response_model: Type[BaseModel]) -> Optional[BaseModel]:
        """
        Classifies text using Structured Outputs (JSON Schema).
        Returns an instance of the provided Pydantic model.
        """
        if not self.is_ready():
            logger.error("LLM not ready.")
            return None

        try:
            completion = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": "You are a GTD (Getting Things Done) expert. Analyze the user's input and classify it accurately."},
                    {"role": "user", "content": text},
                ],
                response_format=response_model,
            )
            
            result = completion.choices[0].message.parsed
            return result

        except Exception as e:
            logger.error(f"LLM Classification failed: {e}")
            return None

# Singleton
llm_client = LLMClient()
