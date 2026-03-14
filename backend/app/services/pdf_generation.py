
from pathlib import Path
import os
from fpdf import FPDF
from app.models.pdf_data import PDFHeader, PDFPaymentData

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGE_DIR = PROJECT_ROOT / "public/logo_banesco.png"

def create_pdf()->FPDF:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    return pdf


def create_header(pdf:FPDF, image_path:Path, header_data:PDFHeader)->None:
    if image_path.exists():
        pdf.image(str(image_path), x=10, y=10, w=60)
        pdf.ln(15)
    else:
        pdf.set_font("helvetica", "B", 16)
        pdf.set_text_color(0, 51, 102) # Azul oscuro Banesco
        pdf.cell(0, 10, "Pago Electrónico Banesco", ln=True)
        pdf.set_text_color(0, 0, 0) # Reset a negro
        pdf.ln(5)

    details = [
        ("Nombre de la Empresa:", header_data.company_name),
        ("RIF:", header_data.rif),
        ("Tipo de Documento:", header_data.doc_type),
        ("Número de Documento:", header_data.doc_number),
        ("Fecha Envío Documento:", header_data.sent_date),
        ("Fecha Proceso:", header_data.process_date)
    ]

    label_width = 50

    for key, value in details:
        # Bold label
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(label_width, 5, key, ln=0)
        # Regular text value
        pdf.set_font("helvetica", "", 9)
        pdf.cell(0, 5, value, ln=1)

    pdf.ln(2)

def create_payment_data(pdf:FPDF, payment_data:PDFPaymentData)->None:
    headers = ["TIPO DE INFORMACIÓN", "REFERENCIA", "C.I/R.I.F", "NOMBRE", "NÚMERO DE CUENTA", "MONTO", "ESTATUS"]

    # Adjust column widths to fit A4 Portrait width (approx 190mm available)
    col_widths = [35, 22, 22, 38, 40, 15, 28]

    pdf.set_font("helvetica", "B", 8)
    for i in range(len(headers)):
        pdf.cell(col_widths[i], 5, headers[i], border=0, ln=0, align="L")
    pdf.ln(5)

    data = [
                payment_data.information_type, 
                payment_data.reference, 
                payment_data.ci_rif, 
                payment_data.name, 
                payment_data.account_number, 
                payment_data.amount, 
                payment_data.status
    ]

    pdf.set_font("helvetica", "", 8)
    for i in range(len(data)):
        pdf.cell(col_widths[i], 5, data[i], border=0, ln=0, align="L")
    pdf.ln(5)


def generate_pdf(header_data:PDFHeader, payment_data:PDFPaymentData, pdf_path:Path):
    pdf = create_pdf()
    create_header(pdf, IMAGE_DIR, header_data)
    create_payment_data(pdf, payment_data)
    safe_filename = "".join(c for c in payment_data.name if c.isalnum() or c in " _-").strip()
    output_filename = f"{safe_filename}.pdf"
    pdf_path_name= pdf_path / output_filename
    pdf.output(str(pdf_path_name))


