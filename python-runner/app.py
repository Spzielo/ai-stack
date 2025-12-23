from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any, List
import logging
import uuid
from core.classifier import classifier
from core.models import ItemType
from core.notifier import notifier

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
        
        # 2. Database Routing
        conn = get_db_connection()
        cur = conn.cursor()
        
        if result.type == ItemType.TASK:
            # Insert into TASKS
            # We use the summary as the title, and the Full content as description.
            query = """
                INSERT INTO tasks (title, description, due_at, created_at)
                VALUES (%s, %s, %s, NOW())
                RETURNING id;
            """
            cur.execute(query, (result.summary, request.content, result.due_date))
            
        else:
            # Insert into NOTES (or Projects as Notes for now)
            # We use the full content as content, and summary as title.
            query = """
                INSERT INTO notes (title, content, created_at)
                VALUES (%s, %s, NOW())
                RETURNING id;
            """
            cur.execute(query, (result.summary, request.content))
            
            # --- RAG SYNC START ---
            # Sync to Qdrant immediately (blocking for now, better async later)
            try:
                # Need to fetch the ID we just created
                # Note: cur.fetchone() is already called below, so we need to grab it carefully
                pass 
            except Exception as vector_err:
                logger.error(f"Vector sync failed: {vector_err}")
            # --- RAG SYNC END ---

        new_id = cur.fetchone()[0]
        
        # Now we have the ID, we can sync
        if result.type != ItemType.TASK:
             from core.vector import vector_store
             vector_store.upsert_note(
                 note_id=str(new_id),
                 content=request.content,
                 metadata={"title": result.summary, "type": result.type.value}
             )

        conn.commit()
        cur.close()
        conn.close()

        # 3. Notification
        emoji = "✅" if result.type == ItemType.TASK else "📝"
        notifier.info(
            f"Captured ({result.type.value.title()})",
            f"{emoji} {result.summary}\n> {result.reasoning}"
        )

        return {
            "id": str(new_id),
            "status": "captured",
            "classification": result.model_dump()
        }

    except Exception as e:
        logger.error(f"Capture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
def chat_completions(request: OpenAIChatRequest):
    # Extract last user message
    user_message = ""
    for m in reversed(request.messages):
        if m.role == "user":
            user_message = m.content
            break
            
    if not user_message:
         user_message = "Hello"

    # Call RAG
    # Note: We ignore history for now, but RAGService could support it later
    result = rag_service.answer(user_message)
    answer_text = result["answer"]
    
    # Append sources to answer (optional, but helpful in UI)
    if result["sources"]:
        answer_text += "\n\n**Sources:**\n"
        for s in result["sources"]:
            title = s.get('title', 'Note')
            # Extract excerpt
            excerpt = s.get('content', '')[:50].replace("\n", " ") + "..."
            answer_text += f"- *{title}*: {excerpt}\n"

    # Format response
    import time
    return {
        "id": "chatcmpl-" + str(uuid.uuid4()),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": answer_text
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": len(user_message),
            "completion_tokens": len(answer_text),
            "total_tokens": len(user_message) + len(answer_text)
        }
    }

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
