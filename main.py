"""
DDR (Detailed Diagnostic Report) Generator — main entry point.

Usage:
  python main.py <inspection_report.pdf> <thermal_report.pdf> [--output-dir DIR] [--output-name NAME]
"""

import argparse
from pathlib import Path

from ddr_system.config import EXTRACTED_IMAGES_DIR, EXTRACTED_JSON_DIR
from ddr_system.ddr_generator import DDRLLMError, build_skeleton_ddr, generate_ddr
from ddr_system.image_extractor import extract_images_from_pdf, ensure_images_dir
from ddr_system.models import ExtractedReport, ObservationSource
from ddr_system.observation_extractor import (
    build_extracted_report,
    save_observations_json,
)
from ddr_system.pdf_loader import load_pdf_text
from ddr_system.report_writer import write_markdown_file, write_pdf


def run(
    inspection_pdf: Path,
    thermal_pdf: Path,
    output_dir: Path | None = None,
    output_name: str = "ddr_report",
    extract_only: bool = False,
    model: str | None = None,
) -> tuple[Path, Path]:
    """
    Run the full DDR pipeline: extract → merge (LLM) → write Markdown & PDF.

    Returns (path_to_md, path_to_pdf).
    """
    out = output_dir or Path("output")
    out.mkdir(parents=True, exist_ok=True)
    ensure_images_dir(EXTRACTED_IMAGES_DIR)

    # 1) Load text from both PDFs
    inspection_text = load_pdf_text(inspection_pdf)
    thermal_text = load_pdf_text(thermal_pdf)

    # 2) Extract images and save to extracted/images
    inspection_images = extract_images_from_pdf(
        inspection_pdf, EXTRACTED_IMAGES_DIR, prefix="inspection"
    )
    thermal_images = extract_images_from_pdf(
        thermal_pdf, EXTRACTED_IMAGES_DIR, prefix="thermal"
    )

    # 3) Build structured reports and save JSON
    inspection_report = build_extracted_report(
        report_type="inspection",
        source_path=str(inspection_pdf),
        text_by_page=inspection_text,
        image_filenames=inspection_images,
        source=ObservationSource.INSPECTION,
    )
    thermal_report = build_extracted_report(
        report_type="thermal",
        source_path=str(thermal_pdf),
        text_by_page=thermal_text,
        image_filenames=thermal_images,
        source=ObservationSource.THERMAL,
    )

    EXTRACTED_JSON_DIR.mkdir(parents=True, exist_ok=True)
    save_observations_json(inspection_report, EXTRACTED_JSON_DIR / "inspection_observations.json")
    save_observations_json(thermal_report, EXTRACTED_JSON_DIR / "thermal_observations.json")

    # 4) Generate DDR via Ollama (or skeleton if extract_only)
    if extract_only:
        ddr = build_skeleton_ddr(inspection_report, thermal_report)
    else:
        ddr = generate_ddr(inspection_report, thermal_report, model=model)

    # 5) Save DDR JSON for reference
    (out / f"{output_name}.json").write_text(
        ddr.model_dump_json(indent=2), encoding="utf-8"
    )

    # 6) Write Markdown and PDF (images base = extracted/images)
    md_path = out / f"{output_name}.md"
    pdf_path = out / f"{output_name}.pdf"
    write_markdown_file(ddr, md_path, images_base_path=EXTRACTED_IMAGES_DIR)
    write_pdf(ddr, pdf_path, images_base_path=EXTRACTED_IMAGES_DIR)

    return md_path, pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Detailed Diagnostic Report (DDR) from Inspection and Thermal PDFs."
    )
    parser.add_argument(
        "inspection_pdf",
        type=Path,
        help="Path to the Inspection Report PDF",
    )
    parser.add_argument(
        "thermal_pdf",
        type=Path,
        help="Path to the Thermal Report PDF",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("output"),
        help="Directory for output files (default: output)",
    )
    parser.add_argument(
        "--output-name",
        "-n",
        type=str,
        default="ddr_report",
        help="Base name for output files (default: ddr_report)",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Skip LLM; build report from extracted data only (use when Ollama is not running)",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=None,
        help="Ollama model name (default: llama3)",
    )
    args = parser.parse_args()

    if not args.inspection_pdf.exists():
        raise SystemExit(f"Inspection PDF not found: {args.inspection_pdf}")
    if not args.thermal_pdf.exists():
        raise SystemExit(f"Thermal PDF not found: {args.thermal_pdf}")

    try:
        md_path, pdf_path = run(
            args.inspection_pdf,
            args.thermal_pdf,
            output_dir=args.output_dir,
            output_name=args.output_name,
            extract_only=args.extract_only,
            model=args.model,
        )
        print(f"DDR Markdown: {md_path}")
        print(f"DDR PDF: {pdf_path}")
        if args.extract_only:
            print("(Extract-only mode: no LLM analysis. Run without --extract-only when Ollama is available.)")
    except DDRLLMError as e:
        print("Error:", e, flush=True)
        print("\nTo run without the LLM (extraction + skeleton report only), use: --extract-only")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
