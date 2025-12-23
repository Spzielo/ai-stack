"""
RAG Logic
core/rag.py

Handles the Chat logic:
Retrieves context -> Builds Prompt -> Calls LLM.
"""
import logging
from typing import Dict, Any
from core.vector import vector_store
from core.llm import llm_client

logger = logging.getLogger(__name__)

class RAGService:
    def answer(self, user_query: str) -> Dict[str, Any]:
        
        # 1. Retrieve Context
        hits = vector_store.search(user_query, limit=3)
        
        context_text = ""
        if hits:
            context_text = "\n---\n".join([f"Note: {h['content']}" for h in hits])
        else:
            context_text = "No relevant notes found."

        # 2. Build Prompt
        system_prompt = f"""You are the user's Second Brain.
Answer the question based strictly on the Context provided below.
If the answer is not in the context, say "I don't have that information in my memory."

Context:
{context_text}
"""
        
        # 3. Call LLM (Standard completion)
        try:
             completion = llm_client._client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query},
                ]
            )
             answer = completion.choices[0].message.content
             return {
                 "answer": answer,
                 "sources": hits
             }
        except Exception as e:
            logger.error(f"RAG answer failed: {e}")
            return {"answer": "Error generating answer.", "sources": []}

rag_service = RAGService()
