from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import re
from typing import List, Dict, Any
from io import BytesIO


class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
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

    def _extract_links(self, text: str) -> Dict[str, str]:
        """Extract GitHub, LinkedIn, Portfolio links from text"""
        links = {}
        
        # GitHub
        github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w-]+'
        github_match = re.search(github_pattern, text, re.IGNORECASE)
        if github_match:
            links['GitHub'] = github_match.group(0)
            if not links['GitHub'].startswith('http'):
                links['GitHub'] = 'https://' + links['GitHub']
        
        # LinkedIn
        linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            links['LinkedIn'] = linkedin_match.group(0)
            if not links['LinkedIn'].startswith('http'):
                links['LinkedIn'] = 'https://' + links['LinkedIn']
        
        # Portfolio (common patterns)
        portfolio_patterns = [
            r'(?:https?://)?(?:www\.)?[\w-]+\.(?:com|net|io|dev|me)/[\w-]*',
            r'(?:https?://)?(?:portfolio|website):\s*([\w\.-]+)',
        ]
        for pattern in portfolio_patterns:
            portfolio_match = re.search(pattern, text, re.IGNORECASE)
            if portfolio_match and 'github' not in portfolio_match.group(0).lower() and 'linkedin' not in portfolio_match.group(0).lower():
                links['Portfolio'] = portfolio_match.group(0)
                if not links['Portfolio'].startswith('http'):
                    links['Portfolio'] = 'https://' + links['Portfolio']
                break
        
        return links

    def generate_report(
        self, 
        job_description: str,
        candidates: List[Dict[str, Any]],
        resume_texts: Dict[str, str]
    ) -> BytesIO:
        """
        Generate a comprehensive PDF report
        
        Args:
            job_description: The job description text
            candidates: List of candidate analysis results
            resume_texts: Dict mapping filename to full resume text
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []

        # Title Page
        story.append(Paragraph("Candidate Analysis Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        report_date = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(f"<b>Generated:</b> {report_date}", self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))

        # Job Description Summary
        story.append(Paragraph("Job Description", self.styles['SectionHeader']))
        jd_text = job_description[:500] + "..." if len(job_description) > 500 else job_description
        story.append(Paragraph(jd_text.replace('\n', '<br/>'), self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))

        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        summary_text = f"Total candidates analyzed: <b>{len(candidates)}</b><br/>"
        avg_score = sum(c['match_score'] for c in candidates) / len(candidates) if candidates else 0
        summary_text += f"Average match score: <b>{avg_score:.2f}/10</b>"
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(PageBreak())

        # Individual Candidate Reports
        for idx, candidate in enumerate(candidates, 1):
            # Candidate Header
            story.append(Paragraph(f"Candidate #{idx}: {candidate['candidate_name']}", self.styles['SectionHeader']))
            
            # Score and filename
            score_color = '#16a34a' if candidate['match_score'] >= 7 else '#ea580c' if candidate['match_score'] >= 5 else '#dc2626'
            score_text = f"<font color='{score_color}'><b>Match Score: {candidate['match_score']}/10</b></font>"
            story.append(Paragraph(score_text, self.styles['Normal']))
            story.append(Paragraph(f"<i>File: {candidate['filename']}</i>", self.styles['Normal']))
            story.append(Spacer(1, 0.15*inch))

            # Extract and display links
            resume_text = resume_texts.get(candidate['filename'], '')
            links = self._extract_links(resume_text)
            
            if links:
                story.append(Paragraph("<b>Professional Links:</b>", self.styles['CandidateName']))
                link_data = [[platform, f'<link href="{url}">{url}</link>'] for platform, url in links.items()]
                link_table = Table(link_data, colWidths=[1.5*inch, 5*inch])
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
                story.append(Spacer(1, 0.15*inch))

            # Justification
            story.append(Paragraph("<b>Analysis:</b>", self.styles['CandidateName']))
            story.append(Paragraph(candidate['justification'], self.styles['Normal']))
            story.append(Spacer(1, 0.15*inch))

            # Strengths
            story.append(Paragraph("<b>Key Strengths:</b>", self.styles['CandidateName']))
            for strength in candidate['strengths']:
                story.append(Paragraph(f"• {strength}", self.styles['Normal']))
            story.append(Spacer(1, 0.15*inch))

            # Gaps
            story.append(Paragraph("<b>Areas for Development:</b>", self.styles['CandidateName']))
            for gap in candidate['gaps']:
                story.append(Paragraph(f"• {gap}", self.styles['Normal']))
            
            # Add page break between candidates (except last)
            if idx < len(candidates):
                story.append(PageBreak())

        doc.build(story)
        buffer.seek(0)
        return buffer