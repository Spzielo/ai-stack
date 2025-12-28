# n8n Workflows for Crypto One-Glance

This directory contains n8n workflow JSON files for the Crypto One-Glance module.

## Workflows

### 1. crypto_daily_metrics.json
**Schedule**: Daily at 07:10 UTC  
**Purpose**: Fetch daily market metrics from CoinGecko

**Flow**:
1. Get active assets from database
2. Fetch batch prices from CoinGecko API
3. Build metrics payload
4. Ingest into database via `/crypto/ingest/metrics`
5. Send success/error notification to Slack #crypto-logs

### 2. crypto_daily_scoring.json
**Schedule**: Daily at 08:00 UTC (after metrics ingestion)  
**Purpose**: Compute scores and detect status changes

**Flow**:
1. Trigger scoring computation via `/crypto/compute/scores`
2. Check for status changes
3. Send alerts to Slack #crypto-alertes for each change
4. Send summary to Slack #crypto-logs

## Import Instructions

1. Access n8n at `http://localhost:5678`
2. Go to **Workflows** → **Import from File**
3. Select each JSON file and import
4. Activate the workflows

## Environment Variables Required

Add to `.env`:
```env
SLACK_WEBHOOK_CRYPTO_ALERTES=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_WEBHOOK_CRYPTO_LOGS=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Manual Testing

You can manually execute each workflow:
1. Open the workflow in n8n
2. Click **Execute Workflow** button
3. Check the execution log and Slack channels
