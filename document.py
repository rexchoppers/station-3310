import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import textwrap

def generate_spy_pad_pdf(pad_lines):
    width, height = A4
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width/2, height - 150, "STRICTLY CONFIDENTIAL")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 200, "MINISTRY OF REXCHOPPERS")
    c.setFont("Helvetica", 12)

    # Watermark
    c.setFillColorRGB(0.8, 0.8, 0.8)
    c.setFont("Helvetica-Bold", 72)
    c.rotate(45)
    c.drawCentredString(height/2, -width/4, "TOP SECRET")
    c.rotate(-45)
    c.setFillColor(colors.black)

    c.showPage()

    # === Pad Pages ===
    c.setFont("Courier", 12)
    y = height - 50
    page_num = 1

    for i, row in enumerate(pad_lines, start=1):
        grouped = " ".join(textwrap.wrap(row.replace(" ", ""), 5))
        c.rect(30, y-3, 8, 8)
        c.drawString(50, y, f"{i:03d}  {grouped}")
        y -= 15

        if y < 50:
            c.setFont("Helvetica", 8)
            c.drawRightString(width - 30, 30, f"Page {page_num}")
            c.showPage()
            c.setFont("Courier", 12)
            y = height - 50
            page_num += 1

    c.setFont("Helvetica", 8)
    c.drawRightString(width - 30, 30, f"Page {page_num}")
    c.save()

    buffer.seek(0)
    return buffer.getvalue()
