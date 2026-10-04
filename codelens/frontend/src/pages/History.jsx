import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './History.css'

const API_URL = 'http://localhost:5000/api/analyses'

function formatDate(value) {
  if (!value) return 'Date unavailable'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Date unavailable'

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function History() {
  const navigate = useNavigate()
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadAnalyses = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const response = await fetch(API_URL, {
        method: 'GET',
        credentials: 'include',
      })
      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          response.status === 401
            ? 'Please sign in to view your analysis history.'
            : data.error || 'Unable to load your analysis history.'
        )
      }

      setAnalyses(Array.isArray(data.analyses) ? data.analyses : [])
    } catch (requestError) {
      setError(requestError.message || 'Unable to connect to CodeLens.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      void loadAnalyses()
    }, 0)

    return () => window.clearTimeout(timerId)
  }, [loadAnalyses])

  const handleLogout = async () => {
    try {
      await fetch('http://localhost:5000/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      })
    } finally {
      navigate('/login', { replace: true })
    }
  }

  return (
    <main className="history-page">
      <header className="history-topbar">
        <button className="history-brand" type="button" onClick={() => navigate('/dashboard')}>
          <span className="history-logo">CL</span>
          <span>CodeLens</span>
        </button>

        <nav className="history-nav" aria-label="Main navigation">
          <button type="button" onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button type="button" onClick={() => navigate('/analyze')}>Analyse</button>
          <button className="history-nav-active" type="button" aria-current="page">History</button>
          <button type="button" onClick={() => navigate('/profile')}>Profile</button>
        </nav>

        <button className="history-logout" type="button" onClick={handleLogout}>Logout</button>
      </header>

      <section className="history-content">
        <div className="history-heading">
          <div>
            <span className="history-kicker">CODELENS WORKSPACE</span>
            <h1>Your <span>analysis history.</span></h1>
            <p>Review the code analyses saved to your account.</p>
          </div>
          <button className="history-new-button" type="button" onClick={() => navigate('/analyze')}>
            Analyse new code <span aria-hidden="true">→</span>
          </button>
        </div>

        {loading ? (
          <section className="history-state" role="status" aria-live="polite">
            <span className="history-spinner" aria-hidden="true" />
            <h2>Loading your history</h2>
            <p>Fetching your saved analyses…</p>
          </section>
        ) : error ? (
          <section className="history-state history-error" role="alert">
            <span className="history-state-mark" aria-hidden="true">!</span>
            <h2>History could not be loaded</h2>
            <p>{error}</p>
            <button type="button" onClick={loadAnalyses}>Try again</button>
          </section>
        ) : analyses.length === 0 ? (
          <section className="history-state">
            <span className="history-state-mark" aria-hidden="true">+</span>
            <h2>No analyses yet</h2>
            <p>Analyses you save will appear here, ready for you to review.</p>
            <button type="button" onClick={() => navigate('/analyze')}>Start your first analysis <span aria-hidden="true">→</span></button>
          </section>
        ) : (
          <>
            <div className="history-list-heading">
              <div>
                <span>YOUR LIBRARY</span>
                <h2>{analyses.length} {analyses.length === 1 ? 'analysis' : 'analyses'}</h2>
              </div>
              <span className="history-sort-label">Most recently updated first</span>
            </div>
            <div className="history-grid">
              {analyses.map((analysis) => {
                const source = typeof analysis.source_code === 'string' ? analysis.source_code : ''
                const result = analysis.analysis_result && typeof analysis.analysis_result === 'object'
                  ? analysis.analysis_result
                  : {}
                const resultSections = Object.keys(result)

                return (
                  <article className="history-card" key={analysis.id}>
                    <div className="history-card-top">
                      <span className="history-card-icon" aria-hidden="true">{`0${(analysis.id % 9) + 1}`}</span>
                      <span className="history-updated">UPDATED {formatDate(analysis.updated_at)}</span>
                    </div>
                    <h3>{analysis.name || 'Untitled analysis'}</h3>
                    <p className="history-created">Created {formatDate(analysis.created_at)}</p>
                    <div className="history-metadata" aria-label="Analysis metadata">
                      <span>{source.length.toLocaleString()} characters</span>
                      <span>{source ? source.split(/\r\n|\r|\n/).length : 0} lines</span>
                      <span>{resultSections.length} result sections</span>
                    </div>
                    {resultSections.length > 0 && (
                      <div className="history-tags" aria-label="Available analysis data">
                        {resultSections.slice(0, 4).map((section) => (
                          <span key={section}>{section.replaceAll('_', ' ')}</span>
                        ))}
                        {resultSections.length > 4 && <span>+{resultSections.length - 4} more</span>}
                      </div>
                    )}
                    <details className="history-source">
                      <summary>View source code</summary>
                      <pre><code>{source || 'No source code was saved.'}</code></pre>
                    </details>
                  </article>
                )
              })}
            </div>
          </>
        )}
      </section>

      <footer className="history-footer">
        <span>CodeLens</span>
        <span>Compiler-powered code understanding</span>
      </footer>
    </main>
  )
}

export default History
