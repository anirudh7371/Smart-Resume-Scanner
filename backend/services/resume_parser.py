from typing import List, Optional
from backend.src.models.schemas import ResumeExtract
import io
import re
import spacy
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document
from PIL import Image
import pytesseract
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import requests

class ResumeParser:
    """
    Production-ready Resume Parser using section-first extraction.
    Extracts:
      - Candidate info: name, emails, phones
      - Skills, Certifications
      - Education, Experience
      - Achievements, Projects, Publications
      - Languages, Interests
    """

    def __init__(
        self,
        skill_source: Optional[str] = None,
        cert_source: Optional[str] = None,
        nlp_model: str = "en_core_web_sm",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.nlp = spacy.load(nlp_model)
        # Load ontologies
        self.skills_list = self._load_ontology(skill_source, default_type="skills")
        self.cert_list = self._load_ontology(cert_source, default_type="certifications")
        # Embeddings
        self.embedder = SentenceTransformer(embedding_model)
        self.skill_embeddings = self.embedder.encode(self.skills_list, normalize_embeddings=True)
        self.cert_embeddings = self.embedder.encode(self.cert_list, normalize_embeddings=True)

    # -------------------- File Parsing -------------------- #
    def parse_bytes(self, content: bytes, filename: str) -> ResumeExtract:
        ext = filename.split('.')[-1].lower()
        text = ""
        try:
            if ext == "pdf":
                text = pdf_extract_text(io.BytesIO(content))
            elif ext == "docx":
                doc = Document(io.BytesIO(content))
                text = "\n".join([p.text for p in doc.paragraphs])
            elif ext in ["png", "jpg", "jpeg"]:
                image = Image.open(io.BytesIO(content))
                text = pytesseract.image_to_string(image)
            elif ext == "txt":
                text = content.decode(errors='ignore')
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        except Exception as e:
            logger.error(f"Failed to parse file {filename}: {e}")
        return self.parse_text(text)

    # -------------------- Section-first Text Parsing -------------------- #
    def parse_text(self, text: str) -> ResumeExtract:
        sections = self._detect_sections(text)

        return ResumeExtract(
            candidate_name=self._extract_name(text),
            emails=self._extract_emails(text),
            phones=self._extract_phones(text),
            skills=self._extract_skills_from_section(sections.get("Skills", "")),
            certifications=self._extract_certifications_from_section(sections.get("Certifications", "")),
            education=self._extract_education_from_section(sections.get("Education", "")),
            experience=self._extract_experience_from_section(sections.get("Experience", "")),
            achievements=self._extract_semantic_section(sections.get("Achievements", ""), ["award", "honor", "achievement", "winner"]),
            projects=self._extract_semantic_section(sections.get("Projects", ""), ["project", "developed", "built", "designed", "implemented"]),
            publications=self._extract_semantic_section(sections.get("Publications", ""), ["publication", "paper", "journal", "conference"]),
            languages=self._extract_semantic_section(sections.get("Languages", ""), ["language", "fluent", "proficient"]),
            interests=self._extract_semantic_section(sections.get("Interests", ""), ["interest", "hobby", "extracurricular", "passion"]),
            raw_text=text,
            sections=sections
        )

    # -------------------- Section Detection -------------------- #
    def _detect_sections(self, text: str) -> dict:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        sections = {}
        current_section = "Header"
        buffer = []

        section_keywords = {
            "Education": ["education", "qualifications", "academic background"],
            "Experience": ["experience", "work experience", "employment history", "professional experience"],
            "Skills": ["skills", "technical skills", "expertise"],
            "Projects": ["projects", "project experience", "portfolio"],
            "Achievements": ["achievements", "honors", "awards", "recognitions"],
            "Certifications": ["certifications", "certificates", "licenses"],
            "Publications": ["publications", "papers", "journals"],
            "Languages": ["languages", "known languages", "proficiencies"],
            "Interests": ["interests", "hobbies", "extracurricular"]
        }

        for line in lines:
            found = False
            for sec, keywords in section_keywords.items():
                if any(k.lower() in line.lower() for k in keywords):
                    if buffer:
                        sections[current_section] = "\n".join(buffer)
                    current_section = sec
                    buffer = []
                    found = True
                    break
            if not found:
                buffer.append(line)
        if buffer:
            sections[current_section] = "\n".join(buffer)
        return sections

    # -------------------- Extraction Helpers -------------------- #
    def _extract_name(self, text: str) -> str:
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text
        return "Unknown"

    def _extract_emails(self, text: str) -> List[str]:
        return list(dict.fromkeys(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)))

    def _extract_phones(self, text: str) -> List[str]:
        return list(dict.fromkeys(re.findall(r"(?:\+?\d{1,3}[-.\s]?)?\d{10}", text)))

    # --- Skills & Certifications --- #
    def _extract_skills_from_section(self, section_text: str) -> List[str]:
        return self._semantic_match(section_text, self.skills_list, self.skill_embeddings)

    def _extract_certifications_from_section(self, section_text: str) -> List[str]:
        return self._semantic_match(section_text, self.cert_list, self.cert_embeddings)

    def _semantic_match(self, text: str, ontology: List[str], embeddings: np.ndarray) -> List[str]:
        if not text.strip():
            return []
        sentences = [s.strip() for s in text.split("\n") if s.strip()]
        text_embeddings = self.embedder.encode(sentences, normalize_embeddings=True)
        found = set()
        for i, emb in enumerate(embeddings):
            sims = np.dot(text_embeddings, emb)
            if np.any(sims > 0.65):
                found.add(ontology[i])
        return list(found)

    # --- Education & Experience --- #
    def _extract_education_from_section(self, text: str) -> List[str]:
        if not text.strip():
            return []
        degree_keywords = ["bachelor", "master", "phd", "mba", "b.sc", "m.sc", "b.tech", "m.tech", "ba", "ma"]
        return [line for line in text.splitlines() if any(k in line.lower() for k in degree_keywords)]

    def _extract_experience_from_section(self, text: str) -> List[str]:
        if not text.strip():
            return []
        exp_keywords = ["developer", "engineer", "manager", "analyst", "consultant", "intern", "lead", "architect", "scientist"]
        return [line for line in text.splitlines() if any(k in line.lower() for k in exp_keywords)]

    # --- Generic semantic section extractor --- #
    def _extract_semantic_section(self, text: str, keywords: List[str]) -> List[str]:
        if not text.strip():
            return []
        doc = self.nlp(text)
        results = []
        for sent in doc.sents:
            if any(k.lower() in sent.text.lower() for k in keywords):
                results.append(sent.text.strip())
        return results

    # -------------------- Ontology Loader -------------------- #
    def _load_ontology(self, source: Optional[str], default_type: str) -> List[str]:
        default_skills = [
            "Python", "Java", "AWS", "TensorFlow", "PyTorch", "Docker", "Kubernetes",
            "PostgreSQL", "MongoDB", "NLP", "Machine Learning", "Deep Learning",
            "React", "Node.js", "C++", "SQL", "Git", "Linux", "Azure", "GCP"
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
