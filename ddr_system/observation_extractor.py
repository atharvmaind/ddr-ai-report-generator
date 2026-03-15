"""Extract structured observations from report text and link to extracted images."""

import re
from pathlib import Path

from ddr_system.models import ExtractedObservation, ExtractedReport, ObservationSource


def _split_into_blocks(text: str) -> list[str]:
    """Split text into non-empty blocks (paragraphs or bullet-like lines)."""
    if not text or not text.strip():
        return []
    # Split on double newlines or numbered/bullet lines
    blocks = re.split(r"\n\s*\n+|\n(?=\s*[\d•\-*]\s)", text.strip())
    return [b.strip() for b in blocks if b.strip() and len(b.strip()) > 2]


def _infer_area_from_text(block: str) -> str | None:
    """Try to infer area/location from text (e.g. 'Roof', 'Wall', 'Room 101')."""
    area_patterns = [
        r"(?:area|location|section|zone)\s*[:\-]?\s*([^\n.,;]+)",
        r"(?:roof|wall|floor|ceiling|basement|attic|room|kitchen|bathroom)[^\n.]*",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[-–]\s*(?:observation|finding|issue)",
    ]
    block_lower = block.lower()
    for pat in area_patterns:
        m = re.search(pat, block, re.IGNORECASE)
        if m:
            return m.group(1).strip() if m.lastindex else m.group(0).strip()
    return None


def extract_observations_from_text(
    text_by_page: dict[int, str],
    source: ObservationSource,
    source_path: str = "",
    image_filenames: list[str] | None = None,
) -> list[ExtractedObservation]:
    """
    Convert raw text (per page) into a list of ExtractedObservation.
    image_filenames: list of image filenames from this report (order may follow page order).
    """
    image_filenames = image_filenames or []
    observations: list[ExtractedObservation] = []
    page_images: dict[int, list[str]] = {}
    # Assume images are named with page number like prefix_1_0.png -> page 1
    for f in image_filenames:
        match = re.search(r"_(\d+)_\d+\.", f)
        if match:
            p = int(match.group(1))
            page_images.setdefault(p, []).append(f)

    for page, text in sorted(text_by_page.items()):
        if not text.strip():
            continue
        blocks = _split_into_blocks(text)
        for block in blocks:
            area = _infer_area_from_text(block)
            refs = page_images.get(page, [])
            obs = ExtractedObservation(
                source=source,
                area=area,
                issue=None,
                text=block,
                page=page,
                image_refs=refs.copy(),
                raw_metadata={"block": block[:200]},
            )
            observations.append(obs)
        # If no blocks parsed, treat full page as one observation
        if not blocks and text.strip():
            obs = ExtractedObservation(
                source=source,
                area=None,
                text=text.strip(),
                page=page,
                image_refs=page_images.get(page, []),
                raw_metadata={},
            )
            observations.append(obs)

    return observations


def build_extracted_report(
    report_type: str,
    source_path: str,
    text_by_page: dict[int, str],
    image_filenames: list[str],
    source: ObservationSource,
) -> ExtractedReport:
    """Build ExtractedReport from text and image list."""
    observations = extract_observations_from_text(
        text_by_page, source, source_path, image_filenames
    )
    return ExtractedReport(
        report_type=report_type,
        source_path=source_path,
        observations=observations,
        raw_text_by_page=dict(text_by_page),
        image_filenames=list(image_filenames),
    )


def observations_to_json(report: ExtractedReport) -> str:
    """Serialize ExtractedReport to JSON string."""
    return report.model_dump_json(indent=2)


def save_observations_json(report: ExtractedReport, output_path: str | Path) -> None:
    """Save ExtractedReport to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(observations_to_json(report), encoding="utf-8")
