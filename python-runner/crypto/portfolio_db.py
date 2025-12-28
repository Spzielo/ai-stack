"""
Database operations for portfolio positions.
"""

import logging
from typing import List, Optional, Tuple
from decimal import Decimal
from psycopg2.extras import RealDictCursor

from core.db import get_db_connection

logger = logging.getLogger(__name__)


def add_position(asset_id: int, quantity: Decimal, purchase_price: Decimal, 
                 purchase_date: str, notes: Optional[str] = None) -> dict:
    """Add a new portfolio position."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        invested_amount = quantity * purchase_price
        
        cur.execute("""
            INSERT INTO crypto.positions 
                (asset_id, quantity, purchase_price_usd, purchase_date, invested_amount_usd, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, asset_id, quantity, purchase_price_usd, purchase_date, 
                      invested_amount_usd, notes, created_at
        """, (asset_id, quantity, purchase_price, purchase_date, invested_amount, notes))
        
        result = cur.fetchone()
        conn.commit()
        return dict(result)
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding position: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def get_all_positions() -> List[dict]:
    """Get all portfolio positions with asset info."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                p.id, p.asset_id, p.quantity, p.purchase_price_usd, 
                p.purchase_date, p.invested_amount_usd, p.notes,
                a.symbol, a.name, a.category
            FROM crypto.positions p
            JOIN crypto.assets a ON p.asset_id = a.id
            ORDER BY p.purchase_date DESC
        """)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def update_position(position_id: int, quantity: Optional[Decimal] = None,
                   purchase_price: Optional[Decimal] = None,
                   purchase_date: Optional[str] = None,
                   notes: Optional[str] = None) -> dict:
    """Update an existing position."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get current position to calculate invested_amount if needed
        if quantity is not None or purchase_price is not None:
            cur.execute("""
                SELECT quantity, purchase_price_usd 
                FROM crypto.positions 
                WHERE id = %s
            """, (position_id,))
            current = cur.fetchone()
            if not current:
                raise ValueError(f"Position {position_id} not found")
            
            # Use new values if provided, otherwise keep current
            final_quantity = quantity if quantity is not None else current['quantity']
            final_price = purchase_price if purchase_price is not None else current['purchase_price_usd']
            invested_amount = final_quantity * final_price
        
        # Build dynamic update query
        updates = []
        params = []
        
        if quantity is not None:
            updates.append("quantity = %s")
            params.append(quantity)
        
        if purchase_price is not None:
            updates.append("purchase_price_usd = %s")
            params.append(purchase_price)
        
        if purchase_date is not None:
            updates.append("purchase_date = %s")
            params.append(purchase_date)
        
        if notes is not None:
            updates.append("notes = %s")
            params.append(notes)
        
        # Update invested_amount if quantity or price changed
        if quantity is not None or purchase_price is not None:
            updates.append("invested_amount_usd = %s")
            params.append(invested_amount)
        
        updates.append("updated_at = NOW()")
        params.append(position_id)
        
        query = f"""
            UPDATE crypto.positions 
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, asset_id, quantity, purchase_price_usd, purchase_date, 
                      invested_amount_usd, notes, updated_at
        """
        
        cur.execute(query, params)
        result = cur.fetchone()
        conn.commit()
        
        if not result:
            raise ValueError(f"Position {position_id} not found")
        
        return dict(result)
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating position: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def delete_position(position_id: int) -> bool:
    """Delete a position."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM crypto.positions WHERE id = %s RETURNING id", (position_id,))
        result = cur.fetchone()
        conn.commit()
        return result is not None
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting position: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def get_position_by_id(position_id: int) -> Optional[dict]:
    """Get a single position by ID."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                p.id, p.asset_id, p.quantity, p.purchase_price_usd, 
                p.purchase_date, p.invested_amount_usd, p.notes,
                a.symbol, a.name
            FROM crypto.positions p
            JOIN crypto.assets a ON p.asset_id = a.id
            WHERE p.id = %s
        """, (position_id,))
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()
