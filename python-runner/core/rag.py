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
        system_prompt = f"""Tu es un expert GTD (Getting Things Done).
Utilise le contexte suivant (tes notes/tâches) pour répondre à la question de l'utilisateur.
Si tu ne trouves pas la réponse dans le contexte, dis-le poliment.
Réponds TOUJOURS en Français.

Contexte:
{context_text}
"""
        
        # 3. Call LLM (Standard completion)
        try:
             completion = llm_client._client.chat.completions.create(
                model=llm_client._model,
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

    def answer_stream(self, user_query: str):
        """Retrieves context and streams response."""
        # 1. Retrieve
        if self.vector_store:
            relevant_notes = self.vector_store.search(user_query)
        else:
            relevant_notes = []
            
        context_text = "\n\n".join([f"- {n.get('content', '')}" for n in relevant_notes])
        if not context_text:
            context_text = "Aucune note pertinente trouvée."

        # 2. Build Prompt
        system_prompt = f"""Tu es un expert GTD (Getting Things Done).
Utilise le contexte suivant (tes notes/tâches) pour répondre à la question de l'utilisateur.
Si tu ne trouves pas la réponse dans le contexte, dis-le poliment.
Réponds TOUJOURS en Français.

Contexte:
{context_text}
"""
        
        # 3. Stream Answer
        full_answer = ""
        for chunk in llm_client.chat_stream(user_query, system_prompt=system_prompt):
            full_answer += chunk
            yield chunk

        # 4. Append Sources
        if relevant_notes:
            yield "\n\n**Sources :**\n"
            for s in relevant_notes:
                title = s.get('title', 'Note')
                excerpt = s.get('content', '')[:50].replace("\n", " ") + "..."
                yield f"- *{title}*: {excerpt}\n"

rag_service = RAGService()
