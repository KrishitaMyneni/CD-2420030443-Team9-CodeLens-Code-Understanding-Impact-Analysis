import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Register.css'

function Register() {
  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleRegister = async (event) => {
    event.preventDefault()

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const response = await fetch(
        'http://localhost:5000/api/auth/register',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            name,
            email,
            password,
          }),
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.error || 'Registration failed.'
        )
      }

      setSuccess(
        'Account created successfully. Redirecting to login...'
      )

      setName('')
      setEmail('')
      setPassword('')

      setTimeout(() => {
        navigate('/login')
      }, 900)
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
    <main className="register-page">

      <div className="register-topbar">

        <button
          className="register-brand"
          type="button"
          onClick={() => navigate('/login')}
        >
          <div className="register-logo">
            CL
          </div>

          <span>CodeLens</span>
        </button>

        <div className="register-topbar-text">
          Code Understanding & Impact Analysis
        </div>

      </div>

      <section className="register-content">

        <div className="register-intro">

          <span className="register-kicker">
            CODE ANALYSIS, EXPLAINED
          </span>

          <h1>
            Understand your code
            <br />
            <span>before you change it.</span>
          </h1>

          <p>
            Explore your program through its
            syntax tree, control flow, data flow,
            and dependencies — all in one place.
          </p>

          <div className="compiler-flow">

            <div className="flow-item">
              <span>01</span>
              <strong>AST</strong>
              <small>Structure</small>
            </div>

            <div className="flow-line"></div>

            <div className="flow-item">
              <span>02</span>
              <strong>TAC</strong>
              <small>Instructions</small>
            </div>

            <div className="flow-line"></div>

            <div className="flow-item">
              <span>03</span>
              <strong>CFG</strong>
              <small>Control Flow</small>
            </div>

            <div className="flow-line"></div>

            <div className="flow-item flow-highlight">
              <span>04</span>
              <strong>IMPACT</strong>
              <small>Dependencies</small>
            </div>

          </div>

        </div>

        <div className="register-card">

          <div className="register-card-header">

            <span>
              GET STARTED
            </span>

            <h2>
              Create your account
            </h2>

            <p>
              Set up your CodeLens workspace.
            </p>

          </div>

          <form
            className="register-form"
            onSubmit={handleRegister}
          >

            <div className="register-field">

              <label htmlFor="name">
                Name
              </label>

              <input
                id="name"
                type="text"
                value={name}
                onChange={(event) =>
                  setName(event.target.value)
                }
                placeholder="Your name"
                autoComplete="name"
                required
              />

            </div>

            <div className="register-field">

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

            <div className="register-field">

              <div className="register-label-row">

                <label htmlFor="password">
                  Password
                </label>

                <span>
                  Minimum 6 characters
                </span>

              </div>

              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Create a password"
                autoComplete="new-password"
                minLength={6}
                required
              />

            </div>

            {error && (
              <div className="register-message register-error">
                {error}
              </div>
            )}

            {success && (
              <div className="register-message register-success">
                {success}
              </div>
            )}

            <button
              className="register-submit"
              type="submit"
              disabled={loading}
            >

              <span>
                {loading
                  ? 'Creating account...'
                  : 'Create account'}
              </span>

              {!loading && (
                <span className="register-arrow">
                  →
                </span>
              )}

            </button>

          </form>

          <div className="register-login">

            <span>
              Already have an account?
            </span>

            <button
              type="button"
              onClick={() =>
                navigate('/login')
              }
            >
              Log in
            </button>

          </div>

        </div>

      </section>

      <footer className="register-footer">

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

export default Register