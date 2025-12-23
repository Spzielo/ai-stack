# 🗺️ AI OS — Roadmap

Objectif : Construire un "Second Cerveau" personnel autonome, robuste et intelligent.

## 🏁 Phase 1 : Fondation & Infrastructure (Stable)
*Créer un socle technique robuste, sécurisé et documenté.*

- [x] **Architecture** : Docker Compose (n8n, Postgres, Qdrant, Python, OpenWebUI).
- [x] **Base de Données** : Postgres dédié (`brain`), schémas (`captures`, `tasks`, `notes`).
- [x] **API** : Python Runner refondu en FastAPI (Async).
- [x] **Sécurité** : Tailscale (VPN), gestion des Secrets (`.env`), Ports fermés.
- [x] **Robustesse** : Gestion des dépendances (Poetry), Backup Git Auto.
- [x] **Observabilité** : Notifications Slack (Canaux Logs & Alertes).
- [x] **UX** : Environnement Dev/Prod (`make dev`), Fix Icône iOS.

## 🧠 Phase 2 : Intelligence & Traitement (Work In Progress)
*Donner vie au cerveau : transformer la donnée brute en information structurée.*

- [ ] **Ingestion** : Endpoint `/capture` capable de recevoir Texte, Audio, Liens.
- [ ] **Classification** : Router intelligemment (Note vs Tâche vs Projet) via LLM.
- [ ] **Enrichissement** : Résumer les notes, extraire les dates des tâches.
- [ ] **Mémoire** : Indexer le contenu dans Qdrant (RAG) pour le retrouver.
- [ ] **Actions** : Exécuter des scripts Python complexes sur demande.

## 🕹️ Phase 3 : Interface & Cockpit (Futur)
*Piloter le système via une interface unifiée.*

- [ ] **Dashboard** : Visualiser les tâches en cours, le flux d'idées.
- [ ] **Chat** : Interagir avec le cerveau via Open WebUI (RAG connecté).
- [ ] **Mobile** : Raccourcis iOS pour capture rapide (Voix -> Texte).

## 🔮 Phase 4 : Autonomie (Exploration)
*Le système prend des initiatives.*

- [ ] **Agents** : "Research Agent" qui veille sur des sujets.
- [ ] **Agenda** : Gestion autonome du calendrier.
