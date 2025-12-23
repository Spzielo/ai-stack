# ADR-002: Framework Python (FastAPI vs Flask)

* **Status**: Accepted
* **Date**: 2025-12-22

## Context
Le service `python-runner` est le cœur logique du système. Il doit recevoir des requêtes HTTP (Webhooks n8n, UI) et traiter des tâches (classification, embeddings).
Le choix initial s'est porté sur Flask par simplicité.

## Decision
Migrer de **Flask** vers **FastAPI**.

## Consequences
### ✅ Positif
*   **Asynchrone (ASGI)** : Performance accrue pour les I/O (appels DB, appels API OpenAI).
*   **Validation des données** : Pydantic garantit que les données entrants sont propres (Typage fort).
*   **Documentation** : Swagger UI générée automatiquement (`/docs`).

### ❌ Négatif
*   Courbe d'apprentissage légèrement plus élevée pour l'async/await.
