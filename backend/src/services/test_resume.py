import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .resume_parser import ResumeParser
parser = ResumeParser()
sample_resume_text = """
Anirudh
Yamunanagar, India· anirudh7371@gmail.com· +918295250473· Indian Citizen
LinkedIn· GitHub
Education
Vellore Institute of Technology Vellore
Bachelor of Technology in Computer Science and Engineering, 8.73 CGPA Sept 2022 – May 2026
Work Experience
CodeBiceps Chandigarh, India
AI Engineer Intern May 2025 – July 2025
• Architected an AI-driven system using RAG and NLP to convert Lighthouse reports into optimization insights, resolving
30+ issues across 5+ platforms and boosting web app scalability via Agile SDLC
• Built RESTful APIs with Flask, Google Gemini, and RAG pipelines, deployed on Azure, improving frontend load
efficiency by 25% through iterative Agile SDLC development cycles
KuppiSmart Solutions Pvt Ltd Hyderabad, India
ML and AI Developer Intern May 2024 – June 2024
• Developed and optimized deep learning models for livestock condition assessment using TensorFlow and OpenCV,
increasing classification accuracy by 25% through advanced data preprocessing and augmentation techniques
• Automated data collection and preprocessing pipelines with Python and Pandas, reducing manual labeling efforts by 40%
and accelerating model retraining cycles
Projects
AI Interviewer - Software-Based Interview Assistant - GitHub Sept 2025
• Built an AI-powered interviewer that generates and evaluates technical and behavioral questions from Excel input using
LangChain, LLMs, and RAG, reducing HR screening workload by 60% and review time
• Containerized services with Docker and deployed on Google Cloud Run with CloudSQL as the backend database,
ensuring 99.9% uptime and enabling concurrent usage by 100+ recruiters/interviewers
FinWise - AI Personal Finance Assistant - GitHub June 2025
• Launched a comprehensive AI-driven personal finance platform using Next.js, Python, and PostgreSQL, supporting
500+ users with intelligent expense tracking, OCR receipt scanning, and automated budgeting insights
• Integrated LangChain and Gemini API to deliver personalized financial recommendations, increasing user engagement
by 85% and reducing manual budget planning efforts by 70%
Legal Document Demystifier - GitHub April 2025
• Engineered an AI system to interpret and simplify complex legal documents using FastAPI, RAG, and Google Gemini
API, delivering structured clause, entity, and risk summaries with 92% accuracy on 500+ real legal samples
• Deployed a secure, Dockerized backend integrated with Firebase Auth and Firestore, enabling real-time document
chat that reduced manual legal review time by 65% for early testers
Technical Skills
Programming Languages: C++, Python, SQL, JavaScript, HTML/CSS
Machine Learning & AI: Deep Learning, NLP, Generative AI, LLM Fine-Tuning, RAG, Transformers
ML/DL Frameworks: TensorFlow, Scikit-learn, OpenCV, Hugging Face, LangChain
Web Technologies: Flask, React.js, RESTful APIs
Databases and Tools: MongoDB, MySQL, Docker, AWS, Git
Core Computer Science: Data Structures and Algorithms, Object Oriented Programming, Computer Networks,
Operating Systems, Database Management
Achievements and Responsibilities
Achieved 1st place among 500+ participants in AI-ML Marvels Hackathon at graVITas'23, VIT Vellore, for developing an
innovative AI/ML solution
Secured Runner-up position out of 200+ teams in DevJams Hackathon organized by Google Developer Student Club
Top 10 Finalist among 400+ teams in Code-a-thon conducted by Caterpillar Inc.
AI/ML Mentor & Speaker: Conducted workshops and mentoring sessions for AI/ML enthusiasts, guiding participants
through projects and model building
Open Source Contributor: Enhanced pgmpy library with BIC-based structure learning for probabilistic models.
"""

parsed_resume = parser.parse_text(sample_resume_text)
print(parsed_resume.model_dump_json(indent=4))

