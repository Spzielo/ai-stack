# Changelog - AI Stack

## [2025-12-28] - Module Crypto One-Glance

### Ajouté
- ✨ **Nouveau module Crypto One-Glance** pour le suivi long terme de cryptomonnaies
- 📊 Base de données PostgreSQL avec 7 tables (assets, sources, metrics_daily, events, scores, thesis_notes)
- 🎯 Watchlist de 18 cryptomonnaies (DeFi, L1, L2, Infrastructure, Oracle)
- 📡 API REST complète avec endpoints :
  - `GET /crypto/dashboard` - Vue d'ensemble
  - `GET /crypto/assets/{symbol}` - Fiche détaillée
  - `GET /crypto/assets/{symbol}/timeline` - Historique
  - `POST /crypto/ingest/metrics` - Ingestion données
  - `POST /crypto/compute/scores` - Calcul scores
- 🤖 Script Python standalone `collect_crypto_metrics.py` pour collecte automatique
- 📈 Système de scoring automatisé (0-30 points) :
  - Fondamentaux (TVL, stabilité, part de marché)
  - Tokenomics (unlocks, inflation, utilité)
  - Momentum (tendance prix, volatilité)
- 🚦 Statuts décisionnels : ACCUMULER / OBSERVER / RISKOFF
- ⚠️ Flags de risque (tvl_drop, unlock_imminent, exploit_recent, etc.)
- ⏰ Automatisation CRON (collecte à 8h10, scoring à 9h00)
- 📚 Documentation complète (README, guide d'utilisation, exemples)

### Technique
- Module Python `crypto/` avec models, db, scoring, routes, api_clients
- Migration SQL `001_create_crypto_schema.sql`
- Scripts : `seed_crypto_watchlist.py`, `collect_crypto_metrics.py`, `test_crypto_module.py`
- Workflows n8n simplifiés (optionnel)
- Intégration CoinGecko API pour les prix

### Testé
- ✅ 17 assets ingérés avec succès
- ✅ Scores calculés pour tous les assets
- ✅ Dashboard API fonctionnel
- ✅ Collecte automatique via CRON configurée
- ✅ Sync Dashboard/Localhost corrigé (Volume Docker)
- ✅ Feature "Search & Add" validée

### Améliorations (Update soir)
- ✨ **Recherche Globale** : Ajout d'une modale pour rechercher et ajouter n'importe quelle crypto via CoinGecko.
- 🐛 **Fix UI** : Correction du bouton "Ajouter" qui crashait (undefined event).
- 🛠️ **Dev Experience** : Ajout du volume mount `./dashboard` dans docker-compose pour le hot-reload du frontend.

---

## [2025-12-26] - Job Hunter Refinement

### Corrigé
- 🐛 Résolution de `ModuleNotFoundError: No module named 'requests'` dans le service job-hunter
- ✅ Vérification du bouton "Chasser" déclenchant Google News et workflow n8n
- ✅ Configuration workflow n8n avec webhook et credentials OpenAI
- ✅ UI reflétant correctement le mode "active hunting"

---

## [2025-12-20] - Restricting Commercial Access

### Ajouté
- 🔒 Restriction d'accès au module commercial (rôles ADMIN/DIRECTION uniquement)
- 👥 Espace d'administration pour gérer les rôles utilisateurs
- 🛡️ Contrôle d'accès basé sur les rôles (RBAC)

---

## [2025-12-18] - Security Audit and Hardening

### Sécurité
- 🔍 Audit de sécurité complet
- 🔐 Vérification de l'exposition de `plainTextPassword`
- ✅ Audit des Server Actions avec RBAC
- 🛡️ Restriction d'accès aux données selon les rôles

---

## [2025-12-14] - Vercel & Modular Toggles Setup

### Ajouté
- ☁️ Configuration Vercel pour production et preview
- 🎛️ Système de toggles modulaires (Concours, Blog, Gagnants, etc.)
- 🔧 Interface admin pour activer/désactiver les modules

---

## [2025-12-07] - Debugging Mobile Connectivity Issues

### Corrigé
- 📱 Résolution des erreurs "Failed to fetch" sur mobile
- 🔄 Implémentation proxy Next.js pour les appels API backend
- ✅ Fonctionnalité de login utilisateur sur mobile via ngrok

---

## [2025-12-05] - Deploying Site to Production

### Déploiement
- 🚀 Déploiement frontend Next.js sur Vercel
- 🗄️ Déploiement backend NestJS sur Railway
- 🌐 Intégration domaines OVH (lesfilsdemel.fr, lesfilsdemel.com)
- 📝 Configuration variables d'environnement
- 🐳 Dockerfile pour le backend
