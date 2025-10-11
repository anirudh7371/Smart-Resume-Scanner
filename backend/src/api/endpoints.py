from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import List, Optional
from src.services.resume_parser import ResumeParser
from src.services.match_engine import MatchEngine
from src.models.schemas import JobDescription, ResumeExtract, MatchOutput

router = APIRouter()
parser = ResumeParser()
engine = MatchEngine()

@router.post("/upload_resume", response_model=ResumeExtract)
async def upload_resume(file: UploadFile = File(...)):
    """
    Accept a PDF or text resume, parse it, store (on storage layer), and return structured extract.
    """
    content = await file.read()
    try:
        extract = parser.parse_bytes(content, filename=file.filename)
        # TODO: store extract via storage service and return id
        return extract
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/analyze_match", response_model=MatchOutput)
async def analyze_match(resume_text: Optional[str] = Form(None),
                        resume_id: Optional[str] = Form(None),
                        job_title: str = Form(...),
                        job_description: str = Form(...)):
    """
    Accept either resume_text or resume_id (already stored), compute semantic matching and return JSON.
    """
    if resume_text is None and resume_id is None:
        raise HTTPException(status_code=400, detail="Provide resume_text or resume_id")
    # If resume_id -> fetch from storage (TODO)
    if resume_text:
        extract = parser.parse_text(resume_text)
    else:
        # TODO: implement storage fetch
        extract = parser.fetch_by_id(resume_id)
    job = JobDescription(title=job_title, description=job_description)
    result = engine.score_candidate(extract, job)
    return result

@router.get("/get_shortlist")
def get_shortlist(job_id: str, top_k: int = 10):
    """
    Return top-k candidates for a stored job (TODO: implement storage retrieval).
    """
    # placeholder
    return {"job_id": job_id, "top_k": top_k, "candidates": []}
