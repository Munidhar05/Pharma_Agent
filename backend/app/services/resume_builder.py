import os
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


class ResumeBuilderService:
    """
    Service to generate clean, ATS-compliant PDF and DOCX tailored resumes.
    Strictly follows ATS best practices:
    - Standard single-column layout
    - Universal headings (SUMMARY, TECHNICAL SKILLS, EDUCATION, PROJECTS)
    - No tables, graphics, text boxes, or columns that confound ATS parsing engines
    - Strictly truthful information sourced exclusively from verified candidate profile
    """

    @classmethod
    def generate_pdf_resume(
        cls,
        output_path: str,
        full_name: str,
        contact_info: Dict[str, Any],
        headline: str,
        summary: str,
        skills: List[str],
        education: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
        experience: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generates an ATS-compliant PDF document using ReportLab."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        # Custom ATS Typography Styles
        name_style = ParagraphStyle(
            "ATS_Name",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1A202C"),
            alignment=0
        )
        headline_style = ParagraphStyle(
            "ATS_Headline",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#2B6CB0")
        )
        contact_style = ParagraphStyle(
            "ATS_Contact",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#4A5568")
        )
        section_style = ParagraphStyle(
            "ATS_Section",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#2D3748"),
            spaceBefore=10,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "ATS_Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#2D3748")
        )
        bullet_style = ParagraphStyle(
            "ATS_Bullet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            leftIndent=14,
            textColor=colors.HexColor("#2D3748")
        )

        story = []

        # 1. Header (Name & Headline)
        story.append(Paragraph(full_name, name_style))
        if headline:
            story.append(Paragraph(headline, headline_style))

        # Contact line
        contact_parts = []
        if contact_info.get("email"):
            contact_parts.append(contact_info["email"])
        if contact_info.get("phone"):
            contact_parts.append(contact_info["phone"])
        if contact_info.get("location"):
            contact_parts.append(contact_info["location"])
        if contact_info.get("linkedin"):
            contact_parts.append(contact_info["linkedin"])
        if contact_info.get("github"):
            contact_parts.append(contact_info["github"])

        if contact_parts:
            story.append(Spacer(1, 4))
            story.append(Paragraph(" | ".join(contact_parts), contact_style))

        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=8))

        # 2. Professional Summary
        if summary:
            story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
            story.append(Paragraph(summary, body_style))
            story.append(Spacer(1, 8))

        # 3. Technical Skills
        if skills:
            story.append(Paragraph("TECHNICAL SKILLS", section_style))
            story.append(Paragraph("<b>Core Competencies:</b> " + ", ".join(skills), body_style))
            story.append(Spacer(1, 8))

        # 4. Education
        if education:
            story.append(Paragraph("EDUCATION", section_style))
            for edu in education:
                deg_str = f"<b>{edu.get('degree', 'Degree')} in {edu.get('field_of_study', '')}</b>"
                inst_str = edu.get("institution", "")
                yr_str = f"{edu.get('end_year')}" if edu.get("end_year") else ""
                cgpa_str = f" | CGPA: {edu.get('cgpa_or_percentage')}" if edu.get("cgpa_or_percentage") else ""
                story.append(Paragraph(f"{deg_str} &mdash; {inst_str} ({yr_str}{cgpa_str})", body_style))
            story.append(Spacer(1, 8))

        # 5. Selected Technical Projects
        if projects:
            story.append(Paragraph("SELECTED TECHNICAL PROJECTS", section_style))
            for proj in projects:
                p_title = proj.get("title", "Project")
                p_role = proj.get("role", "Developer")
                p_tech = ", ".join(proj.get("technologies", []))
                story.append(Paragraph(f"<b>{p_title}</b> | <i>{p_role}</i>", body_style))
                if p_tech:
                    story.append(Paragraph(f"<b>Technologies:</b> {p_tech}", bullet_style))
                if proj.get("description"):
                    story.append(Paragraph(f"• {proj['description']}", bullet_style))
                for hl in proj.get("highlights", []):
                    story.append(Paragraph(f"• {hl}", bullet_style))
                story.append(Spacer(1, 6))

        # 6. Experience (if present)
        if experience:
            story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_style))
            for exp in experience:
                comp = exp.get("company_name", "")
                title = exp.get("job_title", "")
                story.append(Paragraph(f"<b>{title}</b> &mdash; {comp}", body_style))
                if exp.get("description"):
                    story.append(Paragraph(f"• {exp['description']}", bullet_style))
                story.append(Spacer(1, 6))

        doc.build(story)
        return output_path

    @classmethod
    def generate_docx_resume(
        cls,
        output_path: str,
        full_name: str,
        contact_info: Dict[str, Any],
        headline: str,
        summary: str,
        skills: List[str],
        education: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
        experience: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generates an ATS-compliant, editable DOCX document using python-docx."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = docx.Document()

        # Set 0.75 in margins
        for section in doc.sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)

        # Name Header
        title_para = doc.add_paragraph()
        run_name = title_para.add_run(full_name)
        run_name.bold = True
        run_name.font.size = Pt(18)
        run_name.font.color.rgb = RGBColor(0x1A, 0x20, 0x2C)

        if headline:
            h_para = doc.add_paragraph()
            run_h = h_para.add_run(headline)
            run_h.bold = True
            run_h.font.size = Pt(11)
            run_h.font.color.rgb = RGBColor(0x2B, 0x6C, 0xB0)

        # Contact line
        contact_parts = []
        if contact_info.get("email"):
            contact_parts.append(contact_info["email"])
        if contact_info.get("phone"):
            contact_parts.append(contact_info["phone"])
        if contact_info.get("location"):
            contact_parts.append(contact_info["location"])
        if contact_info.get("linkedin"):
            contact_parts.append(contact_info["linkedin"])
        if contact_info.get("github"):
            contact_parts.append(contact_info["github"])

        if contact_parts:
            c_para = doc.add_paragraph(" | ".join(contact_parts))
            c_para.style.font.size = Pt(9)
            c_para.style.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

        # Section: Summary
        if summary:
            h = doc.add_heading("PROFESSIONAL SUMMARY", level=2)
            h.style.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
            doc.add_paragraph(summary)

        # Section: Technical Skills
        if skills:
            h = doc.add_heading("TECHNICAL SKILLS", level=2)
            h.style.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
            p = doc.add_paragraph()
            r_bold = p.add_run("Core Competencies: ")
            r_bold.bold = True
            p.add_run(", ".join(skills))

        # Section: Education
        if education:
            h = doc.add_heading("EDUCATION", level=2)
            h.style.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
            for edu in education:
                deg_str = f"{edu.get('degree', 'Degree')} in {edu.get('field_of_study', '')}"
                inst_str = edu.get("institution", "")
                yr_str = f"({edu.get('end_year')})" if edu.get("end_year") else ""
                cgpa_str = f" | CGPA: {edu.get('cgpa_or_percentage')}" if edu.get("cgpa_or_percentage") else ""
                p = doc.add_paragraph()
                r_deg = p.add_run(f"{deg_str} ")
                r_deg.bold = True
                p.add_run(f"— {inst_str} {yr_str}{cgpa_str}")

        # Section: Selected Projects
        if projects:
            h = doc.add_heading("SELECTED TECHNICAL PROJECTS", level=2)
            h.style.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
            for proj in projects:
                p = doc.add_paragraph()
                r_title = p.add_run(f"{proj.get('title', 'Project')} ")
                r_title.bold = True
                p.add_run(f"| {proj.get('role', 'Developer')}")
                
                if proj.get("technologies"):
                    doc.add_paragraph(f"Technologies: {', '.join(proj['technologies'])}", style="List Bullet")
                if proj.get("description"):
                    doc.add_paragraph(proj["description"], style="List Bullet")
                for hl in proj.get("highlights", []):
                    doc.add_paragraph(hl, style="List Bullet")

        # Section: Experience
        if experience:
            h = doc.add_heading("PROFESSIONAL EXPERIENCE", level=2)
            h.style.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
            for exp in experience:
                p = doc.add_paragraph()
                r_t = p.add_run(f"{exp.get('job_title', '')} ")
                r_t.bold = True
                p.add_run(f"— {exp.get('company_name', '')}")
                if exp.get("description"):
                    doc.add_paragraph(exp["description"], style="List Bullet")

        doc.save(output_path)
        return output_path

