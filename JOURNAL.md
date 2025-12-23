# Journal de Bord

Ce document trace les réflexions, les impasses et les leçons apprises tout au long du projet.

## 2025-12-23 : Durcissement de l'Infrastructure

### 💡 Leçon : La gestion des dépendances
Nous avons initialement utilisé `pip install` dans le Dockerfile. Bien que fonctionnel, cela manquait de reproductibilité.
**Décision** : Passage immédiat à **Poetry**. C'est un coût initial (temps de build un peu plus long, complexité Dockerfile) mais cela garantit que la Prod est *identique* au Dev.

### ↩️ Pivot : Notifications
Nous avons exploré **Pushover** pour les notifications mobiles.
**Problème** : Trop limité pour une gestion de logs structurée (bruit vs signal).
**Pivot** : Revenir en arrière (suppression complète du code Pushover) et implémenter **Slack**.
**Gain** : Slack permet de créer des canaux séparés (`#log` vs `#alert`), ce qui est crucial pour ne pas "noyer" l'utilisateur sous les infos techniques.

---

## 2025-12-22 : Problèmes de Frontend (Icônes)

### 🐛 Bug : L'icône fantôme sur iOS
Sur iOS, ajouter n8n à l'écran d'accueil affichait un carré blanc ou un "N" par défaut, malgré nos hacks HTML.
**Solution trouvée** : iOS/Safari est très capricieux sur le cache et la découverte d'icônes.
**Fix** :
1.  Utiliser un nom de fichier standard (`apple-touch-icon.png`).
2.  Ne PAS ajouter de balises HTML manuelles (laisser Safari découvrir implicitement).
3.  Utiliser une icône *solide* (pas de transparence).

---

## 2025-12-22 : Architecture API

### 🚀 Migration Flask -> FastAPI
On a démarré en Flask par habitude. Mais Flask est synchrone (bloquant).
Pour un "Cerveau" qui devra traiter des requêtes IA potentiellement longues, bloquer le thread principal est dangereux.
**Action** : Réécriture complète en **FastAPI** (ASGI/Async).
**Résultat** : Plus moderne, validation automatique via Pydantic, et prêt pour l'avenir.

---

## 2025-12-23: Phase 5 - Souveraineté & Optimisation (Ollama)

### 💡 Objectif
S'affranchir des coûts API (OpenAI) et garantir la confidentialité en faisant tourner l'IA localement sur le Mac.

### 🚧 Challenge : Robustesse des Modèles Locaux
Nous avons migré de `gpt-4o` (très robuste sur le JSON structuré) vers des modèles locaux.
**Problème** : `llama3` et `llama3.1:70b` étaient soit absents, soit trop lourds (500 Error, crash).
**Solution** :
1.  **Architecture Adaptative** : Le code (`llm.py`) essaie d'abord un parsing strict (Pydantic). S'il échoue (404/500/Format), il bascule sur un mode "JSON standard" plus tolérant.
2.  **Choix du Modèle** : Validation de **`qwen2.5:32b`**. Il s'est avéré bien meilleur que Llama 3.1 (8b) pour comprendre le contexte ("Buy milk" -> Tagué comme "errand", ce que Llama a manqué).

### ✅ État Final
Le système est complet :
- **Intelligent** (Classification Qwen).
- **Mémoire** (RAG via Qdrant Local).
- **Interface** (Open WebUI connecté au Brain).
- **Gratuit** (100% Local).
