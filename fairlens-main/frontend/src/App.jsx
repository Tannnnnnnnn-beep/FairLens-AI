import React, { useState } from 'react';
import axios from 'axios';
import { FiShield, FiUploadCloud, FiPlay, FiMessageCircle, FiBarChart2 } from 'react-icons/fi';
import { useDropzone } from 'react-dropzone';
import Dashboard from './components/Dashboard';
import CareerCoach from './components/CareerCoach';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  // Navigation state: 'audit' or 'coach'
  const [activeTab, setActiveTab] = useState('audit');

  // Audit states
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'text/csv': ['.csv']
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      const file = acceptedFiles[0];
      if (file) {
        setSelectedFile(file);
        setError(null);
      }
    }
  });

  const handleRunAudit = async () => {
    if (!selectedFile) return;
    
    setLoading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/audit`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResults(response.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "An error occurred during the audit. Please check backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="bg-decor"></div>

      {/* Top Navbar */}
      <nav className="navbar fade-up">
        <div className="logo-area">
          <div className="logo-icon">
             <span className="logo-dot"></span>
             <FiShield size={20} />
          </div>
          <div>
            <div className="logo-text">FairLens AI</div>
            <div className="logo-subtext">HIRING.BIAS / V2.0</div>
          </div>
        </div>
        
        {/* Tab Navigation */}
        <div className="nav-tabs">
          <button 
            className={`nav-tab ${activeTab === 'audit' ? 'nav-tab-active' : ''}`}
            onClick={() => setActiveTab('audit')}
            id="tab-audit"
          >
            <FiBarChart2 size={16} />
            Bias Audit
          </button>
          <button 
            className={`nav-tab ${activeTab === 'coach' ? 'nav-tab-active' : ''}`}
            onClick={() => setActiveTab('coach')}
            id="tab-coach"
          >
            <FiMessageCircle size={16} />
            Career Coach
          </button>
        </div>

        <div className="nav-actions">
          <button className="btn btn-primary" style={{ padding: '0.6rem 1.25rem' }}>
            {activeTab === 'audit' ? 'New audit' : 'New chat'}
          </button>
        </div>
      </nav>

      {/* ==================== BIAS AUDIT TAB ==================== */}
      {activeTab === 'audit' && (
        <>
          {!results && (
            <>
              <main className="hero fade-up delay-100">
                <div className="hero-tag">✨ AUDIT HIRING AI IN SECONDS</div>
                <h1>
                  Catch <span className="italic-highlight">bias</span> before<br/>it reaches your candidates.
                </h1>
                <p>
                  FairLens AI audits your hiring model against gender, college tier, and
                  other sensitive attributes — with fairness metrics, counterfactual tests,
                  and explainable recommendations.
                </p>
                
                {error && (
                   <div className="fade-up delay-300" style={{ color: 'var(--error-color)', marginBottom: '1.5rem', fontWeight: 500 }}>
                     {error}
                   </div>
                )}
              </main>

              <div className="dropzone-container fade-up delay-300">
                <div className="upload-card">
                  <div className="upload-card-header">
                    <span className="green-dot"></span>
                    CSV → BIAS.ENGINE V1.0
                  </div>
                  <div className="upload-zone-wrapper">
                    <div {...getRootProps()} className={`upload-zone-dashed ${isDragActive ? 'active' : ''}`}>
                      <input {...getInputProps()} />
                      <FiUploadCloud className="upload-zone-icon" />
                      <div className="upload-zone-title">
                        Drop a CSV or click to browse
                      </div>
                      <div className="upload-zone-subtext">
                        expected columns: name, gender, college_tier, skills, projects, test_score, decision
                      </div>
                    </div>
                  </div>
                  <div className="upload-card-footer">
                    <div className={`upload-status ${selectedFile ? 'ready' : ''}`}>
                      {selectedFile ? `Selected: ${selectedFile.name}` : `Awaiting dataset...`}
                    </div>
                    
                    <button 
                      className="btn btn-primary" 
                      disabled={!selectedFile || loading}
                      onClick={handleRunAudit}
                      id="btn-run-audit"
                    >
                      {loading ? (
                        <div className="loader"></div>
                      ) : (
                        <>
                          <FiPlay fill="currentColor" size={14} /> Run audit
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}

          {results && (
            <div className="app-container fade-up" style={{ marginTop: '1rem' }}>
              <Dashboard results={results} onReset={() => { setResults(null); setSelectedFile(null); }} />
            </div>
          )}
        </>
      )}

      {/* ==================== CAREER COACH TAB ==================== */}
      {activeTab === 'coach' && (
        <main className="hero fade-up delay-100" style={{ marginTop: '1rem' }}>
          <CareerCoach />
        </main>
      )}
    </>
  );
}

export default App;
