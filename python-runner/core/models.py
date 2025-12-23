"""
Data Models
core/models.py
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class ItemType(str, Enum):
    TASK = "task"
    NOTE = "note"
    PROJECT = "project"
    QUESTION = "question" # Providing info vs Asking info
    CHAT = "chat"         # Casual conversation
    DELETE = "delete"

class ClassificationResult(BaseModel):
    """Structure for LLM Output"""
    type: ItemType = Field(..., description="The type of the item: task (actionable), note (info), or project (multi-step).")
    summary: str = Field(..., description="A concise summary or title of the item.")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    due_date: Optional[str] = Field(None, description="Extracted due date if mentioned (ISO format or descriptive).")
    tags: list[str] = Field(default_factory=list, description="Relevant tags/keywords.")
    reasoning: str = Field(..., description="Brief explanation of why this classification was chosen.")

