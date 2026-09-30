import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Analyze.css'

/* =========================================================
   SMALL HELPERS
========================================================= */

function formatValue(value) {
  if (value === null || value === undefined) {
    return '—'
  }

  if (typeof value === 'boolean') {
    return value ? 'true' : 'false'
  }

  return String(value)
}

function DataPill({ children }) {
  return (
    <span className="analysis-data-pill">
      {children}
    </span>
  )
}

/* =========================================================
   AST
========================================================= */

function AstNode({
  label,
  value,
  depth = 0,
}) {
  const isObject =
    value !== null &&
    typeof value === 'object'

  const [open, setOpen] = useState(
    depth < 2
  )

  if (!isObject) {
    return (
      <div
        className="ast-leaf"
        style={{
          '--ast-depth': depth,
        }}
      >
        <span className="ast-leaf-branch" />

        <span className="ast-leaf-label">
          {label}
        </span>

        <span className="ast-leaf-value">
          {formatValue(value)}
        </span>
      </div>
    )
  }

  const entries = Array.isArray(value)
    ? value.map((item, index) => [
        `[${index}]`,
        item,
      ])
    : Object.entries(value)

  return (
    <div className="ast-node">
      <button
        type="button"
        className="ast-node-header"
        style={{
          '--ast-depth': depth,
        }}
        onClick={() =>
          setOpen(!open)
        }
      >
        <span className="ast-toggle">
          {open ? '−' : '+'}
        </span>

        <span className="ast-node-label">
          {label}
        </span>

        <span className="ast-node-kind">
          {Array.isArray(value)
            ? 'LIST'
            : 'NODE'}
        </span>
      </button>

      {open && entries.length > 0 && (
        <div className="ast-children">
          {entries.map(
            ([childLabel, childValue], index) => (
              <AstNode
                key={`${childLabel}-${index}`}
                label={childLabel}
                value={childValue}
                depth={depth + 1}
              />
            )
          )}
        </div>
      )}
    </div>
  )
}

function AstViewer({ data }) {
  if (!data) {
    return (
      <EmptyState
        icon="AST"
        title="No AST available"
        description="Run the analysis to generate the abstract syntax tree."
      />
    )
  }

  return (
    <div className="result-view ast-view">
      <ResultHeader
        eyebrow="ABSTRACT SYNTAX TREE"
        title="Program structure"
        badge="AST"
      />

      <div className="ast-tree">
        {Array.isArray(data) ? (
          data.map((item, index) => (
            <AstNode
              key={index}
              label={`Node ${index + 1}`}
              value={item}
            />
          ))
        ) : (
          Object.entries(data).map(
            ([key, value]) => (
              <AstNode
                key={key}
                label={key}
                value={value}
              />
            )
          )
        )}
      </div>
    </div>
  )
}

/* =========================================================
   EXPLANATION
========================================================= */

function ExplanationViewer({ data }) {
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon="i"
        title="No explanation available"
        description="Run the analysis to generate a program explanation."
      />
    )
  }

  return (
    <div className="result-view explanation-view">
      <ResultHeader
        eyebrow="PROGRAM EXPLANATION"
        title="What CodeLens found"
        badge={`${data.length} INSIGHTS`}
      />

      <div className="explanation-list">
        {data.map((item, index) => (
          <div
            className="explanation-card"
            key={index}
          >
            <div className="explanation-number">
              {String(index + 1).padStart(
                2,
                '0'
              )}
            </div>

            <div className="explanation-card-content">
              <span>
                ANALYSIS INSIGHT
              </span>

              <p>
                {typeof item === 'string'
                  ? item
                  : JSON.stringify(item)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* =========================================================
   SYMBOL TABLE
========================================================= */

function SymbolTableViewer({ data }) {
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon="Σ"
        title="No symbols found"
        description="No symbol-table entries were returned for this program."
      />
    )
  }

  return (
    <div className="result-view">
      <ResultHeader
        eyebrow="SYMBOL TABLE"
        title="Declared program symbols"
        badge={`${data.length} SYMBOLS`}
      />

      <div className="table-wrapper">
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
            {data.map(
              (symbol, index) => (
                <tr key={index}>
                  <td>
                    <span className="symbol-name">
                      {formatValue(
                        symbol.name
                      )}
                    </span>
                  </td>

                  <td>
                    <DataPill>
                      {formatValue(
                        symbol.type
                      )}
                    </DataPill>
                  </td>

                  <td>
                    {formatValue(
                      symbol.kind
                    )}
                  </td>

                  <td>
                    {formatValue(
                      symbol.scope
                    )}
                  </td>

                  <td>
                    <span className="line-number">
                      {formatValue(
                        symbol.line
                      )}
                    </span>
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/* =========================================================
   TAC
========================================================= */

function TacViewer({ data }) {
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon="T3"
        title="No TAC generated"
        description="Three-address code will appear here after analysis."
      />
    )
  }

  return (
    <div className="result-view">
      <ResultHeader
        eyebrow="THREE-ADDRESS CODE"
        title="Intermediate instructions"
        badge={`${data.length} INSTRUCTIONS`}
      />

      <div className="tac-list">
        {data.map((instruction, index) => (
          <div
            className="tac-row"
            key={index}
          >
            <span className="tac-index">
              {String(index + 1).padStart(
                2,
                '0'
              )}
            </span>

            <code>
              {formatValue(
                instruction
              )}
            </code>
          </div>
        ))}
      </div>
    </div>
  )
}

/* =========================================================
   BASIC BLOCKS
========================================================= */

function BasicBlocksViewer({
  data,
}) {
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon="B"
        title="No basic blocks"
        description="The control-flow blocks generated by the compiler will appear here."
      />
    )
  }

  return (
    <div className="result-view">
      <ResultHeader
        eyebrow="BASIC BLOCKS"
        title="Linear execution regions"
        badge={`${data.length} BLOCKS`}
      />

      <div className="basic-block-grid">
        {data.map(
          (block, index) => (
            <div
              className="basic-block-card"
              key={
                block.id ??
                index
              }
            >
              <div className="basic-block-header">
                <div>
                  <span>
                    BLOCK
                  </span>

                  <strong>
                    {formatValue(
                      block.id ??
                        index + 1
                    )}
                  </strong>
                </div>

                <span className="block-index">
                  {String(index + 1).padStart(
                    2,
                    '0'
                  )}
                </span>
              </div>

              <div className="basic-block-instructions">
                {(
                  block.instructions ||
                  []
                ).map(
                  (
                    instruction,
                    instructionIndex
                  ) => (
                    <div
                      className="block-instruction"
                      key={
                        instructionIndex
                      }
                    >
                      <span>
                        {instructionIndex +
                          1}
                      </span>

                      <code>
                        {formatValue(
                          instruction
                        )}
                      </code>
                    </div>
                  )
                )}
              </div>
            </div>
          )
        )}
      </div>
    </div>
  )
}

/* =========================================================
   CFG
========================================================= */

function CfgViewer({ data }) {
  if (!data) {
    return (
      <EmptyState
        icon="CFG"
        title="No control-flow graph"
        description="Run the analysis to generate control-flow information."
      />
    )
  }

  const nodes = data.nodes || []
  const edges = data.edges || []

  return (
    <div className="result-view">
      <ResultHeader
        eyebrow="CONTROL FLOW GRAPH"
        title="Program execution paths"
        badge={`${nodes.length} NODES`}
      />

      <div className="cfg-section">
        <div className="cfg-section-title">
          <span>GRAPH NODES</span>

          <small>
            {nodes.length} control-flow regions
          </small>
        </div>

        <div className="cfg-node-grid">
          {nodes.map(
            (node, index) => (
              <div
                className="cfg-node-card"
                key={
                  node.id ??
                  index
                }
              >
                <div className="cfg-node-top">
                  <span>
                    NODE
                  </span>

                  <strong>
                    {formatValue(
                      node.id ??
                        index + 1
                    )}
                  </strong>
                </div>

                <div className="cfg-connections">
                  <div>
                    <span>
                      PREDECESSORS
                    </span>

                    <div className="connection-values">
                      {node.predecessors &&
                      node.predecessors.length > 0 ? (
                        node.predecessors.map(
                          (
                            item,
                            itemIndex
                          ) => (
                            <DataPill
                              key={
                                itemIndex
                              }
                            >
                              {formatValue(
                                item
                              )}
                            </DataPill>
                          )
                        )
                      ) : (
                        <span className="connection-empty">
                          None
                        </span>
                      )}
                    </div>
                  </div>

                  <div>
                    <span>
                      SUCCESSORS
                    </span>

                    <div className="connection-values">
                      {node.successors &&
                      node.successors.length > 0 ? (
                        node.successors.map(
                          (
                            item,
                            itemIndex
                          ) => (
                            <DataPill
                              key={
                                itemIndex
                              }
                            >
                              {formatValue(
                                item
                              )}
                            </DataPill>
                          )
                        )
                      ) : (
                        <span className="connection-empty">
                          None
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          )}
        </div>
      </div>

      <div className="cfg-section cfg-edges-section">
        <div className="cfg-section-title">
          <span>GRAPH EDGES</span>

          <small>
            {edges.length} connections
          </small>
        </div>

        <div className="cfg-edge-list">
          {edges.length > 0 ? (
            edges.map(
              (edge, index) => (
                <div
                  className="cfg-edge"
                  key={index}
                >
                  <span>
                    {formatValue(
                      edge.from
                    )}
                  </span>

                  <i>
                    →
                  </i>

                  <span>
                    {formatValue(
                      edge.to
                    )}
                  </span>
                </div>
              )
            )
          ) : (
            <div className="cfg-no-edges">
              No graph edges were returned.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* =========================================================
   DATA FLOW
========================================================= */

function DataFlowViewer({
  data,
}) {
  if (!data) {
    return (
      <EmptyState
        icon="DF"
        title="No data-flow information"
        description="Run the analysis to generate data-flow information."
      />
    )
  }

  const sections = [
    {
      key: 'gen',
      label: 'GEN',
      description:
        'Definitions generated by a block',
    },
    {
      key: 'kill',
      label: 'KILL',
      description:
        'Definitions invalidated by a block',
    },
    {
      key: 'in',
      label: 'IN',
      description:
        'Information entering a block',
    },
    {
      key: 'out',
      label: 'OUT',
      description:
        'Information leaving a block',
    },
  ]

  return (
    <div className="result-view">
      <ResultHeader
        eyebrow="DATA FLOW ANALYSIS"
        title="Definition flow through the program"
        badge="4 SETS"
      />

      <div className="data-flow-grid">
        {sections.map(
          (section) => {
            const value =
              data[section.key]

            return (
              <div
                className="data-flow-card"
                key={section.key}
              >
                <div className="data-flow-card-header">
                  <div>
                    <span>
                      {section.label}
                    </span>

                    <p>
                      {section.description}
                    </p>
                  </div>
                </div>

                <div className="data-flow-content">
                  {value &&
                  typeof value ===
                    'object' &&
                  Object.keys(value)
                    .length > 0 ? (
                    Object.entries(
                      value
                    ).map(
                      (
                        [
                          block,
                          definitions,
                        ],
                        index
                      ) => (
                        <div
                          className="data-flow-row"
                          key={
                            index
                          }
                        >
                          <span className="data-flow-block">
                            {block}
                          </span>

                          <div className="data-flow-values">
                            {Array.isArray(
                              definitions
                            ) ? (
                              definitions.map(
                                (
                                  item,
                                  itemIndex
                                ) => (
                                  <DataPill
                                    key={
                                      itemIndex
                                    }
                                  >
                                    {typeof item ===
                                    'object'
                                      ? JSON.stringify(
                                          item
                                        )
                                      : formatValue(
                                          item
                                        )}
                                  </DataPill>
                                )
                              )
                            ) : (
                              <DataPill>
                                {formatValue(
                                  definitions
                                )}
                              </DataPill>
                            )}
                          </div>
                        </div>
                      )
                    )
                  ) : (
                    <div className="data-flow-empty">
                      No entries
                    </div>
                  )}
                </div>
              </div>
            )
          }
        )}
      </div>
    </div>
  )
}

/* =========================================================
   DEF-USE
========================================================= */

function DefUseViewer({
  data,
}) {
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon="D→U"
        title="No def-use chains"
        description="Definition-to-use relationships will appear here."
      />
    )
  }

  return (
    <div className="result-view">
      <ResultHeader
        eyebrow="DEF-USE ANALYSIS"
        title="Definitions and their uses"
        badge={`${data.length} CHAINS`}
      />

      <div className="def-use-list">
        {data.map(
          (chain, index) => {
            const definition =
              chain.definition || {}

            const uses =
              chain.uses || []

            return (
              <div
                className="def-use-card"
                key={index}
              >
                <div className="def-use-definition">
                  <div className="def-use-label">
                    <span>
                      DEFINITION
                    </span>

                    <strong>
                      {formatValue(
                        definition.variable
                      )}
                    </strong>
                  </div>

                  <div className="def-use-meta">
                    <span>
                      BLOCK
                    </span>

                    <DataPill>
                      {formatValue(
                        definition.block
                      )}
                    </DataPill>

                    <span>
                      INSTRUCTION
                    </span>

                    <DataPill>
                      {formatValue(
                        definition.instruction
                      )}
                    </DataPill>
                  </div>
                </div>

                <div className="def-use-arrow">
                  →
                </div>

                <div className="def-use-uses">
                  <span>
                    USES
                  </span>

                  {uses.length > 0 ? (
                    uses.map(
                      (
                        use,
                        useIndex
                      ) => (
                        <div
                          className="def-use-item"
                          key={
                            useIndex
                          }
                        >
                          <strong>
                            {formatValue(
                              use.variable
                            )}
                          </strong>

                          <span>
                            B
                            {formatValue(
                              use.block
                            )}
                          </span>

                          <span>
                            I
                            {formatValue(
                              use.instruction
                            )}
                          </span>

                          {use.statement && (
                            <code>
                              {
                                use.statement
                              }
                            </code>
                          )}
                        </div>
                      )
                    )
                  ) : (
                    <span className="connection-empty">
                      No uses
                    </span>
                  )}
                </div>
              </div>
            )
          }
        )}
      </div>
    </div>
  )
}

/* =========================================================
   IMPACT
========================================================= */

function ImpactViewer() {
  return (
    <div className="result-view impact-view">
      <ResultHeader
        eyebrow="CHANGE IMPACT ANALYSIS"
        title="Understand what a change affects"
        badge="BEFORE / AFTER"
      />

      <div className="impact-intro">
        <div className="impact-icon">
          →
        </div>

        <div>
          <h3>
            Compare two versions of your program
          </h3>

          <p>
            CodeLens will compare the before and
            after representations to identify changed
            syntax, affected control-flow regions,
            dependent statements, and impacted paths.
          </p>
        </div>
      </div>

      <div className="impact-flow">
        <div className="impact-step">
          <span>
            01
          </span>

          <strong>
            BEFORE
          </strong>

          <small>
            Original program
          </small>
        </div>

        <i />

        <div className="impact-step">
          <span>
            02
          </span>

          <strong>
            CHANGE
          </strong>

          <small>
            Compare representations
          </small>
        </div>

        <i />

        <div className="impact-step impact-step-active">
          <span>
            03
          </span>

          <strong>
            IMPACT
          </strong>

          <small>
            Affected code
          </small>
        </div>
      </div>

      <div className="impact-note">
        <span>
          NEXT
        </span>

        <p>
          The before/after editor and impact
          results will be connected to the existing
          change-impact backend separately.
        </p>
      </div>
    </div>
  )
}

/* =========================================================
   GENERIC UI
========================================================= */

function ResultHeader({
  eyebrow,
  title,
  badge,
}) {
  return (
    <div className="result-header">
      <div>
        <span>
          {eyebrow}
        </span>

        <h3>
          {title}
        </h3>
      </div>

      <span className="result-badge">
        {badge}
      </span>
    </div>
  )
}

function EmptyState({
  icon,
  title,
  description,
}) {
  return (
    <div className="analyze-empty-result">
      <div className="analyze-empty-icon">
        {icon}
      </div>

      <h3>
        {title}
      </h3>

      <p>
        {description}
      </p>
    </div>
  )
}

/* =========================================================
   MAIN PAGE
========================================================= */

function Analyze() {
  const navigate = useNavigate()

  const [code, setCode] = useState(
`int main() {
    int x = 10;
    int y = 20;

    if (x < y) {
        x = x + 1;
    }

    return x;
}`
  )

  const [analysisName, setAnalysisName] =
    useState('')

  const [activeTab, setActiveTab] =
    useState('explanation')

  const [loading, setLoading] =
    useState(false)

  const [error, setError] =
    useState('')

  const [result, setResult] =
    useState(null)

  const analysisTabs = [
    {
      id: 'explanation',
      label: 'Explanation',
      short: '01',
    },
    {
      id: 'ast',
      label: 'AST',
      short: '02',
    },
    {
      id: 'symbol-table',
      label: 'Symbol Table',
      short: '03',
    },
    {
      id: 'tac',
      label: 'TAC',
      short: '04',
    },
    {
      id: 'basic-blocks',
      label: 'Basic Blocks',
      short: '05',
    },
    {
      id: 'cfg',
      label: 'CFG',
      short: '06',
    },
    {
      id: 'data-flow',
      label: 'Data Flow',
      short: '07',
    },
    {
      id: 'def-use',
      label: 'Def-Use',
      short: '08',
    },
    {
      id: 'impact',
      label: 'Impact',
      short: '09',
    },
  ]

  const handleAnalyze = async () => {
    if (!code.trim()) {
      setError(
        'Please enter C source code before running the analysis.'
      )

      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch(
        'http://localhost:5000/api/analyze',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            code: code,
            name: analysisName.trim() || 'Untitled analysis',
          }),
        }
      )

      const data =
        await response.json()

      if (!response.ok) {
        throw new Error(
          data.error ||
            'Analysis failed.'
        )
      }

      setResult(data)
      setActiveTab('explanation')
    } catch (err) {
      setError(
        err.message ||
          'Something went wrong during analysis.'
      )
    } finally {
      setLoading(false)
    }
  }

  const renderResult = () => {
    if (!result) {
      return (
        <EmptyState
          icon="CL"
          title="Your analysis will appear here"
          description="Run the compiler pipeline to explore your program structure, flow, and dependencies."
        />
      )
    }

    const resultKeyMap = {
      explanation: 'explanation',
      ast: 'ast',
      'symbol-table': 'symbols',
      tac: 'tac',
      'basic-blocks': 'basic_blocks',
      cfg: 'cfg',
      'data-flow': 'data_flow',
      'def-use': 'def_use',
    }

    if (
      activeTab === 'impact'
    ) {
      return (
        <ImpactViewer />
      )
    }

    const data =
      result[
        resultKeyMap[activeTab]
      ]

    if (
      data === undefined ||
      data === null
    ) {
      return (
        <EmptyState
          icon="—"
          title="No data available"
          description="This representation was not returned by the current analysis."
        />
      )
    }

    switch (activeTab) {
      case 'explanation':
        return (
          <ExplanationViewer
            data={data}
          />
        )

      case 'ast':
        return (
          <AstViewer
            data={data}
          />
        )

      case 'symbol-table':
        return (
          <SymbolTableViewer
            data={data}
          />
        )

      case 'tac':
        return (
          <TacViewer
            data={data}
          />
        )

      case 'basic-blocks':
        return (
          <BasicBlocksViewer
            data={data}
          />
        )

      case 'cfg':
        return (
          <CfgViewer
            data={data}
          />
        )

      case 'data-flow':
        return (
          <DataFlowViewer
            data={data}
          />
        )

      case 'def-use':
        return (
          <DefUseViewer
            data={data}
          />
        )

      default:
        return (
          <EmptyState
            icon="—"
            title="No data available"
            description="Select an analysis representation."
          />
        )
    }
  }

  return (
    <main className="analyze-page">
      <header className="analyze-topbar">
        <button
          className="analyze-brand"
          type="button"
          onClick={() =>
            navigate('/dashboard')
          }
        >
          <div className="analyze-logo">
            CL
          </div>

          <span>
            CodeLens
          </span>
        </button>

        <nav className="analyze-nav">
          <button
            className="analyze-nav-item"
            type="button"
            onClick={() =>
              navigate('/dashboard')
            }
          >
            Dashboard
          </button>

          <button
            className="analyze-nav-item analyze-nav-active"
            type="button"
          >
            Analyse
          </button>

          <button
            className="analyze-nav-item"
            type="button"
            onClick={() =>
              navigate('/history')
            }
          >
            History
          </button>

          <button
            className="analyze-nav-item"
            type="button"
            onClick={() =>
              navigate('/profile')
            }
          >
            Profile
          </button>
        </nav>

        <button
          className="analyze-back"
          type="button"
          onClick={() =>
            navigate('/dashboard')
          }
        >
          ← Dashboard
        </button>
      </header>

      <section className="analyze-content">
        <div className="analyze-heading">
          <div>
            <span className="analyze-kicker">
              CODE ANALYSIS
            </span>

            <h1>
              Understand your{' '}
              <span>program.</span>
            </h1>

            <p>
              Paste your C source code and explore
              how the compiler understands it.
            </p>
          </div>

          <div className="analyze-heading-meta">
            <span>
              SUPPORTED LANGUAGE
            </span>

            <strong>
              C
            </strong>
          </div>
        </div>

        <div className="analyze-workspace">
          <section className="analyze-editor-panel">
            <div className="analyze-panel-top">
              <div>
                <span>
                  SOURCE CODE
                </span>

                <h2>
                  Program input
                </h2>
              </div>

              <div className="analyze-file-badge">
                C
              </div>
            </div>

            <div className="analyze-name-field">
              <label htmlFor="analysis-name">
                Analysis name
              </label>

              <input
                id="analysis-name"
                type="text"
                value={analysisName}
                onChange={(event) =>
                  setAnalysisName(
                    event.target.value
                  )
                }
                placeholder="e.g. Loop condition analysis"
              />
            </div>

            <div className="analyze-editor">
              <div className="analyze-editor-bar">
                <div className="analyze-editor-dots">
                  <span />
                  <span />
                  <span />
                </div>

                <span>
                  main.c
                </span>

                <span>
                  C
                </span>
              </div>

              <textarea
                value={code}
                onChange={(event) =>
                  setCode(
                    event.target.value
                  )
                }
                spellCheck="false"
                aria-label="C source code"
              />
            </div>

            {error && (
              <div className="analyze-error">
                {error}
              </div>
            )}

            <div className="analyze-editor-footer">
              <span>
                Compiler pipeline enabled
              </span>

              <button
                className="analyze-run-button"
                type="button"
                onClick={
                  handleAnalyze
                }
                disabled={loading}
              >
                {loading
                  ? 'Analysing...'
                  : 'Run analysis'}

                {!loading && (
                  <span>
                    →
                  </span>
                )}
              </button>
            </div>
          </section>

          <section className="analyze-result-panel">
            <div className="analyze-panel-top">
              <div>
                <span>
                  ANALYSIS RESULTS
                </span>

                <h2>
                  Compiler representations
                </h2>
              </div>

              <div className="analyze-status">
                <span
                  className={
                    result
                      ? 'analyze-status-dot analyze-status-ready'
                      : 'analyze-status-dot'
                  }
                />

                {result
                  ? 'Ready'
                  : 'Waiting'}
              </div>
            </div>

            <div className="analyze-tabs">
              {analysisTabs.map(
                (tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    className={
                      activeTab ===
                      tab.id
                        ? 'analyze-tab analyze-tab-active'
                        : 'analyze-tab'
                    }
                    onClick={() =>
                      setActiveTab(
                        tab.id
                      )
                    }
                  >
                    <span>
                      {tab.short}
                    </span>

                    {tab.label}
                  </button>
                )
              )}
            </div>

            <div className="analyze-result-area">
              {renderResult()}
            </div>
          </section>
        </div>

        <section className="analyze-pipeline">
          <div className="analyze-pipeline-header">
            <div>
              <span>
                COMPILER PIPELINE
              </span>

              <h2>
                Source code → understanding
              </h2>
            </div>

            <span>
              CODELENS
            </span>
          </div>

          <div className="analyze-pipeline-flow">
            <div>
              <strong>
                LEX
              </strong>

              <small>
                Tokens
              </small>
            </div>

            <i />

            <div>
              <strong>
                PARSE
              </strong>

              <small>
                Grammar
              </small>
            </div>

            <i />

            <div>
              <strong>
                AST
              </strong>

              <small>
                Structure
              </small>
            </div>

            <i />

            <div>
              <strong>
                TAC
              </strong>

              <small>
                Instructions
              </small>
            </div>

            <i />

            <div>
              <strong>
                CFG
              </strong>

              <small>
                Control flow
              </small>
            </div>

            <i />

            <div className="analyze-pipeline-highlight">
              <strong>
                IMPACT
              </strong>

              <small>
                Dependencies
              </small>
            </div>
          </div>
        </section>
      </section>

      <footer className="analyze-footer">
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

export default Analyze
