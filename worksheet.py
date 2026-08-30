# worksheet.py
# Generates bilingual Hindi-Santali PDFs aligned to NIPUN Bharat

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.units import cm
import datetime

NIPUN_OUTCOMES = {
    "1": "Recognises letters, numbers 1-20, and simple words in mother tongue",
    "2": "Reads two-syllable words; counts and writes numbers 1-100; simple addition",
    "3": "Reads short paragraphs with comprehension; multiplication 1-5; word problems"
}

PAD = [
    ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
    ('TOPPADDING',    (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]


def generate_bilingual_worksheet(
        hindi_text, santali_text, grade="2",
        topic="Foundational Literacy", lesson_steps=None,
        output_path="vaanisetu_worksheet.pdf"):

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    header_s = ParagraphStyle('H', fontSize=15, fontName='Helvetica-Bold',
                               textColor=colors.HexColor('#0D2137'),
                               alignment=1, spaceAfter=4)
    sub_s    = ParagraphStyle('S', fontSize=10, fontName='Helvetica',
                               textColor=colors.HexColor('#1A5276'),
                               alignment=1, spaceAfter=8)
    label_s  = ParagraphStyle('L', fontSize=11, fontName='Helvetica-Bold',
                               textColor=colors.HexColor('#0D2137'), spaceAfter=4)
    body_s   = ParagraphStyle('B', fontSize=10, fontName='Helvetica',
                               leading=16, spaceAfter=4)

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph("VaaniSetu — Bilingual Classroom Worksheet", header_s))
    story.append(Paragraph(
        f"Grade {grade}  |  Topic: {topic}  |  "
        f"Date: {datetime.date.today().strftime('%d %B %Y')}", sub_s))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=colors.HexColor('#0D2137'), spaceAfter=8))

    # ── NIPUN Bharat Competency ──────────────────────────────────────────────
    comp = NIPUN_OUTCOMES.get(str(grade), NIPUN_OUTCOMES["2"])
    story.append(Paragraph("NIPUN Bharat Learning Outcome", label_s))
    comp_data = [[f"Grade {grade}: {comp}"]]
    comp_tbl = Table(comp_data, colWidths=[17*cm])
    comp_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EBF5FB')),
        ('FONTNAME',   (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('BOX',        (0, 0), (-1, -1), 1, colors.HexColor('#1A5276')),
    ] + PAD))
    story.append(comp_tbl)
    story.append(Spacer(1, 0.3*cm))

    # ── Lesson Steps (if provided from LessonEngine) ─────────────────────────
    if lesson_steps:
        story.append(Paragraph("Lesson Content (from today's session)", label_s))
        for i, step in enumerate(lesson_steps, 1):
            step_data = [
                [f"Step {i} ({step['type'].replace('_',' ').title()})",
                 "Hindi", "Santali"],
                [step.get('note', ''), step['hindi'],
                 step.get('santali_translated', '—')]
            ]
            s_tbl = Table(step_data, colWidths=[4*cm, 6.5*cm, 6.5*cm])
            s_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A5276')),
                ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
                ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('BOX',        (0, 0), (-1, -1), 1, colors.HexColor('#AED6F1')),
                ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor('#D0E8F8')),
            ] + PAD))
            story.append(s_tbl)
            story.append(Spacer(1, 0.2*cm))
    else:
        # Fallback: single content entry
        story.append(Paragraph("Lesson Content", label_s))
        content_data = [["Hindi (हिन्दी)", "Santali (ᱥᱟᱱᱛᱟᱲᱤ)"],
                         [hindi_text, santali_text]]
        c_tbl = Table(content_data, colWidths=[8.5*cm, 8.5*cm])
        c_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A5276')),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 11),
            ('VALIGN',     (0, 1), (-1, -1), 'TOP'),
            ('BOX',        (0, 0), (-1, -1), 1, colors.HexColor('#1A5276')),
            ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#AED6F1')),
        ] + PAD))
        story.append(c_tbl)
    story.append(Spacer(1, 0.3*cm))

    # ── Practice Exercises ─────────────────────────────────────────────────
    story.append(Paragraph("Practice Exercises", label_s))
    exercises = [
        "1. Listen to the Santali sentence and repeat it three times.",
        "2. Draw a picture that shows what the lesson is about.",
        "3. Fill in the blank: Write the Hindi word in Santali below.",
        "4. Answer your teacher's question in Santali out loud.",
    ]
    for ex in exercises:
        story.append(Paragraph(ex, body_s))
    story.append(Spacer(1, 0.3*cm))

    # ── Visual Flashcard ───────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor('#AED6F1'), spaceAfter=6))
    story.append(Paragraph("Visual Flashcard (cut out and keep)", label_s))
    fc_data = [
        ["Hindi Word / Sentence", "Santali Translation", "Draw Here"],
        [hindi_text[:40] + ("..." if len(hindi_text) > 40 else ""),
         santali_text[:40] + ("..." if len(santali_text) > 40 else ""),
         ""],
    ]
    fc_tbl = Table(fc_data, colWidths=[6*cm, 6*cm, 5*cm], rowHeights=[None, 2*cm])
    fc_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0D6B3E')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.HexColor('#EAFAF1'), colors.white]),
        ('BOX',        (0, 0), (-1, -1), 1.5, colors.HexColor('#0D6B3E')),
        ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#A9DFBF')),
    ] + PAD))
    story.append(fc_tbl)
    story.append(Spacer(1, 0.3*cm))

    # ── Footer ─────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor('#0D2137'), spaceAfter=4))
    story.append(Paragraph(
        "VaaniSetu — AI Teaching Assistant | SIH 2026 | PS SIH26042 | "
        "NIPUN Bharat Aligned | Government of Jharkhand PALASH MTB-MLE Programme",
        ParagraphStyle('Footer', fontSize=7, fontName='Helvetica',
                       textColor=colors.grey, alignment=1)))
    doc.build(story)
    return output_path