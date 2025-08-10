"""
Document Module for Station 3310

This module provides functionality for generating and previewing PDF documents
containing one-time pad data for spy missions.
"""

import io
import logging
import os
import subprocess
import sys
import tempfile
import textwrap
from typing import List, Optional, Union, BinaryIO

import webbrowser
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_spy_pad_pdf(pad_lines: List[str]) -> bytes:
    """
    Generate a PDF document containing one-time pad data for spy missions.
    
    This function creates a PDF with a cover page and subsequent pages containing
    the one-time pad data, formatted for easy reading by field agents.
    
    Args:
        pad_lines: A list of strings containing the one-time pad data
        
    Returns:
        The generated PDF as bytes
    """
    logging.info(f"Generating spy pad PDF with {len(pad_lines)} lines of pad data")
    
    # Initialize PDF canvas with A4 page size
    width, height = A4
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Create cover page
    _create_cover_page(c, width, height)
    c.showPage()

    # Create pad pages
    _create_pad_pages(c, width, height, pad_lines)
    
    # Save the PDF
    c.save()

    # Return the PDF bytes
    buffer.seek(0)
    return buffer.getvalue()
    
def _create_cover_page(c: canvas.Canvas, width: float, height: float) -> None:
    """
    Create the cover page for the spy pad PDF.
    
    Args:
        c: The PDF canvas to draw on
        width: The width of the page
        height: The height of the page
    """
    # Add title
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width/2, height - 150, "STRICTLY CONFIDENTIAL")
    
    # Add subtitle
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 200, "MINISTRY OF REXCHOPPERS")
    c.setFont("Helvetica", 12)

    # Add watermark
    c.setFillColorRGB(0.8, 0.8, 0.8)
    c.setFont("Helvetica-Bold", 72)
    c.rotate(45)
    c.drawCentredString(height/2, -width/4, "TOP SECRET")
    c.rotate(-45)
    c.setFillColor(colors.black)
    
def _create_pad_pages(c: canvas.Canvas, width: float, height: float, pad_lines: List[str]) -> None:
    """
    Create the pages containing the one-time pad data.
    
    Args:
        c: The PDF canvas to draw on
        width: The width of the page
        height: The height of the page
        pad_lines: A list of strings containing the one-time pad data
    """
    # Set up initial values
    c.setFont("Courier", 12)
    y = height - 50
    page_num = 1

    # Add each pad line to the PDF
    for i, row in enumerate(pad_lines, start=1):
        # Format the row with spaces every 5 characters
        grouped = " ".join(textwrap.wrap(row.replace(" ", ""), 5))
        
        # Draw a checkbox and the pad line
        c.rect(30, y-3, 8, 8)
        c.drawString(50, y, f"{i:03d}  {grouped}")
        y -= 15

        # If we've reached the bottom of the page, start a new page
        if y < 50:
            # Add page number to the current page
            c.setFont("Helvetica", 8)
            c.drawRightString(width - 30, 30, f"Page {page_num}")
            c.showPage()
            
            # Reset for the next page
            c.setFont("Courier", 12)
            y = height - 50
            page_num += 1

    # Add page number to the last page
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 30, 30, f"Page {page_num}")

def preview_pdf_external(pdf_bytes: bytes) -> None:
    """
    Open a PDF in the system's default PDF viewer.
    
    This function saves the PDF bytes to a temporary file and opens it
    using the appropriate method for the current operating system.
    
    Args:
        pdf_bytes: The PDF content as bytes
    """
    logging.info("Opening PDF in external viewer")
    
    # Save the PDF to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(pdf_bytes)
        temp_path = f.name
    
    logging.debug(f"Saved PDF to temporary file: {temp_path}")
    
    try:
        # Open the PDF using the appropriate method for the current OS
        if sys.platform == "win32":
            # Windows
            os.startfile(temp_path)
            logging.debug("Opened PDF using os.startfile (Windows)")
        elif sys.platform == "darwin":
            # macOS
            subprocess.run(["open", temp_path], check=True)
            logging.debug("Opened PDF using 'open' command (macOS)")
        else:
            # Linux/Unix
            try:
                subprocess.run(["xdg-open", temp_path], check=True)
                logging.debug("Opened PDF using 'xdg-open' command (Linux/Unix)")
            except (subprocess.SubprocessError, FileNotFoundError):
                # Fall back to webbrowser if xdg-open fails or is not available
                logging.warning("xdg-open failed, falling back to webbrowser")
                webbrowser.open(f"file://{temp_path}")
                logging.debug("Opened PDF using webbrowser")
    except Exception as e:
        logging.error(f"Failed to open PDF: {e}", exc_info=True)
        # Don't re-raise the exception, as this is a non-critical operation