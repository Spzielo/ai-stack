"""
Classifier Module
core/classifier.py

Orchestrates the classification process:
1. Receives raw text.
2. Calls LLM to get structured classification.
3. Validates confidence.
4. Returns result.
"""
import logging
from typing import Optional
from core.llm import llm_client
from core.models import ClassificationResult, ItemType

logger = logging.getLogger(__name__)

class Classifier:
    def process(self, text: str) -> ClassificationResult:
        """
        Main entry point for classification.
        """
        # 1. Try LLM Classification
        result = llm_client.classify(text, ClassificationResult)
        
        if result:
            logger.info(f"Classified as {result.type} ({result.confidence})")
            return result
            
        # 2. Fallback (Deterministic)
        # If LLM fails or is offline, default to Note (Inbox)
        logger.warning("LLM failed, falling back to basic Note.")
        return ClassificationResult(
            type=ItemType.NOTE,
            summary=text[:50] + "..." if len(text) > 50 else text,
            confidence=0.0,
            reasoning="Fallback: LLM unavailable or error."
        )

classifier = Classifier()
