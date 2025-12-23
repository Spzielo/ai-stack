from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any, List
import logging
import uuid
import json
import time
from core.classifier import classifier
from core.models import ItemType
from core.notifier import notifier
from core.llm import llm_client

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()

class CaptureRequest(BaseModel):
    content: str

class RunRequest(BaseModel):
    text: str = ""

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ['BRAIN_DB_HOST'],
        database=os.environ['BRAIN_DB_NAME'],
        user=os.environ['BRAIN_DB_USER'],
        password=os.environ['BRAIN_DB_PASSWORD'],
        port=os.environ['BRAIN_DB_PORT']
    )
    return conn

@app.post("/capture")
async def capture(request: CaptureRequest):
    try:
        # 1. Smart Classification
        result = classifier.process(request.content)
        
        # 2. Execute Capture
        item_id = _save_capture(result, request.content)

        # 3. Notification
        emoji = "✅" if result.type == ItemType.TASK else "📝"
        notifier.info(
            f"Captured ({result.type.value.title()})",
            f"{emoji} {result.summary}\n> {result.reasoning}"
        )

        return {
            "id": str(item_id),
            "status": "captured",
            "classification": result.model_dump()
        }

    except Exception as e:
        logger.error(f"Capture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _save_capture(classification: Any, content: str) -> str:
    """Helper to save Task/Note to DB and Vector Store"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if classification.type == ItemType.TASK:
            # Insert into TASKS
            due = classification.due_date
            if due == "N/A" or due == "None": due = None
            
            query = """
                INSERT INTO tasks (title, description, due_at, created_at)
                VALUES (%s, %s, %s, NOW())
                RETURNING id;
            """
            cur.execute(query, (classification.summary, content, due))
            
        else:
            # Insert into NOTES (or Projects/Questions/Chat if misclassified but unlikely here)
            # Default fallback for storage is Note
            query = """
                INSERT INTO notes (title, content, created_at)
                VALUES (%s, %s, NOW())
                RETURNING id;
            """
            cur.execute(query, (classification.summary, content))

        new_id = cur.fetchone()[0]
        conn.commit()
    finally:
        cur.close()
        conn.close()

    # Sync to Qdrant (ONLY if not a Task, though storing tasks in vector store is also good practice later)
    if classification.type != ItemType.TASK:
            try:
                from core.vector import vector_store
                vector_store.upsert_note(
                    note_id=str(new_id),
                    content=content,
                    metadata={"title": classification.summary, "type": classification.type.value}
                )
            except Exception as vector_err:
                logger.error(f"Vector sync failed: {vector_err}")
    
    return new_id

from core.rag import rag_service

@app.post("/run")
def run(request: RunRequest):
    # RAG Chat
    result = rag_service.answer(request.text)
    
    return {
        "message": result["answer"],
        "sources": result["sources"]
    }

# --- OpenAI Adapter ---

@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "second-brain",
                "object": "model",
                "created": 1677610602,
                "owned_by": "user"
            }
        ]
    }

class OpenAIChatMessage(BaseModel):
    role: str
    content: str

class OpenAIChatRequest(BaseModel):
    model: str
    messages: List[OpenAIChatMessage]
    stream: bool = False

@app.post("/v1/chat/completions")
async def chat_completions(request: OpenAIChatRequest):
    # Extract last user message
    user_message = ""
    for m in reversed(request.messages):
        if m.role == "user":
            user_message = m.content
            break
            
    if not user_message:
         user_message = "Hello"

    async def event_generator():
        # 1. Classify (Blocking)
        intent = classifier.process(user_message)
        logger.info(f"Chat Intent: {intent.type} ({intent.confidence})")
        
        request_id = "chatcmpl-" + str(uuid.uuid4())
        created = int(time.time())

        # Helper to yield OpenAI formatted chunk
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

        # 2. Branch & Stream
        if intent.type in [ItemType.TASK, ItemType.NOTE, ItemType.PROJECT]:
            # WRITE PATH (Capture) - Not streamed usually, but we simulate it or just send one chunk
            try:
                _save_capture(intent, user_message)
                emoji = "✅" if intent.type == ItemType.TASK else "📝"
                type_fr = "Tâches" if intent.type == ItemType.TASK else "Notes"
                msg = f"{emoji} Enregistré dans tes {type_fr} : **{intent.summary}**"
                notifier.info(f"Capture Chat ({intent.type.value})", intent.summary)
                
                # Yield the success message
                yield yield_chunk(msg)
                
            except Exception as e:
                yield yield_chunk(f"❌ Erreur : {str(e)}")

        elif intent.type == ItemType.CHAT:
            # CONVERSATION PATH (Streamed)
            for chunk in llm_client.chat_stream(user_message):
                 yield yield_chunk(chunk)

        elif intent.type == ItemType.DELETE:
            # DELETION PATH
            # Not streamed, instant result
            msg = _delete_item(intent.summary)
            yield yield_chunk(msg)

        else:
            # READ PATH (RAG Streamed)
            for chunk in rag_service.answer_stream(user_message):
                yield yield_chunk(chunk)
                
        # End stream
        yield yield_chunk(None, finish_reason="stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

from core.reviewer import reviewer

@app.post("/review/daily")
def daily_review():
    try:
        data = reviewer.generate_briefing()
        
        # Format for Slack
        stats = data["stats"]
        tasks = data["tasks"]
        notes = data["notes"]
        
        message = f"*Daily Briefing* 🌅\n"
        message += f"Tu as *{stats['pending_tasks']} tâches* en attente et tu as pris *{stats['new_notes']} notes* ces dernières 24h.\n\n"
        
        if tasks:
            message += "*Priorités :*\n"
            for t in tasks:
                prio = "🔥" if t['priority'] > 2 else "•"
                message += f"{prio} {t['title']}\n"
        
        if notes:
            message += "\n*Pensées récentes :*\n"
            for n in notes:
                message += f"📝 {n['title']}\n"
                
        # Send Notification
        notifier.info("Daily Review", message)
        
        return {"status": "sent", "data": data}

    except Exception as e:
        logger.error(f"Review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _delete_item(query: str) -> str:
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
    from core.vector import vector_store
    deleted_content = vector_store.delete_similar(query)
    
    if deleted_content:
        return f"🗑️ Note supprimée : **{deleted_content}**"
    
    return "❌ Je n'ai rien trouvé de correspondant à supprimer."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
