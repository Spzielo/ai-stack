import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

DATA_DIR = "data"
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

def _load_history() -> List[Dict[str, Any]]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def _save_history(history: List[Dict[str, Any]]):
    # Ensure data dir exists
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def save_analysis_result(offer_data: Dict, match_result: Dict, generated_content: Dict) -> str:
    """Saves an analysis result and returns its ID."""
    run_id = str(uuid.uuid4())
    
    entry = {
        "id": run_id,
        "timestamp": datetime.now().isoformat(),
        "company": offer_data.get("company") or "Entreprise Inconnue",
        "role": offer_data.get("role") or "Poste Inconnu",
        "score": match_result.get("total_score", 0),
        "level": match_result.get("level", "N/A"),
        "offer_metadata": offer_data,
        "match": match_result,
        "generated_content": generated_content
    }
    
    history = _load_history()
    # Prepend new entry
    history.insert(0, entry)
    _save_history(history)
    
    return run_id

def get_history_summary() -> List[Dict[str, Any]]:
    """Returns a lightweight list of past analyses."""
    history = _load_history()
    summary = []
    for entry in history:
        summary.append({
            "id": entry["id"],
            "timestamp": entry["timestamp"],
            "company": entry.get("company"),
            "role": entry.get("role"),
            "score": entry.get("score"),
            "level": entry.get("level")
        })
    return summary

def get_analysis_detail(run_id: str) -> Optional[Dict[str, Any]]:
    """Returns full details for a specific run ID."""
    history = _load_history()
    for entry in history:
        if entry["id"] == run_id:
            return entry
    return None
