"""
Additional database functions for watchlist management.
"""

import logging
from typing import Optional
from psycopg2.extras import RealDictCursor

from core.db import get_db_connection

logger = logging.getLogger(__name__)


def add_to_watchlist(symbol: str, name: str, coingecko_id: str, category: str = 'Other') -> dict:
    """Add a crypto to the watchlist."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Check if asset already exists
        cur.execute("SELECT id, tracking_type FROM crypto.assets WHERE symbol = %s", (symbol,))
        existing = cur.fetchone()
        
        if existing:
            # Update to watchlist if it's not already
            if existing['tracking_type'] != 'watchlist':
                cur.execute("""
                    UPDATE crypto.assets 
                    SET tracking_type = 'watchlist'
                    WHERE id = %s
                    RETURNING id, symbol, name, category, tracking_type
                """, (existing['id'],))
                result = cur.fetchone()
            else:
                result = existing
        else:
            # Insert new asset
            cur.execute("""
                INSERT INTO crypto.assets (symbol, name, category, chain, tracking_type)
                VALUES (%s, %s, %s, 'multi', 'watchlist')
                RETURNING id, symbol, name, category, tracking_type
            """, (symbol.upper(), name, category))
            result = cur.fetchone()
            
            # Insert source
            cur.execute("""
                INSERT INTO crypto.sources (asset_id, coingecko_id)
                VALUES (%s, %s)
            """, (result['id'], coingecko_id))
        
        conn.commit()
        return dict(result)
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding to watchlist: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def remove_from_watchlist(symbol: str) -> bool:
    """
    Remove a crypto from watchlist (sets is_active=false to preserve history).
    Returns True if successful.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE crypto.assets 
            SET is_active = false
            WHERE symbol = %s AND tracking_type = 'watchlist'
            RETURNING id
        """, (symbol.upper(),))
        
        result = cur.fetchone()
        conn.commit()
        return result is not None
    except Exception as e:
        conn.rollback()
        logger.error(f"Error removing from watchlist: {e}")
        raise
    finally:
        cur.close()
        conn.close()
