"""
Core Data Models
core/models.py
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field
import uuid

# --- Enums ---

class Source(str, Enum):
    """Origin of the capture."""
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    EMAIL = "email"
    IMESSAGE = "imessage"
    CALL = "call"
    MANUAL = "manual"
    SHORTCUT = "shortcut"

class ItemType(str, Enum):
    """Type of item after clarification."""
    TASK = "task"           # Action to do
    EVENT = "event"         # Calendar event
    PROJECT = "project"     # Multi-step
    NOTE = "note"           # Information to keep
    REFERENCE = "reference" # Archive
    QUESTION = "question"   # Info request (RAG)
    CHAT = "chat"           # Casual
    DELETE = "delete"       # Deletion request
    UNKNOWN = "unknown"     # Needs clarification

class Priority(str, Enum):
    """Priority Level."""
    CRITICAL = "critical"   # Today, non-negotiable
    HIGH = "high"           # This week
    NORMAL = "normal"       # This month
    LOW = "low"             # Someday
    NONE = "none"           # Unassigned

class Urgency(str, Enum):
    """Perceived Urgency."""
    IMMEDIATE = "immediate"  # Now
    TODAY = "today"          # EOD
    SOON = "soon"            # Few days
    SOMETIME = "sometime"    # No pressure
    UNKNOWN = "unknown"

class DecisionType(str, Enum):
    """Types of decisions."""
    CLARIFICATION = "clarification"
    CONFLICT = "conflict"
    DELEGATION = "delegation"
    PRIORITIZATION = "prioritization"
    GO_NO_GO = "go_no_go"

# --- Models ---

class Context(BaseModel):
    """Metadata for capture."""
    captured_at: datetime = Field(default_factory=datetime.now)
    sender: Optional[str] = None
    urgency: Urgency = Urgency.UNKNOWN
    raw_source: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class Capture(BaseModel):
    """Raw input into the system."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: Source
    content: str
    context: Context = Field(default_factory=Context)

class ClarifiedItem(BaseModel):
    """Processed item ready for prioritization."""
    id: str
    item_type: ItemType
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.NONE
    due_date: Optional[datetime] = None
    source_capture: Optional[Capture] = None
    suggested_actions: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    needs_human_decision: bool = False
    decision_context: Optional[str] = None
    
    # Aliases for backward compatibility in logic
    @property
    def type(self): return self.item_type
    @property
    def summary(self): return self.title
    @property
    def reasoning(self): return self.decision_context or ""

class Decision(BaseModel):
    """Decision prepared for human."""
    id: str
    question: str
    options: List[str]
    recommendation: Optional[str] = None
    reasoning: Optional[str] = None
    deadline: Optional[datetime] = None
    related_items: List[str] = Field(default_factory=list)

# --- Legacy / LLM Specific ---

class ClassificationResult(BaseModel):
    """Structure for LLM Output (kept for core.llm compatibility)."""
    type: ItemType
    summary: str = Field(description="A concise summary of the content in French")
    confidence: float
    reasoning: str
    due_date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD or None")
    
    class Config:
        extra = "ignore"
