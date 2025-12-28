# Crypto One-Glance Module

Module de suivi long terme de cryptomonnaies avec scoring automatisé et alertes.

## 🎯 Objectif

Suivre un portefeuille de 18 cryptos avec :
- Vision consolidée (dashboard)
- Scoring automatisé (Fondamentaux / Tokenomics / Momentum)
- Alertes proactives sur événements critiques
- Aide à la décision : ACCUMULER / OBSERVER / RISKOFF

## 📊 Watchlist Actuelle

**DeFi (8)** : AAVE, MKR, UNI, CRV, COMP, SNX, LDO, RPL  
**L1 (4)** : ETH, SOL, AVAX, NEAR  
**L2 (3)** : ARB, OP, MATIC  
**Infrastructure (2)** : GRT, FIL  
**Oracle (1)** : LINK

## 🏗️ Architecture

```
CoinGecko/DefiLlama → n8n → FastAPI → PostgreSQL
                              ↓
                          Slack Alerts
```

## 🔧 Configuration

### Variables d'environnement

Ajouter à `.env` :

```env
# Crypto Module APIs (optionnel pour CoinGecko free tier)
COINGECKO_API_KEY=
DEFILLAMA_API_KEY=
TOKENUNLOCKS_API_KEY=

# Crypto Slack Webhooks
SLACK_WEBHOOK_CRYPTO_ALERTES=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_WEBHOOK_CRYPTO_LOGS=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### n8n Workflows

Importer les workflows depuis `n8n-custom/workflows/` :
1. `crypto_daily_metrics.json` - Collecte quotidienne (07:10 UTC)
2. `crypto_daily_scoring.json` - Calcul scores (08:00 UTC)

## 📡 API Endpoints

### Lecture
- `GET /crypto/dashboard` - Vue d'ensemble watchlist
- `GET /crypto/assets/{symbol}` - Fiche détaillée (one-pager)
- `GET /crypto/assets/{symbol}/timeline` - Historique événements + métriques
- `GET /crypto/assets/{symbol}/metrics?range=30d` - Métriques sur période

### Ingestion (utilisé par n8n)
- `POST /crypto/ingest/metrics` - Ingestion batch métriques
- `POST /crypto/ingest/events` - Ingestion batch événements

### Computation (utilisé par n8n)
- `POST /crypto/compute/scores` - Calcul scores tous assets

## 🎯 Scoring

**Total : 0-30 points**

- **Fondamentaux (0-10)** : TVL trends, stabilité, part de marché
- **Tokenomics (0-10)** : Unlocks, inflation, utilité
- **Momentum (0-10)** : Tendance prix, volatilité

**Statuts** :
- ≥ 22 pts → 🟢 **ACCUMULER**
- 15-21 pts → 🟡 **OBSERVER**
- < 15 pts → 🔴 **RISKOFF**

**Flags de risque** :
- `tvl_drop_7d` / `tvl_drop_30d`
- `unlock_imminent`
- `exploit_recent`
- `governance_conflict`

## 🚀 Utilisation

### Tester l'API

```bash
# Dashboard
curl http://localhost:8000/crypto/dashboard | jq

# Fiche AAVE
curl http://localhost:8000/crypto/assets/AAVE | jq

# Timeline 90 jours
curl http://localhost:8000/crypto/assets/AAVE/timeline?days=90 | jq
```

### Tester l'ingestion manuelle

```bash
# Ingest test metric
curl -X POST http://localhost:8000/crypto/ingest/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{
      "symbol": "AAVE",
      "date": "2025-12-28",
      "price_usd": 285.42,
      "market_cap": 4250000000,
      "volume_24h": 180000000
    }]
  }'

# Compute scores
curl -X POST http://localhost:8000/crypto/compute/scores
```

## 📁 Structure

```
python-runner/
├── crypto/
│   ├── __init__.py
│   ├── models.py          # Pydantic models
│   ├── db.py              # Database operations
│   ├── scoring.py         # Scoring engine
│   ├── api_clients.py     # External APIs
│   └── routes.py          # FastAPI endpoints
└── migrations/
    └── 001_create_crypto_schema.sql

n8n-custom/
└── workflows/
    ├── crypto_daily_metrics.json
    └── crypto_daily_scoring.json
```

## 🔮 Roadmap

**Phase 1 (MVP)** ✅ :
- Database schema
- API endpoints
- Scoring engine
- n8n workflows

**Phase 2 (Enrichissement)** :
- RAG avec Qdrant (gouvernance)
- UI OpenWebUI (dashboard, one-pager)
- Scraping forums gouvernance

**Phase 3 (Avancé)** :
- Détection whale movements
- Corrélation BTC/ETH
- Export PDF fiches
