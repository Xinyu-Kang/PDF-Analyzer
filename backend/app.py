from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
import logging
import json

from document_processor import DocumentProcessor
from document_analyzer import DocumentAnalyzer
from config import AppConfig, configure_dspy, LOGGING_CONFIG


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize heavy resources once
    logger.info("Starting up backend resources...")
    configure_dspy()
    app.state.document_processor = DocumentProcessor()
    app.state.document_analyzer = DocumentAnalyzer()
    yield  # Run the application
    logger.info("Shutting down backend resources...")

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Dependency functions
def get_processor():
    return app.state.document_processor

def get_analyzer():
    return app.state.document_analyzer

@app.post("/analyze/")
async def analyze_document(
    file: UploadFile = File(...),
    processor: DocumentProcessor = Depends(get_processor),
    analyzer: DocumentAnalyzer = Depends(get_analyzer)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    temp_dir = AppConfig.TEMP_DIR
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save file.")

    try:
        logger.info(f"Loading document: {file.filename}")
        text, images = processor.process(temp_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction error: {e}")

    try:
        logger.info("Analyzing document content with LLM...")
        result = analyzer(text, images)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {e}")

    try:
        os.remove(temp_file_path)
    except Exception as e:
        logger.warning(f"Could not remove temporary file: {e}")

    print("\n---------- Results ----------\n")
    print(json.dumps(result, indent=2))

    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)