from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class EducationItem(BaseModel):
    text: str
    confidence: float = 0.0

class ExperienceItem(BaseModel):
    text: str
    start: Optional[str] = None
    end: Optional[str] = None
    confidence: float = 0.0

class ResumeExtract(BaseModel):
    candidate_name: Optional[str] = Field(None, description="Detected candidate name")
    candidate_name_confidence: float = 0.0
    emails: List[str] = []
    phones: List[str] = []
    skills: List[str] = []
    skills_confidences: Dict[str, float] = {}
    education: List[EducationItem] = []
    experience: List[ExperienceItem] = []
    certifications: List[str] = []
    certifications_confidences: Dict[str, float] = {}
    raw_text: str
    parse_warnings: List[str] = []
