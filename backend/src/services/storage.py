from pymongo import MongoClient, ASCENDING, DESCENDING
from bson.objectid import ObjectId
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.config import settings

class MongoStorageAdapter:
    def __init__(self, db_url: str):
        try:
            self.client = MongoClient(db_url, serverSelectionTimeoutMS=5000)
            self.db = self.client["resumescreener"]
            self.db.command("ping")

            # Indexes for optimization
            self.db.resumes.create_index([("upload_date", DESCENDING)])
            self.db.jobs.create_index([("created_at", DESCENDING)])
            print("Connected to MongoDB successfully!")

        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            raise

    # Resume Methods

    def save_resume(self, resume_extract: Dict[str, Any]) -> str:
        resume_extract["upload_date"] = resume_extract.get("upload_date", datetime.utcnow())
        result = self.db.resumes.insert_one(resume_extract)
        return str(result.inserted_id)

    def get_resume(self, resume_id: str) -> Optional[Dict[str, Any]]:
        try:
            resume = self.db.resumes.find_one({"_id": ObjectId(resume_id)})
            if resume:
                resume["_id"] = str(resume["_id"])
            return resume
        except Exception as e:
            print(f"Error retrieving resume {resume_id}: {e}")
            return None

    def get_all_resumes(self, limit: int = 20) -> List[Dict[str, Any]]:
        resumes = list(self.db.resumes.find().sort("upload_date", DESCENDING).limit(limit))
        for r in resumes:
            r["_id"] = str(r["_id"])
        return resumes

    # Job Methods

    def save_job(self, job: Dict[str, Any]) -> str:
        job["created_at"] = job.get("created_at", datetime.utcnow())
        result = self.db.jobs.insert_one(job)
        return str(result.inserted_id)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        try:
            job = self.db.jobs.find_one({"_id": ObjectId(job_id)})
            if job:
                job["_id"] = str(job["_id"])
            return job
        except Exception as e:
            print(f"Error retrieving job {job_id}: {e}")
            return None

    # Shortlist Methods

    def get_shortlist(self, job_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        resumes = list(
            self.db.resumes.find().sort("upload_date", DESCENDING).limit(top_k)
        )
        for r in resumes:
            r["_id"] = str(r["_id"])
        return resumes

    def delete_resume(self, resume_id: str) -> bool:
        result = self.db.resumes.delete_one({"_id": ObjectId(resume_id)})
        return result.deleted_count > 0

    def delete_job(self, job_id: str) -> bool:
        result = self.db.jobs.delete_one({"_id": ObjectId(job_id)})
        return result.deleted_count > 0

    def close(self):
        """Gracefully closes the MongoDB connection."""
        self.client.close()

storage_adapter = MongoStorageAdapter(db_url=settings.DATABASE_URL)
