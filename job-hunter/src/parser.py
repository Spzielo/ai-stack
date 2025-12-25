import re
from typing import Dict, Any, List
from .models import JobOffer, JobMetadata, Requirement, JobScope, JobKeyword
from .llm_utils import LLMService

class OfferParser:
    def __init__(self):
        self.llm = LLMService()

    def parse(self, raw_text: str) -> JobOffer:
        # 1. Regex Extraction (Fast & Cheap)
        # TODO: Add specific regex for email, dates, etc if needed.
        
        # 2. LLM Extraction (Smart)
        system_prompt = """
        You are an expert HR Recruiter. Analyze the job offer below and extract structured data.
        
        Output JSON format:
        {
            "metadata": {
                "company": "...",
                "role": "...",
                "location": "...",
                "contract": "CDI/Freelance/etc",
                "salary_range": "..."
            },
            "requirements": {
                "years_min": int,
                "level": "Junior/Confirme/Senior/Direction",
                "sectors": ["..."]
            },
            "scope": {
                "revenue": "...",
                "team_size": "...", 
                "sites": "..."
            },
            "context_keywords": ["Redressement", "Croissance", "Creation", "Transformation", "Stabilite"],
            "technical_keywords": [{"term": "Python", "weight": 10}, ...],
            "soft_skills": [{"term": "Leadership", "weight": 8}, ...],
            "must_have": ["..."],
            "nice_to_have": ["..."],
            "key_missions": ["..."]
        }
        """
        
        data = self.llm.extract_json(system_prompt, raw_text)
        
        # 3. Convert to Pydantic Model
        # We act defensively if keys are missing
        meta = data.get("metadata", {})
        reqs = data.get("requirements", {})
        scope = data.get("scope", {})
        
        return JobOffer(
            metadata=JobMetadata(
                company=meta.get("company"),
                role=meta.get("role", "Unknown Role"),
                location=meta.get("location", "Remote"),
                contract=meta.get("contract", "Autre"),
                salary_range=meta.get("salary_range")
            ),
            raw_text=raw_text,
            context_keywords=data.get("context_keywords", []),
            technical_keywords=[JobKeyword(**k) for k in data.get("technical_keywords", [])],
            soft_skills=[JobKeyword(**k) for k in data.get("soft_skills", [])],
            requirements=Requirement(
                years_min=reqs.get("years_min", 0),
                level=reqs.get("level", "Confirmé"),
                sectors=reqs.get("sectors", [])
            ),
            scope=JobScope(
                revenue=scope.get("revenue"),
                team_size=scope.get("team_size"),
                sites=scope.get("sites")
            ),
            must_have=data.get("must_have", []),
            nice_to_have=data.get("nice_to_have", []),
            key_missions=data.get("key_missions", [])
        )
