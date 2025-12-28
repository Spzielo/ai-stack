"""
Pydantic models for Crypto One-Glance module.
"""

from datetime import date, datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


# Enums

class AssetCategory(str, Enum):
    DEFI = "DeFi"
    L1 = "L1"
    L2 = "L2"
    ORACLE = "Oracle"
    INFRA = "Infra"


class EventType(str, Enum):
    GOVERNANCE = "GOVERNANCE"
    UNLOCK = "UNLOCK"
    EXPLOIT = "EXPLOIT"
    RELEASE = "RELEASE"
    WHALE = "WHALE"
    REGULATION = "REGULATION"


class EventSeverity(int, Enum):
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class Status(str, Enum):
    ACCUMULER = "ACCUMULER"
    OBSERVER = "OBSERVER"
    RISKOFF = "RISKOFF"


# Domain Models

class Asset(BaseModel):
    id: int
    symbol: str
    name: str
    category: Optional[AssetCategory] = None
    chain: Optional[str] = None
    is_active: bool = True


class Source(BaseModel):
    asset_id: int
    coingecko_id: Optional[str] = None
    defillama_slug: Optional[str] = None
    tokenunlocks_id: Optional[str] = None
    governance_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    github_url: Optional[str] = None


class MetricDaily(BaseModel):
    asset_id: int
    date: date
    price_usd: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    tvl: Optional[float] = None
    fees_24h: Optional[float] = None
    revenue_24h: Optional[float] = None
    raw: Optional[dict] = None


class Event(BaseModel):
    id: Optional[int] = None
    asset_id: int
    event_hash: str
    timestamp: datetime
    type: EventType
    title: str
    url: Optional[str] = None
    severity: EventSeverity
    summary: Optional[str] = None
    content: Optional[str] = None


class Score(BaseModel):
    asset_id: int
    date: date
    fundamentals_score: float = Field(ge=0, le=10)
    tokenomics_score: float = Field(ge=0, le=10)
    momentum_score: float = Field(ge=0, le=10)
    total_score: float = Field(ge=0, le=30)
    status: Status
    flags: List[str] = []


class ThesisNote(BaseModel):
    asset_id: int
    thesis: Optional[str] = None
    risks: Optional[str] = None
    catalyst_90d: Optional[str] = None
    catalyst_12m: Optional[str] = None
    dca_plan: Optional[str] = None


# Request/Response Models

class MetricItem(BaseModel):
    symbol: str
    date: date
    price_usd: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    tvl: Optional[float] = None
    fees_24h: Optional[float] = None
    revenue_24h: Optional[float] = None
    raw: Optional[dict] = None


class MetricsBatchRequest(BaseModel):
    items: List[MetricItem]


class EventItem(BaseModel):
    symbol: str
    timestamp: datetime
    type: EventType
    title: str
    url: Optional[str] = None
    severity: EventSeverity
    summary: Optional[str] = None
    content: Optional[str] = None


class EventsBatchRequest(BaseModel):
    items: List[EventItem]


class IngestResponse(BaseModel):
    ingested: int
    skipped: int = 0
    errors: List[str] = []


class StatusChange(BaseModel):
    symbol: str
    from_status: Optional[Status]
    to_status: Status
    reason: str


class ComputeScoresResponse(BaseModel):
    computed: int
    status_changes: List[StatusChange] = []


class DashboardAsset(BaseModel):
    symbol: str
    name: str
    category: Optional[str]
    tracking_type: Optional[str] = "watchlist"  # Add tracking_type
    price_usd: Optional[float]
    total_score: Optional[float]
    status: Optional[Status]
    flags: List[str] = []
    last_event: Optional[dict] = None


class DashboardResponse(BaseModel):
    updated_at: datetime
    assets: List[DashboardAsset]


class AssetDetail(BaseModel):
    # Basic info
    symbol: str
    name: str
    category: Optional[str]
    chain: Optional[str]
    
    # Current metrics
    price_usd: Optional[float]
    market_cap: Optional[float]
    tvl: Optional[float]
    
    # Scoring
    total_score: Optional[float]
    fundamentals_score: Optional[float]
    tokenomics_score: Optional[float]
    momentum_score: Optional[float]
    status: Optional[Status]
    flags: List[str] = []
    
    # Thesis
    thesis: Optional[str]
    risks: Optional[str]
    catalyst_90d: Optional[str]
    catalyst_12m: Optional[str]
    dca_plan: Optional[str]
    
    # Recent data
    recent_events: List[dict] = []
    metrics_30d: List[dict] = []


class TimelineItem(BaseModel):
    timestamp: datetime
    type: str  # "event" or "metric"
    data: dict
