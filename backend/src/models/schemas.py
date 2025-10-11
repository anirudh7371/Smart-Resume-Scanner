from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class EducationItem(BaseModel):
    text: str
    start: Optional[str] = None
    end: Optional[str] = None
    confidence: float = 0.0

class ExperienceItem(BaseModel):
    text: str
    start: Optional[str] = None
    end: Optional[str] = None
    confidence: float = 0.0

class ResumeExtract(BaseModel):
    candidate_name: Optional[str] = Field(None, description="Detected candidate name")
    emails: List[str] = []
    phones: List[str] = []
    skills: List[str] = []
    certifications: List[str] = []
    education: List[str] = []
    experience: List[str] = []
    achievements: List[str] = []
    projects: List[str] = []
    publications: List[str] = []
    languages: List[str] = []
    interests: List[str] = []
    raw_text: str
    sections: Dict[str, str] = Field({}, description="Dictionary of detected sections and their content")
