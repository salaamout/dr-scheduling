"""
Export functions for CSV, PDF, and ZIP generation.
"""

import csv
import io
import zipfile
from fpdf import FPDF
from database import get_log_entries, LOG_CATEGORIES


def export_csv(log_category):
    """Export a log category to CSV format. Returns a string."""
    entries = get_log_entries(log_category)
    output = io.StringIO()
    writer = csv.writer(output)

    # Base headers
    base = ["Full Name", "Chart ID", "Date of Birth"]

    # Category-specific headers (no follow-up date; notes only for Darlene)
    if log_category == "Priority Patients":
        extra = ["Advocate", "Community", "Surgery Type"]
    elif log_category == "Guzman Referrals":
        extra = ["Problem", "Appointment Timeframe"]
    elif log_category == "Laser":
        extra = ["Procedure Type", "Eye", "Date"]
    elif log_category == "Dermatology":
        extra = ["Advocate", "Community", "Procedure", "# Procedures", "Date"]
    elif log_category == "Darlene Prosthetics":
        extra = ["Notes"]
    else:
        extra = []

    writer.writerow(base + extra)

    for entry in entries:
        base_data = [
            entry["full_name"],
            entry["chart_id"],
            entry["date_of_birth"],
        ]

        if log_category == "Priority Patients":
            extra_data = [entry["advocate"] or "", entry["community"] or "", entry["surgery_type"] or ""]
        elif log_category == "Guzman Referrals":
            extra_data = [entry["problem"] or "", entry["appointment_timeframe"] or ""]
        elif log_category == "Laser":
            extra_data = [entry["procedure_type"] or "", entry["eye"] or "", entry["laser_date"] or ""]
        elif log_category == "Dermatology":
            extra_data = [
                entry["advocate"] or "", entry["community"] or "",
                entry["procedure"] or "", entry["procedure_count"] or 1,
                entry["derm_date"] or "",
            ]
        elif log_category == "Darlene Prosthetics":
            extra_data = [entry["notes"] or ""]
        else:
            extra_data = []

        writer.writerow(base_data + extra_data)

    return output.getvalue()


def export_pdf(log_category):
    """Export a log category to PDF format. Returns bytes."""
    entries = get_log_entries(log_category)

    pdf = FPDF(orientation="L", format="letter")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, f"Medical Mission Log: {log_category}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    # Category-specific column setup (no follow-up date; notes only for Darlene)
    if log_category == "Priority Patients":
        headers = ["Full Name", "Chart ID", "DOB", "Advocate", "Community", "Surgery Type"]
        col_widths = [55, 35, 35, 45, 45, 50]
    elif log_category == "Guzman Referrals":
        headers = ["Full Name", "Chart ID", "DOB", "Problem", "Appt Timeframe"]
        col_widths = [60, 40, 40, 65, 60]
    elif log_category == "Laser":
        headers = ["Full Name", "Chart ID", "DOB", "Procedure", "Eye", "Date"]
        col_widths = [55, 35, 35, 50, 30, 40]
    elif log_category == "Dermatology":
        headers = ["Full Name", "Chart ID", "DOB", "Advocate", "Community", "Procedure", "#", "Date"]
        col_widths = [45, 28, 28, 35, 35, 35, 16, 30]
    elif log_category == "Darlene Prosthetics":
        headers = ["Full Name", "Chart ID", "DOB", "Notes"]
        col_widths = [65, 40, 40, 120]
    else:
        headers = ["Full Name", "Chart ID", "DOB"]
        col_widths = [90, 60, 60]

    # Table header
    pdf.set_font("Helvetica", "B", 9)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align="C")
    pdf.ln()

    # Table rows
    pdf.set_font("Helvetica", "", 8)
    for entry in entries:
        base = [
            entry["full_name"][:25],
            entry["chart_id"][:12],
            entry["date_of_birth"] or "",
        ]
        if log_category == "Priority Patients":
            row_data = base + [
                (entry["advocate"] or "")[:20], (entry["community"] or "")[:20],
                (entry["surgery_type"] or "")[:20],
            ]
        elif log_category == "Guzman Referrals":
            row_data = base + [
                (entry["problem"] or "")[:25], (entry["appointment_timeframe"] or "")[:20],
            ]
        elif log_category == "Laser":
            row_data = base + [
                (entry["procedure_type"] or "")[:20], entry["eye"] or "",
                entry["laser_date"] or "",
            ]
        elif log_category == "Dermatology":
            row_data = base + [
                (entry["advocate"] or "")[:18], (entry["community"] or "")[:18],
                (entry["procedure"] or "")[:18], str(entry["procedure_count"] or 1),
                entry["derm_date"] or "",
            ]
        elif log_category == "Darlene Prosthetics":
            row_data = base + [
                (entry["notes"] or "")[:55],
            ]
        else:
            row_data = base

        for i, value in enumerate(row_data):
            pdf.cell(col_widths[i], 7, str(value), border=1)
        pdf.ln()

    # If no entries
    if not entries:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 10, "No entries in this log.", new_x="LMARGIN", new_y="NEXT", align="C")

    return pdf.output()


def export_all_zip():
    """Export all log categories as separate CSV files in a ZIP. Returns bytes."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for category in LOG_CATEGORIES:
            csv_data = export_csv(category)
            filename = f"{category.lower().replace(' ', '_')}_log.csv"
            zf.writestr(filename, csv_data)
    zip_buffer.seek(0)
    return zip_buffer.getvalue()
