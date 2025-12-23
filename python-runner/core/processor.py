"""
Capture Processor — Clarification and Structuring.
core/processor.py

Merges Regex Heuristics with LLM Intelligence.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional

from core.models import (
    Capture, ClarifiedItem, ItemType, Priority, Urgency, ClassificationResult
)
from core.llm import llm_client

logger = logging.getLogger(__name__)

class CaptureProcessor:
    """
    Rational Brain: Clarify and Structure.
    """

    # User's Patterns for Urgency detection (LLM doesn't do this well yet)
    URGENCY_KEYWORDS = {
        Urgency.IMMEDIATE: ["urgent", "asap", "maintenant", "immédiat", "critique"],
        Urgency.TODAY: ["aujourd'hui", "ce soir", "avant ce soir"],
        Urgency.SOON: ["cette semaine", "bientôt", "rapidement", "dès que possible"],
    }

    def process(self, capture: Capture) -> ClarifiedItem:
        """
        Main pipeline.
        1. LLM Classification (Type, Title, Date)
        2. Heuristic Enhancement (Urgency, Priority)
        """
        content = capture.content
        logger.info(f"Processing capture: {content[:30]}...")

        # 1. LLM Intelligence
        llm_result = llm_client.classify(content, ClassificationResult)
        
        if llm_result:
            # Trust LLM for fundamental structure
            item_type = llm_result.type
            title = llm_result.summary
            confidence = llm_result.confidence
            
            # Parse LLM date
            due_date = None
            if llm_result.due_date and llm_result.due_date not in ["None", "N/A"]:
                try:
                    due_date = datetime.fromisoformat(llm_result.due_date)
                except:
                    pass
        else:
            # Fallback if LLM fails
            item_type = ItemType.NOTE
            title = content[:80]
            confidence = 0.5
            due_date = None

        # 2. Heuristic Enrichment (Urgency logic provided by user)
        # We use the raw content for keyword matching
        urgency = self._detect_urgency(content.lower())
        
        # 3. Compute Priority based on Urgency + Context
        priority = self._compute_priority(urgency)
        
        # 4. Decision Need
        # If confidence is low or unknown type, flag for decision
        needs_decision = (confidence < 0.7) or (item_type == ItemType.UNKNOWN)

        # 5. Suggest Actions
        clarified = ClarifiedItem(
            id=capture.id,
            item_type=item_type,
            title=title,
            description=content,
            priority=priority,
            due_date=due_date,
            source_capture=capture,
            confidence=confidence,
            needs_human_decision=needs_decision,
            decision_context=llm_result.reasoning if llm_result else "Fallback processing"
        )
        
        clarified.suggested_actions = self._suggest_actions(clarified)
        
        return clarified

    def _detect_urgency(self, content: str) -> Urgency:
        """Detect urgency keywords."""
        for urgency, keywords in self.URGENCY_KEYWORDS.items():
            if any(kw in content for kw in keywords):
                return urgency
        return Urgency.UNKNOWN

    def _compute_priority(self, urgency: Urgency) -> Priority:
        """Map urgency to priority."""
        urgency_to_priority = {
            Urgency.IMMEDIATE: Priority.CRITICAL,
            Urgency.TODAY: Priority.HIGH,
            Urgency.SOON: Priority.NORMAL,
            Urgency.SOMETIME: Priority.LOW,
            Urgency.UNKNOWN: Priority.NONE,
        }
        return urgency_to_priority.get(urgency, Priority.NONE)

    def _suggest_actions(self, item: ClarifiedItem) -> list[str]:
        """Suggest actions based on type."""
        actions = []
        if item.item_type == ItemType.TASK:
            actions.append("Ajouter à la liste de tâches")
            if item.priority == Priority.CRITICAL:
                actions.append("Faire maintenant")
        elif item.item_type == ItemType.EVENT:
            actions.append("Ajouter au calendrier")
        elif item.item_type == ItemType.NOTE:
            actions.append("Archiver")
        elif item.item_type == ItemType.QUESTION:
            actions.append("Rechercher réponse")
            
        return actions

processor = CaptureProcessor()
