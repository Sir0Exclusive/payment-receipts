from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from io import BytesIO
import qrcode
import barcode
from barcode.writer import ImageWriter
import pandas as pd
import os
import argparse
import hashlib
import json
from datetime import datetime

def read_recipients_from_excel(file_path):
    df = pd.read_excel(file_path)
    return df.to_dict(orient='records')

def generate_receipt_hash(receipt_data):
    """Generate a unique hash for tamper detection"""
    data_string = json.dumps(receipt_data, sort_keys=True)
    return hashlib.sha256(data_string.encode()).hexdigest()

def generate_qr_and_barcode(receipt_id, receipt_data):
    """Generate QR code and barcode for the receipt (in-memory)"""
    # Create verification URL (will be hosted on GitHub Pages)
    verify_url = f"https://Sir0Exclusive.github.io/payment-receipts/verify.html?id={receipt_id}"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    
    # Generate barcode
    code128 = barcode.get_barcode_class('code128')
    barcode_obj = code128(receipt_id, writer=ImageWriter())
    barcode_buffer = BytesIO()
    barcode_obj.write(barcode_buffer)
    barcode_buffer.seek(0)

    return qr_buffer, barcode_buffer

def save_receipt_data(receipt_id, receipt_data, receipt_hash, output_dir):
    """Save receipt data as JSON for web portal"""
    data = {
        'id': receipt_id,
        'data': receipt_data,
        'hash': receipt_hash,
        'timestamp': datetime.now().isoformat()
    }
    
    json_dir = os.path.join(output_dir, 'data')
    os.makedirs(json_dir, exist_ok=True)
    json_path = os.path.join(json_dir, f"{receipt_id}.json")
    
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return json_path

def create_receipt_pdf(recipient, signature_path, output_path, name, qr_image, barcode_image, receipt_hash):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Subtle border
    c.setLineWidth(0.8)
    c.setStrokeColorRGB(0.75, 0.75, 0.75)
    c.rect(18 * mm, 18 * mm, width - 36 * mm, height - 36 * mm)
    c.setStrokeColorRGB(0, 0, 0)

    # Header
    c.setFont("Helvetica-Bold", 22)
    c.drawString(24 * mm, height - 35 * mm, "Payment Receipt")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 24 * mm, height - 32 * mm, "Original")
    c.setLineWidth(1)
    c.line(24 * mm, height - 40 * mm, width - 24 * mm, height - 40 * mm)

    # Receipt meta
    c.setFont("Helvetica-Bold", 10)
    c.drawString(24 * mm, height - 52 * mm, "Receipt No")
    c.setFont("Helvetica", 10)
    c.drawString(55 * mm, height - 52 * mm, f"{recipient.get('Receipt No', 'AUTO')}")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(120 * mm, height - 52 * mm, "Date")
    c.setFont("Helvetica", 10)
    c.drawString(135 * mm, height - 52 * mm, f"{recipient['Date']}")

    # Parties
    c.setFont("Helvetica-Bold", 10)
    c.drawString(24 * mm, height - 68 * mm, "Issued By")
    c.setFont("Helvetica", 10)
    c.drawString(55 * mm, height - 68 * mm, f"{name}")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(24 * mm, height - 82 * mm, "Received From")
    c.setFont("Helvetica", 10)
    c.drawString(55 * mm, height - 82 * mm, f"{recipient['Name']}")

    # Amounts
    amount = recipient['Amount']
    if not str(amount).startswith('¥'):
        amount = f"¥{amount}"
    due_amount = recipient.get('Due Amount', '')
    if due_amount and not str(due_amount).startswith('¥'):
        due_amount = f"¥{due_amount}"

    def parse_currency(value):
        if value is None:
            return 0.0
        text = str(value).replace('¥', '').replace(',', '').strip()
        try:
            return float(text) if text else 0.0
        except ValueError:
            return 0.0

    amount_value = parse_currency(amount)
    due_value = parse_currency(due_amount)
    paid_value = max(amount_value - due_value, 0.0)
    status_text = "PAID" if due_value <= 0 else "DUE"
    paid_display = f"¥{paid_value:,.2f}" if paid_value % 1 else f"¥{int(paid_value)}"

    c.setLineWidth(0.8)
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.line(24 * mm, height - 92 * mm, width - 24 * mm, height - 92 * mm)
    c.setStrokeColorRGB(0, 0, 0)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(24 * mm, height - 105 * mm, "Description")
    c.setFont("Helvetica", 10)
    c.drawString(55 * mm, height - 105 * mm, f"{recipient['Description']}")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(24 * mm, height - 120 * mm, "Amount")
    c.setFont("Helvetica", 10)
    c.drawString(55 * mm, height - 120 * mm, f"{amount}")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(24 * mm, height - 135 * mm, "Due Amount")
    c.setFont("Helvetica", 10)
    c.drawString(55 * mm, height - 135 * mm, f"{due_amount}")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(24 * mm, height - 150 * mm, "Payment Status")
    c.setFont("Helvetica", 10)
    c.drawString(55 * mm, height - 150 * mm, status_text)

    # Total highlight
    c.setFillColorRGB(0.95, 0.95, 0.98)
    c.rect(24 * mm, height - 170 * mm, width - 48 * mm, 12 * mm, fill=True, stroke=False)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(26 * mm, height - 162 * mm, "Total Paid")
    c.drawRightString(width - 26 * mm, height - 162 * mm, f"{paid_display}")

    # Signature + verification
    c.setFont("Helvetica-Bold", 9)
    c.drawString(24 * mm, height - 190 * mm, "Authorized Signature")
    c.drawImage(signature_path, 24 * mm, height - 212 * mm, width=45*mm, height=16*mm, mask='auto')

    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(width - 24 * mm, height - 190 * mm, "Scan to Verify")
    c.drawImage(ImageReader(qr_image), width - 50 * mm, height - 215 * mm, width=22*mm, height=22*mm)
    c.drawImage(ImageReader(barcode_image), width - 80 * mm, height - 215 * mm, width=26*mm, height=18*mm)

    # Watermark (tamper-evident)
    c.saveState()
    c.setFont("Helvetica-Bold", 28)
    c.setFillColorRGB(0.88, 0.88, 0.88)
    c.translate(width / 2, height / 2)
    c.rotate(30)
    c.drawCentredString(0, 0, "VERIFY ONLINE")
    c.restoreState()

    # Verification Hash (tamper-proof)
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(24 * mm, 34 * mm, f"Verification Hash: {receipt_hash[:32]}...")
    c.setFillColorRGB(0, 0, 0)

    # Footer
    c.setLineWidth(0.8)
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.line(24 * mm, 28 * mm, width - 24 * mm, 28 * mm)
    c.setStrokeColorRGB(0, 0, 0)
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2, 20 * mm, "Verify this receipt online. This document is valid without a stamp.")

    c.save()

def lock_pdf(input_pdf, output_pdf):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    # Set permissions: allow printing and viewing, disallow editing
    writer.add_metadata(reader.metadata)
    writer.encrypt(user_password="", owner_password="owner123", permissions_flag=0b0000010000000100)
    with open(output_pdf, "wb") as f:
        writer.write(f)


def main():
    parser = argparse.ArgumentParser(description="Generate payment receipts.")
    parser.add_argument('--name', type=str, help='Recipient name')
    parser.add_argument('--amount', type=str, help='Amount in Yen')
    parser.add_argument('--due', type=str, help='Due Amount in Yen')
    parser.add_argument('--date', type=str, help='Date')
    parser.add_argument('--desc', type=str, help='Description')
    parser.add_argument('--receipt', type=str, help='Receipt No')
    args = parser.parse_args()

    signature_path = "signature.png"
    output_dir = "receipts"
    os.makedirs(output_dir, exist_ok=True)
    author_name = "RABIUL MD SARWAR IBNA"

    if args.name and args.amount and args.date and args.desc:
        # Generate for a single recipient (from command line)
        recipient = {
            'Name': args.name,
            'Amount': args.amount,
            'Due Amount': args.due if args.due else '',
            'Date': args.date,
            'Description': args.desc,
            'Receipt No': args.receipt if args.receipt else 'AUTO'
        }
        receipt_id = args.receipt if args.receipt else f"R{datetime.now().strftime('%Y%m%d%H%M%S')}"
        receipt_hash = generate_receipt_hash(recipient)
        qr_image, barcode_image = generate_qr_and_barcode(receipt_id, recipient)
        save_receipt_data(receipt_id, recipient, receipt_hash, output_dir)
        
        temp_pdf = os.path.join(output_dir, f"{recipient['Name']}_temp.pdf")
        final_pdf = os.path.join(output_dir, f"{recipient['Name']}_receipt.pdf")
        create_receipt_pdf(recipient, signature_path, temp_pdf, author_name, qr_image, barcode_image, receipt_hash)
        lock_pdf(temp_pdf, final_pdf)
        os.remove(temp_pdf)
        print(f"Receipt generated for {recipient['Name']} in {output_dir}/")
    else:
        # Generate for all recipients in Excel (use data file to preserve macro workbook)
        excel_path = "recipients_data.xlsx"
        if not os.path.exists(excel_path):
            excel_path = "recipients.xlsx"
        recipients = read_recipients_from_excel(excel_path)
        for recipient in recipients:
            receipt_id = str(recipient.get('Receipt No', f"R{datetime.now().strftime('%Y%m%d%H%M%S')}"))
            receipt_hash = generate_receipt_hash(recipient)
            qr_image, barcode_image = generate_qr_and_barcode(receipt_id, recipient)
            save_receipt_data(receipt_id, recipient, receipt_hash, output_dir)
            
            temp_pdf = os.path.join(output_dir, f"{recipient['Name']}_temp.pdf")
            final_pdf = os.path.join(output_dir, f"{recipient['Name']}_receipt.pdf")
            create_receipt_pdf(recipient, signature_path, temp_pdf, author_name, qr_image, barcode_image, receipt_hash)
            lock_pdf(temp_pdf, final_pdf)
            os.remove(temp_pdf)
        print(f"Receipts generated in {output_dir}/")

if __name__ == "__main__":
    main()

