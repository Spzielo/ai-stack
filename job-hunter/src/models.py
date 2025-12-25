from typing import List, Optional, Dict, Literal, Any
from pydantic import BaseModel, Field
from enum import Enum

# --- Enums ---

class Level(str, Enum):
    JUNIOR = "Junior"
    CONFIRMED = "Confirmé"
    SENIOR = "Senior"
    DIRECTION = "Direction"
    EXECUTIVE = "Executive"

class ContractType(str, Enum):
    CDI = "CDI"
    CDD = "CDD"
    FREELANCE = "Freelance"
    INTERNSHIP = "Stage"
    OTHER = "Autre"

class ContextType(str, Enum):
    TURNAROUND = "Redressement"
    GROWTH = "Croissance"
    TRANSFORMATION = "Transformation"
    CREATION = "Création"
    STABILITY = "Stabilité"
    UNKNOWN = "Inconnu"

# --- Master CV Sub-Models ---

class Contact(BaseModel):
    phone: str
    email: str
    linkedin: str

class SalaryTarget(BaseModel):
    min_k: int
    max_k: int
    currency: str
    package_elements: List[str]

class ProfileGeneral(BaseModel):
    name: str
    title_principal: str
    title_variations: Dict[str, str] = {}
    value_proposition: str
    elevator_pitch_30s: str
    contact: Contact
    location: str
    mobility_geographic: str
    mobility_radius_km: int = 0
    availability: str
    salary_target: SalaryTarget
    target_roles: List[str] = []
    target_sectors: List[str] = []
    target_company_size: List[str] = []
    target_contexts: List[str] = []
    values: List[str] = []
    code_of_conduct: List[str] = []

class CompanyDetails(BaseModel):
    groupe: Optional[str] = None
    secteur_precis: Optional[str] = None
    implantation: Optional[str] = None
    ca_groupe: Optional[str] = None
    effectif_groupe: Optional[str] = None
    type: Optional[str] = None
    positionnement: Optional[str] = None

class RoleEvolution(BaseModel):
    periode: str
    titre: str
    focus: str

class RealisationItem(BaseModel):
    id: str
    title: str
    context: str
    challenge: str
    action_detaillee: List[str]
    result_detaille: Dict[str, str]
    figures: str
    impact_mesurable: List[str]
    competences_mobilisees: List[str]
    keywords: List[str]

class RealisationCategory(BaseModel):
    category: str
    items: List[RealisationItem]

class Experience(BaseModel):
    id: str
    company: str
    company_details: Optional[CompanyDetails] = None
    role_official: str
    roles_evolution: List[RoleEvolution] = []
    start_date: str
    end_date: Optional[str] = None
    duration_months: int
    location: str
    employment_type: str
    reporting: str
    membre_instances: List[str] = []
    perimetre_detaille: Dict[str, Any] = {}
    context_arrival: str
    mission_assigned: str
    missions_principales_detaillees: Dict[str, List[str]] = {}
    realisations_ultra_detaillees: List[RealisationCategory] = []
    kpi_pilotes_quotidien: List[Dict[str, Any]] = []
    outils_utilises_quotidien: List[str] = []
    situations_complexes_gerees: List[Dict[str, Any]] = []
    competences_directeur_site_specifiques: List[str] = []
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    variantes_discours: Dict[str, str] = {}

class MasterCVMetadata(BaseModel):
    last_update: str
    version: str
    status: str
    profil_type: str

class MasterCV(BaseModel):
    metadata: MasterCVMetadata
    profile_general: ProfileGeneral
    experiences: List[Experience]
    # Keeping these loosely typed for now as they might be simple strings or legacy objects depending on user JSON tail
    competences: List[Any] = [] 
    education: List[Any] = []
    languages: List[str] = []

# --- Job Offer Analysis Models (Unchanged) ---

class JobMetadata(BaseModel):
    company: Optional[str] = None
    role: str
    location: str
    contract: ContractType
    salary_range: Optional[str] = None
    publication_date: Optional[str] = None

class Requirement(BaseModel):
    years_min: int = 0
    level: Level = Level.CONFIRMED
    sectors: List[str] = []

class JobScope(BaseModel):
    revenue: Optional[str] = None
    team_size: Optional[str] = None
    sites: Optional[str] = None

class JobKeyword(BaseModel):
    term: str
    weight: int
    synonyms: List[str] = []

class JobOffer(BaseModel):
    metadata: JobMetadata
    raw_text: str
    
    context_keywords: List[str] = []
    
    technical_keywords: List[JobKeyword] = []
    soft_skills: List[JobKeyword] = []
    
    requirements: Requirement
    scope: JobScope
    
    must_have: List[str] = []
    nice_to_have: List[str] = []
    key_missions: List[str] = []

# --- Match Result Models (Unchanged) ---

class CategoryScore(BaseModel):
    score: float
    max_score: float
    details: Dict[str, Any] = {}

class MatchResult(BaseModel):
    total_score: float
    level: str
    recommendation: str
    
    details: Dict[str, CategoryScore]
    
    strengths: List[str] = []
    weaknesses: List[str] = []
    personalization_tips: List[str] = []
