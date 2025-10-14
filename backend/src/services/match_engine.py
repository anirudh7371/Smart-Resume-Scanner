from typing import List, Dict, Any
import numpy as np
import json
import re
import ollama
from loguru import logger
import google.generativeai as genai
from src.config import settings
from src.models.schemas import ResumeExtract, JobDescription, MatchOutput
from src.services.bias_mitigator import BiasMitigator


class MatchEngine:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.embedding_model_name = settings.GEMINI_EMBEDDING_MODEL
        self.model_name = settings.OLLAMA_MODEL
        self.bias_mitigator = BiasMitigator()
        self.dimension = settings.EMBEDDING_DIMENSION
        self.job_cache: Dict[str, List[float]] = {}

    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using Gemini Embedding API."""
        try:
            result = await genai.embed_content_async(
                model=self.embedding_model_name,
                content=texts,
                task_type="RETRIEVAL_DOCUMENT"
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return [[0.0] * self.dimension for _ in texts]

    async def score_resume_against_job_text(
        self, resume: ResumeExtract, job_description_text: str
    ) -> MatchOutput:
        """Score a resume vs job description using local LLM via Ollama."""

        resume_summary = f"Skills: {', '.join(resume.skills)}. " \
                         f"Experience: {', '.join(resume.experience[:2])}. " \
                         f"Education: {', '.join(resume.education[:2])}"

        # Compute simple cosine similarity
        job_emb = (await self._embed_texts([job_description_text]))[0]
        resume_emb = (await self._embed_texts([resume_summary]))[0]
        similarity = np.dot(job_emb, resume_emb) / (
            np.linalg.norm(job_emb) * np.linalg.norm(resume_emb)
        )
        base_score = float(np.clip((similarity + 1) * 5, 0, 10))

        # Build the LLM prompt
        prompt = f"""
You are an expert recruiter. Compare this resume to the job description.

CANDIDATE:
Name: {resume.candidate_name}
Skills: {', '.join(resume.skills)}
Experience: {' | '.join(resume.experience[:3])}
Education: {' | '.join(resume.education)}

JOB DESCRIPTION:
{job_description_text}

Provide JSON only:
{{
  "match_score": <1-10>,
  "strengths": ["strength1", "strength2", "strength3"],
  "gaps": ["gap1", "gap2"],
  "justification": "<2-3 sentences>"
}}
        """.strip()

        # Call local Ollama model
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {"role": "system", "content": "You are a professional recruiter assistant."},
                {"role": "user", "content": prompt}
            ])
            text = response['message']['content']
            match = re.search(r"\{.*\}", text, re.DOTALL)
            parsed = json.loads(match.group(0)) if match else {}
        except Exception as e:
            logger.warning(f"Ollama LLM parsing failed: {e}")
            parsed = {}

        # Extract fields safely
        strengths = parsed.get("strengths", resume.skills[:3])
        gaps = parsed.get("gaps", ["More relevant experience needed"])
        justification = parsed.get(
            "justification",
            f"Candidate shows {base_score:.1f}/10 alignment with the role."
        )
        llm_score = parsed.get("match_score", base_score)

        job = JobDescription(title="Position", description=job_description_text, required_skills=[])
        mitigated = self.bias_mitigator.apply_checks(llm_score, resume, job)
        final_score = mitigated.get("score", llm_score)

        return MatchOutput(
            candidate_name=resume.candidate_name or "Unknown",
            match_score=round(final_score, 2),
            strengths=strengths[:5],
            gaps=gaps[:5],
            justification=justification,
            details={"similarity": float(similarity), "base_score": base_score}
        )