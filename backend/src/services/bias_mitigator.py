from typing import Dict, Any, List
from loguru import logger
import re
import json
import numpy as np
from src.models.schemas import ResumeExtract, JobDescription

class BiasMitigator:
    """
    Implements more robust bias mitigation strategies.
    """

    def __init__(self, patterns_path: str = "bias_patterns.json"):
        self.bias_patterns = self._load_patterns(patterns_path)

    def _load_patterns(self, path: str) -> Dict[str, str]:
        """Load bias patterns from a JSON file."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("Bias patterns file not found or invalid. Using default patterns.")
            return {
                'gender': r'\b(he|she|his|her|male|female|man|woman|boy|girl)\b',
                'age': r'\b(young|old|senior|junior|experienced|years old|age)\b',
                'ethnicity': r'\b(asian|african|european|american|indian|chinese)\b',
                'name_origin': r'\b(foreign|international|native|local)\b'
            }

    def apply_checks(
        self,
        score: float,
        resume: ResumeExtract,
        job: JobDescription,
    ) -> Dict[str, Any]:
        """Apply bias mitigation checks and return adjusted results."""
        result = {
            "score": score,
            "bias_flags": [],
            "adjustments": []
        }

        bias_detected = self._detect_bias_patterns(resume.raw_text)
        if bias_detected:
            logger.warning(f"Potential bias patterns detected: {bias_detected}")
            result["bias_flags"] = bias_detected

        result["score"] = np.clip(score, 0.0, 10.0)
        result = self._apply_fairness_constraints(result, resume, job)

        return result

    def _detect_bias_patterns(self, text: str) -> List[str]:
        """Detect potential bias patterns in text."""
        detected = []
        for bias_type, pattern in self.bias_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                detected.append(bias_type)
        return detected

    def _apply_fairness_constraints(
        self,
        result: Dict[str, Any],
        resume: ResumeExtract,
        job: JobDescription,
    ) -> Dict[str, Any]:
        """Apply more dynamic fairness constraints."""
        score = result["score"]

        num_required_skills = len(job.required_skills)
        if num_required_skills == 0:
            return result

        matching_skills = set(resume.skills) & set(job.required_skills)
        skill_match_ratio = len(matching_skills) / num_required_skills

        if skill_match_ratio > 0.5 and score < 4.0:
            adjustment = (skill_match_ratio - 0.5) * 2
            result["score"] = min(10.0, score + adjustment)
            result["adjustments"].append(f"Fairness boost applied: +{adjustment:.2f}")
            logger.info("Applying fairness boost for qualified candidate with low score.")

        if skill_match_ratio < 0.2 and score > 8.0:
            adjustment = (0.2 - skill_match_ratio) * 10
            result["score"] = max(0.0, score - adjustment)
            result["adjustments"].append(f"Fairness cap applied: -{adjustment:.2f}")
            logger.info("Applying fairness cap for under-qualified candidate with high score.")

        return result

    def get_fairness_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a fairness report for a batch of candidate evaluations."""
        if not results:
            return {"error": "No results to analyze"}

        scores = [r.get("score", 0) for r in results]
        bias_flags = [flag for r in results for flag in r.get("bias_flags", [])]

        return {
            "total_candidates": len(results),
            "average_score": np.mean(scores),
            "score_variance": np.var(scores),
            "bias_flags_detected": len(bias_flags),
            "unique_bias_types": list(set(bias_flags)),
            "recommendation": self._generate_fairness_recommendation(scores, bias_flags)
        }

    def _generate_fairness_recommendation(self, scores: List[float], bias_flags: List[str]) -> str:
        if len(bias_flags) > len(scores) * 0.3:
            return "High bias risk detected. Consider manual review of evaluations."
        if np.var(scores) > 6.0:
            return "High score variance detected. Review evaluation criteria for consistency."
        return "Evaluation appears fair and consistent."