import { useState, useEffect, useMemo } from 'react'
import './App.css'

import 'katex/dist/katex.min.css'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import markedKatex from 'marked-katex-extension'


marked.setOptions({
  breaks: true,
  gfm: true,
  headerIds: false,
  mangle: false
})
marked.use(markedKatex({ throwOnError: false }))

const normalizeMathDelimiters = (text) => {
  if (!text) return ''
  return text
    .replace(/\\\\\[/gs, '\\[')
    .replace(/\\\\\)/gs, '\\)')
    .replace(/\\\\\(/gs, '\\(')
    .replace(/\\\\\]/gs, '\\]')
    .replace(/\\\[(.+?)\\\]/gs, (_, expr) => `\n$$\n${expr}\n$$\n`)
    .replace(/\\\((.+?)\\\)/gs, (_, expr) => `$${expr}$`)
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [question, setQuestion] = useState('')
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [useLocalLLM, setUseLocalLLM] = useState(false)
  const [originalQuestion, setOriginalQuestion] = useState('')
  const [cloudProvider, setCloudProvider] = useState('gemini') // 'gemini' or 'mistral'
  const [showCloudDropdown, setShowCloudDropdown] = useState(false)


  const sanitizedContent = useMemo(() => {
    const content = response?.data || response?.answer
    if (!content) return ''

    const rawText = Array.isArray(content)
      ? content.join('\n\n')
      : typeof content === 'string'
        ? content
        : JSON.stringify(content, null, 2)

    const normalizedText = normalizeMathDelimiters(rawText)
    const html = marked.parse(normalizedText)
    
    return DOMPurify.sanitize(html, {
      ADD_TAGS: ['math', 'semantics', 'mrow', 'mi', 'mn', 'mo', 'msup', 'mfrac', 'msqrt', 'mtext', 'annotation', 'mtable', 'mtr', 'mtd', 'mlabeledtr', 'mfenced', 'mover', 'munder', 'munderover'],
      ADD_ATTR: ['mathvariant', 'mathsize', 'mathcolor', 'mathbackground', 'encoding']
    })
  }, [response])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!question.trim()) {
      setError('Please enter a question')
      return
    }
    setLoading(true); setError(null); setResponse(null); setOriginalQuestion(question.trim())

    try {
      const res = await fetch(`${API_URL}/LS/content/v1/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question.trim(),
          local_llm: useLocalLLM,
          provider: useLocalLLM ? undefined : cloudProvider
        })
      })
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)
      const data = await res.json()
      setResponse(data)
    } catch (err) {
      setError(err.message || 'Failed to generate content.')
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => { setQuestion(''); setResponse(null); setError(null); setOriginalQuestion('') }
  const providerUsed = useLocalLLM ? 'local' : `cloud (${cloudProvider})`

  // Close dropdown logic
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!e.target.closest('.provider-dropdown-container')) setShowCloudDropdown(false)
    }
    if (showCloudDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showCloudDropdown])

  const handleCloudProviderSelect = (provider) => { setCloudProvider(provider); setShowCloudDropdown(false) }

  return (
    <div className="app">
      {/* --- SIDEBAR START --- */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon-wrapper">
              <svg className="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <span className="logo-text">Literature Surveyor</span>
          </div>
        </div>

        <div className="sidebar-action-area">
          <div className="new-chat-btn" onClick={handleClear}>
            <svg className="new-chat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            <span>New Chat</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <circle cx="11" cy="11" r="8" strokeWidth="2"/>
              <path strokeLinecap="round" strokeWidth="2" d="M21 21l-4.35-4.35"/>
            </svg>
            <span>Academic Search</span>
          </div>

          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Science Navigator</span>
            <svg className="nav-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>

          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
            <span>Practice</span>
            <svg className="nav-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>

          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
            <span>Uni-Lab</span>
          </div>

          <div className="nav-item">
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <span>Computation</span>
            <svg className="nav-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>

          <div className="nav-item">
             <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
             </svg>
            <span>History</span>
            <svg className="nav-menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" style={{width:'16px', height:'16px', marginLeft:'auto'}}>
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="language-selector">
            <svg className="language-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <circle cx="12" cy="12" r="10" strokeWidth="2"/>
              <path strokeLinecap="round" strokeWidth="2" d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
            </svg>
            <span>English (EN)</span>
            <svg className="language-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          <button className="login-button">
             Log in
          </button>
        </div>
      </aside>
      {/* --- SIDEBAR END --- */}

      {/* Main Content */}
      <main className="main-content">
        <div className="content-header">
          <h1 className="main-title">Literature Surveyor</h1>
          <p className="main-subtitle">Ask any question and get AI-powered insights</p>
        </div>

        <form onSubmit={handleSubmit} className="main-form">
          <div className="form-group">
            <label className="form-label">Your Research Domain</label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Enter your research domain here (e.g. AI in Agriculture)..."
              className="question-textarea"
              rows="3"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Model Provider</label>
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
                  <svg className="dropdown-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/></svg>
                </button>
                {showCloudDropdown && !useLocalLLM && (
                  <div className="provider-dropdown">
                    <button type="button" className={`dropdown-option ${cloudProvider === 'gemini' ? 'selected' : ''}`} onClick={() => handleCloudProviderSelect('gemini')}>Gemini</button>
                    <button type="button" className={`dropdown-option ${cloudProvider === 'mistral' ? 'selected' : ''}`} onClick={() => handleCloudProviderSelect('mistral')}>Mistral</button>
                  </div>
                )}
              </div>
              <button
                type="button"
                className={`provider-option ${useLocalLLM ? 'active' : ''}`}
                onClick={() => { setUseLocalLLM(true); setShowCloudDropdown(false) }}
                disabled={loading}
              >
                Local (Ollama)
              </button>
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading || !question.trim()}>
              {loading ? <><span className="spinner"></span> Generating...</> : 'Generate Report'}
            </button>
            <button type="button" onClick={handleClear} className="btn btn-secondary" disabled={loading}>Clear</button>
          </div>
        </form>

        {loading && (
          <div className="loading-state">
            <div className="loading-spinner-large"></div>
            <p className="loading-text">Analyzing literature...</p>
          </div>
        )}
        {error && (
          <div className="alert alert-error">
            <div className="alert-content">
              <p className="alert-title">Error</p>
              <p className="alert-message">{error}</p>
            </div>
          </div>
        )}
        {!response && !error && !loading && (
          <div className="empty-state">
            <svg className="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <p className="empty-text">Your answer will appear here. Ask a question to get started!</p>
          </div>
        )}
        {response && !loading && (
          <div className="answer-panel">
            <div className="answer-header">
              <h2 className="answer-title">Research Report</h2>
            </div>
            <div className="answer-subheader">
              <span className="provider-badge">Provider: {providerUsed}</span>
            </div>
            <div className="answer-body">
              <div className="answer-content content-text" dangerouslySetInnerHTML={{ __html: sanitizedContent }} />
            </div>
            <div className="answer-footer">
              <div className="answer-meta">
                <p className="original-question-label">Original Question:</p>
                <p className="original-question-text">{originalQuestion}</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App