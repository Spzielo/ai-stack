"""
Pydantic models for portfolio positions.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal


class PositionCreate(BaseModel):
    """Request to create a new position."""
    symbol: str
    quantity: Decimal = Field(gt=0)
    purchase_price_usd: Decimal = Field(gt=0)
    purchase_date: date
    notes: Optional[str] = None


class PositionUpdate(BaseModel):
    """Request to update a position."""
    quantity: Optional[Decimal] = Field(default=None, gt=0)
    purchase_price_usd: Optional[Decimal] = Field(default=None, gt=0)
    purchase_date: Optional[date] = None
    notes: Optional[str] = None


class Position(BaseModel):
    """Portfolio position with current value calculations."""
    id: int
    symbol: str
    name: str
    quantity: Decimal
    purchase_price_usd: Decimal
    current_price_usd: Optional[Decimal]
    invested_amount_usd: Decimal
    current_value_usd: Optional[Decimal]
    profit_loss_usd: Optional[Decimal]
    profit_loss_percent: Optional[Decimal]
    purchase_date: date
    notes: Optional[str]


class PortfolioSummary(BaseModel):
    """Summary of entire portfolio."""
    total_invested: Decimal
    total_value: Decimal
    total_profit_loss: Decimal
    total_profit_loss_percent: Decimal


class PortfolioResponse(BaseModel):
    """Response with all positions and summary."""
    positions: list[Position]
    summary: PortfolioSummary
