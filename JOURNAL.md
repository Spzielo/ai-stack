# Journal de Bord

Ce document trace les réflexions, les impasses et les leçons apprises tout au long du projet.

## 2025-12-28 - Module Crypto One-Glance Déployé ✅

**Réalisations** :
- ✨ Création complète du module Crypto One-Glance
- 📊 18 cryptos suivies avec données réelles (ETH $2937, SOL $124, etc.)
- 🤖 Automatisation CRON configurée (8h10 collecte, 9h00 scoring)
- 📡 API REST complète et testée
- 🎯 Système de scoring opérationnel (fondamentaux, tokenomics, momentum)

**Décisions techniques** :
- Approche script Python standalone plutôt que workflow n8n complexe
- CRON système pour l'automatisation (plus simple que n8n)
- Mapping hardcodé des assets (évite dépendance à un endpoint supplémentaire)
- CoinGecko API en free tier (suffisant pour 18 assets)

**Prochaines étapes** :
- Laisser accumuler 7-30 jours de données pour affiner les scores
- Optionnel : configurer webhooks Slack pour notifications
- Phase 2 : RAG avec Qdrant pour gouvernance

### 💡 Leçon : Developer Experience (DX) & Frontend
**Problème** : En modifiant `crypto.html`, rien ne changeait sur localhost.
**Cause** : Le conteneur Docker `dashboard` était une image statique (buildée) sans lien avec le dossier local.
**Fix** : Ajout d'un `volume` dans docker-compose.
**Retenue** : Pour tout service Frontend, **toujours** mapper le volume de dev dès le jour 1. Sinon, on perd du temps à "rebuilder" pour changer une couleur.

### 🚀 Shift : D'une liste fermée à l'Open World
Initialement, je pensais restreindre à une "watchlist curée".
**Feedback** : L'utilisateur veut suivre "PEPE" ou "TURBO" immédiatement.
**Action** : Ouverture via l'API Search de CoinGecko.
**Architecture** : Backend agit comme proxy (pour gérer les clés/rate limits futurs) -> Frontend affiche. C'est plus propre que d'appeler CoinGecko depuis le JS (CORS, sécurité).

---

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
