import sys
import logging
import logging.config
import json
from document_processor import DocumentProcessor
from document_analyzer import DocumentAnalyzer
from config import configure_dspy, LOGGING_CONFIG


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python c_main.py <document_path>")
        sys.exit(1)
    doc_path = sys.argv[1]

    try:
        logger.info(f"Loading document: {doc_path}")
        processor = DocumentProcessor()
        text, images = processor.process(doc_path)  # Assuming process() now returns (text, images)
    except Exception as e:
        logger.exception(f"Failed to process document '{doc_path}': {e}")
        sys.exit(1)

    try:
        logger.info("Analyzing document content with LLM...")
        configure_dspy()
        analyzer = DocumentAnalyzer()
        result = analyzer(text, images)
    except Exception as e:
        logger.exception(f"Document analysis failed: {e}")
        sys.exit(1)

    print("\n---------- Results ----------\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()