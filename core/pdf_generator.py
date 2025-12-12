import os
from fpdf import FPDF
from datetime import datetime


def generate_sanction_letter(data: dict) -> str:
    """
    Generate a clean sanction letter PDF from user + loan data.
    Returns the file path of the generated PDF.
    """

    # Extract necessary fields
    name = data.get("name", "Applicant")
    approved_amount = data.get("approved_amount", 0)
    tenure = data.get("tenure", 12)
    emi = data.get("emi", 0)
    pan = data.get("pan", "")
    timestamp = data.get("sanction_timestamp") or datetime.utcnow().isoformat()

    # Output file
    filename = f"sanction_letter_{name.replace(' ', '_')}.pdf"
    filepath = os.path.join(os.getcwd(), filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Loan Sanction Letter", ln=True, align="C")

    pdf.ln(8)
    pdf.set_font("Arial", size=12)

    pdf.multi_cell(0, 8, f"Date of Issue: {timestamp}")
    pdf.multi_cell(0, 8, f"Borrower Name: {name}")
    pdf.multi_cell(0, 8, f"PAN: {pan}")
    pdf.multi_cell(0, 8, f"Approved Loan Amount: Rs.    {approved_amount:,}")
    pdf.multi_cell(0, 8, f"Loan Tenure: {tenure} months")
    pdf.multi_cell(0, 8, f"Monthly EMI: Rs. {emi:,}")

    pdf.ln(10)
    pdf.multi_cell(
        0,
        8,
        "Congratulations! Based on the information provided and our "
        "credit evaluation, your personal loan has been approved. Please "
        "retain this document for your records.",
    )

    pdf.ln(10)
    pdf.multi_cell(
        0,
        8,
        "This is a system-generated sanction letter and does not require a signature.",
    )

    pdf.output(filepath)
    return filepath
