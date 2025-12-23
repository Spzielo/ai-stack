"""
Brain — Central Orchestrator.
core/brain.py
"""

import logging
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from core.models import Capture, ClarifiedItem, Decision, Source, Context, ItemType
from core.processor import processor
from core.prioritizer import prioritizer, UserContext
from core.decisions import decision_engine, DecisionType
from core.notifier import notifier
from core.db import get_db_connection
from core.vector import vector_store

logger = logging.getLogger(__name__)

@dataclass
class BrainState:
    """Internal state."""
    pending_items: List[ClarifiedItem] = field(default_factory=list)
    pending_decisions: List[Decision] = field(default_factory=list)
    processed_today: int = 0
    last_review: Optional[datetime] = None

class Brain:
    """
    The Central Brain.
    Orchestrates ingestion, clarification, prioritization, and storage.
    """

    def __init__(self):
        self.state = BrainState()

    def ingest(self, capture: Capture) -> ClarifiedItem:
        logger.info(f"Ingestion capture [{capture.source.value}]: {capture.content[:50]}...")
        
        # 1. Clarifier
        item = processor.process(capture)
        
        # 2. Scorer
        score = prioritizer.score(item)
        logger.info(f"Priority Score: {score:.1f}/100")
        
        # 3. Decision Needed?
        if decision_engine.needs_decision(item):
            decision = decision_engine.prepare(item)
            self.state.pending_decisions.append(decision)
            self._notify_decision_needed(decision)
        
        # 4. Notify if Urgent
        if score >= 80:
            self._notify_urgent_item(item, score)
        
        # 5. Persist (DB + Vector)
        self._persist_item(item, capture.content)

        # 6. Update State
        self.state.pending_items.append(item)
        self.state.processed_today += 1
        
        return item

    def ingest_raw(
        self, 
        content: str, 
        source: Source = Source.MANUAL,
        sender: Optional[str] = None
    ) -> ClarifiedItem:
        """Shortcut for raw input."""
        capture = Capture(
            source=source,
            content=content,
            context=Context(sender=sender)
        )
        return self.ingest(capture)
    
    def get_today_focus(self, n: int = 3) -> List[ClarifiedItem]:
        return prioritizer.top_actions(self.state.pending_items, n=n)

    def daily_review(self) -> dict:
        attention = prioritizer.needs_attention_today(self.state.pending_items)
        focus = self.get_today_focus()
        decisions = self.state.pending_decisions
        
        review = {
            "date": datetime.now().isoformat(),
            "needs_attention": len(attention),
            "focus_items": [i.title for i in focus],
            "pending_decisions": len(decisions),
            "total_pending": len(self.state.pending_items),
        }
        
        self.state.last_review = datetime.now()
        
        if focus or attention:
            notifier.info(
                "📋 Revue quotidienne",
                f"{len(attention)} items urgents\n"
                f"{len(decisions)} décisions en attente\n"
                f"Focus: {focus[0].title if focus else 'Aucun'}"
            )
        
        return review

    def resolve_decision(self, decision_id: str, chosen_option: str) -> bool:
        for i, dec in enumerate(self.state.pending_decisions):
            if dec.id == decision_id:
                logger.info(f"Decision {decision_id} resolved: {chosen_option}")
                self.state.pending_decisions.pop(i)
                return True
        return False

    def _notify_decision_needed(self, decision: Decision) -> None:
        notifier.warning(
            "🧠 Décision requise",
            f"{decision.question}\n"
            f"Options: {', '.join(decision.options[:2])}..."
        )

    def _notify_urgent_item(self, item: ClarifiedItem, score: float) -> None:
        notifier.warning(
            f"⚡ Urgent ({score:.0f}/100)",
            f"{item.title}\n"
            f"→ {item.suggested_actions[0] if item.suggested_actions else 'Action requise'}"
        )

    def _persist_item(self, item: ClarifiedItem, content: str):
        """Saves item to Postgres and Vector Store."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            if item.item_type == ItemType.TASK:
                query = """
                    INSERT INTO tasks (title, description, due_at, created_at)
                    VALUES (%s, %s, %s, NOW())
                    RETURNING id;
                """
                # item.due_date is already a datetime or None from Pydantic
                cur.execute(query, (item.title, content, item.due_date))
                
            else:
                # Default logic: Note
                query = """
                    INSERT INTO notes (title, content, created_at)
                    VALUES (%s, %s, NOW())
                    RETURNING id;
                """
                cur.execute(query, (item.title, content))

            new_id = cur.fetchone()[0]
            conn.commit()
            
            # Sync to Qdrant (Everything except tasks, typically)
            if item.item_type != ItemType.TASK:
                try:
                    vector_store.upsert_note(
                        note_id=str(new_id),
                        content=content,
                        metadata={
                            "title": item.title, 
                            "type": item.item_type.value,
                            "priority": item.priority.value
                        }
                    )
                except Exception as vector_err:
                    logger.error(f"Vector sync failed: {vector_err}")
                    
        except Exception as e:
            logger.error(f"Persistence failed: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    def delete_item(self, query: str) -> str:
        """Tries to delete Task first, then Note."""
        logger.info(f"Attempting deletion for query: '{query}'")
        
        # 1. Try Task (SQL)
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Fuzzy match task title
            search_sql = "SELECT id, title FROM tasks WHERE title ILIKE %s LIMIT 1;"
            cur.execute(search_sql, (f"%{query}%",))
            row = cur.fetchone()
            
            if row:
                task_id, title = row
                del_sql = "DELETE FROM tasks WHERE id = %s;"
                cur.execute(del_sql, (task_id,))
                conn.commit()
                conn.close()
                return f"🗑️ Tâche supprimée : **{title}**"
                
        except Exception as e:
            logger.error(f"SQL Delete failed: {e}")
            conn.rollback()
        finally:
            if not cur.closed: cur.close()
            if not conn.closed: conn.close()
            
        # 2. Try Note (Vector)
        # Assuming vector_store is imported at module level
        deleted_content = vector_store.delete_similar(query)
        
        if deleted_content:
            return f"🗑️ Note supprimée : **{deleted_content}**"
        
        return "❌ Je n'ai rien trouvé de correspondant à supprimer."

brain = Brain()
