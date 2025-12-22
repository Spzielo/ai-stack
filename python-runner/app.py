from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any

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
def capture(request: CaptureRequest):
    if not request.content:
        raise HTTPException(status_code=400, detail="Content is required")
        
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(
            "INSERT INTO captures (content, source) VALUES (%s, %s) RETURNING id;",
            (request.content, 'api')
        )
        new_id = cur.fetchone()['id']
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"id": new_id, "status": "captured"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run")
def run(request: RunRequest):
    text = request.text
    
    # Exemple simple
    result = {
        "length": len(text),
        "upper": text.upper(),
        "message": "Python runner OK (FastAPI)"
    }
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
