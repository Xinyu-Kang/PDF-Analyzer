# Document Scanner and Analyzer

This project is a document scanner and analyzer designed to process PDF documents to extract high-level descriptions, summaries, and notable information. 

The project includes both a backend API built with FastAPI and a front-end web application built with React and TypeScript.

---

## Project Architecture
```text
document-scanner/
├── backend/
│   ├── app.py                 # FastAPI application entry point
│   ├── main.py                # Minimal CLI tool (optional)
│   ├── config.py              # Application configuration and logging setup
│   ├── document_processor.py  # PDF processing and OCR fallback logic
│   ├── document_analyzer.py   # DSPy-based document analysis module
│   ├── exceptions.py          # Custom exception classes
│   ├── requirements.txt       # Python virtual environment dependencies
│   └── .env                   # Environment variables (not committed)
├── frontend/
│   ├── public/
│   │   └── index.html         # HTML template
│   ├── src/
│   │   ├── App.tsx            # React application code
│   │   ├── App.css            # CSS styles for the front-end
│   │   ├── index.tsx          # React DOM render entry point
│   │   └── index.css          # Global CSS
│   └── package.json           # Frontend dependencies and scripts
└── README.md                  # This documentation
```
- **Backend:**  
  The backend is built using FastAPI. It handles file uploads at `/analyze/`, processes the document using a combination of direct text extraction, OCR (if necessary), and then analyzes the content using DSPy.

- **Frontend:**  
  The front-end (React/TypeScript) provides a interface allowing users to browse and select a PDF file, then submit it for analysis. It displays status messages, error messages, and formatted results.

---
## Prerequisites

- **Python 3.10–3.12** (for the backend)
- **Node.js and `npm`** (for the frontend)

---
## Setup

### Backend Setup

1. **Create and Activate Virtual Environment:**
  ```bash
  cd backend
  python -m venv .venv
  source .venv/bin/activate  # Linux/MacOS; on Windows use `.venv\Scripts\activate`
  ```
2. **Install Dependencies:**
  ```bash
  pip install -r requirements.txt
  ```
3.	**Configure Environment Variables:**
   
  Create a `.env` file in the backend directory and add:
  ```env
  OPENAI_API_KEY=your_api_key_here
  DSPY_MODEL=openai/gpt-4o-mini
  TEMP_DIR=temp
  MAX_FILE_SIZE_MB=2
  LOG_LEVEL=INFO
  LOG_FILE=app.log
  ```
  Input your OpenAI API key for `OPENAI_API_KEY`. Change the configuration variables if needed.

4.	**Run the FastAPI App:**
  ```bash
  uvicorn app:app --reload
  ```
  The API will run on http://localhost:8000.
  It might take some on the first start up for DocTR to download the OCR models.

### Frontend Setup

1.	**Install Node.js:**
   
  Ensure Node.js and `npm` (or `yarn`) are installed.

2.  **Navigate to the Frontend Directory:**
  ```bash
  cd frontend
  ```

3.	**Install Dependencies:**
  ```bash
  npm install
  ```

4.	**Run the Frontend Application:**
  ```bash
  npm start
  ```
  The front-end application should run on http://localhost:3000.
