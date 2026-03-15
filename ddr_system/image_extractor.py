"""Extract embedded images from PDFs and save to extracted/images."""

from pathlib import Path

import fitz  # PyMuPDF

from ddr_system.config import EXTRACTED_IMAGES_DIR


def ensure_images_dir(base_dir: Path | None = None) -> Path:
    """Create extracted/images if it does not exist. Return the path."""
    root = base_dir or EXTRACTED_IMAGES_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def extract_images_from_pdf(
    pdf_path: str | Path,
    output_dir: Path | None = None,
    prefix: str = "img",
) -> list[str]:
    """
    Extract all embedded images from the PDF and save under output_dir.

    Returns list of saved filenames (e.g. img_inspection_1_p1.png).
    output_dir defaults to EXTRACTED_IMAGES_DIR.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    out = output_dir or ensure_images_dir()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    seen_hashes: set[int] = set()

    doc = fitz.open(path)
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                try:
                    base_image = doc.extract_image(xref)
                except Exception:
                    continue
                ext = base_image.get("ext", "png").lower()
                if ext == "jpeg":
                    ext = "jpg"
                # Deduplicate by stream hash to avoid saving same image many times
                stream = base_image.get("image")
                h = hash(stream) if stream else xref
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                # Filename: prefix_page_imgindex.ext
                one_based = page_num + 1
                fname = f"{prefix}_{one_based}_{img_index}.{ext}"
                out_path = out / fname
                with open(out_path, "wb") as f:
                    f.write(base_image["image"])
                saved.append(fname)
    finally:
        doc.close()

    return saved
