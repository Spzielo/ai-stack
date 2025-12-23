"""
Decision Engine — Prepares human decisions.
core/decisions.py
"""

import logging
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from core.models import ClarifiedItem, Decision, Priority, DecisionType

logger = logging.getLogger(__name__)

class DecisionContext(BaseModel):
    """Enriched decision context."""
    related_items: List[ClarifiedItem] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    past_decisions: List[str] = Field(default_factory=list)

class DecisionEngine:
    """
    Engine for preparing human decisions.
    """

    def needs_decision(self, item: ClarifiedItem) -> bool:
        reasons = []
        if item.confidence < 0.7: reasons.append("confiance_faible")
        if item.priority == Priority.CRITICAL: reasons.append("priorité_critique")
        if item.needs_human_decision: reasons.append("marqué_pour_décision")
        return len(reasons) > 0

    def prepare(
        self, 
        item: ClarifiedItem, 
        decision_type: DecisionType = DecisionType.CLARIFICATION,
        context: Optional[DecisionContext] = None
    ) -> Decision:
        context = context or DecisionContext()
        
        question = self._formulate_question(item, decision_type)
        options = self._generate_options(item, decision_type)
        recommendation = self._make_recommendation(item, decision_type, context)
        reasoning = self._build_reasoning(item, decision_type, context)
        
        decision = Decision(
            id=f"dec-{item.id}",
            question=question,
            options=options,
            recommendation=recommendation,
            reasoning=reasoning,
            related_items=[item.id],
        )
        
        if item.due_date:
            decision.deadline = item.due_date - timedelta(days=1)
        
        logger.info(f"Decision prepared: {decision.id} ({decision_type.value})")
        return decision

    def _formulate_question(self, item: ClarifiedItem, dtype: DecisionType) -> str:
        templates = {
            DecisionType.CLARIFICATION: f"Comment dois-je traiter : « {item.title} » ?",
            DecisionType.GO_NO_GO: f"Dois-je avancer sur : « {item.title} » ?",
            DecisionType.DELEGATION: f"Qui doit s'occuper de : « {item.title} » ?",
            DecisionType.PRIORITIZATION: f"Quelle priorité pour : « {item.title} » ?",
            DecisionType.CONFLICT: f"Comment résoudre le conflit pour : « {item.title} » ?",
        }
        return templates.get(dtype, f"Que faire avec : « {item.title} » ?")

    def _generate_options(self, item: ClarifiedItem, dtype: DecisionType) -> List[str]:
        if dtype == DecisionType.CLARIFICATION:
            return [
                "C'est une tâche → ajouter aux rappels",
                "C'est un événement → ajouter au calendrier",
                "C'est une note → archiver",
                "Ignorer / supprimer",
            ]
        elif dtype == DecisionType.GO_NO_GO:
            return ["Go ✅", "No-go ❌", "Reporter", "Besoin de plus d'infos"]
        elif dtype == DecisionType.DELEGATION:
             return ["Je le fais", "Déléguer", "Automatiser", "Supprimer"]
        elif dtype == DecisionType.PRIORITIZATION:
            return ["Critique", "Haute", "Normale", "Basse"]
        return ["Oui", "Non", "Reporter"]

    def _make_recommendation(
        self, 
        item: ClarifiedItem, 
        dtype: DecisionType,
        context: DecisionContext
    ) -> Optional[str]:
        if item.confidence >= 0.8 and dtype == DecisionType.CLARIFICATION:
            return item.suggested_actions[0] if item.suggested_actions else None
        return None

    def _build_reasoning(
        self, 
        item: ClarifiedItem, 
        dtype: DecisionType,
        context: DecisionContext
    ) -> str:
        parts = []
        parts.append(f"Type détecté : {item.item_type.value}")
        parts.append(f"Confiance : {item.confidence:.0%}")
        if item.due_date:
            parts.append(f"Échéance : {item.due_date.strftime('%d/%m/%Y')}")
        if item.priority != Priority.NONE:
            parts.append(f"Priorité : {item.priority.value}")
        if context.constraints:
            parts.append(f"Contraintes : {', '.join(context.constraints)}")
        return "\n".join(parts)

decision_engine = DecisionEngine()
