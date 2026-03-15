"""Write DDR to Markdown and PDF."""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer

from ddr_system.models import DDRReport


def _escape_md(s: str) -> str:
    """Escape markdown special chars in inline text where needed."""
    return s.replace("\\", "\\\\").replace("|", "\\|")


def ddr_to_markdown(report: DDRReport, images_base_path: Path | None = None) -> str:
    """
    Convert DDR to Markdown string.
    images_base_path: base directory for image refs (e.g. extracted/images).
    """
    c = report.content
    base = images_base_path or Path("extracted/images")
    lines = [
        "# Detailed Diagnostic Report (DDR)",
        "",
        "## Sources",
        f"- **Inspection Report:** {report.inspection_source or 'Not Available'}",
        f"- **Thermal Report:** {report.thermal_source or 'Not Available'}",
        "",
        "---",
        "",
        "## 1. Property Issue Summary",
        "",
        c.property_issue_summary or "Not Available",
        "",
        "## 2. Area-wise Observations",
        "",
    ]
    for area_obs in c.area_wise_observations:
        lines.append(f"### {_escape_md(area_obs.area)}")
        lines.append("")
        for obs in area_obs.observations:
            lines.append(f"- {_escape_md(obs)}")
        lines.append("")
        if area_obs.image_ref and area_obs.image_ref != "Image Not Available":
            img_path = base / area_obs.image_ref
            lines.append(f"![Observation image]({img_path.as_posix()})")
        else:
            lines.append("*Image Not Available*")
        lines.append("")
        if area_obs.notes:
            lines.append(f"*Notes:* {_escape_md(area_obs.notes)}")
            lines.append("")
    lines.extend([
        "## 3. Probable Root Cause",
        "",
        c.probable_root_cause or "Not Available",
        "",
        "## 4. Severity Assessment",
        "",
    ])
    for sev in c.severity_assessment:
        lines.append(f"- **{_escape_md(sev.item)}**: {sev.severity}")
        lines.append(f"  - *Reasoning:* {_escape_md(sev.reasoning)}")
        lines.append("")
    lines.extend([
        "## 5. Recommended Actions",
        "",
    ])
    for action in c.recommended_actions:
        lines.append(f"- {_escape_md(action)}")
    lines.extend([
        "",
        "## 6. Additional Notes",
        "",
        c.additional_notes or "Not Available",
        "",
        "## 7. Missing or Unclear Information",
        "",
    ])
    for m in c.missing_or_unclear_information:
        lines.append(f"- {_escape_md(m)}")
    if not c.missing_or_unclear_information:
        lines.append("None identified.")
    if c.conflicts:
        lines.extend(["", "## Conflicts Between Reports", ""])
        for conflict in c.conflicts:
            lines.append(f"- {_escape_md(conflict)}")
    return "\n".join(lines)


def write_markdown_file(report: DDRReport, output_path: str | Path, images_base_path: Path | None = None) -> None:
    """Write DDR to a Markdown file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ddr_to_markdown(report, images_base_path), encoding="utf-8")


def write_pdf(
    report: DDRReport,
    output_path: str | Path,
    images_base_path: Path | None = None,
) -> None:
    """
    Write DDR to a PDF file using reportlab.
    images_base_path: directory where extracted images are stored.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    base_img = Path(images_base_path) if images_base_path else Path("extracted/images")

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )
    styles = getSampleStyleSheet()
    story = []

    def add_heading(text: str, level: int = 1) -> None:
        style = styles["Heading1"] if level == 1 else styles["Heading2"]
        story.append(Paragraph(text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style))
        story.append(Spacer(1, 0.2 * inch))

    def add_para(text: str) -> None:
        if not text:
            return
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
        story.append(Paragraph(safe, styles["Normal"]))
        story.append(Spacer(1, 0.1 * inch))

    c = report.content

    story.append(Paragraph("Detailed Diagnostic Report (DDR)", styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))
    add_para(f"Inspection: {report.inspection_source or 'Not Available'}")
    add_para(f"Thermal: {report.thermal_source or 'Not Available'}")
    story.append(Spacer(1, 0.2 * inch))

    add_heading("1. Property Issue Summary")
    add_para(c.property_issue_summary or "Not Available")

    add_heading("2. Area-wise Observations")
    for area_obs in c.area_wise_observations:
        area_safe = area_obs.area.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(f"<b>{area_safe}</b>", styles["Normal"]))
        for obs in area_obs.observations:
            add_para(f"• {obs}")
        if area_obs.image_ref and area_obs.image_ref != "Image Not Available":
            img_path = base_img / area_obs.image_ref
            if img_path.exists():
                try:
                    story.append(RLImage(str(img_path), width=4 * inch, height=3 * inch))
                except Exception:
                    add_para("Image Not Available")
            else:
                add_para("Image Not Available")
        else:
            add_para("Image Not Available")
        if area_obs.notes:
            add_para(f"Notes: {area_obs.notes}")
        story.append(Spacer(1, 0.15 * inch))

    add_heading("3. Probable Root Cause")
    add_para(c.probable_root_cause or "Not Available")

    add_heading("4. Severity Assessment")
    for sev in c.severity_assessment:
        add_para(f"<b>{sev.item}</b>: {sev.severity}")
        add_para(f"Reasoning: {sev.reasoning}")

    add_heading("5. Recommended Actions")
    for action in c.recommended_actions:
        add_para(f"• {action}")

    add_heading("6. Additional Notes")
    add_para(c.additional_notes or "Not Available")

    add_heading("7. Missing or Unclear Information")
    if c.missing_or_unclear_information:
        for m in c.missing_or_unclear_information:
            add_para(f"• {m}")
    else:
        add_para("None identified.")

    if c.conflicts:
        add_heading("Conflicts Between Reports")
        for conflict in c.conflicts:
            add_para(f"• {conflict}")

    doc.build(story)
