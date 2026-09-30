import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Login.css'

function Login() {
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (event) => {
    event.preventDefault()

    setLoading(true)
    setError('')

    try {
      const response = await fetch(
        'http://localhost:5000/api/auth/login',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            email,
            password,
          }),
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.error || 'Login failed.'
        )
      }

      navigate('/dashboard')
    } catch (err) {
      setError(
        err.message ||
          'Something went wrong. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-page">

      <div className="login-topbar">

        <button
          className="login-brand"
          type="button"
          onClick={() => navigate('/login')}
        >
          <div className="login-logo">
            CL
          </div>

          <span>CodeLens</span>
        </button>

        <div className="login-topbar-text">
          Code Understanding & Impact Analysis
        </div>

      </div>

      <section className="login-content">

        <div className="login-intro">

          <span className="login-kicker">
            WELCOME BACK
          </span>

          <h1>
            Your code.
            <br />
            <span>Understood.</span>
          </h1>

          <p>
            Continue exploring your programs through
            their structure, control flow, data flow,
            and dependencies.
          </p>

          <div className="login-flow">

            <div className="login-flow-item">
              <span>01</span>
              <strong>READ</strong>
              <small>Understand</small>
            </div>

            <div className="login-flow-line"></div>

            <div className="login-flow-item">
              <span>02</span>
              <strong>TRACE</strong>
              <small>Analyze</small>
            </div>

            <div className="login-flow-line"></div>

            <div className="login-flow-item login-flow-highlight">
              <span>03</span>
              <strong>IMPACT</strong>
              <small>Compare</small>
            </div>

          </div>

        </div>

        <div className="login-card">

          <div className="login-card-header">

            <span>
              SIGN IN
            </span>

            <h2>
              Welcome back
            </h2>

            <p>
              Log in to continue to your workspace.
            </p>

          </div>

          <form
            className="login-form"
            onSubmit={handleLogin}
          >

            <div className="login-field">

              <label htmlFor="email">
                Email
              </label>

              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="you@example.com"
                autoComplete="email"
                required
              />

            </div>

            <div className="login-field">

              <div className="login-label-row">

                <label htmlFor="password">
                  Password
                </label>

                <button
                  type="button"
                  className="login-forgot"
                >
                  Forgot password?
                </button>

              </div>

              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />

            </div>

            {error && (
              <div className="login-message">
                {error}
              </div>
            )}

            <button
              className="login-submit"
              type="submit"
              disabled={loading}
            >

              <span>
                {loading
                  ? 'Signing in...'
                  : 'Log in'}
              </span>

              {!loading && (
                <span className="login-arrow">
                  →
                </span>
              )}

            </button>

          </form>

          <div className="login-register">

            <span>
              Don't have an account?
            </span>

            <button
              type="button"
              onClick={() =>
                navigate('/register')
              }
            >
              Create account
            </button>

          </div>

        </div>

      </section>

      <footer className="login-footer">

        <span>
          CodeLens
        </span>

        <span>
          Compiler-powered code understanding
        </span>

      </footer>

    </main>
  )
}

export default Login