from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtCore import QByteArray, QBuffer, QIODevice

class PdfPreviewWidget(QWidget):
    def __init__(self, pdf_bytes, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Create a QByteArray from the PDF bytes
        byte_array = QByteArray(pdf_bytes)
        
        # Create a QBuffer to wrap the QByteArray
        self.buffer = QBuffer(self)
        self.buffer.setData(byte_array)
        self.buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        
        # Load the PDF document from the buffer
        self.pdf_doc = QPdfDocument(self)
        self.pdf_doc.load(self.buffer)

        # Create and set up the PDF view
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_doc)

        layout.addWidget(self.pdf_view)
        self.setLayout(layout)
