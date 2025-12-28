#!/usr/bin/env python3
"""
Collect Top 50 Cryptocurrencies by Market Cap
Automatically adds/updates the top 50 cryptos from CoinGecko
"""

import os
import sys
import requests
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import get_db_connection


def fetch_top50_from_coingecko():
    """Fetch top 50 cryptos by market cap from CoinGecko."""
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 50,
        'page': 1,
        'sparkline': False
    }
    
    print(f"📡 Fetching top 50 cryptos from CoinGecko...")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Received {len(data)} cryptos")
        return data
    except requests.RequestException as e:
        print(f"❌ Error fetching CoinGecko data: {e}")
        return []


def categorize_crypto(symbol, name):
    """Simple categorization based on symbol/name."""
    symbol = symbol.upper()
    name_lower = name.lower()
    
    # DeFi protocols
    defi_keywords = ['aave', 'maker', 'uniswap', 'curve', 'compound', 'synthetix', 'lido', 'rocket']
    if any(kw in name_lower for kw in defi_keywords):
        return 'DeFi'
    
    # Layer 1
    l1_keywords = ['ethereum', 'solana', 'cardano', 'avalanche', 'polkadot', 'near', 'cosmos', 'algorand', 'tezos', 'fantom']
    if any(kw in name_lower for kw in l1_keywords) or symbol in ['ETH', 'SOL', 'ADA', 'AVAX', 'DOT', 'NEAR', 'ATOM', 'ALGO', 'XTZ', 'FTM']:
        return 'L1'
    
    # Layer 2
    l2_keywords = ['arbitrum', 'optimism', 'polygon', 'immutable', 'starknet']
    if any(kw in name_lower for kw in l2_keywords) or symbol in ['ARB', 'OP', 'MATIC', 'IMX']:
        return 'L2'
    
    # Stablecoins
    if symbol in ['USDT', 'USDC', 'DAI', 'BUSD', 'TUSD', 'USDD', 'FRAX'] or 'stablecoin' in name_lower:
        return 'Stablecoin'
    
    # Infrastructure
    infra_keywords = ['chainlink', 'graph', 'filecoin', 'arweave', 'render']
    if any(kw in name_lower for kw in infra_keywords) or symbol in ['LINK', 'GRT', 'FIL', 'AR', 'RNDR']:
        return 'Infrastructure'
    
    # Default
    return 'Other'


def upsert_top50_assets(cryptos):
    """Insert or update top 50 assets in database."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    added = 0
    updated = 0
    
    for crypto in cryptos:
        symbol = crypto['symbol'].upper()
        name = crypto['name']
        coingecko_id = crypto['id']
        category = categorize_crypto(symbol, name)
        
        # Check if asset exists
        cur.execute(
            "SELECT id, tracking_type FROM crypto.assets WHERE symbol = %s",
            (symbol,)
        )
        existing = cur.fetchone()
        
        if existing:
            # Update existing asset
            cur.execute("""
                UPDATE crypto.assets 
                SET name = %s, tracking_type = 'top50', category = %s
                WHERE symbol = %s
            """, (name, category, symbol))
            
            # Update source
            cur.execute("""
                INSERT INTO crypto.sources (asset_id, coingecko_id)
                VALUES (%s, %s)
                ON CONFLICT (asset_id) 
                DO UPDATE SET coingecko_id = EXCLUDED.coingecko_id
            """, (existing[0], coingecko_id))
            
            updated += 1
        else:
            # Insert new asset
            cur.execute("""
                INSERT INTO crypto.assets (symbol, name, category, chain, tracking_type)
                VALUES (%s, %s, %s, 'multi', 'top50')
                RETURNING id
            """, (symbol, name, category))
            
            asset_id = cur.fetchone()[0]
            
            # Insert source
            cur.execute("""
                INSERT INTO crypto.sources (asset_id, coingecko_id)
                VALUES (%s, %s)
            """, (asset_id, coingecko_id))
            
            added += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    return added, updated


def main():
    """Main execution."""
    print("=" * 60)
    print("Crypto One-Glance: Top 50 Update")
    print("=" * 60)
    
    # Fetch top 50
    cryptos = fetch_top50_from_coingecko()
    if not cryptos:
        print("❌ Failed to fetch top 50")
        return 1
    
    # Upsert into database
    added, updated = upsert_top50_assets(cryptos)
    
    print(f"\n📊 Results:")
    print(f"  ➕ Added: {added} new cryptos")
    print(f"  🔄 Updated: {updated} existing cryptos")
    print(f"  📈 Total top 50: {len(cryptos)}")
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    exit(main())
