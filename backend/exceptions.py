class DocumentProcessingError(Exception):
    """Base class for document processing errors"""
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(message)

class InvalidDocumentError(DocumentProcessingError):
    """Raised for invalid document formats or content"""

class ContentExtractionError(DocumentProcessingError):
    """Raised when content extraction from document fails"""
