"""Configuration for DDR system."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTRACTED_IMAGES_DIR = PROJECT_ROOT / "extracted" / "images"
EXTRACTED_JSON_DIR = PROJECT_ROOT / "extracted"

# Ollama (local LLM)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# DDR generation system prompt (sent to Ollama)
DDR_SYSTEM_PROMPT = """You are an expert building diagnostic analyst. Your task is to merge an Inspection Report and a Thermal Report into a single Detailed Diagnostic Report (DDR).

Rules:
- Never invent or hallucinate facts. Use only information present in the provided reports.
- If information is missing, state "Not Available".
- If the two reports conflict on a fact, state the conflict explicitly in the "conflicts" array (e.g., "Inspection states X; Thermal report states Y.").
- Structure the output strictly as valid JSON matching the required schema.
- For each area-wise observation, set image_ref to the actual image filename when an image was provided in the data; otherwise use "Image Not Available".
- Be precise and professional. Preserve technical terms and measurements from the source reports."""
