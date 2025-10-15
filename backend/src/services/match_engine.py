from typing import List, Dict, Any
import numpy as np
import google.generativeai as genai
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.config import settings
from src.models.schemas import ResumeExtract, JobDescription, MatchOutput


class MatchEngine:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.embedding_model_name = settings.GEMINI_EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.job_cache: Dict[str, List[float]] = {}
        self.llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            temperature=0.3,
            base_url="http://localhost:11434"
        )
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert recruiter. Analyze resumes and provide structured JSON output only."),
            ("user", "{input}")
        ])
        self.parser = JsonOutputParser()
        self.chain = self.prompt_template | self.llm | self.parser

    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        result = await genai.embed_content_async(
            model=self.embedding_model_name,
            content=texts,
            task_type="RETRIEVAL_DOCUMENT"
        )
        return result["embedding"]

    async def score_resume_against_job_text(
        self, resume: ResumeExtract, job_description_text: str
    ) -> MatchOutput:

        resume_summary = f"Skills: {', '.join(resume.skills)}. " \
                         f"Experience: {', '.join(resume.experience[:2])}. " \
                         f"Education: {', '.join(resume.education[:2])}"

        job_emb = (await self._embed_texts([job_description_text]))[0]
        resume_emb = (await self._embed_texts([resume_summary]))[0]
        similarity = np.dot(job_emb, resume_emb) / (
            np.linalg.norm(job_emb) * np.linalg.norm(resume_emb)
        )
        base_score = float(np.clip((similarity + 1) * 5, 0, 10))

        prompt_content = f"""
Compare this resume to the job description and provide analysis.

CANDIDATE:
Name: {resume.candidate_name}
Skills: {', '.join(resume.skills)}
Experience: {' | '.join(resume.experience[:3])}
Education: {' | '.join(resume.education)}

JOB DESCRIPTION:
{job_description_text}

Respond with valid JSON only (no markdown, no extra text):
{{
  "match_score": <number between 1-10>,
  "strengths": ["strength1", "strength2", "strength3"],
  "gaps": ["gap1", "gap2"],
  "justification": "<2-3 sentences explaining the match>"
}}
        """.strip()

        parsed = await self.chain.ainvoke({"input": prompt_content})

        strengths = parsed.get("strengths", resume.skills[:3])
        gaps = parsed.get("gaps", ["More relevant experience needed"])
        justification = parsed.get(
            "justification",
            f"Candidate shows {base_score:.1f}/10 alignment with the role."
        )
        llm_score = float(parsed.get("match_score", base_score))
        final_score = np.clip(llm_score, 0.0, 10.0)

        return MatchOutput(
            candidate_name=resume.candidate_name or "Unknown",
            match_score=round(final_score, 2),
            strengths=strengths[:5],
            gaps=gaps[:5],
            justification=justification,
            details={"similarity": float(similarity), "base_score": base_score}
        )

    async def score_candidate_against_job(
        self, resume: ResumeExtract, job: JobDescription
    ) -> MatchOutput:
        return await self.score_resume_against_job_text(resume, job.description)