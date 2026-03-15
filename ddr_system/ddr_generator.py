"""Generate final DDR by merging Inspection and Thermal reports using Ollama (local LLM)."""

import json

import ollama

from ddr_system.config import DDR_SYSTEM_PROMPT, OLLAMA_MODEL
from ddr_system.models import (
    AreaObservation,
    DDRContent,
    DDRReport,
    ExtractedReport,
)


class DDRLLMError(Exception):
    """Raised when the local LLM (Ollama) fails."""

    pass


def _build_user_prompt(inspection: ExtractedReport, thermal: ExtractedReport) -> str:
    """Build the user message with inspection observations, thermal observations, and image references."""
    insp_data = inspection.model_dump(mode="json")
    therm_data = thermal.model_dump(mode="json")
    return (
        "Merge the following two reports into one Detailed Diagnostic Report (DDR). "
        "Output valid JSON only, no other text. Use only information from these reports; "
        'if something is missing write "Not Available"; if reports conflict, list each in "conflicts". '
        "For each area-wise observation, set image_ref to the image filename when one was extracted, "
        'otherwise "Image Not Available".\n\n'
        "## Inspection Report (observations and image references)\n"
        f"{json.dumps(insp_data, indent=2)}\n\n"
        "## Thermal Report (observations and image references)\n"
        f"{json.dumps(therm_data, indent=2)}\n\n"
        "## Required JSON schema for the DDR content (output this JSON only):\n"
        '{"property_issue_summary": "<string>", '
        '"area_wise_observations": [{"area": "<string>", "observations": ["<string>"], "image_ref": "<filename or Image Not Available>", "notes": "<string or null>"}], '
        '"probable_root_cause": "<string>", '
        '"severity_assessment": [{"item": "<string>", "severity": "<Low|Medium|High|Critical>", "reasoning": "<string>"}], '
        '"recommended_actions": ["<string>"], '
        '"additional_notes": "<string>", '
        '"missing_or_unclear_information": ["<string>"], '
        '"conflicts": ["<string>"]}'
    )


def _parse_llm_json(response_text: str) -> DDRContent:
    """Extract JSON from LLM response and parse into DDRContent."""
    text = response_text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()
    data = json.loads(text)
    return DDRContent.model_validate(data)


def generate_ddr(
    inspection_report: ExtractedReport,
    thermal_report: ExtractedReport,
    model: str | None = None,
) -> DDRReport:
    """
    Call Ollama to merge both reports and produce a structured DDR.
    Sends inspection observations, thermal observations, and image references to the model.
    """
    model_name = model or OLLAMA_MODEL
    user_prompt = _build_user_prompt(inspection_report, thermal_report)
    full_prompt = f"{DDR_SYSTEM_PROMPT}\n\n{user_prompt}"

    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": full_prompt}],
        )
    except Exception as e:
        raise DDRLLMError(
            f"Ollama error: {e}. Ensure Ollama is running (ollama serve) and the model is pulled (ollama pull {model_name})."
        ) from e

    content = response.get("message", {}).get("content")
    if not content:
        raise DDRLLMError("Empty response from Ollama.")

    try:
        ddr_content = _parse_llm_json(content)
    except (json.JSONDecodeError, ValueError) as e:
        raise DDRLLMError(f"Model did not return valid DDR JSON: {e}") from e

    return DDRReport(
        inspection_source=inspection_report.source_path,
        thermal_source=thermal_report.source_path,
        content=ddr_content,
    )


def build_skeleton_ddr(
    inspection_report: ExtractedReport,
    thermal_report: ExtractedReport,
) -> DDRReport:
    """
    Build a DDR from extracted data without calling the LLM.
    Use with --extract-only when Ollama is not running.
    """
    area_obs_map: dict[str, list[str]] = {}
    image_ref_map: dict[str, str] = {}

    for obs in inspection_report.observations + thermal_report.observations:
        area = obs.area or "General"
        if area not in area_obs_map:
            area_obs_map[area] = []
            image_ref_map[area] = (obs.image_refs[0] if obs.image_refs else "Image Not Available")
        area_obs_map[area].append(obs.text)
        if obs.image_refs and image_ref_map[area] == "Image Not Available":
            image_ref_map[area] = obs.image_refs[0]

    area_wise = [
        AreaObservation(
            area=area,
            observations=texts,
            image_ref=image_ref_map.get(area, "Image Not Available"),
        )
        for area, texts in area_obs_map.items()
    ]

    content = DDRContent(
        property_issue_summary="Not Available (extract-only mode; run without --extract-only for LLM summary).",
        area_wise_observations=area_wise,
        probable_root_cause="Not Available",
        severity_assessment=[],
        recommended_actions=[],
        additional_notes="Report generated in extract-only mode. No LLM analysis was performed.",
        missing_or_unclear_information=["Full analysis requires Ollama (remove --extract-only when Ollama is running)."],
        conflicts=[],
    )
    return DDRReport(
        inspection_source=inspection_report.source_path,
        thermal_source=thermal_report.source_path,
        content=content,
    )
