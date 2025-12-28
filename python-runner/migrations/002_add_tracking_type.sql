-- Migration: Add tracking_type to crypto.assets
-- This allows us to distinguish between top50 and watchlist cryptos

ALTER TABLE crypto.assets 
ADD COLUMN IF NOT EXISTS tracking_type VARCHAR(20) DEFAULT 'watchlist';

-- Add index for filtering
CREATE INDEX IF NOT EXISTS idx_assets_tracking_type ON crypto.assets(tracking_type);

-- Mark existing assets as watchlist
UPDATE crypto.assets SET tracking_type = 'watchlist' WHERE tracking_type IS NULL;

-- Add comment
COMMENT ON COLUMN crypto.assets.tracking_type IS 'Type of tracking: top50 (automatic) or watchlist (manual)';
