import feedparser
import requests
import time
from typing import List, Dict, Any
from .models import JobOffer
from .parser import OfferParser
from .scorer import ScoringEngine
from .models import MasterCV
import src.storage as storage

class JobHunter:
    def __init__(self, master_cv: MasterCV):
        self.cv = master_cv
        self.parser = OfferParser()
        self.scorer = ScoringEngine(master_cv)
        # Default sources: Google News RSS for specific Executive queries
        # This aggregates results from many job boards (HelloWork, Cadremploi, APEC, Local Press...)
        base_rss = "https://news.google.com/rss/search?q={}&hl=fr&gl=FR&ceid=FR:fr"
        queries = [
            "Directeur+de+Site+emploi",
            "Directeur+Régional+emploi", 
            "Directeur+Usine+Agroalimentaire",
            "Directeur+Filiale",
            "Directeur+Opérations"
        ]
        self.sources = [base_rss.format(q) for q in queries]
        self.n8n_webhook_url = "http://n8n:5678/webhook/hunt"

    def _trigger_n8n(self):
        """Triggers the n8n workflow via webhook."""
        try:
            print(f"🔌 Triggering n8n workflow at {self.n8n_webhook_url}...")
            # We use a short timeout because we don't need to wait for n8n to finish
            requests.post(self.n8n_webhook_url, json={"trigger": "manual_hunt"}, timeout=2)
        except Exception as e:
            # Swallow error as n8n might not be configured or we don't want to block the main hunt
            print(f"⚠️ Could not trigger n8n: {e}")

    def hunt(self, sources: List[str] = None) -> Dict[str, Any]:
        """
        Fetches offers from sources, scores them, and returns the top 20.
        Also triggers n8n workflow.
        """
        # 1. Trigger n8n in background (fire and forget logic mostly)
        self._trigger_n8n()

        urls = sources if sources else self.sources
        all_leads = []
        
        print(f"🏹 Starting hunt on {len(urls)} sources...")
        
        for url in urls:
            try:
                print(f"Fetching {url}...")
                feed = feedparser.parse(url)
                print(f"Found {len(feed.entries)} entries.")
                
                for entry in feed.entries:
                    # Construct raw text from title + summary/content
                    # RSS structures vary, try to get the most info
                    content = entry.title + "\n\n" 
                    if 'content' in entry:
                        content += entry.content[0].value
                    elif 'summary' in entry:
                        content += entry.summary
                    elif 'description' in entry:
                        content += entry.description
                        
                    link = entry.link if 'link' in entry else ""
                    
                    # Deduplication check could be here (e.g. check storage for this link)
                    # For MVP we re-score (fast enough) or check ID if provided
                    
                    # 1. Parse (Fast Regex first ideally, but using our Parser)
                    # Note: Using LLM parser on 100s of offers is slow/expensive. 
                    # Optimization: We should have a "FastFilter" here.
                    # For this implementation, we will use the Parser but validte it's cost effective.
                    # Actually, for the "Active Hunting" feature user requested, let's assume we proceed.
                    
                    # To be safe and fast, let's do a keyword pre-filter relevant to the CV
                    # If "Director" or "Manager" or "Responsable" or "Chef" not in title, skip?
                    # User is "Directeur de Site", so let's filter a bit.
                    keywords = ["directeur", "responsable", "manager", "head", "lead", "chef", "direction", "site", "usine", "centrale"]
                    if not any(k in entry.title.lower() for k in keywords):
                        continue

                    # Parse
                    offer = self.parser.parse(content)
                    
                    # Inject link into metadata manually since parser sees only text
                    # (Metadata doesn't have link field yet, maybe we assume it's part of source)
                    
                    # Score
                    match_result = self.scorer.compute_match(offer)
                    
                    # If score is decent, save and add to list
                    if match_result.total_score > 40:
                        # Generate content only for top results? No, let's do it lazy or now.
                        # Let's simple-save now.
                        
                        # We won't generate CV/CL for ALL 100 items, only for top 20 to save tokens.
                        
                        all_leads.append({
                            "offer": offer,
                            "match": match_result,
                            "link": link,
                            "original_date": entry.published if 'published' in entry else ""
                        })
                        
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                
        # Sort by score descending
        all_leads.sort(key=lambda x: x["match"].total_score, reverse=True)
        
        # Keep Top 20
        top_20 = all_leads[:20]
        
        # Now finalize: Generate CVs for Top 20 and Save to History
        from .generator import ContentGenerator
        generator = ContentGenerator(self.cv)
        
        results_for_api = []
        
        for lead in top_20:
            offer = lead['offer']
            match = lead['match']
            
            # Generate
            cv = generator.generate_cv(offer, match)
            cl = generator.generate_cover_letter(offer, match)
            
            gen_content = {
                "cv_markdown": cv,
                "cover_letter_markdown": cl
            }
            
            # Save
            run_id = storage.save_analysis_result(
                offer.metadata.model_dump(),
                match.model_dump(),
                gen_content
            )
            
            # Prepare result object
            results_for_api.append({
                "id": run_id,
                "role": offer.metadata.role,
                "company": offer.metadata.company,
                "score": match.total_score,
                "level": match.level,
                "link": lead["link"]
            })
            
        return {
            "scanned_count": len(all_leads), # This is filtered count actually
            "top_20": results_for_api
        }
