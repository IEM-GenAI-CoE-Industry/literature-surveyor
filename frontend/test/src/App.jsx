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
    .replace(/\\\\\[(.+?)\\\\\]/gs, (_, expr) => `\n$$\n${expr}\n$$\n`)
    .replace(/\\\\\((.+?)\\\\\)/gs, (_, expr) => `$${expr}$`)
}

function App() {
  // API URL (from Vite env). Ensure your .env contains VITE_API_URL="http://localhost:8001" or the deployed backend URL.
  // Fallback to localhost:8001 when the env var is missing.
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'
  const [question, setQuestion] = useState('')
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [useLocalLLM, setUseLocalLLM] = useState(false)
  const [originalQuestion, setOriginalQuestion] = useState('')
  const [cloudProvider, setCloudProvider] = useState('gemini') // 'gemini' or 'mistral'
  const [showCloudDropdown, setShowCloudDropdown] = useState(false)
  const [history, setHistory] = useState([])


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
    e && e.preventDefault()
    const query = (typeof e === 'string') ? e : question
    if (!query || !query.trim()) {
      setError('Please enter a question')
      return
    }
    setLoading(true); setError(null); setResponse(null); setOriginalQuestion(query.trim())

    try {
      const res = await fetch(`${API_URL}/LS/content/v1/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: query.trim(),
          local_llm: useLocalLLM,
          provider: useLocalLLM ? undefined : cloudProvider
        })
      })
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)
      const data = await res.json()
      setResponse(data)

      // Update history: store { query, date, summary_preview }
      try {
        const sd = data?.structured_data || null
        const preview = sd?.overview || (data?.answer ? data.answer.slice(0, 160) : '')
        const entry = { query: query.trim(), date: new Date().toISOString(), summary_preview: preview }
        setHistory(prev => {
          // dedupe by query
          const filtered = prev.filter(h => h.query !== entry.query)
          const updated = [entry, ...filtered].slice(0, 50)
          localStorage.setItem('ls_history', JSON.stringify(updated))
          return updated
        })
      } catch (err) {
        console.warn('Failed to update history', err)
      }
    } catch (err) {
      setError(err.message || 'Failed to generate content.')
    } finally {
      setLoading(false)
    }
  }

  // Run a saved query (from history). Accepts a raw query string.
  const runSavedQuery = async (savedQuery) => {
    setQuestion(savedQuery)
    await handleSubmit(savedQuery)
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

  // Load history from localStorage on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem('ls_history')
      if (raw) setHistory(JSON.parse(raw))
    } catch (err) {
      console.warn('Failed to load history', err)
    }
  }, [])

  // Clear history (UI + localStorage)
  const clearHistory = () => {
    try {
      localStorage.removeItem('ls_history')
    } catch (err) {
      console.warn('Failed to clear history', err)
    }
    setHistory([])
  }

  // Convert overview text into an array of concise bullet points
  const getOverviewPoints = (overview) => {
    if (!overview) return []
    // Prefer explicit newlines; otherwise split into sentences
    const byLines = overview.split(/\n+/).map(s => s.trim()).filter(Boolean)
    // Return only the first explicit line as the single overview point
    if (byLines.length >= 1) return [byLines[0]]

    // fallback: split into sentences and return only the first sentence
    const sentences = overview
      .split(/\.\s+/)
      .map(s => s.trim())
      .filter(Boolean)
    if (sentences.length >= 1) return [sentences[0]]

    // last resort: the whole overview as a single point
    return [overview.trim()]
  }

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
            <span>+ Academic Search</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-item">
             <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
             </svg>
            <span>History</span>
            <svg className="nav-menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" style={{width:'16px', height:'16px', marginLeft:'auto'}}>
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </div>

          <div className="history-actions">
            <button type="button" className="clear-history-btn" onClick={clearHistory} disabled={history.length===0}>Clear History</button>
          </div>

          {/* History list (clickable) */}
          <div className="history-list">
            {history.length ? history.map((h, idx) => (
              <div key={`hist-${idx}`} className="history-item" onClick={() => runSavedQuery(h.query)}>
                <div className="history-query">{h.query}</div>
                <div className="history-meta">
                  <span className="history-date">{new Date(h.date).toLocaleString()}</span>
                  <span className="history-preview">{h.summary_preview ? `${h.summary_preview.slice(0,120)}${h.summary_preview.length>120? '...':''}` : ''}</span>
                </div>
              </div>
            )) : (
              <div className="history-empty">No history yet</div>
            )}
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
        {response && !loading && (() => {
          const sd = response.structured_data || null
          if (sd) {
            const papers = sd.papers || []
            const ideas = sd.ideas || []
            const venuesConfs = (sd.venues && sd.venues.conferences) || []
            const venuesJourn = (sd.venues && sd.venues.journals) || []

            return (
              <div className="dashboard">
                <div className="dashboard-grid">
                  <div className="card venues-card">
                    <h4 className="card-title">Discovered Venues</h4>
                    <div className="venues-columns">
                      <div>
                        <h5>Conferences</h5>
                        {venuesConfs.length ? (
                          <ul>
                            {venuesConfs.map((v, i) => <li key={`conf-${i}`}>{v}</li>)}
                          </ul>
                        ) : <p>None</p>}
                      </div>
                      <div>
                        <h5>Journals</h5>
                        {venuesJourn.length ? (
                          <ul>
                            {venuesJourn.map((v, i) => <li key={`jour-${i}`}>{v}</li>)}
                          </ul>
                        ) : <p>None</p>}
                      </div>
                    </div>
                  </div>

                  <div className="card ideas-card">
                    <h4 className="card-title">Research Ideas</h4>
                    <ul>
                      {ideas.slice(0,5).map((it, i) => <li key={`idea-${i}`}>{it}</li>)}
                    </ul>
                  </div>

                  <div className="card literature-card">
                    <h4 className="card-title">Literature</h4>
                    <div className="papers-grid">
                      {papers.slice(0,5).map((p, i) => (
                        <div className="paper-card" key={`paper-${i}`}>
                          <div className="paper-header">
                            <h5 className="paper-title">{p.title}</h5>
                            <div className="paper-badges">
                              {p.cited_by_count !== undefined && (
                                <span className="citation-badge">⭐ {p.cited_by_count} Citations</span>
                              )}
                            </div>
                          </div>
                          <p className="paper-summary">{p.summary}</p>
                          <div className="paper-meta">
                            <span className="paper-source">{p.source} {p.year ? `| ${p.year}` : ''}</span>
                            <a className="scholar-link" href={`https://scholar.google.com/scholar?q=${encodeURIComponent(p.title)}`} target="_blank" rel="noopener noreferrer">Open in Scholar</a>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Overview moved to bottom full-width */}
                <div className="overview-card card">
                  <h3 className="card-title">{sd.domain}</h3>
                  {(() => {
                    const points = getOverviewPoints(sd.overview)
                    if (!points || points.length === 0) {
                      return <p className="card-overview">{sd.overview}</p>
                    }
                    return (
                      <ul className="overview-list">
                        {points.map((pt, idx) => <li key={`ov-${idx}`}>{pt}</li>)}
                      </ul>
                    )
                  })()}
                </div>

                <div className="answer-footer">
                  <div className="answer-meta">
                    <p className="original-question-label">Original Question:</p>
                    <p className="original-question-text">{originalQuestion}</p>
                  </div>
                </div>
              </div>
            )
          }

          // fallback: render legacy text block
          return (
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
          )
        })()}
      </main>
    </div>
  )
}

export default App