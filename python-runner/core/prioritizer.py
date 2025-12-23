"""
Prioritizer — Rational Prioritization Logic.
core/prioritizer.py
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel

from core.models import ClarifiedItem, Priority, ItemType

logger = logging.getLogger(__name__)

class UserContext(BaseModel):
    """User context for prioritization."""
    current_energy: str = "normal"  # low | normal | high
    available_hours_today: float = 8.0
    is_deep_work_time: bool = False
    focus_project: Optional[str] = None

class Prioritizer:
    """
    Rational Prioritization Engine.
    """

    WEIGHTS = {
        "deadline": 0.4,
        "priority": 0.3,
        "type": 0.2,
        "confidence": 0.1,
    }

    def score(self, item: ClarifiedItem, context: Optional[UserContext] = None) -> float:
        context = context or UserContext()
        
        deadline_score = self._score_deadline(item.due_date)
        priority_score = self._score_priority(item.priority)
        type_score = self._score_type(item.item_type)
        confidence_score = item.confidence * 100
        
        total = (
            self.WEIGHTS["deadline"] * deadline_score +
            self.WEIGHTS["priority"] * priority_score +
            self.WEIGHTS["type"] * type_score +
            self.WEIGHTS["confidence"] * confidence_score
        )
        
        total = self._apply_context_modifiers(total, item, context)
        
        return min(100, max(0, total))

    def rank(
        self, 
        items: List[ClarifiedItem], 
        context: Optional[UserContext] = None,
        limit: Optional[int] = None
    ) -> List[tuple[ClarifiedItem, float]]:
        
        scored = [(item, self.score(item, context)) for item in items]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        if limit:
            scored = scored[:limit]
            
        return scored

    def top_actions(
        self, 
        items: List[ClarifiedItem], 
        context: Optional[UserContext] = None,
        n: int = 3
    ) -> List[ClarifiedItem]:
        
        tasks = [i for i in items if i.item_type == ItemType.TASK]
        ranked = self.rank(tasks, context, limit=n)
        return [item for item, _ in ranked]

    def needs_attention_today(self, items: List[ClarifiedItem]) -> List[ClarifiedItem]:
        today = datetime.now().date()
        
        urgent = []
        for item in items:
            if item.due_date and item.due_date.date() <= today:
                urgent.append(item)
            elif item.priority == Priority.CRITICAL:
                urgent.append(item)
            elif item.needs_human_decision:
                urgent.append(item)
                
        return urgent

    def _score_deadline(self, due_date: Optional[datetime]) -> float:
        if not due_date:
            return 30
            
        now = datetime.now()
        delta = (due_date - now).total_seconds() / 3600
        
        if delta < 0: return 100
        if delta < 24: return 90
        if delta < 72: return 70
        if delta < 168: return 50
        return 30

    def _score_priority(self, priority: Priority) -> float:
        mapping = {
            Priority.CRITICAL: 100,
            Priority.HIGH: 75,
            Priority.NORMAL: 50,
            Priority.LOW: 25,
            Priority.NONE: 10,
        }
        return mapping.get(priority, 10)

    def _score_type(self, item_type: ItemType) -> float:
        mapping = {
            ItemType.TASK: 80,
            ItemType.EVENT: 70,
            ItemType.PROJECT: 60,
            ItemType.NOTE: 30,
            ItemType.REFERENCE: 20,
            ItemType.UNKNOWN: 50,
        }
        return mapping.get(item_type, 50)

    def _apply_context_modifiers(
        self, 
        score: float, 
        item: ClarifiedItem, 
        context: UserContext
    ) -> float:
        if context.current_energy == "low":
            if "complexe" in (item.title + str(item.description)).lower():
                score *= 0.7
                
        if context.focus_project:
            if context.focus_project.lower() in item.title.lower():
                score *= 1.3
                
        if context.is_deep_work_time:
            if item.item_type == ItemType.TASK:
                score *= 1.2
            elif item.item_type == ItemType.NOTE:
                score *= 0.5
                
        return score

prioritizer = Prioritizer()
