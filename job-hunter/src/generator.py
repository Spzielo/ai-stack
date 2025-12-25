from .models import MasterCV, JobOffer, MatchResult

class ContentGenerator:
    def __init__(self, master_cv: MasterCV):
        self.cv = master_cv

    def generate_cv(self, offer: JobOffer, match: MatchResult) -> str:
        # Markdown Template adapted for the new complex structure
        
        prof = self.cv.profile_general
        
        md = f"""# {prof.name}
## {prof.title_principal}
**{prof.location}** | {prof.contact.email} | {prof.contact.phone}
[LinkedIn]({prof.contact.linkedin})

> **PROFIL**: {prof.value_proposition}

---
### 🎯 MATCHING AVEC LE POSTE : {offer.metadata.role}
**Verdict : {match.recommendation} (Score: {match.total_score}/100)**
*Points forts :* {', '.join(match.strengths) if match.strengths else "Expertise sectorielle et fonctionnelle"}

---
### 💼 EXPÉRIENCE PROFESSIONNELLE

"""
        # Iterate over experiences
        for exp in self.cv.experiences:
            # Format dates
            dates = f"{exp.start_date} - {exp.end_date or 'Présent'}"
            
            md += f"""### {exp.role_official} | **{exp.company}**
*{dates} | {exp.location}*
"""
            if exp.company_details:
                md += f"> *{exp.company_details.secteur_precis} ({exp.company_details.type}) - {exp.company_details.ca_groupe}*\n\n"
            
            md += f"**Mission:** {exp.mission_assigned}\n\n"
            
            # Add selected key realizations (flattening categories for MVP CV)
            md += "**Réalisations Clés :**\n"
            limit = 3
            count = 0
            for cat in exp.realisations_ultra_detaillees:
                for item in cat.items:
                    if count >= limit: break
                    md += f"- **{item.title}**: {item.figures or 'Succès mesuré'}\n"
                    count += 1
                if count >= limit: break
            
            md += "\n"
                
        md += "\n### 🛠️ COMPÉTENCES CLÉS\n"
        # Extract from last exp + profile
        skills = set()
        if self.cv.experiences:
            skills.update(self.cv.experiences[0].technical_skills[:6])
            skills.update(self.cv.experiences[0].competences_directeur_site_specifiques[:4])
            
        for s in skills:
            md += f"- {s}\n"
            
        return md

    def generate_cover_letter(self, offer: JobOffer, match: MatchResult) -> str:
        prof = self.cv.profile_general
        
        # Prepare content to avoid backslashes in f-strings (Python < 3.12 limitation)
        company_name = offer.metadata.company or "votre entreprise"
        sector_focused = prof.target_sectors[0] if prof.target_sectors else 'Management'
        
        context_interest = 'les défis opérationnels'
        if offer.context_keywords:
            context_interest = offer.context_keywords[0]
            
        mission_str = "structurer et développer l'activité"
        if offer.key_missions:
            mission_str = offer.key_missions[0]
            
        tech_str = "la performance"
        if offer.technical_keywords:
            tech_str = ', '.join([k.term for k in offer.technical_keywords[:2]])
            
        exp_years = 0
        if self.cv.experiences:
            exp_years = sum(e.duration_months for e in self.cv.experiences) // 12
            
        company_ref = "Mericq"
        if self.cv.experiences:
            company_ref = self.cv.experiences[0].company
            
        realization_1 = "Piloter des P&L complexes"
        realization_2 = "Manager des équipes pluridisciplinaires"
        
        if self.cv.experiences and self.cv.experiences[0].realisations_ultra_detaillees:
            # Try to get items from the first category
            items = self.cv.experiences[0].realisations_ultra_detaillees[0].items
            if len(items) > 0: realization_1 = items[0].title
            if len(items) > 1: realization_2 = items[1].title
        
        # AIDA Structure
        return f"""
{prof.name}
{prof.contact.email}
{prof.contact.phone}
{prof.location}

À l'attention du Recruteur,
Chez {company_name}

**Objet : Candidature pour le poste de {offer.metadata.role}**

Madame, Monsieur,

**[ATTENTION]**
Expert en {sector_focused} avec une forte appétence pour {context_interest}, j'ai découvert votre offre pour le poste de {offer.metadata.role} avec un grand intérêt.

**[INTÉRÊT]**
Votre recherche d'un profil capable de {mission_str} résonne parfaitement avec mon parcours. J'ai noté l'importance que vous accordez à {tech_str}.

**[DÉSIR]**
Au cours de mes {exp_years} années d'expérience, notamment chez {company_ref}, j'ai pu :
- {realization_1}
- {realization_2}

Je suis convaincu de pouvoir apporter la même rigueur et le même engagement à vos équipes.

**[ACTION]**
Je serais ravi de convenir d'un entretien pour vous détailler mes motivations et mon adéquation avec vos enjeux actuels.

Dans cette attente, je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

{prof.name}
"""
