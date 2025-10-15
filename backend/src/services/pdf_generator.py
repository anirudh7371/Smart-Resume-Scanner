from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import re
from typing import List, Dict, Any
from io import BytesIO


class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#4338ca'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='CandidateName',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=HexColor('#374151'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))

    # ✅ Smarter link extractor (handles partial URLs and text-only mentions)
    def _extract_links(self, text: str) -> Dict[str, str]:
        links = {}

        # GitHub detection (handles "github.com/username" or "GitHub: username")
        github_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/[^\s,]+', text, re.IGNORECASE)
        if not github_match:
            github_alt = re.search(r'github\s*[:\-]?\s*([\w\-/\.]+)', text, re.IGNORECASE)
            if github_alt:
                username = github_alt.group(1).replace(" ", "").strip('/')
                gh_url = f"https://github.com/{username}" if "github.com" not in username else f"https://{username}"
                links['GitHub'] = gh_url
        else:
            gh_url = github_match.group(0)
            if not gh_url.startswith("http"):
                gh_url = "https://" + gh_url
            links['GitHub'] = gh_url

        # LinkedIn detection (handles both direct URLs and partial)
        linkedin_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[^\s,]+', text, re.IGNORECASE)
        if not linkedin_match:
            linkedin_alt = re.search(r'linkedin\s*[:\-]?\s*([\w\-/\.]+)', text, re.IGNORECASE)
            if linkedin_alt:
                li = linkedin_alt.group(1).replace(" ", "").strip('/')
                li_url = f"https://linkedin.com/in/{li}" if "linkedin.com" not in li else f"https://{li}"
                links['LinkedIn'] = li_url
        else:
            li_url = linkedin_match.group(0)
            if not li_url.startswith("http"):
                li_url = "https://" + li_url
            links['LinkedIn'] = li_url

        # Portfolio / website detection (avoid false positives)
        portfolio_pattern = r'(?:https?://)?(?:www\.)?(?!linkedin|github)[\w-]+\.(?:com|net|io|dev|me)(?:/[^\s]*)?'
        portfolio_match = re.search(portfolio_pattern, text, re.IGNORECASE)
        if portfolio_match:
            link = portfolio_match.group(0)
            if not link.startswith("http"):
                link = "https://" + link
            links['Portfolio'] = link

        return links

    # 🔍 Detailed analysis (more accurate experience/project parsing)
    def _generate_detailed_analysis(self, resume_text: str, job_description: str) -> Dict[str, str]:
        """Extract deeper insights from résumé text and job description."""
        analysis = {}

        # Experience detection (handles "3+ years", "worked for 2 years", etc.)
        exp_pattern = r'(\d+)\s*(?:\+?\s*)?(?:years?|yrs?).*(?:experience|work|industry)?'
        exp_matches = re.findall(exp_pattern, resume_text, re.IGNORECASE)
        total_exp = max(map(int, exp_matches)) if exp_matches else 0
        analysis['Experience'] = f"{total_exp} years of experience detected." if total_exp else "Experience details not clearly stated."

        # Project mentions
        project_keywords = ['project', 'developed', 'built', 'implemented', 'designed', 'deployed', 'led', 'created']
        project_lines = [line for line in resume_text.split('\n') if any(k in line.lower() for k in project_keywords)]
        project_count = len(project_lines)
        analysis['Projects'] = f"{project_count} project(s) mentioned." if project_count else "No clear project mentions found."

        # Skill overlap (JD vs résumé)
        jd_keywords = set(re.findall(r'\b[A-Za-z0-9\+\#\.]{2,}\b', job_description.lower()))
        resume_keywords = set(re.findall(r'\b[A-Za-z0-9\+\#\.]{2,}\b', resume_text.lower()))
        overlap = jd_keywords.intersection(resume_keywords)
        overlap_ratio = (len(overlap) / len(jd_keywords)) * 100 if jd_keywords else 0
        analysis['Skill Match'] = f"~{overlap_ratio:.1f}% overlap between resume and job description skills."

        # Education info
        education_keywords = ['btech', 'b.e', 'bachelor', 'mtech', 'm.sc', 'phd', 'degree', 'university', 'college']
        edu_lines = [line for line in resume_text.split('\n') if any(k in line.lower() for k in education_keywords)]
        analysis['Education'] = f"{len(edu_lines)} educational qualification(s) detected." if edu_lines else "Education info not found."

        return analysis

    def generate_report(
        self,
        job_description: str,
        candidates: List[Dict[str, Any]],
        resume_texts: Dict[str, str]
    ) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
        story = []

        # Header
        story.append(Paragraph("Candidate Analysis Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2 * inch))

        report_date = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(f"<b>Generated:</b> {report_date}", self.styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))

        # Job Description
        story.append(Paragraph("Job Description", self.styles['SectionHeader']))
        jd_text = job_description[:500] + "..." if len(job_description) > 500 else job_description
        story.append(Paragraph(jd_text.replace('\n', '<br/>'), self.styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))

        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        summary_text = f"Total candidates analyzed: <b>{len(candidates)}</b><br/>"
        avg_score = sum(c['match_score'] for c in candidates) / len(candidates) if candidates else 0
        summary_text += f"Average match score: <b>{avg_score:.2f}/10</b>"
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(PageBreak())

        # Per-Candidate Details
        for idx, candidate in enumerate(candidates, 1):
            story.append(Paragraph(f"Candidate #{idx}: {candidate['candidate_name']}", self.styles['SectionHeader']))

            # Score with color coding
            score_color = '#16a34a' if candidate['match_score'] >= 7 else '#ea580c' if candidate['match_score'] >= 5 else '#dc2626'
            score_text = f"<font color='{score_color}'><b>Match Score: {candidate['match_score']}/10</b></font>"
            story.append(Paragraph(score_text, self.styles['Normal']))
            story.append(Paragraph(f"<i>File: {candidate['filename']}</i>", self.styles['Normal']))
            story.append(Spacer(1, 0.15 * inch))

            # Extract cleaned résumé text
            resume_text = resume_texts.get(candidate['filename'], '')
            links = self._extract_links(resume_text)

            # Professional Links
            if links:
                story.append(Paragraph("<b>Professional Links:</b>", self.styles['CandidateName']))
                link_data = [[platform, f'<link href="{url}">{url}</link>'] for platform, url in links.items()]
                link_table = Table(link_data, colWidths=[1.5 * inch, 5 * inch])
                link_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#d1d5db'))
                ]))
                story.append(link_table)
                story.append(Spacer(1, 0.15 * inch))

            # Summary
            story.append(Paragraph("<b>Analysis Summary:</b>", self.styles['CandidateName']))
            story.append(Paragraph(candidate['justification'], self.styles['Normal']))
            story.append(Spacer(1, 0.15 * inch))

            # Strengths
            story.append(Paragraph("<b>Key Strengths:</b>", self.styles['CandidateName']))
            for strength in candidate['strengths']:
                story.append(Paragraph(f"• {strength}", self.styles['Normal']))
            story.append(Spacer(1, 0.15 * inch))

            # Gaps
            story.append(Paragraph("<b>Areas for Development:</b>", self.styles['CandidateName']))
            for gap in candidate['gaps']:
                story.append(Paragraph(f"• {gap}", self.styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))

            # Detailed Analysis
            story.append(Paragraph("<b>Detailed Analysis:</b>", self.styles['CandidateName']))
            detailed = self._generate_detailed_analysis(resume_text, job_description)
            detail_table = [[k, v] for k, v in detailed.items()]
            detail_table_obj = Table(detail_table, colWidths=[1.5 * inch, 5 * inch])
            detail_table_obj.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#eef2ff')),
                ('TEXTCOLOR', (0, 0), (-1, -1), black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#c7d2fe'))
            ]))
            story.append(detail_table_obj)

            if idx < len(candidates):
                story.append(PageBreak())

        doc.build(story)
        buffer.seek(0)
        return buffer
