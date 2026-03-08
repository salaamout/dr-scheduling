"""
Export functions for CSV and PDF generation.
"""

import csv
import io
from fpdf import FPDF
from database import get_log_entries, LOG_CATEGORIES


def export_csv(log_category):
    """Export a log category to CSV format. Returns a string."""
    entries = get_log_entries(log_category)
    output = io.StringIO()
    writer = csv.writer(output)

    # Base headers
    base = ["Full Name", "Chart ID", "Date of Birth", "Date of Encounter", "Status"]

    # Category-specific headers
    if log_category == "Priority Patients":
        extra = ["Advocate", "Community"]
    elif log_category == "Guzman Referrals":
        extra = ["Problem", "Appointment Timeframe"]
    elif log_category == "Laser":
        extra = ["Procedure Type", "Eye", "Date"]
    elif log_category == "Dermatology":
        extra = ["Advocate", "Community", "Procedure", "Date"]
    else:
        extra = []

    writer.writerow(base + extra + ["Notes", "Follow-up Date"])

    for entry in entries:
        base_data = [
            entry["full_name"],
            entry["chart_id"],
            entry["date_of_birth"],
            entry["date_of_encounter"] or "",
            entry["status"],
        ]

        if log_category == "Priority Patients":
            extra_data = [entry["advocate"] or "", entry["community"] or ""]
        elif log_category == "Guzman Referrals":
            extra_data = [entry["problem"] or "", entry["appointment_timeframe"] or ""]
        elif log_category == "Laser":
            extra_data = [entry["procedure_type"] or "", entry["eye"] or "", entry["laser_date"] or ""]
        elif log_category == "Dermatology":
            extra_data = [entry["advocate"] or "", entry["community"] or "", entry["procedure"] or "", entry["derm_date"] or ""]
        else:
            extra_data = []

        writer.writerow(base_data + extra_data + [entry["notes"], entry["follow_up_date"] or ""])

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

    # Category-specific column setup
    if log_category == "Priority Patients":
        headers = ["Full Name", "Chart ID", "DOB", "Encounter", "Status", "Advocate", "Community", "Notes", "Follow-up"]
        col_widths = [42, 25, 25, 28, 22, 35, 35, 40, 25]
    elif log_category == "Guzman Referrals":
        headers = ["Full Name", "Chart ID", "DOB", "Encounter", "Status", "Problem", "Appt Timeframe", "Notes", "Follow-up"]
        col_widths = [42, 25, 25, 28, 22, 40, 35, 40, 25]
    elif log_category == "Laser":
        headers = ["Full Name", "Chart ID", "DOB", "Encounter", "Status", "Procedure", "Eye", "Date", "Notes", "Follow-up"]
        col_widths = [40, 25, 25, 28, 22, 35, 18, 25, 40, 25]
    elif log_category == "Dermatology":
        headers = ["Full Name", "Chart ID", "DOB", "Encounter", "Status", "Advocate", "Community", "Procedure", "Date", "Notes"]
        col_widths = [38, 22, 25, 25, 20, 30, 30, 30, 25, 37]
    else:
        headers = ["Full Name", "Chart ID", "DOB", "Encounter", "Status", "Notes", "Follow-up"]
        col_widths = [55, 30, 30, 35, 25, 70, 30]

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
            entry["date_of_encounter"] or "",
            entry["status"] or "",
        ]
        if log_category == "Priority Patients":
            row_data = base + [
                (entry["advocate"] or "")[:20], (entry["community"] or "")[:20],
                (entry["notes"] or "")[:25], entry["follow_up_date"] or "",
            ]
        elif log_category == "Guzman Referrals":
            row_data = base + [
                (entry["problem"] or "")[:25], (entry["appointment_timeframe"] or "")[:20],
                (entry["notes"] or "")[:25], entry["follow_up_date"] or "",
            ]
        elif log_category == "Laser":
            row_data = base + [
                (entry["procedure_type"] or "")[:20], entry["eye"] or "",
                entry["laser_date"] or "", (entry["notes"] or "")[:25],
                entry["follow_up_date"] or "",
            ]
        elif log_category == "Dermatology":
            row_data = base + [
                (entry["advocate"] or "")[:18], (entry["community"] or "")[:18],
                (entry["procedure"] or "")[:18], entry["derm_date"] or "",
                (entry["notes"] or "")[:22],
            ]
        else:
            row_data = base + [
                (entry["notes"] or "")[:40], entry["follow_up_date"] or "",
            ]

        for i, value in enumerate(row_data):
            pdf.cell(col_widths[i], 7, str(value), border=1)
        pdf.ln()

    # If no entries
    if not entries:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 10, "No entries in this log.", new_x="LMARGIN", new_y="NEXT", align="C")

    return pdf.output()


def export_all_csv():
    """Export all log categories to a single CSV. Returns a string."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Log Category", "Full Name", "Chart ID", "Date of Birth",
        "Date of Encounter", "Status", "Advocate", "Community",
        "Problem", "Appointment Timeframe", "Procedure Type", "Eye", "Laser Date",
        "Procedure", "Derm Date", "Notes", "Follow-up Date"
    ])

    for category in LOG_CATEGORIES:
        entries = get_log_entries(category)
        for entry in entries:
            writer.writerow([
                category,
                entry["full_name"],
                entry["chart_id"],
                entry["date_of_birth"],
                entry["date_of_encounter"] or "",
                entry["status"],
                entry["advocate"] or "",
                entry["community"] or "",
                entry["problem"] or "",
                entry["appointment_timeframe"] or "",
                entry["procedure_type"] or "",
                entry["eye"] or "",
                entry["laser_date"] or "",
                entry["procedure"] or "",
                entry["derm_date"] or "",
                entry["notes"],
                entry["follow_up_date"] or "",
            ])

    return output.getvalue()
