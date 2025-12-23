# ADR-001: Architecture Microservices via Docker Compose

* **Status**: Accepted
* **Date**: 2025-12-22

## Context
Nous devons construire une stack IA personnelle ("Second Brain") qui soit :
1.  Modulaire (pour remplacer des briques).
2.  Facile à déployer localement (Mac Mini).
3.  Sécurisée.

## Decision
Nous utilisons **Docker Compose** pour orchestrer un ensemble de services interconnectés :
*   **n8n** : Orchestrateur Low-Code.
*   **Postgres** : Stockage relationnel.
*   **Qdrant** : Base vectorielle (RAG).
*   **Python Runner** : Logique métier complexe / IA.
*   **Open WebUI** : Interface Chat.

## Consequences
### ✅ Positif
*   Isolation parfaite des dépendances.
*   Réseau interne Docker facile à sécuriser (pas de ports exposés).
*   Reproductibilité totale.

### ❌ Négatif
*   Consommation mémoire plus élevée (chaque service a son runtime).
*   Complexité de communication inter-conteneurs (DNS interne).
