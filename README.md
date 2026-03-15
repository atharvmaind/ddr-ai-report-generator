# DDR — Detailed Diagnostic Report Generator

A Python AI system that generates a **Detailed Diagnostic Report (DDR)** by merging an **Inspection Report** and a **Thermal Report** (PDFs). Uses a local LLM via [Ollama](https://ollama.com)—no API keys required.

---

## Project Overview

The system ingests two PDF reports (inspection and thermal), extracts all text and embedded images, structures the observations, and uses a local language model (default: **llama3**) to produce a single, structured DDR with summaries, area-wise observations, root cause analysis, severity assessment, and recommended actions. Output is produced as **Markdown** and **PDF**.

---

## System Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│  Inspection PDF     │     │  Thermal PDF        │
└──────────┬──────────┘     └──────────┬──────────┘
           │                           │
           ▼                           ▼
┌──────────────────────────────────────────────────┐
│  PDF Loader (pdfplumber) + Image Extractor       │
│  (PyMuPDF) → extracted/images/, JSON observations │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  Observation Extractor → Structured JSON         │
│  (inspection_observations, thermal_observations)  │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  DDR Generator (Ollama / llama3)                  │
│  Merges reports, no hallucination, conflict flag │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  Report Writer → Markdown + PDF (reportlab)      │
└──────────────────────────────────────────────────┘
```

---

## Features

- **Dual PDF input:** Inspection report and thermal report
- **Text & image extraction:** All text and embedded images extracted; images saved to `extracted/images/`
- **Structured observations:** Text converted to JSON with area, issue, and image references
- **Local LLM (Ollama):** Merges both reports using llama3 (or another model)—no cloud API or API keys
- **Structured DDR output:** Property issue summary, area-wise observations, probable root cause, severity assessment, recommended actions, additional notes, missing/unclear information
- **Image linking:** Each observation can reference an image; "Image Not Available" when missing
- **Integrity rules:** No hallucination; "Not Available" for missing data; explicit conflict section when reports disagree
- **Export:** Markdown and PDF reports plus JSON for automation

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ddr-report-generator.git
cd ddr-report-generator
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
# source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The project is fully runnable after cloning and running the above.

### 4. Install and run Ollama (for LLM-based DDR)

- Download and install from **[https://ollama.com](https://ollama.com)** (Windows, macOS, or Linux).
- Pull the default model:

```bash
ollama pull llama3
```

Ollama runs locally; **no API keys are required.**

---

## How to Run

**Basic run (requires Ollama running with `llama3`):**

```bash
python main.py inspection.pdf thermal.pdf -o output -n ddr_report
```

**Example with your own filenames:**

```bash
python main.py inspection_report_sample.pdf thermal_report_sample.pdf -o output -n ddr_report
```

| Argument / Option | Description |
|-------------------|-------------|
| `inspection.pdf` | Path to the **Inspection Report** PDF |
| `thermal.pdf` | Path to the **Thermal Report** PDF |
| `-o output` | Output directory (default: `output`) |
| `-n ddr_report` | Base name for generated files (default: `ddr_report`) |
| `-m` / `--model` | Ollama model name (default: `llama3`) |
| `--extract-only` | Skip LLM; only extract and build a skeleton report |

---

## Example Command Usage

```bash
# Default: output in ./output, base name ddr_report
python main.py inspection.pdf thermal.pdf -o output -n ddr_report

# Use a different Ollama model
python main.py inspection.pdf thermal.pdf -o output -n ddr_report -m llama3.2

# Extract only (no Ollama needed): PDFs → extracted data + skeleton report
python main.py inspection.pdf thermal.pdf -o output -n ddr_report --extract-only
```

---

## Input Files

- **Inspection Report PDF:** Building/property inspection findings (visual, structural, condition).
- **Thermal Report PDF:** Thermal imaging results (temperature anomalies, heat patterns).

The system extracts all text and embedded images from both PDFs and merges them into one DDR.

---

## Output: DDR Report

The generated **Detailed Diagnostic Report** includes:

1. **Property Issue Summary** — High-level summary of findings  
2. **Area-wise Observations** — Findings by area, with linked images or "Image Not Available"  
3. **Probable Root Cause** — Inferred causes from both reports  
4. **Severity Assessment** — Per-item severity (e.g. Low/Medium/High/Critical) with reasoning  
5. **Recommended Actions** — Suggested next steps  
6. **Additional Notes** — Extra context  
7. **Missing or Unclear Information** — Gaps or ambiguities  
8. **Conflicts** — Explicit disagreements between inspection and thermal reports (if any)

**Generated files:**

- `output/ddr_report.md` — DDR in Markdown  
- `output/ddr_report.pdf` — DDR as PDF  
- `output/ddr_report.json` — DDR in JSON  
- `extracted/images/` — Extracted images from both PDFs  
- `extracted/inspection_observations.json` — Structured inspection data  
- `extracted/thermal_observations.json` — Structured thermal data  

---

## Using Ollama

1. **Install Ollama:** [https://ollama.com](https://ollama.com)  
2. **Pull the default model:**

   ```bash
   ollama pull llama3
   ```

3. Run the project (with Ollama running in the background):

   ```bash
   python main.py inspection.pdf thermal.pdf -o output -n ddr_report
   ```

No API keys or cloud sign-up are required; the LLM runs entirely on your machine.

---

## Project Folder Structure

```
project/
├── main.py                 # Entry point: CLI and pipeline orchestration
├── ddr_system/             # Main package
│   ├── __init__.py
│   ├── config.py           # Paths, Ollama model, system prompt
│   ├── models.py           # Pydantic models (observations, DDR)
│   ├── pdf_loader.py       # PDF text extraction (pdfplumber)
│   ├── image_extractor.py  # Image extraction (PyMuPDF)
│   ├── observation_extractor.py  # Text → structured JSON
│   ├── ddr_generator.py    # Ollama-based DDR generation
│   └── report_writer.py    # Markdown and PDF output
├── extracted/              # Created at run time (gitignored: images/)
│   └── images/             # Extracted images from PDFs
├── output/                 # Created at run time (gitignored)
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Configuration

Optional: create a `.env` file in the project root to override the default Ollama model:

```env
OLLAMA_MODEL=llama3
```

**.env is listed in .gitignore** and must not be committed; use it only for local overrides.

---

## Dependencies

| Package        | Purpose                    |
|----------------|----------------------------|
| pdfplumber     | PDF text extraction        |
| pymupdf        | PDF image extraction       |
| pillow         | Image handling              |
| pydantic       | Data models and validation  |
| python-dotenv  | Optional .env config        |
| reportlab      | PDF report generation       |
| tqdm           | Progress display            |
| ollama         | Ollama Python client       |

---

## License

Use and adapt as needed for your project. If you publish a fork, consider adding a LICENSE file and crediting the original repo.
