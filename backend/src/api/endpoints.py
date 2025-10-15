from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional, List
import io
from loguru import logger
from src.services.resume_parser import ResumeParser
from src.services.match_engine import MatchEngine
from src.services.storage import storage_adapter
from src.services.pdf_generator import PDFReportGenerator
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document
from src.models.schemas import JobDescription, ResumeExtract, MatchOutput

router = APIRouter()
try:
    resume_parser = ResumeParser()
    match_engine = MatchEngine()
    pdf_generator = PDFReportGenerator()
    logger.info("Successfully initialized services.")
except Exception as e:
    logger.error(f"Fatal error during service initialization: {e}")
    resume_parser = None
    match_engine = None
    pdf_generator = None

@router.on_event("startup")
async def startup_event():
    if not resume_parser or not match_engine:
        logger.warning("Application is starting in a DEGRADED state.")

@router.post("/match-multiple", tags=["Resume Matching"])
async def match_multiple_candidates(
    job_description_text: Optional[str] = Form(None),
    job_description_file: Optional[UploadFile] = File(None),
    resume_files: List[UploadFile] = File(...),
    top_k: int = Form(5)
):
    """
    Analyzes multiple resumes against a job description and returns top K candidates.
    """
    if not resume_parser or not match_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Services are not available."
        )

    job_desc_text = ""
    if job_description_file:
        content = await job_description_file.read()
        try:
            ext = job_description_file.filename.split('.')[-1].lower()
            if ext == "pdf":
                job_desc_text = pdf_extract_text(io.BytesIO(content))
            elif ext in ["docx", "doc"]:
                doc = Document(io.BytesIO(content))
                job_desc_text = "\n".join([p.text for p in doc.paragraphs])
            else:
                job_desc_text = content.decode(errors='ignore')
        except Exception as e:
            logger.error(f"Failed to parse job description file: {e}")
            raise HTTPException(status_code=400, detail="Invalid job description file")
    elif job_description_text:
        job_desc_text = job_description_text
    else:
        raise HTTPException(status_code=400, detail="Job description is required")

    candidates = []
    resume_texts = {}
    
    for resume_file in resume_files:
        try:
            content = await resume_file.read()
            resume_extract = resume_parser.parse_bytes(content, filename=resume_file.filename)
            candidates.append({
                "resume": resume_extract,
                "filename": resume_file.filename
            })
            resume_texts[resume_file.filename] = resume_extract.raw_text
        except Exception as e:
            logger.error(f"Failed to parse {resume_file.filename}: {e}")
            continue

    if not candidates:
        raise HTTPException(status_code=400, detail="No valid resumes could be parsed")

    scored_candidates = []
    for candidate in candidates:
        try:
            match_result = await match_engine.score_resume_against_job_text(
                candidate["resume"], 
                job_desc_text
            )
            scored_candidates.append({
                "candidate_name": candidate["resume"].candidate_name or "Unknown",
                "filename": candidate["filename"],
                "match_score": match_result.match_score,
                "strengths": match_result.strengths,
                "gaps": match_result.gaps,
                "justification": match_result.justification
            })
        except Exception as e:
            logger.error(f"Failed to score {candidate['filename']}: {e}")
            continue

    scored_candidates.sort(key=lambda x: x["match_score"], reverse=True)
    top_candidates = scored_candidates[:top_k]

    logger.success(f"Analyzed {len(candidates)} candidates, returning top {len(top_candidates)}")
    
    return {
        "total_candidates": len(candidates),
        "top_k": top_k,
        "top_candidates": top_candidates,
        "resume_texts": resume_texts
    }

@router.post("/generate-report", tags=["Resume Matching"])
async def generate_pdf_report(
    job_description_text: str = Form(...),
    candidates_json: str = Form(...),
    resume_texts_json: str = Form(...)
):
    """
    Generate a PDF report from match results
    """
    if not pdf_generator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PDF generation service not available"
        )
    
    try:
        import json
        candidates = json.loads(candidates_json)
        resume_texts = json.loads(resume_texts_json)
        
        pdf_buffer = pdf_generator.generate_report(
            job_description=job_description_text,
            candidates=candidates,
            resume_texts=resume_texts
        )
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=candidate_analysis_report.pdf"}
        )
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

@router.post("/parse", response_model=ResumeExtract, tags=["Resume Parsing"])
async def parse_resume(file: UploadFile = File(...)):
    """Upload a resume file to parse it into a structured JSON format."""
    if not resume_parser:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The resume parsing service is not available."
        )

    logger.info(f"Received file for parsing: {file.filename}")
    content = await file.read()
    try:
        extract = resume_parser.parse_bytes(content, filename=file.filename)
        resume_id = storage_adapter.save_resume(extract.model_dump())
        logger.success(f"Successfully parsed and saved resume: {extract.candidate_name} with ID: {resume_id}")
        return extract
    except Exception as e:
        logger.error(f"Error parsing resume {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse the resume file: {e}"
        )

@router.post("/match", response_model=MatchOutput, tags=["Resume Matching"])
async def analyze_match(
    resume_text: str = Form(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
    required_skills: Optional[str] = Form(None)
):
    """Analyzes the match between a resume's text and a job description."""
    if not match_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The matching service is not available."
        )

    logger.info(f"Analyzing match for job title: {job_title}")
    try:
        resume_extract = resume_parser.parse_text(resume_text)
        skills_list = [skill.strip() for skill in required_skills.split(',')] if required_skills else []
        job = JobDescription(title=job_title, description=job_description, required_skills=skills_list)
        result = await match_engine.score_candidate_against_job(resume_extract, job)
        logger.success(f"Match analysis complete for '{resume_extract.candidate_name}'. Score: {result.match_score}")
        return result
    except Exception as e:
        logger.error(f"Error during match analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )

@router.get("/resumes", response_model=List[ResumeExtract], tags=["Resume Data"])
async def get_all_resumes(limit: int = 20):
    resumes = storage_adapter.get_all_resumes(limit=limit)
    return [ResumeExtract(**resume) for resume in resumes]