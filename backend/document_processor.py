from pathlib import Path
import pymupdf
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import dspy
from PIL import Image
import logging
from config import AppConfig


logger = logging.getLogger(__name__)

from exceptions import (
    InvalidDocumentError,
    ContentExtractionError,
)

class DocumentProcessor:

    def __init__(self):
        self.validate = dspy.Predict(ValidContent)
        self.ocr = ocr_predictor(pretrained=True)
        
    def process(self, path: str) -> tuple[str, list[Image.Image]]:
        """
        Process a PDF to extract text and images.
        
        :param pdf_path: The path to the PDF file.
        :return: A tuple (text, images) where 'text' is the extracted text and 'images' is a list of PIL images for each page.
        """
        pdf_path = Path(path)
        self._validate_file(pdf_path)
        
        try:
            with pymupdf.open(pdf_path) as doc:
                if len(doc) > AppConfig.MAX_FILE_PAGE:
                    logger.error(f"File page count exceeds {AppConfig.MAX_FILE_PAGE} pages limit.")
                    raise InvalidDocumentError(f"File page count exceeds limit {AppConfig.MAX_FILE_PAGE} pages.")
                logger.info(f"Extracting text and images from: {pdf_path}")
                text = ""
                images = []
                for page in doc:
                    text += self._extract_page_text(page)
                    images.append(self._render_page_image(page))               
                if not self._is_valid_content(text):
                    logger.info("Text extraction quality insufficient, attempting OCR extraction...")
                    text = self._ocr_fallback(pdf_path)
                    
                return text, images
                
        except pymupdf.FileDataError as e:
            raise InvalidDocumentError(f"Invalid PDF structure: {e}") from e
        

    def _validate_file(self, pdf_path: Path):
        """Pre-processing validation"""
        if not pdf_path.exists():
            raise FileNotFoundError(f"File not found: {pdf_path}")
            
        if pdf_path.stat().st_size > AppConfig.MAX_FILE_SIZE:
            raise InvalidDocumentError(
                f"File size {pdf_path.stat().st_size} exceeds limit {AppConfig.MAX_FILE_SIZE} bytes."
            )

    def _extract_page_text(self, page) -> str:
        """Extract and return text from a single page"""
        try:
            text = page.get_text().strip()
            if not text:
                logger.debug("Empty page encountered.")
            return text + "\n"
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}", exc_info=True)
            raise ContentExtractionError("Text extraction failed") from e

    def _render_page_image(self, page) -> Image.Image:
        """Render a single page as an image"""
        try:
            zoom = 2
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
            return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
        except Exception as e:
            logger.error(f"Image rendering failed: {e}", exc_info=True)
            raise ContentExtractionError("Image rendering failed") from e
        
    def _ocr_fallback(self, pdf_path: Path) -> str:
        """OCR processing via DocTR as a fallback for text extraction"""
        try:
            doc = DocumentFile.from_pdf(pdf_path)
            result = self.ocr(doc)
            return result.render()
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}", exc_info=True)
            raise ContentExtractionError(f"OCR extraction failed: {str(e)}") from e
    
    def _is_valid_content(self, text):
        """Determine if the extracted text is valid"""
        if text.strip() == "":
            return False
        return self.validate(text=text).is_valid

class ValidContent(dspy.Signature):
    """Determine if the text content is mostly readable and understandable."""
    text: str = dspy.InputField(desc="Text content extracted from a PDF document")
    is_valid: bool = dspy.OutputField(desc="Whether the content is mostly readable and understandable")

