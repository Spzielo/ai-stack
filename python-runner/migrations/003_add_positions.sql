-- Migration: Add portfolio positions table
-- Allows users to track their crypto investments

CREATE TABLE IF NOT EXISTS crypto.positions (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES crypto.assets(id) ON DELETE CASCADE,
    
    -- Purchase details
    quantity DECIMAL(20, 8) NOT NULL,
    purchase_price_usd DECIMAL(20, 8) NOT NULL,
    purchase_date DATE NOT NULL,
    invested_amount_usd DECIMAL(20, 2) NOT NULL,
    
    -- Optional metadata
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT positive_price CHECK (purchase_price_usd > 0),
    CONSTRAINT positive_invested CHECK (invested_amount_usd > 0)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_positions_asset ON crypto.positions(asset_id);
CREATE INDEX IF NOT EXISTS idx_positions_date ON crypto.positions(purchase_date);

-- Comments
COMMENT ON TABLE crypto.positions IS 'User portfolio positions for tracking investments';
COMMENT ON COLUMN crypto.positions.quantity IS 'Amount of crypto owned';
COMMENT ON COLUMN crypto.positions.purchase_price_usd IS 'Price per unit at purchase time';
COMMENT ON COLUMN crypto.positions.invested_amount_usd IS 'Total amount invested (quantity × price)';
