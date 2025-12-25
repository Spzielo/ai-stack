from typing import List, Optional
from .models import MasterCV, JobOffer, MatchResult, CategoryScore, Level, Experience

class ScoringEngine:
    def __init__(self, master_cv: MasterCV):
        self.cv = master_cv

    def compute_match(self, offer: JobOffer) -> MatchResult:
        # 1. Experience Score (Max 30)
        exp_score = self._score_experience(offer)
        
        # 2. Technical Skills (Max 35)
        tech_score = self._score_technical(offer)
        
        # 3. Scope (Max 15)
        scope_score = self._score_scope(offer)
        
        # 4. Context (Max 10)
        context_score = self._score_context(offer)
        
        # 5. Location (Max 5)
        loc_score = self._score_location(offer)
        
        # 6. Bonus (Max 5)
        bonus_score = self._score_bonus(offer)
        
        total = exp_score.score + tech_score.score + scope_score.score + context_score.score + loc_score.score + bonus_score.score
        total = min(100, max(0, total)) # Clamp 0-100
        
        # Determine Level
        if total >= 90: level = "Excellent Match 🌟"
        elif total >= 75: level = "Bon Match ✅"
        elif total >= 60: level = "Acceptable ⚠️"
        else: level = "Faible ❌"
        
        return MatchResult(
            total_score=total,
            level=level,
            recommendation=self._get_recommendation(total),
            details={
                "experience": exp_score,
                "technical": tech_score,
                "scope": scope_score,
                "context": context_score,
                "location": loc_score,
                "bonus": bonus_score
            }
        )

    # --- Helpers ---
    
    def _score_experience(self, offer: JobOffer) -> CategoryScore:
        score = 0
        details = {}
        
        # 1.1 Years (10pts)
        total_years = sum(exp.duration_months for exp in self.cv.experiences) / 12
        required_years = offer.requirements.years_min
        
        if total_years >= required_years + 5: pts = 10
        elif total_years >= required_years: pts = 8
        elif total_years >= required_years - 2: pts = 5
        else: pts = 0
        score += pts
        details['years_pts'] = pts
        
        # 1.2 Level (10pts)
        # Check against profile_general.title_principal or variations
        pts = 0
        target_titles = [self.cv.profile_general.title_principal.lower()] + \
                        [v.lower() for v in self.cv.profile_general.title_variations.values()] + \
                        [r.lower() for r in self.cv.profile_general.target_roles]
                        
        if any(t in offer.metadata.role.lower() for t in target_titles):
            pts = 10
        else:
            # Partial match?
            pts = 5 
            
        score += pts
        details['level_pts'] = pts
        
        # 1.3 Sector (10pts)
        # Check if any target sector matches offer requirements
        # required sectors might be empty if not extracted, so check text?
        # Using target_sectors from profile
        sector_match = False
        if offer.requirements.sectors:
            sector_match = any(
                s.lower() in [req.lower() for req in offer.requirements.sectors] 
                for s in self.cv.profile_general.target_sectors
            )
        else:
            # Fallback: check raw text for sector keywords
            sector_match = any(s.lower() in offer.raw_text.lower() for s in self.cv.profile_general.target_sectors)
            
        if sector_match: pts = 10
        else: pts = 2 # lenient fallback
        score += pts
        details['sector_pts'] = pts
        
        return CategoryScore(score=score, max_score=30, details=details)

    def _score_technical(self, offer: JobOffer) -> CategoryScore:
        score = 0
        details = {}
        # 2.1 Technical Keywords (20pts)
        matched = []
        missing = []
        
        # Flatten CV skills from new structure
        # Skills are in:
        # 1. self.cv.experiences[i].technical_skills (list of str)
        # 2. self.cv.experiences[i].competences_directeur_site_specifiques (list of str)
        # 3. self.cv.competences (if any, legacy)
        
        cv_skills = set()
        for exp in self.cv.experiences:
            for s in exp.technical_skills:
                cv_skills.add(s.lower())
            for s in exp.competences_directeur_site_specifiques:
                cv_skills.add(s.lower())
                
        # Also check profile_general if we add skills there later, 
        # currently they are mostly in experiences.
            
        required_skills = [k.term.lower() for k in offer.technical_keywords]
        
        if not required_skills:
            score += 15 # Default if extraction failed or no hard skills
        else:
            matches = 0
            for req in required_skills:
                # Fuzzy match? "salesforce" in "salesforce crm"?
                if any(req in s or s in req for s in cv_skills):
                    matches += 1
                    matched.append(req)
                else:
                    missing.append(req)
            
            # Proportional score
            if required_skills:
                score += (matches / len(required_skills)) * 20
        
        details['matched'] = matched
        details['missing'] = missing
        
        # 2.2 Soft Skills (15pts) 
        # From experiences.soft_skills + profile_general.values/code_of_conduct
        cv_soft = set()
        for exp in self.cv.experiences:
            for s in exp.soft_skills:
                cv_soft.add(s.lower())
        for v in self.cv.profile_general.values:
            cv_soft.add(v.lower())
            
        required_soft = [k.term.lower() for k in offer.soft_skills]
        if required_soft:
             matches_soft = 0
             for req in required_soft:
                 if any(req in s for s in cv_soft):
                     matches_soft += 1
             score += (matches_soft / len(required_soft)) * 15
        else:
            score += 10 # Default good
        
        return CategoryScore(score=min(35, score), max_score=35, details=details)

    def _score_scope(self, offer: JobOffer) -> CategoryScore:
        # 3.1 Team Size & Revenue logic
        # Check if offer scope mentions "directeur" or "m€" and if our profile matches
        
        score = 5 # base
        
        # If offer mentions revenue (e.g. "P&L"), match!
        if 'p&l' in offer.raw_text.lower() or 'ebitda' in offer.raw_text.lower():
             score += 5
             
        # If offer mentions team management
        if 'management' in offer.raw_text.lower() or 'équipe' in offer.raw_text.lower():
            score += 5
            
        return CategoryScore(score=score, max_score=15, details={"note": "Scope estimation based on keywords"})

    def _score_context(self, offer: JobOffer) -> CategoryScore:
        score = 5
        # Check overlap between target_contexts and offer text
        matches = []
        for ctx in self.cv.profile_general.target_contexts:
            if ctx.split('/')[0].strip().lower() in offer.raw_text.lower(): # e.g. "Redressement"
                matches.append(ctx)
                score += 2.5
                
        return CategoryScore(score=min(10, score), max_score=10, details={'matches': matches})

    def _score_location(self, offer: JobOffer) -> CategoryScore:
        # Check against profile_general.location and mobility
        cv_loc = self.cv.profile_general.location.lower()
        offer_loc = offer.metadata.location.lower()
        
        score = 0
        if any(z.lower() in offer_loc for z in ["montélimar", "drôme", "rhône-alpes", "aura", "suisse", "grand-est"]):
            score = 5
        # Also check mobility_geographic string
        elif "france" in self.cv.profile_general.mobility_geographic.lower() and "france" in offer_loc:
             score = 3
             
        return CategoryScore(score=score, max_score=5)

    def _score_bonus(self, offer: JobOffer) -> CategoryScore:
        return CategoryScore(score=0, max_score=5)

    def _get_recommendation(self, score: float) -> str:
        if score >= 90: return "🔥 Candidature Prioritaire !"
        if score >= 75: return "✅ Candidature Recommandée"
        if score >= 60: return "⚠️ Candidature Possible (à adapter)"
        return "⛔ Ne pas candidater"
