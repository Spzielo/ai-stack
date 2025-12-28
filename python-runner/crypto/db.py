"""
Database operations for Crypto One-Glance module.
"""

import hashlib
import logging
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor

from core.db import get_db_connection
from crypto.models import (
    Asset,
    MetricDaily,
    Event,
    Score,
    ThesisNote,
    EventType,
    EventSeverity,
    Status,
)

logger = logging.getLogger(__name__)


def generate_event_hash(asset_id: int, event_type: str, title: str, timestamp: datetime) -> str:
    """Generate unique hash for event deduplication."""
    content = f"{asset_id}:{event_type}:{title}:{timestamp.isoformat()}"
    return hashlib.sha256(content.encode()).hexdigest()


def get_active_assets() -> List[dict]:
    """Get all active assets with their sources."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                a.id, a.symbol, a.name, a.category, a.chain, a.tracking_type,
                s.coingecko_id, s.defillama_slug, s.tokenunlocks_id,
                s.governance_url, s.twitter_handle, s.github_url
            FROM crypto.assets a
            LEFT JOIN crypto.sources s ON a.id = s.asset_id
            WHERE a.is_active = true
            ORDER BY a.symbol
        """)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def get_asset_by_symbol(symbol: str) -> Optional[dict]:
    """Get asset by symbol."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, symbol, name, category, chain, is_active, tracking_type
            FROM crypto.assets
            WHERE symbol = %s
        """, (symbol,))
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def get_assets_by_tracking_type(tracking_type: str) -> List[dict]:
    """Get assets filtered by tracking type ('top50' or 'watchlist')."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                a.id, a.symbol, a.name, a.category, a.chain, a.tracking_type,
                s.coingecko_id, s.defillama_slug, s.tokenunlocks_id,
                s.governance_url, s.twitter_handle, s.github_url
            FROM crypto.assets a
            LEFT JOIN crypto.sources s ON a.id = s.asset_id
            WHERE a.is_active = true AND a.tracking_type = %s
            ORDER BY a.symbol
        """, (tracking_type,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def upsert_metrics(metrics: List[MetricDaily]) -> Tuple[int, int]:
    """
    Insert or update daily metrics.
    Returns (inserted_count, updated_count).
    """
    if not metrics:
        return 0, 0
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        values = [
            (
                m.asset_id,
                m.date,
                m.price_usd,
                m.market_cap,
                m.volume_24h,
                m.tvl,
                m.fees_24h,
                m.revenue_24h,
                psycopg2.extras.Json(m.raw) if m.raw else None,
            )
            for m in metrics
        ]
        
        execute_values(
            cur,
            """
            INSERT INTO crypto.metrics_daily 
                (asset_id, date, price_usd, market_cap, volume_24h, tvl, fees_24h, revenue_24h, raw)
            VALUES %s
            ON CONFLICT (asset_id, date) 
            DO UPDATE SET
                price_usd = EXCLUDED.price_usd,
                market_cap = EXCLUDED.market_cap,
                volume_24h = EXCLUDED.volume_24h,
                tvl = EXCLUDED.tvl,
                fees_24h = EXCLUDED.fees_24h,
                revenue_24h = EXCLUDED.revenue_24h,
                raw = EXCLUDED.raw,
                created_at = NOW()
            """,
            values,
        )
        
        conn.commit()
        inserted = len(metrics)
        return inserted, 0
    except Exception as e:
        conn.rollback()
        logger.error(f"Error upserting metrics: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def upsert_events(events: List[Event]) -> Tuple[int, int]:
    """
    Insert events with hash-based deduplication.
    Returns (inserted_count, skipped_count).
    """
    if not events:
        return 0, 0
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        inserted = 0
        skipped = 0
        
        for event in events:
            try:
                cur.execute(
                    """
                    INSERT INTO crypto.events 
                        (asset_id, event_hash, timestamp, type, title, url, severity, summary, content)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_hash) DO NOTHING
                    """,
                    (
                        event.asset_id,
                        event.event_hash,
                        event.timestamp,
                        event.type.value,
                        event.title,
                        event.url,
                        event.severity.value,
                        event.summary,
                        event.content,
                    ),
                )
                if cur.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.warning(f"Error inserting event {event.title}: {e}")
                skipped += 1
        
        conn.commit()
        return inserted, skipped
    except Exception as e:
        conn.rollback()
        logger.error(f"Error upserting events: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def upsert_scores(scores: List[Score]) -> int:
    """Insert or update scores."""
    if not scores:
        return 0
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        values = [
            (
                s.asset_id,
                s.date,
                s.fundamentals_score,
                s.tokenomics_score,
                s.momentum_score,
                s.total_score,
                s.status.value,
                psycopg2.extras.Json(s.flags),
            )
            for s in scores
        ]
        
        execute_values(
            cur,
            """
            INSERT INTO crypto.scores 
                (asset_id, date, fundamentals_score, tokenomics_score, momentum_score, 
                 total_score, status, flags)
            VALUES %s
            ON CONFLICT (asset_id, date) 
            DO UPDATE SET
                fundamentals_score = EXCLUDED.fundamentals_score,
                tokenomics_score = EXCLUDED.tokenomics_score,
                momentum_score = EXCLUDED.momentum_score,
                total_score = EXCLUDED.total_score,
                status = EXCLUDED.status,
                flags = EXCLUDED.flags,
                created_at = NOW()
            """,
            values,
        )
        
        conn.commit()
        return len(scores)
    except Exception as e:
        conn.rollback()
        logger.error(f"Error upserting scores: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def get_latest_metrics(asset_id: int, days: int = 30) -> List[dict]:
    """Get latest metrics for an asset."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute(
            """
            SELECT date, price_usd, market_cap, volume_24h, tvl, fees_24h, revenue_24h
            FROM crypto.metrics_daily
            WHERE asset_id = %s
            ORDER BY date DESC
            LIMIT %s
            """,
            (asset_id, days),
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def get_latest_score(asset_id: int) -> Optional[dict]:
    """Get latest score for an asset."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute(
            """
            SELECT date, fundamentals_score, tokenomics_score, momentum_score,
                   total_score, status, flags
            FROM crypto.scores
            WHERE asset_id = %s
            ORDER BY date DESC
            LIMIT 1
            """,
            (asset_id,),
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def get_recent_events(asset_id: int, limit: int = 10) -> List[dict]:
    """Get recent events for an asset."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute(
            """
            SELECT id, timestamp, type, title, url, severity, summary
            FROM crypto.events
            WHERE asset_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
            """,
            (asset_id, limit),
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def get_thesis_note(asset_id: int) -> Optional[dict]:
    """Get thesis note for an asset."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute(
            """
            SELECT thesis, risks, catalyst_90d, catalyst_12m, dca_plan, updated_at
            FROM crypto.thesis_notes
            WHERE asset_id = %s
            """,
            (asset_id,),
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def get_previous_score(asset_id: int, before_date: date) -> Optional[dict]:
    """Get the score before a given date."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute(
            """
            SELECT status
            FROM crypto.scores
            WHERE asset_id = %s AND date < %s
            ORDER BY date DESC
            LIMIT 1
            """,
            (asset_id, before_date),
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()
