
from core.db import get_db_connection
from psycopg2.extras import RealDictCursor
import json
from datetime import date
from typing import List, Dict, Optional

def get_assets(active_only=True) -> List[Dict]:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        query = "SELECT * FROM stocks.assets"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY symbol"
        cur.execute(query)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def add_asset(symbol: str, name: str, sector: str = None, industry: str = None, 
              currency: str = 'USD', exchange: str = None) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if exists
        cur.execute("SELECT id FROM stocks.assets WHERE symbol = %s", (symbol,))
        existing = cur.fetchone()
        if existing:
            # Re-activate if needed
            cur.execute("UPDATE stocks.assets SET is_active = TRUE WHERE id = %s", (existing[0],))
            conn.commit()
            return existing[0]

        cur.execute("""
            INSERT INTO stocks.assets (symbol, name, sector, industry, currency, exchange)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (symbol, name, sector, industry, currency, exchange))
        conn.commit()
        return cur.fetchone()[0]
    finally:
        cur.close()
        conn.close()

def update_asset_metrics(asset_id: int, metrics: Dict):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        today = date.today()
        # Upsert metrics
        cur.execute("""
            INSERT INTO stocks.metrics_daily 
            (asset_id, date, price, market_cap, volume, pe_ratio, dividend_yield, fifty_two_week_high, fifty_two_week_low, raw)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (asset_id, date) DO UPDATE SET
                price = EXCLUDED.price,
                market_cap = EXCLUDED.market_cap,
                volume = EXCLUDED.volume,
                pe_ratio = EXCLUDED.pe_ratio,
                dividend_yield = EXCLUDED.dividend_yield,
                fifty_two_week_high = EXCLUDED.fifty_two_week_high,
                fifty_two_week_low = EXCLUDED.fifty_two_week_low,
                raw = EXCLUDED.raw
        """, (
            asset_id, today,
            metrics.get('price'),
            metrics.get('market_cap'),
            metrics.get('volume'),
            metrics.get('pe_ratio'),
            metrics.get('dividend_yield'),
            metrics.get('fifty_two_week_high'),
            metrics.get('fifty_two_week_low'),
            json.dumps(metrics.get('raw', {}))
        ))
        conn.commit()
    finally:
        cur.close()
        conn.close()

def get_positions() -> List[Dict]:
    """
    Get all positions with current asset details.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Join with assets and latest metrics
        # Note: We take the latest metrics for ANY date to get current price approximation if today's run not done
        cur.execute("""
            WITH latest_metrics AS (
                SELECT DISTINCT ON (asset_id) *
                FROM stocks.metrics_daily
                ORDER BY asset_id, date DESC
            )
            SELECT 
                p.id,
                p.asset_id,
                a.symbol,
                a.name,
                a.sector,
                a.currency,
                p.quantity,
                p.purchase_price,
                p.purchase_date,
                p.invested_amount,
                p.notes,
                m.price as current_price,
                m.date as last_updated,
                (p.quantity * COALESCE(m.price, p.purchase_price)) as current_value,
                ((p.quantity * COALESCE(m.price, p.purchase_price)) - p.invested_amount) as pnl,
                CASE WHEN p.invested_amount > 0 THEN
                    (((p.quantity * COALESCE(m.price, p.purchase_price)) - p.invested_amount) / p.invested_amount) * 100
                ELSE 0 END as pnl_percent
            FROM stocks.positions p
            JOIN stocks.assets a ON p.asset_id = a.id
            LEFT JOIN latest_metrics m ON p.asset_id = m.asset_id
        """)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def add_position(asset_id, quantity, price, date, notes=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO stocks.positions (asset_id, quantity, purchase_price, purchase_date, invested_amount, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (asset_id, quantity, price, date, float(quantity) * float(price), notes))
        conn.commit()
    finally:
        cur.close()
        conn.close()

def delete_position(position_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM stocks.positions WHERE id = %s", (position_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()
