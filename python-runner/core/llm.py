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
        self._api_key = os.getenv("OPENAI_API_KEY", "ollama") # Default to 'ollama' if missing
        self._base_url = os.getenv("LLM_BASE_URL") # e.g. http://host.docker.internal:11434/v1
        
        if self._base_url:
             logger.info(f"Using Custom LLM Provider at {self._base_url}")
             self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        else:
             if not self._api_key or self._api_key == "ollama":
                  logger.warning("OPENAI_API_KEY not found and no LLM_BASE_URL. LLM features disabled.")
                  self._client = None
             else:
                  self._client = OpenAI(api_key=self._api_key)
            
        self._model = os.getenv("LLM_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o"))

    def is_ready(self) -> bool:
        return self._client is not None

    def classify(self, text: str, response_model: Type[BaseModel]) -> Optional[BaseModel]:
        """
        Classifies text. Adapts to model capabilities:
        1. Tries strict Structured Outputs (best for OpenAI).
        2. Fallback to JSON Mode (best for Ollama/Local).
        3. Fallback to Raw parsing.
        """
        if not self.is_ready():
            logger.error("LLM not ready.")
            return None

        messages = [
            {"role": "system", "content": "You are a GTD expert. Classify the following input. Return ONLY Valid JSON."},
            {"role": "user", "content": text},
        ]

        # Attempt 1: Strict Structured Output (OpenAI / Latest Ollama)
        try:
            completion = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=messages,
                response_format=response_model,
            )
            return completion.choices[0].message.parsed
        except Exception as e:
            logger.warning(f"Strict parsing failed ({e}). Trying standard JSON mode...")

        # Attempt 2: Standard JSON Mode (Ollama fallback)
        try:
            # We need to manually construct the schema prompt or just ask for JSON
            # For simplicity in this fallback, we just ask for JSON format
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            raw_json = completion.choices[0].message.content
            return response_model.model_validate_json(raw_json)
        except Exception as e:
            logger.error(f"JSON mode failed ({e}). classification aborted.")
            return None

# Singleton
llm_client = LLMClient()
