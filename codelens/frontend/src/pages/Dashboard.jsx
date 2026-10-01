import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Dashboard.css'

function Dashboard() {
  const navigate = useNavigate()

  const [user, setUser] = useState(null)
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await fetch(
          'http://localhost:5000/api/auth/me',
          {
            method: 'GET',
            credentials: 'include',
          }
        )

        if (!response.ok) {
          navigate('/login', { replace: true })
          return
        }

        const data = await response.json()

        setUser(data.user)

        const analysesResponse = await fetch(
          'http://localhost:5000/api/analyses',
          {
            method: 'GET',
            credentials: 'include',
          }
        )

        if (analysesResponse.ok) {
          const analysesData = await analysesResponse.json()

          setAnalyses(
            analysesData.analyses || []
          )
        }
      } catch {
        navigate('/login', { replace: true })
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [navigate])

  const handleLogout = async () => {
    try {
      await fetch(
        'http://localhost:5000/api/auth/logout',
        {
          method: 'POST',
          credentials: 'include',
        }
      )
    } finally {
      navigate('/login', { replace: true })
    }
  }

  if (loading) {
    return (
      <main className="dashboard-loading">
        <div className="dashboard-loading-mark">
          CL
        </div>

        <p>Loading your workspace...</p>
      </main>
    )
  }

  return (
    <main className="dashboard-page">
      <header className="dashboard-topbar">
        <button
          className="dashboard-brand"
          type="button"
          onClick={() => navigate('/dashboard')}
        >
          <div className="dashboard-logo">
            CL
          </div>

          <span>CodeLens</span>
        </button>

        <nav className="dashboard-nav">
          <button
            className="dashboard-nav-item dashboard-nav-active"
            type="button"
            onClick={() => navigate('/dashboard')}
          >
            Dashboard
          </button>

          <button
            className="dashboard-nav-item"
            type="button"
            onClick={() => navigate('/analyze')}
          >
            Analyse
          </button>

          <button
            className="dashboard-nav-item"
            type="button"
            onClick={() => navigate('/history')}
          >
            History
          </button>

          <button
            className="dashboard-nav-item"
            type="button"
            onClick={() => navigate('/profile')}
          >
            Profile
          </button>
        </nav>

        <div className="dashboard-user-area">
          <div className="dashboard-user">
            <div className="dashboard-avatar">
              {user?.name
                ?.charAt(0)
                ?.toUpperCase()}
            </div>

            <span>{user?.name}</span>
          </div>

          <button
            className="dashboard-logout"
            type="button"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </header>

      <section className="dashboard-content">
        <div className="dashboard-heading">
          <div>
            <span className="dashboard-kicker">
              CODELENS WORKSPACE
            </span>

            <h1>
              Welcome back,{' '}
              <span>{user?.name}</span>
            </h1>

            <p>
              Understand your code before you
              change it.
            </p>
          </div>

          <button
            className="dashboard-primary-action"
            type="button"
            onClick={() => navigate('/analyze')}
          >
            <span>Analyse new code</span>

            <span className="dashboard-action-arrow">
              →
            </span>
          </button>
        </div>

        <div className="dashboard-stats">
          <div className="dashboard-stat-card">
            <span className="dashboard-stat-label">
              TOTAL ANALYSES
            </span>

            <strong>{analyses.length}</strong>

            <p>
              Programs analysed
            </p>
          </div>

          <div className="dashboard-stat-card">
            <span className="dashboard-stat-label">
              CODE STRUCTURE
            </span>

            <strong>AST</strong>

            <p>
              Syntax representation
            </p>
          </div>

          <div className="dashboard-stat-card">
            <span className="dashboard-stat-label">
              CONTROL FLOW
            </span>

            <strong>CFG</strong>

            <p>
              Program execution paths
            </p>
          </div>

          <div className="dashboard-stat-card dashboard-stat-highlight">
            <span className="dashboard-stat-label">
              CHANGE IMPACT
            </span>

            <strong>→</strong>

            <p>
              Trace affected code
            </p>
          </div>
        </div>

        <div className="dashboard-main-grid">
          <section className="dashboard-panel dashboard-quick-panel">
            <div className="dashboard-panel-header">
              <div>
                <span>
                  GET STARTED
                </span>

                <h2>
                  Analyse a program
                </h2>
              </div>

              <span className="dashboard-panel-index">
                01
              </span>
            </div>

            <p>
              Paste your C source code and let
              CodeLens break it down through the
              compiler pipeline.
            </p>

            <div className="dashboard-pipeline">
              <div className="dashboard-pipeline-item">
                <span>01</span>
                <strong>LEX</strong>
                <small>Tokens</small>
              </div>

              <div className="dashboard-pipeline-line" />

              <div className="dashboard-pipeline-item">
                <span>02</span>
                <strong>AST</strong>
                <small>Structure</small>
              </div>

              <div className="dashboard-pipeline-line" />

              <div className="dashboard-pipeline-item">
                <span>03</span>
                <strong>TAC</strong>
                <small>Instructions</small>
              </div>

              <div className="dashboard-pipeline-line" />

              <div className="dashboard-pipeline-item">
                <span>04</span>
                <strong>CFG</strong>
                <small>Flow</small>
              </div>

              <div className="dashboard-pipeline-line" />

              <div className="dashboard-pipeline-item dashboard-pipeline-highlight">
                <span>05</span>
                <strong>IMPACT</strong>
                <small>Dependencies</small>
              </div>
            </div>

            <button
              className="dashboard-panel-button"
              type="button"
              onClick={() => navigate('/analyze')}
            >
              Start analysis
              <span>→</span>
            </button>
          </section>

          <section className="dashboard-panel dashboard-recent-panel">
            <div className="dashboard-panel-header">
              <div>
                <span>
                  RECENT ACTIVITY
                </span>

                <h2>
                  Your analyses
                </h2>
              </div>

              <span className="dashboard-panel-index">
                02
              </span>
            </div>

            {analyses.length === 0 ? (
              <div className="dashboard-empty-state">
                <div className="dashboard-empty-icon">
                  +
                </div>

                <h3>
                  No analyses yet
                </h3>

                <p>
                  Your saved code analyses will
                  appear here.
                </p>

                <button
                  type="button"
                  onClick={() => navigate('/analyze')}
                >
                  Analyse your first program →
                </button>
              </div>
            ) : (
              <div className="dashboard-recent-list">
                {analyses
                  .slice(0, 4)
                  .map((analysis) => (
                    <div
                      className="dashboard-recent-item"
                      key={analysis.id}
                    >
                      <div>
                        <strong>
                          {analysis.name}
                        </strong>

                        <span>
                          {new Date(
                            analysis.updated_at
                          ).toLocaleString()}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={() =>
                          navigate('/history')
                        }
                      >
                        View →
                      </button>
                    </div>
                  ))}
              </div>
            )}
          </section>
        </div>

        <section className="dashboard-explanation">
          <div className="dashboard-explanation-number">
            03
          </div>

          <div className="dashboard-explanation-content">
            <span>
              WHAT CODELENS DOES
            </span>

            <h2>
              From source code to
              <br />
              <em>understanding.</em>
            </h2>

            <p>
              CodeLens uses compiler-based analysis
              to reveal how your program is structured,
              how execution moves through it, how data
              flows between statements, and what parts
              may be affected when your code changes.
            </p>
          </div>

          <div className="dashboard-explanation-tags">
            <span>AST</span>
            <span>SYMBOL TABLE</span>
            <span>TAC</span>
            <span>BASIC BLOCKS</span>
            <span>CFG</span>
            <span>DATA FLOW</span>
            <span>DEF-USE</span>
            <span>IMPACT</span>
          </div>
        </section>
      </section>

      <footer className="dashboard-footer">
        <span>CodeLens</span>

        <span>
          Compiler-powered code understanding
        </span>
      </footer>
    </main>
  )
}

export default Dashboard