#!/usr/bin/env python3
"""
Crypto One-Glance: Daily Metrics Collection Script
Fetches prices from CoinGecko and ingests them into the database.
"""

import os
import sys
import requests
from datetime import date
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Asset mapping: symbol -> coingecko_id
ASSET_MAPPING = {
    'AAVE': 'aave',
    'MKR': 'maker',
    'UNI': 'uniswap',
    'CRV': 'curve-dao-token',
    'COMP': 'compound-governance-token',
    'SNX': 'synthetix-network-token',
    'LDO': 'lido-dao',
    'RPL': 'rocket-pool',
    'ETH': 'ethereum',
    'SOL': 'solana',
    'AVAX': 'avalanche-2',
    'NEAR': 'near',
    'ARB': 'arbitrum',
    'OP': 'optimism',
    'MATIC': 'matic-network',
    'LINK': 'chainlink',
    'GRT': 'the-graph',
    'FIL': 'filecoin'
}

API_BASE_URL = os.getenv('CRYPTO_API_URL', 'http://localhost:8000')


def fetch_coingecko_prices() -> List[Dict]:
    """Fetch prices from CoinGecko API."""
    coin_ids = ','.join(ASSET_MAPPING.values())
    
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'usd',
        'ids': coin_ids,
        'order': 'market_cap_desc',
        'per_page': 250,
        'page': 1
    }
    
    print(f"📡 Fetching prices from CoinGecko for {len(ASSET_MAPPING)} assets...")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Received data for {len(data)} coins")
        return data
    except requests.RequestException as e:
        print(f"❌ Error fetching CoinGecko data: {e}")
        return []


def build_metrics_payload(coingecko_data: List[Dict]) -> Dict:
    """Build metrics payload for ingestion."""
    # Create reverse mapping
    reverse_map = {cg_id: symbol for symbol, cg_id in ASSET_MAPPING.items()}
    
    metrics = []
    today = str(date.today())
    
    for coin in coingecko_data:
        symbol = reverse_map.get(coin['id'])
        if symbol:
            metrics.append({
                'symbol': symbol,
                'date': today,
                'price_usd': coin.get('current_price'),
                'market_cap': coin.get('market_cap'),
                'volume_24h': coin.get('total_volume'),
                'raw': {
                    'source': 'coingecko',
                    'data': coin
                }
            })
    
    return {'items': metrics}


def ingest_metrics(payload: Dict) -> bool:
    """Ingest metrics into the database via API."""
    url = f"{API_BASE_URL}/crypto/ingest/metrics"
    
    print(f"📥 Ingesting {len(payload['items'])} metrics...")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Ingested: {result.get('ingested', 0)} assets")
        print(f"⏭️  Skipped: {result.get('skipped', 0)} assets")
        
        if result.get('errors'):
            print(f"⚠️  Errors: {result['errors']}")
        
        return result.get('ingested', 0) > 0
    except requests.RequestException as e:
        print(f"❌ Error ingesting metrics: {e}")
        return False


def send_slack_notification(message: str, webhook_url: str = None):
    """Send notification to Slack."""
    if not webhook_url:
        webhook_url = os.getenv('SLACK_WEBHOOK_CRYPTO_LOGS')
    
    if not webhook_url:
        print(f"ℹ️  Slack webhook not configured, skipping notification")
        return
    
    try:
        response = requests.post(
            webhook_url,
            json={'text': message},
            timeout=5
        )
        response.raise_for_status()
        print(f"📢 Slack notification sent")
    except requests.RequestException as e:
        print(f"⚠️  Failed to send Slack notification: {e}")


def main():
    """Main execution."""
    print("=" * 60)
    print("Crypto One-Glance: Daily Metrics Collection")
    print("=" * 60)
    
    # Step 1: Fetch from CoinGecko
    coingecko_data = fetch_coingecko_prices()
    if not coingecko_data:
        send_slack_notification("⚠️ Crypto Metrics: Failed to fetch data from CoinGecko")
        return 1
    
    # Step 2: Build payload
    payload = build_metrics_payload(coingecko_data)
    print(f"📦 Built payload with {len(payload['items'])} items")
    
    # Step 3: Ingest
    success = ingest_metrics(payload)
    
    # Step 4: Notify
    if success:
        message = f"✅ Crypto Metrics: Ingested {len(payload['items'])} assets successfully"
        send_slack_notification(message)
        print("\n" + "=" * 60)
        print("✅ SUCCESS")
        print("=" * 60)
        return 0
    else:
        message = "❌ Crypto Metrics: Failed to ingest data"
        send_slack_notification(message)
        print("\n" + "=" * 60)
        print("❌ FAILED")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    exit(main())
