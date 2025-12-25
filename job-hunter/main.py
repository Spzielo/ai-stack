from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os

from src.models import MasterCV, JobOffer
from src.parser import OfferParser
from src.scorer import ScoringEngine
from src.generator import ContentGenerator
from src.hunter import JobHunter
import src.storage as storage

app = FastAPI(title="Job Hunter API", version="1.0")

# CORS Middleware to allow Dashboard (static html or localhost:3000) to fetch
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev, or restrict to ["http://localhost:3000", "http://localhost"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Master CV on startup
MASTER_CV_PATH = "data/master_cv.json"
master_cv = None

def load_master_cv():
    global master_cv
    if os.path.exists(MASTER_CV_PATH):
        with open(MASTER_CV_PATH, "r") as f:
            data = json.load(f)
            master_cv = MasterCV(**data)
    else:
        print("WARNING: Master CV not found at", MASTER_CV_PATH)

load_master_cv()
parser = OfferParser()

class AnalysisRequest(BaseModel):
    raw_text: str
    url: str = ""

class HuntRequest(BaseModel):
    sources: list[str] = []

@app.post("/analyze")
def analyze_offer(request: AnalysisRequest):
    if not master_cv:
        raise HTTPException(status_code=500, detail="Master CV not loaded")
    
    # 1. Parse
    offer = parser.parse(request.raw_text)
    
    # 2. Score
    scorer = ScoringEngine(master_cv)
    match_result = scorer.compute_match(offer)
    
    # 3. Generate
    generator = ContentGenerator(master_cv)
    cv_content = generator.generate_cv(offer, match_result)
    cl_content = generator.generate_cover_letter(offer, match_result)
    
    generated_content = {
        "cv_markdown": cv_content,
        "cover_letter_markdown": cl_content
    }
    
    # 4. Save to History
    run_id = storage.save_analysis_result(
        offer.metadata.model_dump(),
        match_result.model_dump(),
        generated_content
    )
    
    return {
        "id": run_id,
        "offer_metadata": offer.metadata,
        "match": match_result,
        "generated_content": generated_content
    }

@app.post("/hunt")
def trigger_hunt(request: HuntRequest):
    if not master_cv:
        raise HTTPException(status_code=500, detail="Master CV not loaded")
    
    hunter = JobHunter(master_cv)
    results = hunter.hunt(request.sources if request.sources else None)
    
    return results

@app.get("/history")
def get_history():
    """List past analyses (summary)."""
    return storage.get_history_summary()

@app.get("/history/{run_id}")
def get_history_detail(run_id: str):
    """Get full details of a specific analysis."""
    result = storage.get_analysis_detail(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result

@app.get("/")
def health():
    return {"status": "ok", "cv_loaded": master_cv is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
