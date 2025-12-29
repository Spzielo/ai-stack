-- Migration: Create Stocks Schema
-- Version: 004
-- Date: 2025-12-28

-- Create schema
CREATE SCHEMA IF NOT EXISTS stocks;

-- Table: assets
-- Registry of tracked stocks (companies)
CREATE TABLE stocks.assets (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,  -- Ticker (AAPL, MSFT, MC.PA)
    name VARCHAR(100) NOT NULL,
    sector VARCHAR(100),                 -- Technology, Energy, Luxury...
    industry VARCHAR(100),
    currency VARCHAR(10) DEFAULT 'USD',
    exchange VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: metrics_daily
-- Daily market metrics for stocks
CREATE TABLE stocks.metrics_daily (
    id SERIAL PRIMARY KEY,
    asset_id INT REFERENCES stocks.assets(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    price DECIMAL(20,8),
    market_cap DECIMAL(20,2),
    volume DECIMAL(20,2),
    pe_ratio DECIMAL(10,2),
    eps DECIMAL(10,2),
    dividend_yield DECIMAL(5,2),         -- Percentage
    fifty_two_week_high DECIMAL(20,8),
    fifty_two_week_low DECIMAL(20,8),
    raw JSONB,                           -- Raw yfinance info
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asset_id, date)
);

-- Table: positions
-- User portfolio positions
CREATE TABLE stocks.positions (
    id SERIAL PRIMARY KEY,
    asset_id INT REFERENCES stocks.assets(id) ON DELETE CASCADE,
    quantity DECIMAL(20, 8) NOT NULL,
    purchase_price DECIMAL(20, 8) NOT NULL,
    purchase_date DATE NOT NULL,
    invested_amount DECIMAL(20, 2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT positive_price CHECK (purchase_price > 0)
);

-- Indexes
CREATE INDEX idx_stocks_metrics_asset_date ON stocks.metrics_daily(asset_id, date DESC);
CREATE INDEX idx_stocks_positions_asset ON stocks.positions(asset_id);

-- Comments
COMMENT ON SCHEMA stocks IS 'Traditional stock market tracking';
COMMENT ON TABLE stocks.assets IS 'Registry of tracked stocks';
COMMENT ON TABLE stocks.positions IS 'User stock positions';
