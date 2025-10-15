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
ROLE:
Act as an expert AI Recruiter. Your job is to conduct a detailed, unbiased analysis of a candidate's resume compared to a given job description.

CONTEXT:
You will be provided with structured candidate data and a job description. Your analysis should clearly identify how well the candidate's skills, experience, and education align with the job requirements. The final output must be in valid JSON format only.

TASK:
1. Compare:
   Carefully compare the candidate's details against the job description, focusing on:
   - Required and preferred skills
   - Relevant work experience and responsibilities
   - Educational qualifications and certifications

2. Score:
   Assign a "match_score" between **0 and 100**, where 100 represents a perfect alignment with all major requirements.

3. Analyze:
   - Identify strengths where the candidate's profile directly matches the job description.
   - Identify gaps where the candidate lacks required skills, experience, or education.

4. Summarize:
   Write a 2–3 sentence justification explaining the reasoning behind the assigned match score and overall fit.

INPUTS:
CANDIDATE:
Name: {resume.candidate_name}
Skills: {', '.join(resume.skills)}
Experience: {' | '.join(resume.experience[:3])}
Education: {' | '.join(resume.education)}

JOB DESCRIPTION:
{job_description_text}

OUTPUT FORMAT:
Respond with a single valid JSON object only.
Do not include markdown, comments, or text outside the JSON.

JSON SCHEMA:
{{
  "match_score": "<integer between 0 and 100>",
  "strengths": ["strength1", "strength2", "strength3"],
  "gaps": ["gap1", "gap2"],
  "justification": "<2-3 sentences explaining the overall match and reasoning behind the score>"
}}
        """.strip()

        # 🔹 Run through Ollama model
        parsed = await self.chain.ainvoke({"input": prompt_content})

        # 🔹 Parse and postprocess safely
        strengths = parsed.get("strengths", resume.skills[:3])
        gaps = parsed.get("gaps", ["More relevant experience needed"])
        justification = parsed.get(
            "justification",
            f"Candidate shows {base_score:.1f}/10 alignment with the role."
        )

        # Handle both 0–100 or 0–10 scales
        llm_score = float(parsed.get("match_score", base_score))
        if llm_score > 10:
            llm_score /= 10

        final_score = np.clip(llm_score, 0.0, 10.0)

        # 🔹 Construct and return structured MatchOutput
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
