from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Optional
import sys
import os
from loguru import logger
from src.services.resume_parser import ResumeParser
from src.services.match_engine import MatchEngine
from src.services.storage import storage_adapter
from src.models.schemas import JobDescription, ResumeExtract, MatchOutput

router = APIRouter()
try:
    resume_parser = ResumeParser()
    match_engine = MatchEngine()
    logger.info("Successfully initialized ResumeParser and MatchEngine services.")
except Exception as e:
    logger.error(f"Fatal error during service initialization: {e}")
    resume_parser = None
    match_engine = None

@router.on_event("startup")
async def startup_event():
    if not resume_parser or not match_engine:
        logger.warning("Application is starting in a DEGRADED state. One or more services failed to initialize.")

@router.post("/parse", response_model=ResumeExtract, tags=["Resume Parsing"])
async def parse_resume(file: UploadFile = File(..., description="The resume file to parse (PDF, DOCX, or TXT).")):
    """
    Upload a resume file to parse it into a structured JSON format.
    """
    if not resume_parser:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The resume parsing service is not available due to an initialization error."
        )

    logger.info(f"Received file for parsing: {file.filename}")
    content = await file.read()
    try:
        extract = resume_parser.parse_bytes(content, filename=file.filename)
        # Save the parsed resume to the database
        resume_id = storage_adapter.save_resume(extract.model_dump())
        logger.success(f"Successfully parsed and saved resume for candidate: {extract.candidate_name} with ID: {resume_id}")
        return extract
    except Exception as e:
        logger.error(f"Error parsing resume {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse the resume file. Please ensure it is a valid PDF, DOCX, or TXT file. Error: {e}"
        )

@router.post("/match", response_model=MatchOutput, tags=["Resume Matching"])
async def analyze_match(
    resume_text: str = Form(..., description="The full raw text of the resume to be analyzed."),
    job_title: str = Form(..., description="The title of the job position."),
    job_description: str = Form(..., description="The full description of the job."),
    required_skills: Optional[str] = Form(None, description="A comma-separated list of key skills for the job.")
):
    """
    Analyzes the match between a resume's text and a job description using AI.
    """
    if not match_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The matching service is not available due to an initialization error."
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
        logger.error(f"Error during match analysis for job '{job_title}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during the match analysis. Details: {e}"
        )