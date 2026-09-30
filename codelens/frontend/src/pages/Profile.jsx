import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Profile.css'

const USER_URL = 'http://localhost:5000/api/auth/me'
const ANALYSES_URL = 'http://localhost:5000/api/analyses'

function Profile() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [analysisCount, setAnalysisCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [loggingOut, setLoggingOut] = useState(false)

  const loadProfile = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const [userResponse, analysesResponse] = await Promise.all([
        fetch(USER_URL, { method: 'GET', credentials: 'include' }),
        fetch(ANALYSES_URL, { method: 'GET', credentials: 'include' }),
      ])

      if (userResponse.status === 401 || analysesResponse.status === 401) {
        navigate('/login', { replace: true })
        return
      }

      const [userData, analysesData] = await Promise.all([
        userResponse.json(),
        analysesResponse.json(),
      ])

      if (!userResponse.ok) {
        throw new Error(userData.error || 'Unable to load your profile.')
      }
      if (!analysesResponse.ok) {
        throw new Error(analysesData.error || 'Unable to load your analysis count.')
      }

      setUser(userData.user)
      setAnalysisCount(Array.isArray(analysesData.analyses) ? analysesData.analyses.length : 0)
    } catch (requestError) {
      setError(requestError.message || 'Unable to connect to CodeLens.')
    } finally {
      setLoading(false)
    }
  }, [navigate])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  const handleLogout = async () => {
    setLoggingOut(true)
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
    <main className="profile-page">
      <header className="profile-topbar">
        <button className="profile-brand" type="button" onClick={() => navigate('/dashboard')}>
          <span className="profile-logo">CL</span>
          <span>CodeLens</span>
        </button>

        <nav className="profile-nav" aria-label="Main navigation">
          <button type="button" onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button type="button" onClick={() => navigate('/analyze')}>Analyse</button>
          <button type="button" onClick={() => navigate('/history')}>History</button>
          <button className="profile-nav-active" type="button" aria-current="page">Profile</button>
        </nav>

        <button className="profile-logout" type="button" onClick={handleLogout} disabled={loggingOut}>
          {loggingOut ? 'Logging out…' : 'Logout'}
        </button>
      </header>

      <section className="profile-content">
        <div className="profile-heading">
          <span className="profile-kicker">CODELENS WORKSPACE</span>
          <h1>Your <span>profile.</span></h1>
          <p>Account details and your analysis activity.</p>
        </div>

        {loading ? (
          <section className="profile-state" role="status" aria-live="polite">
            <span className="profile-spinner" aria-hidden="true" />
            <h2>Loading your profile</h2>
            <p>Retrieving your account details…</p>
          </section>
        ) : error ? (
          <section className="profile-state profile-error" role="alert">
            <span className="profile-state-mark" aria-hidden="true">!</span>
            <h2>Profile could not be loaded</h2>
            <p>{error}</p>
            <button type="button" onClick={loadProfile}>Try again</button>
          </section>
        ) : user ? (
          <div className="profile-grid">
            <section className="profile-card profile-account-card">
              <div className="profile-card-eyebrow">ACCOUNT DETAILS</div>
              <div className="profile-identity">
                <div className="profile-avatar" aria-hidden="true">
                  {user.name?.charAt(0)?.toUpperCase() || '?'}
                </div>
                <div>
                  <h2>{user.name}</h2>
                  <p>{user.email}</p>
                </div>
              </div>
              <div className="profile-detail-row">
                <span>Full name</span>
                <strong>{user.name}</strong>
              </div>
              <div className="profile-detail-row">
                <span>Email address</span>
                <strong>{user.email}</strong>
              </div>
            </section>

            <section className="profile-card profile-activity-card">
              <div className="profile-card-eyebrow">YOUR ACTIVITY</div>
              <div className="profile-count">{analysisCount}</div>
              <h2>{analysisCount === 1 ? 'Saved analysis' : 'Saved analyses'}</h2>
              <p>Your completed code analyses, available in your history.</p>
              <button type="button" onClick={() => navigate('/history')}>View history <span aria-hidden="true">→</span></button>
            </section>

            <section className="profile-card profile-session-card">
              <div>
                <div className="profile-card-eyebrow">SESSION</div>
                <h2>Signed in to CodeLens</h2>
                <p>Sign out when you are finished with this workspace.</p>
              </div>
              <button type="button" onClick={handleLogout} disabled={loggingOut}>
                {loggingOut ? 'Logging out…' : 'Logout'}
              </button>
            </section>
          </div>
        ) : null}
      </section>

      <footer className="profile-footer">
        <span>CodeLens</span>
        <span>Compiler-powered code understanding</span>
      </footer>
    </main>
  )
}

export default Profile
