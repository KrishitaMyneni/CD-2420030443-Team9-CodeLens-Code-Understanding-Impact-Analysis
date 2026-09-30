import { useState } from 'react'
import './App.css'

function App() {
  const [code, setCode] = useState(
    `int calculate(int x) {
    int y = x * 2;

    if (y >= 10)
        return y + 5;

    return y - 5;
}`
  )

  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('Explanation')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const tabs = [
    'Explanation',
    'AST',
    'Symbols',
    'TAC',
    'Basic Blocks',
    'CFG',
    'Data Flow',
    'Def-Use',
  ]

  const analyzeCode = async () => {
    setLoading(true)
    setError('')
    setResult(null)
    setActiveTab('Explanation')

    try {
      const response = await fetch(
        'http://localhost:5000/api/analyze',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code,
          }),
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.error || 'Analysis failed.'
        )
      }

      setResult(data)
    } catch (err) {
      setError(
        err.message ||
          'Unable to connect to the CodeLens backend.'
      )
    } finally {
      setLoading(false)
    }
  }

  const renderSymbols = () => {
    if (!result?.symbols?.length) {
      return (
        <p className="empty-message">
          No symbols found.
        </p>
      )
    }

    return (
      <div className="table-container">
        <table className="analysis-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Kind</th>
              <th>Scope</th>
              <th>Line</th>
            </tr>
          </thead>

          <tbody>
            {result.symbols.map(
              (symbol, index) => (
                <tr key={index}>
                  <td>{symbol.name}</td>
                  <td>{symbol.type}</td>
                  <td>{symbol.kind}</td>
                  <td>{symbol.scope}</td>
                  <td>{symbol.line}</td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>
    )
  }

  const renderTAC = () => {
    if (!result?.tac?.length) {
      return (
        <p className="empty-message">
          No TAC instructions found.
        </p>
      )
    }

    return (
      <div className="tac-container">
        {result.tac.map(
          (instruction, index) => (
            <div
              className="tac-row"
              key={index}
            >
              <span className="tac-number">
                {index}
              </span>

              <span className="tac-instruction">
                {instruction}
              </span>
            </div>
          )
        )}
      </div>
    )
  }

  const renderBasicBlocks = () => {
    if (!result?.basic_blocks?.length) {
      return (
        <p className="empty-message">
          No basic blocks found.
        </p>
      )
    }

    return (
      <div className="blocks-container">
        {result.basic_blocks.map(
          (block, index) => {
            const isFirst = index === 0
            const isLast =
              index ===
              result.basic_blocks.length - 1

            return (
              <div
                className="basic-block"
                key={block.id}
              >
                <div className="basic-block-header">
                  <div className="block-title">
                    <span className="block-dot"></span>
                    B{block.id}
                  </div>

                  <span className="block-type">
                    {isFirst
                      ? 'ENTRY'
                      : isLast
                        ? 'EXIT / PATH'
                        : 'BASIC BLOCK'}
                  </span>
                </div>

                <div className="block-code">
                  {block.instructions.map(
                    (instruction, instructionIndex) => (
                      <div
                        className="block-code-row"
                        key={instructionIndex}
                      >
                        <span className="block-line-number">
                          {instructionIndex + 1}
                        </span>

                        <code>
                          {instruction}
                        </code>
                      </div>
                    )
                  )}
                </div>
              </div>
            )
          }
        )}
      </div>
    )
  }

  const getCFGPositions = (nodes) => {
    const positions = {}

    if (!nodes?.length) {
      return positions
    }

    const width = 900

    const firstNode = nodes[0]

    positions[firstNode.id] = {
      x: width / 2,
      y: 70,
    }

    const successors =
      firstNode.successors || []

    if (successors.length === 1) {
      positions[successors[0]] = {
        x: width / 2,
        y: 230,
      }
    } else {
      successors.forEach(
        (successor, index) => {
          positions[successor] = {
            x:
              index === 0
                ? 270
                : 630,
            y: 230,
          }
        }
      )
    }

    const positionedIds =
      new Set(
        Object.keys(positions).map(Number)
      )

    const remainingNodes =
      nodes.filter(
        (node) =>
          !positionedIds.has(node.id)
      )

    remainingNodes.forEach(
      (node, index) => {
        positions[node.id] = {
          x: 270 + index * 180,
          y: 390,
        }
      }
    )

    return positions
  }

  const renderCFG = () => {
    if (!result?.cfg?.nodes?.length) {
      return (
        <p className="empty-message">
          No CFG data found.
        </p>
      )
    }

    const positions = getCFGPositions(
      result.cfg.nodes
    )

    const nodeWidth = 150
    const nodeHeight = 82

    return (
      <div className="cfg-wrapper">
        <div className="cfg-description">
          <span className="cfg-description-icon">
            ↳
          </span>

          <div>
            <strong>
              Control Flow Graph
            </strong>

            <p>
              Each node represents a basic
              block and each arrow represents
              a possible control-flow transition.
            </p>
          </div>
        </div>

        <div className="cfg-canvas">
          <svg
            className="cfg-arrows"
            viewBox="0 0 900 500"
            preserveAspectRatio="xMidYMid meet"
          >
            <defs>
              <marker
                id="arrowhead"
                markerWidth="8"
                markerHeight="8"
                refX="7"
                refY="4"
                orient="auto"
              >
                <polygon points="0 0, 8 4, 0 8" />
              </marker>
            </defs>

            {result.cfg.edges.map(
              (edge, index) => {
                const from =
                  positions[edge.from]

                const to =
                  positions[edge.to]

                if (!from || !to) {
                  return null
                }

                const startY =
                  from.y + nodeHeight / 2

                const endY =
                  to.y - nodeHeight / 2

                const controlOffset =
                  Math.max(
                    35,
                    Math.abs(endY - startY) / 2
                  )

                return (
                  <path
                    key={index}
                    d={`
                      M ${from.x} ${startY}
                      C ${from.x} ${
                        startY +
                        controlOffset
                      },
                      ${to.x} ${
                        endY -
                        controlOffset
                      },
                      ${to.x} ${endY}
                    `}
                    markerEnd="url(#arrowhead)"
                  />
                )
              }
            )}
          </svg>

          {result.cfg.nodes.map(
            (node) => {
              const position =
                positions[node.id]

              if (!position) {
                return null
              }

              return (
                <div
                  className="cfg-node"
                  key={node.id}
                  style={{
                    left: `${(position.x / 900) * 100}%`,
                    top: `${(position.y / 500) * 100}%`,
                  }}
                >
                  <div className="cfg-node-header">
                    B{node.id}
                  </div>

                  <div className="cfg-node-body">
                    <span>
                      {node.successors?.length ||
                        0}{' '}
                      outgoing
                    </span>

                    <span>
                      {node.predecessors
                        ?.length || 0}{' '}
                      incoming
                    </span>
                  </div>
                </div>
              )
            }
          )}
        </div>

        <div className="cfg-legend">
          <span>
            <i className="legend-dot"></i>
            Basic block
          </span>

          <span>
            <i className="legend-arrow">→</i>
            Control flow
          </span>
        </div>
      </div>
    )
  }

  const renderTabContent = () => {
    if (!result) {
      return null
    }

    switch (activeTab) {
      case 'Explanation':
        return (
          <div className="explanation">
            {result.explanation?.map(
              (line, index) => (
                <p key={index}>
                  {line}
                </p>
              )
            )}
          </div>
        )

      case 'AST':
        return (
          <pre className="json-viewer">
            {JSON.stringify(
              result.ast,
              null,
              2
            )}
          </pre>
        )

      case 'Symbols':
        return renderSymbols()

      case 'TAC':
        return renderTAC()

      case 'Basic Blocks':
        return renderBasicBlocks()

      case 'CFG':
        return renderCFG()

      case 'Data Flow':
        return (
          <pre className="json-viewer">
            {JSON.stringify(
              result.data_flow,
              null,
              2
            )}
          </pre>
        )

      case 'Def-Use':
        return (
          <pre className="json-viewer">
            {JSON.stringify(
              result.def_use,
              null,
              2
            )}
          </pre>
        )

      default:
        return null
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div>
            <h1>CodeLens</h1>

            <p>
              Code Understanding & Impact Analysis
            </p>
          </div>

          <div className="header-status">
            <span className="status-dot"></span>
            Compiler Ready
          </div>
        </div>
      </header>

      <main className="main">
        <section className="editor-section">
          <div className="section-header">
            <div>
              <div className="section-label">
                INPUT
              </div>

              <h2>Source Code</h2>

              <p>
                Enter a C program to analyze
                its structure and behavior.
              </p>
            </div>

            <button
              className="analyze-button"
              onClick={analyzeCode}
              disabled={loading}
            >
              <span>
                {loading
                  ? 'Analyzing...'
                  : 'Analyze Code'}
              </span>

              {!loading && (
                <span className="button-arrow">
                  →
                </span>
              )}
            </button>
          </div>

          <textarea
            className="code-editor"
            value={code}
            onChange={(event) =>
              setCode(event.target.value)
            }
            spellCheck="false"
          />

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
        </section>

        {result && (
          <section className="results-section">
            <div className="analysis-header">
              <div>
                <div className="section-label">
                  ANALYSIS
                </div>

                <h2>
                  Program Analysis
                </h2>
              </div>

              <div className="success-message">
                <span className="success-dot"></span>
                Analysis completed
              </div>
            </div>

            <div className="result-tabs">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  className={
                    activeTab === tab
                      ? 'active'
                      : ''
                  }
                  onClick={() =>
                    setActiveTab(tab)
                  }
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="result-content">
              <div className="result-heading">
                <h3>{activeTab}</h3>

                <span className="result-badge">
                  {activeTab === 'Explanation'
                    ? 'Overview'
                    : 'Compiler Output'}
                </span>
              </div>

              {renderTabContent()}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App