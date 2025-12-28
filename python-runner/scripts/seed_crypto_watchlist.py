#!/usr/bin/env python3
"""
Seed initial crypto watchlist.
Populates crypto.assets and crypto.sources tables with initial data.
"""

import os
import psycopg2
from psycopg2.extras import execute_values

# Initial watchlist with API mappings
WATCHLIST = [
    # DeFi
    {
        "symbol": "AAVE",
        "name": "Aave",
        "category": "DeFi",
        "chain": "Ethereum",
        "coingecko_id": "aave",
        "defillama_slug": "aave",
        "governance_url": "https://governance.aave.com",
    },
    {
        "symbol": "MKR",
        "name": "Maker",
        "category": "DeFi",
        "chain": "Ethereum",
        "coingecko_id": "maker",
        "defillama_slug": "makerdao",
        "governance_url": "https://vote.makerdao.com",
    },
    {
        "symbol": "UNI",
        "name": "Uniswap",
        "category": "DeFi",
        "chain": "Ethereum",
        "coingecko_id": "uniswap",
        "defillama_slug": "uniswap",
        "governance_url": "https://gov.uniswap.org",
    },
    {
        "symbol": "CRV",
        "name": "Curve DAO",
        "category": "DeFi",
        "chain": "Ethereum",
        "coingecko_id": "curve-dao-token",
        "defillama_slug": "curve-finance",
        "governance_url": "https://gov.curve.fi",
    },
    {
        "symbol": "COMP",
        "name": "Compound",
        "category": "DeFi",
        "chain": "Ethereum",
        "coingecko_id": "compound-governance-token",
        "defillama_slug": "compound",
        "governance_url": "https://compound.finance/governance",
    },
    {
        "symbol": "SNX",
        "name": "Synthetix",
        "category": "DeFi",
        "chain": "Ethereum",
        "coingecko_id": "synthetix-network-token",
        "defillama_slug": "synthetix",
        "governance_url": "https://staking.synthetix.io/gov",
    },
    {
        "symbol": "LDO",
        "name": "Lido DAO",
        "category": "DeFi",
        "chain": "Ethereum",
        "coingecko_id": "lido-dao",
        "defillama_slug": "lido",
        "governance_url": "https://research.lido.fi",
    },
    {
        "symbol": "RPL",
        "name": "Rocket Pool",
        "category": "DeFi",
        "chain": "Ethereum",
        "coingecko_id": "rocket-pool",
        "defillama_slug": "rocket-pool",
    },
    # L1
    {
        "symbol": "ETH",
        "name": "Ethereum",
        "category": "L1",
        "chain": "Ethereum",
        "coingecko_id": "ethereum",
        "defillama_slug": "ethereum",
    },
    {
        "symbol": "SOL",
        "name": "Solana",
        "category": "L1",
        "chain": "Solana",
        "coingecko_id": "solana",
        "defillama_slug": "solana",
    },
    {
        "symbol": "AVAX",
        "name": "Avalanche",
        "category": "L1",
        "chain": "Avalanche",
        "coingecko_id": "avalanche-2",
        "defillama_slug": "avalanche",
    },
    {
        "symbol": "NEAR",
        "name": "NEAR Protocol",
        "category": "L1",
        "chain": "NEAR",
        "coingecko_id": "near",
        "defillama_slug": "near",
    },
    # L2
    {
        "symbol": "ARB",
        "name": "Arbitrum",
        "category": "L2",
        "chain": "Arbitrum",
        "coingecko_id": "arbitrum",
        "defillama_slug": "arbitrum",
        "governance_url": "https://forum.arbitrum.foundation",
    },
    {
        "symbol": "OP",
        "name": "Optimism",
        "category": "L2",
        "chain": "Optimism",
        "coingecko_id": "optimism",
        "defillama_slug": "optimism",
        "governance_url": "https://gov.optimism.io",
    },
    {
        "symbol": "MATIC",
        "name": "Polygon",
        "category": "L2",
        "chain": "Polygon",
        "coingecko_id": "matic-network",
        "defillama_slug": "polygon",
    },
    # Infrastructure
    {
        "symbol": "LINK",
        "name": "Chainlink",
        "category": "Oracle",
        "chain": "Ethereum",
        "coingecko_id": "chainlink",
        "defillama_slug": "chainlink",
    },
    {
        "symbol": "GRT",
        "name": "The Graph",
        "category": "Infra",
        "chain": "Ethereum",
        "coingecko_id": "the-graph",
        "defillama_slug": "the-graph",
        "governance_url": "https://forum.thegraph.com",
    },
    {
        "symbol": "FIL",
        "name": "Filecoin",
        "category": "Infra",
        "chain": "Filecoin",
        "coingecko_id": "filecoin",
        "defillama_slug": "filecoin",
    },
]


def get_db_connection():
    """Get PostgreSQL connection."""
    return psycopg2.connect(
        host=os.environ.get("BRAIN_DB_HOST", "postgres"),
        database=os.environ.get("BRAIN_DB_NAME", "brain"),
        user=os.environ.get("BRAIN_DB_USER", "postgres"),
        password=os.environ.get("BRAIN_DB_PASSWORD", ""),
        port=os.environ.get("BRAIN_DB_PORT", "5432"),
    )


def seed_watchlist():
    """Seed the crypto watchlist."""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Insert assets
        assets_data = [
            (item["symbol"], item["name"], item["category"], item["chain"])
            for item in WATCHLIST
        ]

        execute_values(
            cur,
            """
            INSERT INTO crypto.assets (symbol, name, category, chain)
            VALUES %s
            ON CONFLICT (symbol) DO NOTHING
            RETURNING id, symbol
            """,
            assets_data,
        )

        # Get asset IDs
        cur.execute("SELECT id, symbol FROM crypto.assets")
        asset_map = {row[1]: row[0] for row in cur.fetchall()}

        # Insert sources
        sources_data = []
        for item in WATCHLIST:
            asset_id = asset_map.get(item["symbol"])
            if asset_id:
                sources_data.append(
                    (
                        asset_id,
                        item.get("coingecko_id"),
                        item.get("defillama_slug"),
                        item.get("tokenunlocks_id"),
                        item.get("governance_url"),
                        item.get("twitter_handle"),
                        item.get("github_url"),
                    )
                )

        execute_values(
            cur,
            """
            INSERT INTO crypto.sources (
                asset_id, coingecko_id, defillama_slug, tokenunlocks_id,
                governance_url, twitter_handle, github_url
            )
            VALUES %s
            ON CONFLICT (asset_id) DO NOTHING
            """,
            sources_data,
        )

        conn.commit()
        print(f"✅ Seeded {len(WATCHLIST)} assets successfully")

        # Print summary
        cur.execute(
            """
            SELECT category, COUNT(*) 
            FROM crypto.assets 
            WHERE is_active = true 
            GROUP BY category 
            ORDER BY category
            """
        )
        print("\n📊 Watchlist Summary:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} assets")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error seeding watchlist: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    seed_watchlist()
