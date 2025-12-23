"""
API Gateway.
app.py

Central entry point acting as a Gateway to the Brain.
"""

import logging
import uuid
import json
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.brain import brain
from core.models import Source, ItemType
from core.llm import llm_client
from core.rag import rag_service
from core.classifier import classifier # Still used for Chat vs RAG routing high level?
# Actually, we can use the brain's processor or keep strict routing here.
# For chat, we need to know: Is it a command (Capture) or a Conversation?
# The Brain is good at extracting items.
# Let's keep the existing Classifier for the "Chat Router" part as it differentiates Conversation/Question/Action well.

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Brain API")

# --- Models ---

class CaptureRequest(BaseModel):
    """Raw capture from n8n/shortcuts."""
    source: str = "manual"
    content: str
    sender: Optional[str] = None

class CaptureResponse(BaseModel):
    """Response after brain processing."""
    id: str
    item_type: str
    title: str
    priority: str
    confidence: float
    needs_decision: bool
    suggested_actions: List[str]

class RunRequest(BaseModel):
    text: str = ""

# --- OpenAI Models ---
class OpenAIChatMessage(BaseModel):
    role: str
    content: str

class OpenAIChatRequest(BaseModel):
    model: str
    messages: List[OpenAIChatMessage]
    stream: bool = False


# --- Endpoints ---

@app.post("/capture", response_model=CaptureResponse)
async def capture(request: CaptureRequest):
    """
    Direct input to the Brain.
    """
    try:
        try:
            source_enum = Source(request.source.lower())
        except ValueError:
            source_enum = Source.MANUAL

        item = brain.ingest_raw(
            content=request.content,
            source=source_enum,
            sender=request.sender
        )
        
        return CaptureResponse(
            id=item.id,
            item_type=item.item_type.value,
            title=item.title,
            priority=item.priority.value,
            confidence=item.confidence,
            needs_decision=item.needs_human_decision,
            suggested_actions=item.suggested_actions,
        )

    except Exception as e:
        logger.error(f"Capture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/review")
async def daily_review():
    """Trigger daily review generation."""
    return brain.daily_review()


@app.post("/v1/chat/completions")
async def chat_completions(request: OpenAIChatRequest):
    """
    Smart Router handling Chat, RAG, and Capture via Natural Language.
    """
    user_message = ""
    for m in reversed(request.messages):
        if m.role == "user":
            user_message = m.content
            break
    if not user_message: user_message = "Hello"

    async def event_generator():
        # 1. Router Classification (using existing high-level classifier)
        # We classify intent first: Chat vs Action vs Knowledge
        intent = classifier.process(user_message)
        logger.info(f"Chat Intent: {intent.type} ({intent.confidence})")
        
        request_id = "chatcmpl-" + str(uuid.uuid4())
        created = int(time.time())

        def yield_chunk(content, finish_reason=None):
            chunk = {
                "id": request_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": content} if content else {},
                    "finish_reason": finish_reason
                }]
            }
            return f"data: {json.dumps(chunk)}\n\n"

        # 2. Branching
        if intent.type in [ItemType.TASK, ItemType.NOTE, ItemType.PROJECT]:
            # WRITE PATH (Capture via Brain)
            try:
                # Ingest into Brain
                item = brain.ingest_raw(content=user_message, source=Source.MANUAL)
                
                emoji = "✅" if item.item_type == ItemType.TASK else "📝"
                msg = f"{emoji} Capturé : **{item.title}**\n_{item.item_type.value.title()} - Priorité : {item.priority.value}_"
                
                yield yield_chunk(msg)
                
            except Exception as e:
                yield yield_chunk(f"❌ Erreur : {str(e)}")

        elif intent.type == ItemType.CHAT:
            # CONVERSATION PATH
            for chunk in llm_client.chat_stream(user_message):
                 yield yield_chunk(chunk)

        elif intent.type == ItemType.DELETE:
            # DELETION PATH (Delegated to Brain)
            msg = brain.delete_item(intent.summary)
            yield yield_chunk(msg)

        else:
            # READ PATH (RAG)
            # Question answering
            for chunk in rag_service.answer_stream(user_message):
                yield yield_chunk(chunk)
                
        # End stream
        yield yield_chunk(None, finish_reason="stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- OpenAI Adapter Models List ---
@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [{"id": "second-brain", "object": "model", "created": 1677610602, "owned_by": "user"}]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
