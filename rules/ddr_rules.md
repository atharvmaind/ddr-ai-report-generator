Project: AI DDR Report Generator

Rules:

1. The system must read two PDFs:
   - Inspection Report
   - Thermal Report

2. Extract:
   - Text observations
   - Images

3. Images must be saved in /extracted/images.

4. Extracted text must be saved in structured JSON.

5. Observations must be categorized by:
   - Area
   - Issue
   - Temperature anomaly
   - Structural defect

6. The AI must merge both reports.

7. Handle:
   - Duplicate observations
   - Conflicting statements
   - Missing information

8. If missing data → output "Not Available"

9. Final DDR structure must include:

   1 Property Issue Summary
   2 Area-wise Observations
   3 Probable Root Cause
   4 Severity Assessment
   5 Recommended Actions
   6 Additional Notes
   7 Missing Information

10. Images must be inserted under the correct area observation.

11. The system must never hallucinate facts.

12. Output report should be generated as Markdown and PDF.