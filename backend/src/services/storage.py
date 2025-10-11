"""
Storage layer (abstract). Implement concrete adapters for MongoDB or PostgreSQL.
Keep methods small: save_resume(extract), get_resume(id), save_job(job), list_candidates(job_id, top_k)
"""
from typing import Dict, Any

class StorageAdapter:
    def __init__(self, db_url: str):
        self.db_url = db_url

    def save_resume(self, resume_extract: Dict[str, Any]) -> str:
        # returns resume_id
        raise NotImplementedError

    def get_resume(self, resume_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def save_job(self, job: Dict[str, Any]) -> str:
        raise NotImplementedError

    def get_shortlist(self, job_id: str, top_k: int = 10) -> list:
        raise NotImplementedError
