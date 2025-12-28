"""
Pydantic models for watchlist management.
"""
from pydantic import BaseModel


class WatchlistAddRequest(BaseModel):
    """Request to add a crypto to watchlist."""
    symbol: str
    name: str
    coingecko_id: str
    category: str = 'Other'


class WatchlistResponse(BaseModel):
    """Response after watchlist operation."""
    success: bool
    message: str
    asset: dict = None
