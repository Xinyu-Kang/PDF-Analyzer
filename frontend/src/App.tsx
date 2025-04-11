import React, { useState, ChangeEvent, useRef, useEffect } from 'react';
import './App.css';

interface AnalysisResult {
  description: string;
  summary: string;
  notable_info: string[];
  confidence?: {
    score?: number;
    notes?: string[];
  };
}

const MAX_FILE_SIZE_MB = 2;

const FileUploader: React.FC<{
  onFileSelect: (file: File) => void;
  loading: boolean;
}> = ({ onFileSelect, loading }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <div className="upload-container">
      <input
        type="file"
        accept=".pdf"
        ref={fileInputRef}
        onChange={handleFileChange}
        aria-label="Select PDF file"
        disabled={loading}
        style={{ display: 'none' }}
      />
      <button
        className="browse-button"
        onClick={() => fileInputRef.current?.click()}
        disabled={loading}
        aria-busy={loading}
      >
        Choose PDF File
      </button>
    </div>
  );
};

const AnalysisResults: React.FC<{ result: AnalysisResult }> = ({ result }) => (
  <div className="results" role="region" aria-live="polite">
    <h2>Analysis Results</h2>
    
    <div className="result-section">
      <h3>Document Purpose</h3>
      <p>{result.description || 'No description available'}</p>
    </div>

    <div className="result-section">
      <h3>Key Summary</h3>
      <p>{result.summary || 'No summary generated'}</p>
    </div>

    <div className="result-section">
      <h3>Notable Details</h3>
      {result.notable_info?.length ? (
        <ul>
          {result.notable_info.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>No notable details identified</p>
      )}
    </div>

    {result.confidence && (
      <div className="metadata-section">
        <h3>Analysis Confidence</h3>
        {/* <p>Text Quality: {result.metadata.text_quality || 'unknown'}</p>
        <p>Pages Processed: {result.metadata.images_processed || 0}</p> */}
        {result.confidence.score && (
          <p>Confidence Score: {Math.round(result.confidence.score * 100)}%</p>
        )}
        <p>Notes:</p>
        <ul>
          {result.confidence.notes && (result.confidence.notes.map((item, index) => (
            <li key={index}>{item}</li>
          )))}
        </ul>
      </div>
    )}
  </div>
);

const App: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef(new AbortController());

  useEffect(() => {
    return () => abortControllerRef.current.abort();
  }, []);

  const handleFileSelect = (selectedFile: File) => {
    setError('');
    
    if (selectedFile.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`File size exceeds ${MAX_FILE_SIZE_MB}MB limit`);
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are accepted');
      return;
    }

    setFile(selectedFile);
    setAnalysisResult(null);
  };

  const analyzeDocument = async () => {
    if (!file) return;

    setLoading(true);
    setError('');
    abortControllerRef.current = new AbortController();

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/analyze/', {
        method: 'POST',
        body: formData,
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Analysis failed (${response.status})`);
      }

      const data: unknown = await response.json();
      if (!isAnalysisResult(data)) {
        throw new Error('Invalid response format from server');
      }

      setAnalysisResult(data);
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Analysis failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const isAnalysisResult = (data: unknown): data is AnalysisResult => {
    return (
      typeof data === 'object' &&
      data !== null &&
      'description' in data &&
      'summary' in data &&
      Array.isArray((data as AnalysisResult).notable_info)
    );
  };

  return (
    <div className="App">
      <header className="App-header" role="banner">
        <h1>Document Scanner & Analyzer</h1>
        <p className="subtitle">PDF Content Understanding with LLM</p>
      </header>

      <main className="main-content">
        <FileUploader onFileSelect={handleFileSelect} loading={loading} />
        
        {file && (
          <div className="file-actions">
            <p className="selected-file">
              Selected: <strong>{file.name}</strong>
              <span className="file-size">
                ({Math.round(file.size / 1024)} KB)
              </span>
            </p>
            <button
              className="analyze-button"
              onClick={analyzeDocument}
              disabled={loading}
              aria-label={loading ? 'Analyzing document' : 'Start analysis'}
            >
              {loading ? (
                <>
                  <span className="spinner" aria-hidden="true"></span>
                  Analyzing...
                </>
              ) : (
                'Analyze Document'
              )}
            </button>
          </div>
        )}

        {error && (
          <div className="error" role="alert">
            ⚠️ {error}
          </div>
        )}

        {analysisResult && <AnalysisResults result={analysisResult} />}
      </main>
    </div>
  );
};

export default App;