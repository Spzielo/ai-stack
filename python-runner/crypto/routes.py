"""
FastAPI routes for Crypto One-Glance module.
"""

import logging
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from crypto.models import (
    MetricsBatchRequest,
    EventsBatchRequest,
    IngestResponse,
    ComputeScoresResponse,
    DashboardResponse,
    DashboardAsset,
    AssetDetail,
    TimelineItem,
    MetricDaily,
    Event,
    EventType,
    EventSeverity,
    StatusChange,
)
from crypto.portfolio_models import PositionCreate, PositionUpdate
from crypto import db
from crypto.scoring import compute_all_scores

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crypto", tags=["crypto"])


# --- Ingestion Endpoints ---

@router.post("/ingest/metrics", response_model=IngestResponse)
async def ingest_metrics(request: MetricsBatchRequest):
    """
    Ingest batch of daily metrics.
    """
    try:
        metrics = []
        errors = []
        
        for item in request.items:
            # Get asset by symbol
            asset = db.get_asset_by_symbol(item.symbol)
            if not asset:
                errors.append(f"Asset not found: {item.symbol}")
                continue
            
            metrics.append(
                MetricDaily(
                    asset_id=asset['id'],
                    date=item.date,
                    price_usd=item.price_usd,
                    market_cap=item.market_cap,
                    volume_24h=item.volume_24h,
                    tvl=item.tvl,
                    fees_24h=item.fees_24h,
                    revenue_24h=item.revenue_24h,
                    raw=item.raw,
                )
            )
        
        inserted, updated = db.upsert_metrics(metrics)
        
        return IngestResponse(
            ingested=inserted,
            skipped=len(request.items) - inserted,
            errors=errors,
        )
    
    except Exception as e:
        logger.error(f"Error ingesting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/events", response_model=IngestResponse)
async def ingest_events(request: EventsBatchRequest):
    """
    Ingest batch of events.
    """
    try:
        events = []
        errors = []
        
        for item in request.items:
            # Get asset by symbol
            asset = db.get_asset_by_symbol(item.symbol)
            if not asset:
                errors.append(f"Asset not found: {item.symbol}")
                continue
            
            # Generate event hash
            event_hash = db.generate_event_hash(
                asset['id'],
                item.type.value,
                item.title,
                item.timestamp,
            )
            
            events.append(
                Event(
                    asset_id=asset['id'],
                    event_hash=event_hash,
                    timestamp=item.timestamp,
                    type=item.type,
                    title=item.title,
                    url=item.url,
                    severity=item.severity,
                    summary=item.summary,
                    content=item.content,
                )
            )
        
        inserted, skipped = db.upsert_events(events)
        
        return IngestResponse(
            ingested=inserted,
            skipped=skipped,
            errors=errors,
        )
    
    except Exception as e:
        logger.error(f"Error ingesting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Computation Endpoints ---

@router.post("/compute/scores", response_model=ComputeScoresResponse)
async def compute_scores():
    """
    Compute scores for all active assets.
    """
    try:
        scores, status_changes = compute_all_scores()
        
        # Save scores to database
        db.upsert_scores(scores)
        
        return ComputeScoresResponse(
            computed=len(scores),
            status_changes=[
                StatusChange(
                    symbol=sc['symbol'],
                    from_status=sc['from_status'],
                    to_status=sc['to_status'],
                    reason=sc['reason'],
                )
                for sc in status_changes
            ],
        )
    
    except Exception as e:
        logger.error(f"Error computing scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Read Endpoints ---

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    tracking_type: Optional[str] = Query(default=None, regex="^(top50|watchlist)$")
):
    """
    Get watchlist dashboard with latest scores and events.
    Optional filter by tracking_type: 'top50' or 'watchlist'
    """
    try:
        # Get assets with optional filter
        if tracking_type:
            assets = db.get_assets_by_tracking_type(tracking_type)
        else:
            assets = db.get_active_assets()
        
        dashboard_assets = []
        
        for asset in assets:
            asset_id = asset['id']
            
            # Get latest metrics
            metrics = db.get_latest_metrics(asset_id, days=1)
            latest_metric = metrics[0] if metrics else None
            
            # Get latest score
            score = db.get_latest_score(asset_id)
            
            # Get last event
            events = db.get_recent_events(asset_id, limit=1)
            last_event = None
            if events:
                e = events[0]
                last_event = {
                    "type": e['type'],
                    "title": e['title'],
                    "timestamp": e['timestamp'].isoformat(),
                    "severity": e['severity'],
                }
            
            dashboard_assets.append(
                DashboardAsset(
                    symbol=asset['symbol'],
                    name=asset['name'],
                    category=asset['category'],
                    tracking_type=asset.get("tracking_type", "watchlist"),  # Add tracking_type
                    price_usd=latest_metric['price_usd'] if latest_metric else None,
                    total_score=score['total_score'] if score else None,
                    status=score['status'] if score else None,
                    flags=score['flags'] if score else [],
                    last_event=last_event,
                )
            )
        
        return DashboardResponse(
            updated_at=datetime.now(),
            assets=dashboard_assets,
        )
    
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/{symbol}", response_model=AssetDetail)
async def get_asset_detail(symbol: str):
    """
    Get detailed one-pager for an asset.
    """
    try:
        # Get asset
        asset = db.get_asset_by_symbol(symbol.upper())
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset not found: {symbol}")
        
        asset_id = asset['id']
        
        # Get latest metrics
        metrics = db.get_latest_metrics(asset_id, days=30)
        latest_metric = metrics[0] if metrics else None
        
        # Get latest score
        score = db.get_latest_score(asset_id)
        
        # Get thesis note
        thesis = db.get_thesis_note(asset_id)
        
        # Get recent events
        events = db.get_recent_events(asset_id, limit=10)
        recent_events = [
            {
                "id": e['id'],
                "timestamp": e['timestamp'].isoformat(),
                "type": e['type'],
                "title": e['title'],
                "url": e['url'],
                "severity": e['severity'],
                "summary": e['summary'],
            }
            for e in events
        ]
        
        # Format metrics for sparkline
        metrics_30d = [
            {
                "date": m['date'].isoformat(),
                "price_usd": float(m['price_usd']) if m['price_usd'] else None,
                "tvl": float(m['tvl']) if m['tvl'] else None,
                "volume_24h": float(m['volume_24h']) if m['volume_24h'] else None,
            }
            for m in reversed(metrics)
        ]
        
        return AssetDetail(
            symbol=asset['symbol'],
            name=asset['name'],
            category=asset['category'],
            chain=asset['chain'],
            price_usd=float(latest_metric['price_usd']) if latest_metric and latest_metric['price_usd'] else None,
            market_cap=float(latest_metric['market_cap']) if latest_metric and latest_metric['market_cap'] else None,
            tvl=float(latest_metric['tvl']) if latest_metric and latest_metric['tvl'] else None,
            total_score=score['total_score'] if score else None,
            fundamentals_score=score['fundamentals_score'] if score else None,
            tokenomics_score=score['tokenomics_score'] if score else None,
            momentum_score=score['momentum_score'] if score else None,
            status=score['status'] if score else None,
            flags=score['flags'] if score else [],
            thesis=thesis['thesis'] if thesis else None,
            risks=thesis['risks'] if thesis else None,
            catalyst_90d=thesis['catalyst_90d'] if thesis else None,
            catalyst_12m=thesis['catalyst_12m'] if thesis else None,
            dca_plan=thesis['dca_plan'] if thesis else None,
            recent_events=recent_events,
            metrics_30d=metrics_30d,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting asset detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/{symbol}/timeline", response_model=List[TimelineItem])
async def get_asset_timeline(
    symbol: str,
    days: int = Query(default=90, ge=1, le=365)
):
    """
    Get timeline of events and metrics for an asset.
    """
    try:
        # Get asset
        asset = db.get_asset_by_symbol(symbol.upper())
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset not found: {symbol}")
        
        asset_id = asset['id']
        
        # Get metrics
        metrics = db.get_latest_metrics(asset_id, days=days)
        
        # Get events
        events = db.get_recent_events(asset_id, limit=100)
        
        # Combine into timeline
        timeline = []
        
        for m in metrics:
            timeline.append(
                TimelineItem(
                    timestamp=datetime.combine(m['date'], datetime.min.time()),
                    type="metric",
                    data={
                        "price_usd": float(m['price_usd']) if m['price_usd'] else None,
                        "market_cap": float(m['market_cap']) if m['market_cap'] else None,
                        "volume_24h": float(m['volume_24h']) if m['volume_24h'] else None,
                        "tvl": float(m['tvl']) if m['tvl'] else None,
                    },
                )
            )
        
        for e in events:
            timeline.append(
                TimelineItem(
                    timestamp=e['timestamp'],
                    type="event",
                    data={
                        "event_type": e['type'],
                        "title": e['title'],
                        "url": e['url'],
                        "severity": e['severity'],
                        "summary": e['summary'],
                    },
                )
            )
        
        # Sort by timestamp descending
        timeline.sort(key=lambda x: x.timestamp, reverse=True)
        
        return timeline
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/{symbol}/metrics")
async def get_asset_metrics(
    symbol: str,
    range: str = Query(default="30d", regex="^\\d+d$")
):
    """
    Get metrics for an asset with date range filter.
    """
    try:
        # Parse range
        days = int(range.rstrip('d'))
        
        # Get asset
        asset = db.get_asset_by_symbol(symbol.upper())
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset not found: {symbol}")
        
        # Get metrics
        metrics = db.get_latest_metrics(asset['id'], days=days)
        
        return {
            "symbol": symbol,
            "range": range,
            "metrics": [
                {
                    "date": m['date'].isoformat(),
                    "price_usd": float(m['price_usd']) if m['price_usd'] else None,
                    "market_cap": float(m['market_cap']) if m['market_cap'] else None,
                    "volume_24h": float(m['volume_24h']) if m['volume_24h'] else None,
                    "tvl": float(m['tvl']) if m['tvl'] else None,
                    "fees_24h": float(m['fees_24h']) if m['fees_24h'] else None,
                    "revenue_24h": float(m['revenue_24h']) if m['revenue_24h'] else None,
                }
                for m in reversed(metrics)
            ],
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Trigger Endpoints ---

@router.post("/trigger/collect")
async def trigger_collect():
    """
    Trigger manual data collection from CoinGecko.
    Fetches prices for all active assets (top50 + watchlist).
    """
    import httpx
    from datetime import date
    
    try:
        logger.info("Triggering manual data collection...")
        
        # Get all active assets with their coingecko IDs
        assets = db.get_active_assets()
        
        # Build list of coingecko IDs
        coin_ids = []
        asset_map = {}  # coingecko_id -> asset
        
        for asset in assets:
            if asset.get('coingecko_id'):
                coin_ids.append(asset['coingecko_id'])
                asset_map[asset['coingecko_id']] = asset
        
        if not coin_ids:
            return {
                "success": False,
                "message": "No assets with CoinGecko IDs found",
                "ingested": 0
            }
        
        # Fetch from CoinGecko (batch request)
        url = 'https://api.coingecko.com/api/v3/coins/markets'
        params = {
            'vs_currency': 'usd',
            'ids': ','.join(coin_ids),
            'order': 'market_cap_desc',
            'per_page': 250,
            'page': 1
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            coingecko_data = response.json()
        
        logger.info(f"Received data for {len(coingecko_data)} coins from CoinGecko")
        
        # Build metrics payload
        metrics = []
        today = str(date.today())
        
        for coin in coingecko_data:
            asset = asset_map.get(coin['id'])
            if asset:
                metrics.append(
                    MetricDaily(
                        asset_id=asset['id'],
                        date=today,
                        price_usd=coin.get('current_price'),
                        market_cap=coin.get('market_cap'),
                        volume_24h=coin.get('total_volume'),
                        raw={'source': 'coingecko', 'data': coin}
                    )
                )
        
        # Ingest metrics
        inserted, updated = db.upsert_metrics(metrics)
        
        logger.info(f"Data collection completed: {inserted} inserted, {updated} updated")
        
        return {
            "success": True,
            "message": "Data collection completed successfully",
            "ingested": inserted,
            "updated": updated,
            "total": len(coingecko_data)
        }
    
    except httpx.HTTPError as e:
        logger.error(f"HTTP error during collection: {e}")
        raise HTTPException(status_code=502, detail=f"CoinGecko API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error triggering collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))




# --- Watchlist Management Endpoints ---

@router.post("/watchlist/add")
async def add_to_watchlist_endpoint(symbol: str, name: str, coingecko_id: str, category: str = 'Other'):
    """
    Add a cryptocurrency to your personal watchlist.
    """
    from crypto.watchlist import add_to_watchlist as add_watchlist
    
    try:
        logger.info(f"Adding {symbol} to watchlist")
        result = add_watchlist(symbol, name, coingecko_id, category)
        
        return {
            "success": True,
            "message": f"{symbol} added to watchlist",
            "asset": result
        }
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist_endpoint(symbol: str):
    """
    Remove a cryptocurrency from your watchlist.
    Note: This deactivates the asset but preserves historical data.
    """
    from crypto.watchlist import remove_from_watchlist as remove_watchlist
    
    try:
        logger.info(f"Removing {symbol} from watchlist")
        success = remove_watchlist(symbol)
        
        if success:
            return {
                "success": True,
                "message": f"{symbol} removed from watchlist"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Asset {symbol} not found in watchlist")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Portfolio Endpoints ---

@router.post("/portfolio/positions")
async def create_position(request: PositionCreate):
    """
    Add a new portfolio position.
    """
    from crypto import portfolio_db
    from crypto.portfolio_models import PositionCreate
    
    try:
        # Get asset by symbol
        asset = db.get_asset_by_symbol(request.symbol)
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {request.symbol} not found")
        
        # Calculate invested amount
        invested_amount = request.quantity * request.purchase_price_usd
        
        # Add position
        position = portfolio_db.add_position(
            asset_id=asset['id'],
            quantity=request.quantity,
            purchase_price=request.purchase_price_usd,
            purchase_date=str(request.purchase_date),
            notes=request.notes
        )
        
        logger.info(f"Created position for {request.symbol}: {request.quantity} @ ${request.purchase_price_usd}")
        
        return {
            "success": True,
            "position": {
                "id": position['id'],
                "symbol": request.symbol,
                "quantity": float(position['quantity']),
                "purchase_price_usd": float(position['purchase_price_usd']),
                "invested_amount_usd": float(position['invested_amount_usd']),
                "purchase_date": str(position['purchase_date'])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/positions")
async def get_portfolio():
    """
    Get all portfolio positions with current values and profit/loss calculations.
    """
    from crypto import portfolio_db
    from decimal import Decimal
    
    try:
        positions = portfolio_db.get_all_positions()
        
        portfolio_positions = []
        total_invested = Decimal(0)
        total_value = Decimal(0)
        
        for pos in positions:
            # Get current price
            metrics = db.get_latest_metrics(pos['asset_id'], days=1)
            current_price = Decimal(metrics[0]['price_usd']) if metrics and metrics[0].get('price_usd') else None
            
            # Calculate current value and profit/loss
            quantity = Decimal(pos['quantity'])
            invested = Decimal(pos['invested_amount_usd'])
            
            if current_price:
                current_value = quantity * current_price
                profit_loss = current_value - invested
                profit_loss_percent = (profit_loss / invested * 100) if invested > 0 else Decimal(0)
            else:
                current_value = None
                profit_loss = None
                profit_loss_percent = None
            
            portfolio_positions.append({
                "id": pos['id'],
                "symbol": pos['symbol'],
                "name": pos['name'],
                "category": pos['category'],
                "quantity": float(quantity),
                "purchase_price_usd": float(pos['purchase_price_usd']),
                "current_price_usd": float(current_price) if current_price else None,
                "invested_amount_usd": float(invested),
                "current_value_usd": float(current_value) if current_value else None,
                "profit_loss_usd": float(profit_loss) if profit_loss else None,
                "profit_loss_percent": float(profit_loss_percent) if profit_loss_percent else None,
                "purchase_date": str(pos['purchase_date']),
                "notes": pos['notes']
            })
            
            total_invested += invested
            if current_value:
                total_value += current_value
        
        # Calculate totals
        total_profit_loss = total_value - total_invested
        total_profit_loss_percent = (total_profit_loss / total_invested * 100) if total_invested > 0 else Decimal(0)
        
        return {
            "positions": portfolio_positions,
            "summary": {
                "total_invested": float(total_invested),
                "total_value": float(total_value),
                "total_profit_loss": float(total_profit_loss),
                "total_profit_loss_percent": float(total_profit_loss_percent)
            }
        }
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/portfolio/positions/{position_id}")
async def update_position_endpoint(position_id: int, request: PositionUpdate):
    """
    Update an existing portfolio position.
    """
    from crypto import portfolio_db
    from crypto.portfolio_models import PositionUpdate
    
    try:
        position = portfolio_db.update_position(
            position_id=position_id,
            quantity=request.quantity,
            purchase_price=request.purchase_price_usd,
            purchase_date=str(request.purchase_date) if request.purchase_date else None,
            notes=request.notes
        )
        
        logger.info(f"Updated position {position_id}")
        
        return {
            "success": True,
            "position": {
                "id": position['id'],
                "quantity": float(position['quantity']),
                "purchase_price_usd": float(position['purchase_price_usd']),
                "invested_amount_usd": float(position['invested_amount_usd']),
                "purchase_date": str(position['purchase_date'])
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/portfolio/positions/{position_id}")
async def delete_position_endpoint(position_id: int):
    """
    Delete a portfolio position.
    """
    from crypto import portfolio_db
    
    try:
        success = portfolio_db.delete_position(position_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Position {position_id} not found")
        
        logger.info(f"Deleted position {position_id}")
        
        return {
            "success": True,
            "message": f"Position {position_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting position: {e}")
        raise HTTPException(status_code=500, detail=str(e))
