-- Migration: Create Crypto One-Glance Schema
-- Version: 001
-- Date: 2025-12-28

-- Create schema
CREATE SCHEMA IF NOT EXISTS crypto;

-- Table: assets
-- Core registry of tracked cryptocurrencies
CREATE TABLE crypto.assets (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),  -- DeFi, L1, L2, Oracle, Infra
    chain VARCHAR(50),     -- Main blockchain
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: sources
-- External API mappings for each asset
CREATE TABLE crypto.sources (
    id SERIAL PRIMARY KEY,
    asset_id INT REFERENCES crypto.assets(id) ON DELETE CASCADE,
    coingecko_id VARCHAR(100),
    defillama_slug VARCHAR(100),
    tokenunlocks_id VARCHAR(100),
    governance_url TEXT,
    twitter_handle VARCHAR(50),
    github_url TEXT,
    UNIQUE(asset_id)
);

-- Table: metrics_daily
-- Daily market metrics
CREATE TABLE crypto.metrics_daily (
    id SERIAL PRIMARY KEY,
    asset_id INT REFERENCES crypto.assets(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    price_usd DECIMAL(20,8),
    market_cap DECIMAL(20,2),
    volume_24h DECIMAL(20,2),
    tvl DECIMAL(20,2),           -- For DeFi protocols
    fees_24h DECIMAL(20,2),       -- If available
    revenue_24h DECIMAL(20,2),    -- If available
    raw JSONB,                    -- Raw API response for debugging
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asset_id, date)
);

-- Table: events
-- Timeline events (governance, unlocks, exploits, etc.)
CREATE TABLE crypto.events (
    id SERIAL PRIMARY KEY,
    asset_id INT REFERENCES crypto.assets(id) ON DELETE CASCADE,
    event_hash VARCHAR(64) UNIQUE,  -- For deduplication
    timestamp TIMESTAMP NOT NULL,
    type VARCHAR(30) NOT NULL,      -- GOVERNANCE, UNLOCK, EXPLOIT, RELEASE, WHALE, REGULATION
    title VARCHAR(255) NOT NULL,
    url TEXT,
    severity INT CHECK (severity BETWEEN 1 AND 5),  -- 1=info, 5=critical
    summary TEXT,
    content TEXT,                   -- Full content if available
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: scores
-- Daily scoring results
CREATE TABLE crypto.scores (
    id SERIAL PRIMARY KEY,
    asset_id INT REFERENCES crypto.assets(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    fundamentals_score DECIMAL(4,2),  -- 0-10
    tokenomics_score DECIMAL(4,2),    -- 0-10
    momentum_score DECIMAL(4,2),      -- 0-10
    total_score DECIMAL(4,2),         -- 0-30
    status VARCHAR(20),               -- ACCUMULER, OBSERVER, RISKOFF
    flags JSONB,                      -- Active risk flags
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asset_id, date)
);

-- Table: thesis_notes
-- Investment thesis and catalysts (manually editable)
CREATE TABLE crypto.thesis_notes (
    id SERIAL PRIMARY KEY,
    asset_id INT REFERENCES crypto.assets(id) ON DELETE CASCADE UNIQUE,
    thesis TEXT,
    risks TEXT,
    catalyst_90d TEXT,    -- Short-term catalysts (90 days)
    catalyst_12m TEXT,    -- Medium-term catalysts (12 months)
    dca_plan TEXT,        -- Optional DCA strategy
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_metrics_asset_date ON crypto.metrics_daily(asset_id, date DESC);
CREATE INDEX idx_events_asset_ts ON crypto.events(asset_id, timestamp DESC);
CREATE INDEX idx_events_type ON crypto.events(type);
CREATE INDEX idx_events_severity ON crypto.events(severity);
CREATE INDEX idx_scores_asset_date ON crypto.scores(asset_id, date DESC);

-- Comments for documentation
COMMENT ON SCHEMA crypto IS 'Crypto One-Glance: Long-term crypto portfolio tracking and scoring';
COMMENT ON TABLE crypto.assets IS 'Core registry of tracked cryptocurrencies';
COMMENT ON TABLE crypto.sources IS 'External API mappings (CoinGecko, DefiLlama, etc.)';
COMMENT ON TABLE crypto.metrics_daily IS 'Daily market metrics (price, volume, TVL, etc.)';
COMMENT ON TABLE crypto.events IS 'Timeline events (governance, unlocks, exploits)';
COMMENT ON TABLE crypto.scores IS 'Daily scoring results (fundamentals, tokenomics, momentum)';
COMMENT ON TABLE crypto.thesis_notes IS 'Investment thesis and catalysts (manually editable)';
