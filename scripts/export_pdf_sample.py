"""
One-shot script to generate a realistic retailer-style PDF report
(table: product / rating / review text / date) from a subset of the
Kaggle Amazon Product Reviews dataset (Reviews.csv) — real review
content, just rendered as a PDF report, simulating a retailer's
exported review report.

Usage:
    python scripts/export_pdf_sample.py
"""

from pathlib import Path

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from xml.sax.saxutils import escape

INPUT_PATH = Path("data/raw/Reviews.csv")
OUTPUT_PATH = Path("data/raw/sample_review_report.pdf")
SAMPLE_SIZE = 30
MAX_TEXT_CHARS = 200  # keep the table readable, like a real report would


def main() -> None:
    df = pd.read_csv(INPUT_PATH, nrows=SAMPLE_SIZE)
    styles = getSampleStyleSheet()

    rows = [["Product ID", "Rating", "Review", "Date"]]
    for _, row in df.iterrows():
        review_date = pd.to_datetime(row["Time"], unit="s").date().isoformat()
        summary = str(row.get("Summary", "") or "")
        text = str(row.get("Text", "") or "")
        combined = escape(f"{summary}. {text}".strip(". ")[:MAX_TEXT_CHARS])

        rows.append([
            row["ProductId"],
            str(row["Score"]),
            Paragraph(combined, styles["Normal"]),
            review_date,
        ])

    doc = SimpleDocTemplate(str(OUTPUT_PATH), pagesize=letter)
    table = Table(rows, colWidths=[70, 45, 300, 65], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    doc.build([
        Paragraph("Customer Review Export Report", styles["Title"]),
        Spacer(1, 12),
        table,
    ])
    print(f"Saved {len(rows) - 1} reviews to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
