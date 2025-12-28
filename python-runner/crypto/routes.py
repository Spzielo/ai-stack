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
async def get_dashboard():
    """
    Get watchlist dashboard with latest scores and events.
    """
    try:
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
    Executes the collection script.
    """
    import subprocess
    
    try:
        logger.info("Triggering manual data collection...")
        
        # Execute the collection script
        result = subprocess.run(
            ["python", "scripts/collect_crypto_metrics.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info("Data collection completed successfully")
            return {
                "success": True,
                "message": "Data collection completed successfully",
                "output": result.stdout
            }
        else:
            logger.error(f"Data collection failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Collection failed: {result.stderr}"
            )
    
    except subprocess.TimeoutExpired:
        logger.error("Data collection timed out")
        raise HTTPException(status_code=504, detail="Collection timed out")
    except Exception as e:
        logger.error(f"Error triggering collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

