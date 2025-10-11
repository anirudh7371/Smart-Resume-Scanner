from typing import List, Dict, Any
from pydantic import BaseModel, Field
import numpy as np
import asyncio
import json
import re
from loguru import logger
import google.generativeai as genai

class MatchEngine:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.embedding_model_name = settings.GEMINI_EMBEDDING_MODEL
        self.generation_model = genai.GenerativeModel(settings.GEMINI_GENERATION_MODEL)
        self.bias_mitigator = BiasMitigator()
        self.dimension = settings.EMBEDDING_DIMENSION
        self.job_cache: Dict[str, List[float]] = {}

    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Gemini Embedding API.
        """
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

    async def score_candidate_against_job(
        self, resume: ResumeExtract, job: JobDescription
    ) -> MatchOutput:

        # Prepare text representations
        resume_summary = f"Skills: {', '.join(resume.skills)}. Summary: {resume.raw_text}"
        jd_text = f"Job Title: {job.title}. Description: {job.description}"

        # Cache job embeddings
        if job.title not in self.job_cache:
            jd_emb = (await self._embed_texts([jd_text]))[0]
            self.job_cache[job.title] = jd_emb
        else:
            jd_emb = self.job_cache[job.title]

        resume_emb = (await self._embed_texts([resume_summary]))[0]

        # Cosine similarity
        similarity = np.dot(resume_emb, jd_emb) / (
            np.linalg.norm(resume_emb) * np.linalg.norm(jd_emb)
        )
        base_score = float(np.clip((similarity + 1) * 5, 0, 10))

        # Prompt LLM for structured evaluation 
        prompt = self._build_reasoning_prompt(resume, job, base_score)
        try:
            response = await self.generation_model.generate_content_async(prompt)
            match = re.search(r"\{.*\}", response.text, re.DOTALL)
            parsed = json.loads(match.group(0)) if match else {}
        except Exception as e:
            logger.warning(f"Failed to parse LLM JSON: {e}")
            parsed = {}

        # Extract and refine results 
        strengths = parsed.get("strengths", resume.skills)
        gaps = parsed.get("gaps", list(set(job.required_skills) - set(resume.skills)))
        justification = parsed.get("justification", f"Heuristic score: {base_score:.2f}")
        llm_score = parsed.get("match_score", base_score)

        # Bias mitigation 
        mitigated = self.bias_mitigator.apply_checks(llm_score, resume, job)
        final_score = mitigated.get("score", llm_score)

        return MatchOutput(
            candidate_name=resume.candidate_name or "Unknown",
            match_score=round(final_score, 2),
            strengths=strengths,
            gaps=gaps,
            justification=justification,
            details={"similarity": similarity, "base_score": base_score},
        )

    def _build_reasoning_prompt(
        self, resume: ResumeExtract, job: JobDescription, base_score: float
    ) -> str:
        """
        Build a structured LLM prompt for analyzing candidate-job fit.
        """

        return f"""
            You are an expert technical recruiter. Analyze the candidate’s resume 
            against the given job description and provide a JSON response as follows:

            JSON Output:
            {{
            "candidate_name": "{resume.candidate_name or "Unknown"}",
            "match_score": <number from 1-10>,
            "strengths": ["..."],
            "gaps": ["..."],
            "justification": "<1 short professional paragraph>"
            }}

            Base Similarity Score (vector-based): {base_score:.2f}/10

            ---
            CANDIDATE RESUME:
            {resume.raw_text}
            ---
            JOB DESCRIPTION:
            Title: {job.title}
            {job.description}
            ---
            Only return the JSON object. No explanations or markdown.
                    """.strip()
