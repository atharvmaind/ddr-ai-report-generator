"""Pydantic models for DDR extraction and generation."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ObservationSource(str, Enum):
    """Source of the observation."""

    INSPECTION = "inspection"
    THERMAL = "thermal"


class ExtractedObservation(BaseModel):
    """Single observation extracted from a report (before merging)."""

    source: ObservationSource
    area: Optional[str] = None
    issue: Optional[str] = None
    text: str
    page: int = 0
    image_refs: list[str] = Field(default_factory=list, description="Filenames in extracted/images")
    temperature_anomaly: Optional[str] = None
    structural_defect: Optional[str] = None
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedReport(BaseModel):
    """Structured extraction from one PDF (inspection or thermal)."""

    report_type: str  # "inspection" | "thermal"
    source_path: str = ""
    observations: list[ExtractedObservation] = Field(default_factory=list)
    raw_text_by_page: dict[int, str] = Field(default_factory=dict)
    image_filenames: list[str] = Field(default_factory=list)


# --- DDR output (LLM-generated) ---


class AreaObservation(BaseModel):
    """Area-wise observation in the final DDR."""

    area: str
    observations: list[str] = Field(default_factory=list)
    image_ref: str = "Image Not Available"  # filename or "Image Not Available"
    notes: Optional[str] = None


class SeverityItem(BaseModel):
    """Single severity assessment with reasoning."""

    item: str
    severity: str  # e.g. Low / Medium / High / Critical
    reasoning: str


class DDRContent(BaseModel):
    """Structured content of the final DDR (LLM output)."""

    property_issue_summary: str = "Not Available"
    area_wise_observations: list[AreaObservation] = Field(default_factory=list)
    probable_root_cause: str = "Not Available"
    severity_assessment: list[SeverityItem] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    additional_notes: str = "Not Available"
    missing_or_unclear_information: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list, description="Explicit conflicts between reports")


class DDRReport(BaseModel):
    """Full DDR with metadata."""

    inspection_source: str = ""
    thermal_source: str = ""
    content: DDRContent = Field(default_factory=DDRContent)
