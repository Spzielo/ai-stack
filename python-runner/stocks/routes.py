
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import logging
from . import db, provider

router = APIRouter(prefix="/stocks", tags=["stocks"])
logger = logging.getLogger(__name__)

class SearchResponse(BaseModel):
    query: str
    results: List[dict]

class PositionCreate(BaseModel):
    symbol: str
    quantity: float
    price: float
    date: date
    notes: Optional[str] = None

@router.get("/search", response_model=SearchResponse)
async def search_stocks(query: str):
    """Search for stocks via Yahoo Finance"""
    results = await provider.search_assets(query)
    return {"query": query, "results": results}

@router.post("/watchlist/add")
async def add_to_watchlist(symbol: str):
    """Add a stock to the watchlist and fetch initial data"""
    details = provider.get_asset_details(symbol)
    if not details:
        raise HTTPException(status_code=404, detail="Symbol not found or no data available")
    
    # Add to DB
    asset_id = db.add_asset(
        symbol=details['symbol'],
        name=details['name'],
        sector=details.get('sector'),
        industry=details.get('industry'),
        currency=details.get('currency', 'USD'),
        exchange=None # We could parse this but yfinance exchange format varies
    )
    
    # Save initial metrics
    db.update_asset_metrics(asset_id, details)
    
    return {"status": "added", "asset_id": asset_id, "details": details}

@router.get("/dashboard")
async def get_dashboard():
    """Get all tracked stocks with latest metrics and user positions"""
    # Get assets
    assets = db.get_assets()
    
    # Get details for each (from DB mostly, but ideally we'd have a refresh trigger)
    # For now, we assume the DB has data. The user might need a "refresh" button or cron.
    conn = db.get_db_connection()
    cur = conn.cursor(cursor_factory=db.RealDictCursor)
    
    enriched_assets = []
    try:
        cur.execute("""
            SELECT a.*, m.price, m.pe_ratio, m.market_cap, m.dividend_yield, 
                   m.fifty_two_week_high, m.fifty_two_week_low, m.date as last_updated
            FROM stocks.assets a
            LEFT JOIN (
                SELECT DISTINCT ON (asset_id) *
                FROM stocks.metrics_daily
                ORDER BY asset_id, date DESC
            ) m ON a.id = m.asset_id
            WHERE a.is_active = TRUE
            ORDER BY a.symbol
        """)
        enriched_assets = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    positions = db.get_positions()
    
    return {
        "assets": enriched_assets,
        "positions": positions
    }

@router.post("/positions")
async def add_position(pos: PositionCreate):
    # Ensure asset exists
    conn = db.get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM stocks.assets WHERE symbol = %s", (pos.symbol,))
        row = cur.fetchone()
        if not row:
            # Auto-add if not exists? Yes better UX
            # But we need details
            await add_to_watchlist(pos.symbol) # reusing logic
            cur.execute("SELECT id FROM stocks.assets WHERE symbol = %s", (pos.symbol,))
            row = cur.fetchone()
            
        asset_id = row[0]
        db.add_position(asset_id, pos.quantity, pos.price, pos.date, pos.notes)
        return {"status": "success"}
    finally:
        cur.close()
        conn.close()

@router.delete("/positions/{position_id}")
async def delete_position(position_id: int):
    db.delete_position(position_id)
    return {"status": "deleted"}

@router.post("/refresh/{symbol}")
async def refresh_asset(symbol: str):
    """Force refresh of a specific asset data"""
    conn = db.get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM stocks.assets WHERE symbol = %s", (symbol,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        raise HTTPException(404, "Asset not found")
        
    details = provider.get_asset_details(symbol)
    if details:
        db.update_asset_metrics(row[0], details)
        return {"status": "refreshed", "price": details['price']}
    return {"status": "error", "message": "Could not fetch data"}
