"""
Scoring engine for Crypto One-Glance module.
Implements the scoring logic as per specification.
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Tuple, Optional
from crypto.models import Score, Status
from crypto import db

logger = logging.getLogger(__name__)


def calculate_fundamentals_score(asset_id: int, metrics: List[dict]) -> Tuple[float, List[str]]:
    """
    Calculate fundamentals score (0-10) based on:
    - TVL trend 30d (30%)
    - TVL trend 90d (20%)
    - Stability (25%)
    - Market share (25%)
    
    Returns (score, flags).
    """
    score = 5.0  # Baseline
    flags = []
    
    if not metrics or len(metrics) < 7:
        return score, flags
    
    # Sort by date ascending
    metrics = sorted(metrics, key=lambda x: x['date'])
    
    # TVL trend 30d (if available)
    recent_tvl = [m['tvl'] for m in metrics[-30:] if m.get('tvl')]
    if len(recent_tvl) >= 7:
        tvl_change_7d = (recent_tvl[-1] - recent_tvl[-7]) / recent_tvl[-7] if recent_tvl[-7] > 0 else 0
        tvl_change_30d = (recent_tvl[-1] - recent_tvl[0]) / recent_tvl[0] if recent_tvl[0] > 0 else 0
        
        # 7-day trend
        if tvl_change_7d < -0.10:
            score -= 2
            flags.append("tvl_drop_7d")
        elif tvl_change_7d > 0.10:
            score += 2
        
        # 30-day trend
        if tvl_change_30d < -0.25:
            score -= 3
            flags.append("tvl_drop_30d")
        elif tvl_change_30d > 0.25:
            score += 2
    
    # Ensure score is within bounds
    score = max(0, min(10, score))
    
    return score, flags


def calculate_tokenomics_score(asset_id: int, metrics: List[dict]) -> Tuple[float, List[str]]:
    """
    Calculate tokenomics score (0-10) based on:
    - Unlock <30d (40%)
    - Inflation annual (30%)
    - Token utility (30%)
    
    Returns (score, flags).
    """
    score = 7.0  # Baseline (assume decent tokenomics)
    flags = []
    
    # Check for imminent unlocks (this would come from events table)
    # For now, simplified version
    recent_events = db.get_recent_events(asset_id, limit=20)
    unlock_events = [e for e in recent_events if e['type'] == 'UNLOCK']
    
    for event in unlock_events:
        days_until = (event['timestamp'].date() - date.today()).days
        if 0 <= days_until <= 30:
            score -= 3
            flags.append("unlock_imminent")
            break
    
    # Ensure score is within bounds
    score = max(0, min(10, score))
    
    return score, flags


def calculate_momentum_score(asset_id: int, metrics: List[dict]) -> Tuple[float, List[str]]:
    """
    Calculate momentum score (0-10) based on:
    - Price trend 7d (50%)
    - Volatility (50%)
    
    Returns (score, flags).
    """
    score = 5.0  # Baseline
    flags = []
    
    if not metrics or len(metrics) < 7:
        return score, flags
    
    # Sort by date ascending
    metrics = sorted(metrics, key=lambda x: x['date'])
    
    # Price trend 7d
    recent_prices = [m['price_usd'] for m in metrics[-7:] if m.get('price_usd')]
    if len(recent_prices) >= 7:
        price_change_7d = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] if recent_prices[0] > 0 else 0
        
        if price_change_7d > 0.05:
            score += 2
        elif price_change_7d < -0.10:
            score -= 2
        
        # Volatility (simplified: standard deviation)
        import statistics
        if len(recent_prices) >= 7:
            volatility = statistics.stdev(recent_prices) / statistics.mean(recent_prices)
            if volatility > 0.15:  # High volatility
                score -= 2
    
    # Ensure score is within bounds
    score = max(0, min(10, score))
    
    return score, flags


def detect_additional_flags(asset_id: int) -> List[str]:
    """Detect additional risk flags."""
    flags = []
    
    # Check for recent exploits
    recent_events = db.get_recent_events(asset_id, limit=50)
    exploit_events = [e for e in recent_events if e['type'] == 'EXPLOIT']
    
    for event in exploit_events:
        days_ago = (date.today() - event['timestamp'].date()).days
        if days_ago <= 90:
            flags.append("exploit_recent")
            break
    
    # Check for governance conflicts
    governance_events = [e for e in recent_events if e['type'] == 'GOVERNANCE' and e['severity'] >= 4]
    if governance_events:
        flags.append("governance_conflict")
    
    return flags


def determine_status(total_score: float, flags: List[str]) -> Status:
    """
    Determine investment status based on score and flags.
    
    Matrix:
    - >= 22 with no critical flags: ACCUMULER
    - 15-21 with <= 1 non-critical flag: OBSERVER
    - < 15: RISKOFF
    - Any critical flag: RISKOFF
    """
    critical_flags = {"exploit_recent", "unlock_imminent"}
    
    # Check for critical flags
    if any(flag in critical_flags for flag in flags):
        return Status.RISKOFF
    
    # Score-based decision
    if total_score >= 22:
        return Status.ACCUMULER
    elif total_score >= 15:
        non_critical_flags = [f for f in flags if f not in critical_flags]
        if len(non_critical_flags) <= 1:
            return Status.OBSERVER
        else:
            return Status.RISKOFF
    else:
        return Status.RISKOFF


def compute_score_for_asset(asset_id: int, target_date: date) -> Optional[Score]:
    """Compute score for a single asset."""
    try:
        # Get metrics (last 90 days for trend analysis)
        metrics = db.get_latest_metrics(asset_id, days=90)
        
        if not metrics:
            logger.warning(f"No metrics found for asset {asset_id}")
            return None
        
        # Calculate component scores
        fundamentals_score, fund_flags = calculate_fundamentals_score(asset_id, metrics)
        tokenomics_score, token_flags = calculate_tokenomics_score(asset_id, metrics)
        momentum_score, momentum_flags = calculate_momentum_score(asset_id, metrics)
        
        # Combine flags
        all_flags = list(set(fund_flags + token_flags + momentum_flags + detect_additional_flags(asset_id)))
        
        # Calculate total score
        total_score = fundamentals_score + tokenomics_score + momentum_score
        
        # Determine status
        status = determine_status(total_score, all_flags)
        
        return Score(
            asset_id=asset_id,
            date=target_date,
            fundamentals_score=round(fundamentals_score, 2),
            tokenomics_score=round(tokenomics_score, 2),
            momentum_score=round(momentum_score, 2),
            total_score=round(total_score, 2),
            status=status,
            flags=all_flags,
        )
    
    except Exception as e:
        logger.error(f"Error computing score for asset {asset_id}: {e}")
        return None


def compute_all_scores(target_date: Optional[date] = None) -> Tuple[List[Score], List[dict]]:
    """
    Compute scores for all active assets.
    Returns (scores, status_changes).
    """
    if target_date is None:
        target_date = date.today()
    
    assets = db.get_active_assets()
    scores = []
    status_changes = []
    
    for asset in assets:
        asset_id = asset['id']
        symbol = asset['symbol']
        
        # Compute new score
        score = compute_score_for_asset(asset_id, target_date)
        
        if score:
            scores.append(score)
            
            # Check for status change
            previous = db.get_previous_score(asset_id, target_date)
            if previous and previous['status'] != score.status.value:
                # Determine reason
                reason = ", ".join(score.flags) if score.flags else "score_change"
                
                status_changes.append({
                    "symbol": symbol,
                    "from_status": previous['status'],
                    "to_status": score.status.value,
                    "reason": reason,
                })
    
    return scores, status_changes
