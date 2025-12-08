import { useState, useEffect } from 'react'
import './App.css'

// Get API URL from environment variables or use default
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

function App() {
  const [question, setQuestion] = useState('')
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [useLocalLLM, setUseLocalLLM] = useState(false)
  const [originalQuestion, setOriginalQuestion] = useState('')
  const [cloudProvider, setCloudProvider] = useState('gemini') // 'gemini' or 'mistral'
  const [showCloudDropdown, setShowCloudDropdown] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!question.trim()) {
      setError('Please enter a question')
      return
    }

    setLoading(true)
    setError(null)
    setResponse(null)
    setOriginalQuestion(question.trim())

    try {
      const res = await fetch(`${API_URL}/LS/content/v1/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question.trim(),
          local_llm: useLocalLLM
        })
      })

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }

      const data = await res.json()
      setResponse(data)
    } catch (err) {
      setError(err.message || 'Failed to generate content. Please make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setQuestion('')
    setResponse(null)
    setError(null)
    setOriginalQuestion('')
  }

  const providerUsed = useLocalLLM ? 'local' : `cloud (${cloudProvider})`

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!e.target.closest('.provider-dropdown-container')) {
        setShowCloudDropdown(false)
      }
    }

    if (showCloudDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showCloudDropdown])

  const handleCloudProviderSelect = (provider) => {
    setCloudProvider(provider)
    setShowCloudDropdown(false)
  }

  return (
    <div className="app">
      {/* Left Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon-wrapper">
              <svg className="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span className="logo-text">Literature Surveyor</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-item active">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15.232 5.232L13.414 7.05M11.293 9.172L9.475 10.99M7.657 13.01L5.839 14.828M3 12C3 7.029 7.029 3 12 3C16.971 3 21 7.029 21 12C21 16.971 16.971 21 12 21C7.029 21 3 16.971 3 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>New Chat</span>
          </div>
          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/>
              <path d="M21 21L16.65 16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <span>Academic Search</span>
          </div>
          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 2C6.477 2 2 6.477 2 12C2 17.523 6.477 22 12 22C17.523 22 22 17.523 22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <path d="M12 2C15.314 2 18 4.686 18 8C18 11.314 15.314 14 12 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <span>Science Navigator</span>
            <svg className="nav-arrow" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 8A6 6 0 0 0 6 8C6 11.314 9 12 9 15M15 15H9M15 15V19M15 15L9 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Subscription</span>
          </div>
          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 19.5C4 18.395 4.895 17.5 6 17.5H18C19.105 17.5 20 18.395 20 19.5V20.5C20 21.605 19.105 22.5 18 22.5H6C4.895 22.5 4 21.605 4 20.5V19.5Z" stroke="currentColor" strokeWidth="2"/>
              <path d="M4 19.5V9.5C4 8.395 4.895 7.5 6 7.5H8" stroke="currentColor" strokeWidth="2"/>
              <path d="M20 19.5V9.5C20 8.395 19.105 7.5 18 7.5H16" stroke="currentColor" strokeWidth="2"/>
              <path d="M8 7.5V5.5C8 4.395 8.895 3.5 10 3.5H14C15.105 3.5 16 4.395 16 5.5V7.5" stroke="currentColor" strokeWidth="2"/>
            </svg>
            <span>Library</span>
          </div>
          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 14L9 11H7C5.895 11 5 10.105 5 9V7C5 5.895 5.895 5 7 5H9L12 2L15 5H17C18.105 5 19 5.895 19 7V9C19 10.105 18.105 11 17 11H15L12 14Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Scholars</span>
          </div>
          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 21H21M4 21V7L12 3L20 7V21M4 21H20M9 9V21M15 9V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Knowledge Base</span>
          </div>
          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M14.7 6.3C15.1 5.9 15.1 5.3 14.7 4.9L13.1 3.3C12.7 2.9 12.1 2.9 11.7 3.3L10.3 4.7L13.3 7.7L14.7 6.3ZM3 17.2V21H6.8L17.8 10L14.8 7L3 17.2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Practice</span>
            <svg className="nav-arrow" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 3V5M15 3V5M9 19V21M15 19V21M5 9H3M5 15H3M21 9H19M21 15H19M7 9H17C18.105 9 19 9.895 19 11V13C19 14.105 18.105 15 17 15H7C5.895 15 5 14.105 5 13V11C5 9.895 5.895 9 7 9Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <span>Uni-Lab</span>
          </div>
          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 3V21H21M7 16L12 11L16 15L21 10M21 10H16M21 10V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Computation</span>
            <svg className="nav-arrow" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 6V12L16 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <span>History</span>
            <svg className="nav-menu" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 12H21M3 6H21M3 18H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="language-selector">
            <svg className="language-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="M2 12H22M12 2C14.501 5.738 16 9.402 16 12C16 14.598 14.501 18.262 12 22C9.499 18.262 8 14.598 8 12C8 9.402 9.499 5.738 12 2Z" stroke="currentColor" strokeWidth="2"/>
            </svg>
            <span>English</span>
            <svg className="language-arrow" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M6 9L12 15L18 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <button className="login-button">Log in</button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Header Section */}
        <div className="content-header">
          <h1 className="main-title">Literature Surveyor – AI Research Assistant</h1>
          <p className="main-subtitle">Ask any question and get AI-powered insights for your research</p>
        </div>

        {/* Form Section */}
        <form onSubmit={handleSubmit} className="main-form">
          <div className="form-group">
            <label htmlFor="question-input" className="form-label">Your Question</label>
            <textarea
              id="question-input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Enter your research question here..."
              className="question-textarea"
              rows="4"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label className="form-label">LLM Provider</label>
            <div className="provider-toggle">
              <div className="provider-dropdown-container">
                <button
                  type="button"
                  className={`provider-option ${!useLocalLLM ? 'active' : ''}`}
                  onClick={() => {
                    setUseLocalLLM(false)
                    setShowCloudDropdown(!showCloudDropdown)
                  }}
                  disabled={loading}
                >
                  Cloud ({cloudProvider})
                  <svg className="dropdown-arrow" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M6 9L12 15L18 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
                {showCloudDropdown && !useLocalLLM && (
                  <div className="provider-dropdown">
                    <button
                      type="button"
                      className={`dropdown-option ${cloudProvider === 'gemini' ? 'selected' : ''}`}
                      onClick={() => handleCloudProviderSelect('gemini')}
                    >
                      Gemini
                    </button>
                    <button
                      type="button"
                      className={`dropdown-option ${cloudProvider === 'mistral' ? 'selected' : ''}`}
                      onClick={() => handleCloudProviderSelect('mistral')}
                    >
                      Mistral
                    </button>
                  </div>
                )}
              </div>
              <button
                type="button"
                className={`provider-option ${useLocalLLM ? 'active' : ''}`}
                onClick={() => {
                  setUseLocalLLM(true)
                  setShowCloudDropdown(false)
                }}
                disabled={loading}
              >
                Local (Ollama)
              </button>
            </div>
          </div>

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !question.trim()}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Generating...
                </>
              ) : (
                'Ask'
              )}
            </button>
            <button
              type="button"
              onClick={handleClear}
              className="btn btn-secondary"
              disabled={loading}
            >
              Clear
            </button>
          </div>
        </form>

        {/* Loading State */}
        {loading && (
          <div className="loading-state">
            <div className="loading-spinner-large"></div>
            <p className="loading-text">Generating your answer...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="alert alert-error">
            <svg className="alert-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 8V12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="12" cy="16" r="1" fill="currentColor"/>
            </svg>
            <div className="alert-content">
              <p className="alert-title">Error</p>
              <p className="alert-message">{error}</p>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!response && !error && !loading && (
          <div className="empty-state">
            <svg className="empty-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <p className="empty-text">Your answer will appear here. Ask a question to get started!</p>
          </div>
        )}

        {/* Answer Display */}
        {response && !loading && (
          <div className="answer-panel">
            <div className="answer-header">
              <h2 className="answer-title">Answer</h2>
            </div>
            <div className="answer-subheader">
              <span className="provider-badge">
                Provider: {providerUsed}
              </span>
            </div>
            <div className="answer-body">
              <div className="answer-content">{response.data}</div>
            </div>
            <div className="answer-footer">
              <div className="answer-meta">
                <p className="original-question-label">Original Question:</p>
                <p className="original-question-text">{originalQuestion}</p>
              </div>
              <div className="coming-soon">
                <p className="coming-soon-text">Planned: sources & semantic context (coming soon)</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
