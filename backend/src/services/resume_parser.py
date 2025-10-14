from typing import List, Optional
from src.models.schemas import ResumeExtract
import io
import re
import spacy
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import requests
from loguru import logger
import os
import importlib.util

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.py")
spec = importlib.util.spec_from_file_location("config", CONFIG_PATH)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

GEMINI_EMBEDDING_MODEL = getattr(config, "GEMINI_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
class ResumeParser:
    def __init__(
        self,
        skill_source: Optional[str] = None,
        cert_source: Optional[str] = None,
        nlp_model: str = "en_core_web_sm",
        embedding_model: str = GEMINI_EMBEDDING_MODEL
    ):
        try:
            self.nlp = spacy.load(nlp_model)
        except OSError:
            logger.error(f"Spacy model '{nlp_model}' not found. Please run 'python -m spacy download {nlp_model}'")
            raise
        self.skills_list = self._load_ontology(skill_source, default_type="skills")
        self.cert_list = self._load_ontology(cert_source, default_type="certifications")
        self.embedder = SentenceTransformer(embedding_model)
        self.skill_embeddings = self.embedder.encode(self.skills_list, normalize_embeddings=True)
        self.cert_embeddings = self.embedder.encode(self.cert_list, normalize_embeddings=True)

    def parse_bytes(self, content: bytes, filename: str) -> ResumeExtract:
        ext = filename.split('.')[-1].lower()
        text = ""
        try:
            if ext == "pdf":
                text = pdf_extract_text(io.BytesIO(content))
            elif ext == "docx":
                doc = Document(io.BytesIO(content))
                text = "\n".join([p.text for p in doc.paragraphs])
            elif ext == "txt":
                text = content.decode(errors='ignore')
            else:
                logger.warning(f"Unsupported file type: {ext}. Returning empty text.")
        except Exception as e:
            logger.error(f"Failed to parse file {filename}: {e}")
        return self.parse_text(text)

    def parse_text(self, text: str) -> ResumeExtract:
        sections = self._detect_sections(text)

        return ResumeExtract(
            candidate_name=self._extract_name(text),
            emails=self._extract_emails(text),
            phones=self._extract_phones(text),
            skills=self._extract_skills_from_section(sections.get("Technical Skills", "")),
            certifications=self._extract_certifications_from_section(sections.get("Certifications", "")),
            education=self._extract_education_from_section(sections.get("Education", "")),
            experience=self._extract_experience_from_section(sections.get("Work Experience", "")),
            achievements=self._extract_semantic_section(sections.get("Achievements and Responsibilities", ""), ["award", "honor", "achievement", "winner", "place", "secured", "finalist"]),
            projects=self._extract_semantic_section(sections.get("Projects", ""), ["project", "developed", "built", "designed", "implemented", "launched", "engineered"]),
            publications=self._extract_semantic_section(sections.get("Publications", ""), ["publication", "paper", "journal", "conference"]),
            languages=self._extract_semantic_section(sections.get("Languages", ""), ["language", "fluent", "proficient"]),
            interests=self._extract_semantic_section(sections.get("Interests", ""), ["interest", "hobby", "extracurricular", "passion"]),
            raw_text=text,
            sections=sections
        )

    def _detect_sections(self, text: str) -> dict:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        sections = {}
        current_section = "Header"
        buffer = []

        section_keywords = {
            "Education": ["education"],
            "Work Experience": ["work experience", "employment history", "professional experience"],
            "Technical Skills": ["technical skills", "skills"],
            "Projects": ["projects"],
            "Achievements and Responsibilities": ["achievements and responsibilities", "achievements", "honors", "awards"],
            "Certifications": ["certifications", "licenses"],
            "Publications": ["publications"],
            "Languages": ["languages"],
            "Interests": ["interests", "hobbies"]
        }

        for line in lines:
            is_heading = False
            normalized_line = line.lower().strip(':').strip()
            
            for sec, keywords in section_keywords.items():
                if normalized_line in keywords:
                    if buffer: # Save the previous section's content
                        sections[current_section] = "\n".join(buffer)
                    current_section = sec
                    buffer = [] # Start a new buffer for the new section
                    is_heading = True
                    break
            
            if not is_heading:
                buffer.append(line)
        
        if buffer: # Save the last section
            sections[current_section] = "\n".join(buffer)
            
        return sections


    def _extract_name(self, text: str) -> str:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            first_line = lines[0]
            if '@' not in first_line and '·' not in first_line and len(first_line.split()) < 4:
                return first_line

        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Filter out company names that SpaCy might mislabel
                if " " in ent.text and len(ent.text.split()) < 4:
                    return ent.text
        
        return "Unknown" if not lines else lines[0] # Final fallback

    def _extract_emails(self, text: str) -> List[str]:
        return sorted(list(set(re.findall(r"[\w\.\-]+@[\w\.\-]+", text))))

    def _extract_phones(self, text: str) -> List[str]:
        return sorted(list(set(re.findall(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text))))

    def _extract_skills_from_section(self, section_text: str) -> List[str]:
        if not section_text:
            return []
        
        lines = section_text.split('\n')
        potential_skills = []
        for line in lines:
            line_content = line.split(":", 1)[-1]
            potential_skills.extend(line_content.split(','))
            
        cleaned_skills = [skill.strip() for skill in potential_skills if skill.strip()]
        return self._semantic_match(cleaned_skills, self.skills_list, self.skill_embeddings)

    def _extract_certifications_from_section(self, section_text: str) -> List[str]:
        if not section_text:
            return []
        potential_certs = section_text.split('\n')
        cleaned_certs = [cert.strip() for cert in potential_certs if cert.strip()]
        return self._semantic_match(cleaned_certs, self.cert_list, self.cert_embeddings)

    def _semantic_match(self, text_list: List[str], ontology: List[str], embeddings: np.ndarray, threshold=0.6) -> List[str]:
        if not text_list:
            return []
        text_embeddings = self.embedder.encode(text_list, normalize_embeddings=True)
        
        cosine_scores = np.dot(text_embeddings, embeddings.T)
        
        found = set()
        for i in range(len(text_list)):
            best_match_idx = np.argmax(cosine_scores[i])
            if cosine_scores[i][best_match_idx] > threshold:
                found.add(ontology[best_match_idx])
        for text in text_list:
            for item in ontology:
                if item.lower() in text.lower():
                    found.add(item)
                    
        return sorted(list(found))

    def _extract_education_from_section(self, text: str) -> List[str]:
        if not text:
            return []
        return [line.strip() for line in text.split('\n') if line.strip()]

    def _extract_experience_from_section(self, text: str) -> List[str]:
        if not text:
            return []
        
        lines = text.split('\n')
        experiences = []
        current_job = ""
        
        for line in lines:
            if line.strip().startswith('•'):
                current_job += "\n" + line
            else:
                if current_job:
                    experiences.append(current_job.strip())
                current_job = line
        
        if current_job:
            experiences.append(current_job.strip())
            
        return experiences

    def _extract_semantic_section(self, text: str, keywords: List[str]) -> List[str]:
        if not text:
            return []
        return [s.strip() for s in text.split('\n') if s.strip()]

    def _load_ontology(self, source: Optional[str], default_type: str) -> List[str]:
        default_skills = [
            "Python", "Java", "C++", "JavaScript", "SQL", "HTML", "CSS", 
            "React.js", "Flask", "RESTful APIs", "MongoDB", "MySQL", "Docker", "AWS", "Git", "Google Cloud Run", "CloudSQL", "Azure", "PostgreSQL", "Firebase", "Firestore",
            "Machine Learning", "Deep Learning", "NLP", "Generative AI", "LLM Fine-Tuning", "RAG", "Transformers",
            "TensorFlow", "Scikit-learn", "OpenCV", "Hugging Face", "LangChain", "Pandas",
            "Data Structures and Algorithms", "Object Oriented Programming", "Computer Networks", "Operating Systems", "Database Management"
        ]
        default_certs = [
            "AWS Certified", "Azure Certified", "GCP Certified", "Oracle Certified",
            "Google Certified", "Microsoft Certified"
        ]
        if source is None:
            return default_skills if default_type == "skills" else default_certs
        try:
            if source.startswith("http"):
                resp = requests.get(source)
                resp.raise_for_status()
                return json.loads(resp.text)
            else:
                with open(source, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {default_type} ontology from {source}: {e}")
            return default_skills if default_type == "skills" else default_certs

