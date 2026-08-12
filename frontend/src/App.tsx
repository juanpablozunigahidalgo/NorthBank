import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  fetchAiConfig,
  fetchCompanies,
  fetchFinalBrief,
  fetchResearch,
} from './api'
import CriteriaPage from './CriteriaPage'
import ExternalitiesPage from './ExternalitiesPage'
import AiLabPage from './AiLabPage'
import type {
  AiPromptTrace,
  FinalRecommendationBrief,
  ResearchDossier,
  ResearchResponse,
  RiskDecision,
} from './types/dossier'

const FALLBACK_COMPANIES = [
  'Northvolt AB',
  'Klarna Bank AB',
  'Oda Norway AS',
  'Wolt Enterprises Oy',
  'InPost S.A.',
]

function verdictClass(decision: RiskDecision): string {
  switch (decision) {
    case 'APPROVED':
      return 'verdict proceed' // green
    case 'ESCALATE_TO_COMPLIANCE':
      return 'verdict cautious' // amber = grey zone / review
    case 'REJECTED':
      return 'verdict escalate' // red = hard fail
  }
}

/** Partnerships-facing classification labels */
function verdictHeadline(decision: RiskDecision): string {
  switch (decision) {
    case 'APPROVED':
      return 'Approved'
    case 'REJECTED':
      return 'Rejected'
    case 'ESCALATE_TO_COMPLIANCE':
      return 'Escalate to compliance'
  }
}

function verdictSub(decision: RiskDecision): string {
  switch (decision) {
    case 'APPROVED':
      return 'Clean first-pass — still confirm before a commercial commitment.'
    case 'REJECTED':
      return 'Hard fail (e.g. bankruptcy, invalid tax registration, critical adverse media). Not a partner candidate in this draft.'
    case 'ESCALATE_TO_COMPLIANCE':
      return 'Grey zone (e.g. mid credit, material news, or PEP with adverse conduct). Compliance should clear before you progress.'
  }
}

function verdictMethodNote(): string {
  return 'Set by the deterministic policy engine (pure numbers + pure if→then criteria). The AI does not choose or change this class — see Criteria.'
}

function formatEur(value: number): string {
  return new Intl.NumberFormat('en-EU', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(value)
}

function AiPromptViewer({
  title,
  trace,
  onClose,
}: {
  title: string
  trace: AiPromptTrace
  onClose: () => void
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div
      className="prompt-viewer-backdrop"
      role="presentation"
      onClick={onClose}
    >
      <div
        className="prompt-viewer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="prompt-viewer-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="prompt-viewer-head">
          <div>
            <h2 id="prompt-viewer-title">{title}</h2>
            <p>
              What we sent to the model and what it returned. Does not change Approved /
              Escalate / Rejected. · {trace.model} ·{' '}
              {trace.used_llm ? 'LLM response' : 'Grounded-rules assembler'}
            </p>
          </div>
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Close
          </button>
        </header>
        <div className="prompt-viewer-body">
          <section>
            <h3>1. System prompt</h3>
            <p className="hint">Instructions the model must follow.</p>
            <pre>{trace.system_prompt || '(empty)'}</pre>
          </section>
          <section>
            <h3>2. What we sent (user message)</h3>
            <p className="hint">Structured facts + news pack as evidence.</p>
            <pre>{trace.user_message || '(empty)'}</pre>
          </section>
          <section>
            <h3>3. What the AI returned</h3>
            <p className="hint">Raw model output before UI mapping.</p>
            <pre>{trace.raw_response || '(empty)'}</pre>
          </section>
        </div>
      </div>
    </div>
  )
}

function FlagLine({
  ok,
  warn,
  label,
  value,
}: {
  ok?: boolean
  warn?: boolean
  label: string
  value: string
}) {
  const cls = ok ? 'flag-ok' : warn ? 'flag-warn' : 'flag-bad'
  return (
    <li>
      {label}: <span className={cls}>{value}</span>
    </li>
  )
}

export default function App() {
  const [view, setView] = useState<'research' | 'criteria' | 'externalities' | 'ai'>('research')
  const [companies, setCompanies] = useState<string[]>(FALLBACK_COMPANIES)
  const [query, setQuery] = useState('Northvolt AB')
  const [loading, setLoading] = useState(false)
  const [briefLoading, setBriefLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [response, setResponse] = useState<ResearchResponse | null>(null)
  const [finalBrief, setFinalBrief] = useState<FinalRecommendationBrief | null>(null)
  const [aiConfig, setAiConfig] = useState<{
    ai_provider: string
    ai_model: string
    connected?: boolean
    ux_label?: string
  } | null>(null)
  const [promptViewer, setPromptViewer] = useState<{
    title: string
    trace: AiPromptTrace
  } | null>(null)

  useEffect(() => {
    fetchCompanies()
      .then(setCompanies)
      .catch(() => {
        /* keep demo defaults if API not up yet */
      })
    fetchAiConfig()
      .then((c) =>
        setAiConfig({
          ai_provider: c.ai_provider,
          ai_model: c.ai_model,
          connected: c.connected,
          ux_label: c.ux_label,
        }),
      )
      .catch(() => setAiConfig(null))
  }, [])

  const dossier: ResearchDossier | null = response?.dossier ?? null

  const savedMinutes = useMemo(() => {
    if (!dossier?.elapsed_ms && dossier?.elapsed_ms !== 0) return null
    const seconds = Math.max(dossier.elapsed_ms / 1000, 0.01)
    return Math.max(0, Math.round(60 - seconds / 60))
  }, [dossier])

  async function onGenerate(e?: FormEvent) {
    e?.preventDefault()
    setLoading(true)
    setError(null)
    setFinalBrief(null)
    try {
      const data = await fetchResearch(query.trim())
      setResponse(data)
    } catch (err) {
      setResponse(null)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  async function onFinalBrief() {
    setBriefLoading(true)
    setError(null)
    try {
      const brief = await fetchFinalBrief(query.trim())
      setFinalBrief(brief)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Final brief failed')
    } finally {
      setBriefLoading(false)
    }
  }

  const cf = dossier?.compliance_hard_flags

  return (
    <>
      <header className="topnav">
        <button
          type="button"
          className="brand brand-btn"
          onClick={() => setView('research')}
          aria-label="Go to Prospective partner Dossier"
        >
          North<span>Bank</span>
        </button>
        <nav className="nav-pills" aria-label="Product">
          <button
            type="button"
            className={`nav-pill ${view === 'research' ? 'active' : ''}`}
            onClick={() => setView('research')}
            aria-current={view === 'research' ? 'page' : undefined}
          >
            Research
          </button>
          <button
            type="button"
            className={`nav-pill ${view === 'criteria' ? 'active' : ''}`}
            onClick={() => setView('criteria')}
            aria-current={view === 'criteria' ? 'page' : undefined}
          >
            Criteria
          </button>
          <button
            type="button"
            className={`nav-pill ${view === 'externalities' ? 'active' : ''}`}
            onClick={() => setView('externalities')}
            aria-current={view === 'externalities' ? 'page' : undefined}
          >
            Externalities
          </button>
        </nav>
        <div className="nav-actions">
          {aiConfig && (
            <button
              type="button"
              className={`ai-chip ai-chip-btn ${aiConfig.connected ? 'connected' : 'disconnected'}`}
              onClick={() => setView('ai')}
              title="Open AI Lab — prompts, model, evidence pack"
            >
              {aiConfig.ux_label ||
                (aiConfig.connected
                  ? `AI connected · ${aiConfig.ai_model}`
                  : 'AI disconnected · Grounded-rules analysis')}
            </button>
          )}
        </div>
      </header>

      {view === 'criteria' ? (
        <CriteriaPage />
      ) : view === 'externalities' ? (
        <ExternalitiesPage />
      ) : view === 'ai' ? (
        <AiLabPage dossier={dossier} companyQuery={query} />
      ) : (
      <div className="page">
        <header className="hero">
          <h1>Prospective partner Dossier</h1>
          {!dossier && (
            <ul className="user-questions" aria-label="What this dossier covers">
              <li title="Ownership, status, CEO, board, UBOs">
                <span className="check" aria-hidden>
                  ✓
                </span>
                General data
              </li>
              <li title="Revenue, EBITDA, trend from registry">
                <span className="check" aria-hidden>
                  ✓
                </span>
                Financial health
              </li>
              <li title="Company + CEO news, PEP/sanctions flags, ownership oddities">
                <span className="check" aria-hidden>
                  ✓
                </span>
                External red flags
              </li>
              <li title="Deterministic: Approved · Escalate · Rejected — not set by AI">
                <span className="check" aria-hidden>
                  ✓
                </span>
                Classification
              </li>
              <li title="AI connects hard facts with grounded news; cannot change the class">
                <span className="check" aria-hidden>
                  ✓
                </span>
                AI reflection
              </li>
            </ul>
          )}
        </header>

        <form className="search-bar" onSubmit={onGenerate}>
          <label htmlFor="company">Prospective partner (mock registry · {companies.length} cases)</label>
          <div className="row">
            <select
              id="company"
              className="company-select"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            >
              {companies.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
            <button
              type="submit"
              className="btn btn-dark"
              disabled={loading || !query.trim()}
            >
              {loading ? 'Preparing dossier…' : 'Build first-pass dossier'}
            </button>
          </div>
          <p className="muted select-hint">
            Dropdown lists all companies in the mock Nordic/Polish registry (demo cases).
          </p>
        </form>

        {error && <div className="error">{error}</div>}

        {!dossier && !error && (
          <div className="empty-state">
            <strong>How Partnerships uses this:</strong> enter a merchant → get a draft
            dossier instead of ~1 hour of manual registry / credit / news lookups. Live
            news uses a capped Externalities budget (parallel searches). You still decide —
            this never auto-approves a deal.
          </div>
        )}

        {dossier && (
          <main className="dossier">
            <section className={verdictClass(dossier.recommendation)}>
              <div>
                <p className="label">Classification-Recommendation</p>
                <h2>{verdictHeadline(dossier.recommendation)}</h2>
                <p>{verdictSub(dossier.recommendation)}</p>
                <p className="verdict-method">{verdictMethodNote()}</p>
                <p style={{ marginTop: '0.65rem', color: 'var(--muted)' }}>
                  {dossier.audit_summary}
                </p>
              </div>
              <div className="meta">
                <span>{dossier.company_name}</span>
                <span>
                  {dossier.country_code} · {dossier.company_id}
                </span>
                <span>
                  {dossier.elapsed_ms ?? '—'} ms
                  {savedMinutes !== null
                    ? ` · ~${savedMinutes} min saved vs 1h manual`
                    : ''}
                </span>
              </div>
            </section>

            <section>
              <h3 className="section-title">1. General Data</h3>
              <p className="section-help">
                Legal structure, status, ownership, tax registration.
              </p>
              <div className="grid-2">
                <article className="card">
                  <h3>Legal / ownership</h3>
                  <dl>
                    <dt>Status</dt>
                    <dd>
                      {dossier.ownership.status_code} —{' '}
                      {dossier.ownership.status_description}
                    </dd>
                    <dt>Legal form</dt>
                    <dd>{dossier.ownership.legal_structure}</dd>
                    <dt>CEO</dt>
                    <dd>{dossier.ownership.ceo ?? '—'}</dd>
                    <dt>Board</dt>
                    <dd>
                      {dossier.ownership.board_of_directors.join(', ') || '—'}
                    </dd>
                    <dt>UBOs</dt>
                    <dd>
                      {dossier.ownership.ultimate_beneficial_owners.join(', ') || '—'}
                    </dd>
                    <dt>Parent</dt>
                    <dd>{dossier.ownership.parent_company ?? '—'}</dd>
                    <dt>Ownership notes</dt>
                    <dd>
                      {dossier.ownership.unusual_ownership_patterns ?? 'None flagged'}
                    </dd>
                  </dl>
                </article>

                <article className="card">
                  <h3>Tax registration</h3>
                  {dossier.eu_vat_vies ? (
                    <dl>
                      <dt>VAT number</dt>
                      <dd>{dossier.eu_vat_vies.vat_number}</dd>
                      <dt>VIES valid</dt>
                      <dd>{dossier.eu_vat_vies.valid ? 'Yes' : 'No'}</dd>
                      <dt>Member state</dt>
                      <dd>{dossier.eu_vat_vies.member_state}</dd>
                      <dt>National VAT / F-tax</dt>
                      <dd>
                        {String(cf?.vat_registered)} / {String(cf?.f_tax_registered)}
                      </dd>
                    </dl>
                  ) : (
                    <p className="muted">VAT check unavailable.</p>
                  )}
                </article>
              </div>
            </section>

            <section>
              <h3 className="section-title">2. Financial health</h3>
              <p className="section-help">
                Revenue trend plus credit score, PD and payment behaviour.
              </p>
              <div className="metrics">
                <div>
                  <span>Revenue {dossier.financial_health.latest_year}</span>
                  <strong>
                    {formatEur(dossier.financial_health.latest_revenue_eur)}
                  </strong>
                </div>
                <div>
                  <span>EBITDA {dossier.financial_health.latest_year}</span>
                  <strong
                    className={
                      dossier.financial_health.latest_ebitda_eur < 0 ? 'neg' : ''
                    }
                  >
                    {formatEur(dossier.financial_health.latest_ebitda_eur)}
                  </strong>
                </div>
                <div>
                  <span>Trend</span>
                  <strong>{dossier.financial_health.trend}</strong>
                </div>
              </div>

              <div className="grid-2" style={{ marginBottom: '0.85rem' }}>
                <article className="card">
                  <h3>Credit reference</h3>
                  {dossier.creditsafe ? (
                    <dl>
                      <dt>Score / band</dt>
                      <dd>
                        {dossier.creditsafe.credit_score} ·{' '}
                        {dossier.creditsafe.rating_band}
                      </dd>
                      <dt>Default risk</dt>
                      <dd>{dossier.creditsafe.probability_of_default_pct}%</dd>
                      <dt>Payment behaviour</dt>
                      <dd>{dossier.creditsafe.payment_behavior}</dd>
                      <dt>Suggested limit</dt>
                      <dd>
                        {formatEur(dossier.creditsafe.credit_limit_recommendation_eur)}
                      </dd>
                    </dl>
                  ) : (
                    <p className="muted">Credit opinion unavailable.</p>
                  )}
                </article>
                <article className="card">
                  <h3>Why this matters for Partnerships</h3>
                  <p className="muted" style={{ margin: 0 }}>
                    Weak payment behaviour or a very low credit band usually means slower
                    onboarding, tighter commercial terms, or an early compliance
                    conversation — before you invest relationship time.
                  </p>
                </article>
              </div>

              <table>
                <thead>
                  <tr>
                    <th>Year</th>
                    <th>Revenue</th>
                    <th>EBITDA</th>
                    <th>Margin</th>
                  </tr>
                </thead>
                <tbody>
                  {dossier.financial_health.history.map((row) => (
                    <tr key={row.year}>
                      <td>{row.year}</td>
                      <td>{formatEur(row.revenue_eur)}</td>
                      <td className={row.ebitda_eur < 0 ? 'neg' : ''}>
                        {formatEur(row.ebitda_eur)}
                      </td>
                      <td>{row.profitability_margin_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section>
              <h3 className="section-title">3. External Redflags</h3>
              <p className="section-help">
                Compliance flags plus multi-theme Externalities news (company name + CEO).
              </p>
              <div className="grid-2">
                <article className="card">
                  <h3>Compliance checklist</h3>
                  <ul className="flag-list">
                    <FlagLine
                      label="PEP exposure"
                      value={
                        (cf?.pep_count ?? 0) > 0
                          ? `Yes (${cf?.pep_count})`
                          : 'None flagged'
                      }
                      ok={(cf?.pep_count ?? 0) === 0}
                      warn={(cf?.pep_count ?? 0) > 0}
                    />
                    <FlagLine
                      label="Missing auditor"
                      value={cf?.missing_auditor ? 'Yes' : 'No'}
                      ok={!cf?.missing_auditor}
                    />
                    <FlagLine
                      label="Connected bankruptcies"
                      value={String(cf?.connected_bankruptcy_companies ?? 0)}
                      ok={(cf?.connected_bankruptcy_companies ?? 0) < 2}
                      warn={(cf?.connected_bankruptcy_companies ?? 0) === 1}
                    />
                    <FlagLine
                      label="Sanctions match"
                      value={cf?.sanctions_list_match ? 'Yes' : 'None in this draft'}
                      ok={!cf?.sanctions_list_match}
                    />
                  </ul>
                  {dossier.hard_risk_triggers.length > 0 && (
                    <>
                      <h4>Why the system flagged this</h4>
                      <ul className="plain-list">
                        {dossier.hard_risk_triggers.map((t) => (
                          <li key={t}>{t}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </article>

                <article className="card">
                  <h3>What still needs your judgment</h3>
                  <ul className="plain-list">
                    {dossier.unsure_or_unverified.map((u) => (
                      <li key={u}>{u}</li>
                    ))}
                  </ul>
                </article>
              </div>

              <h3 className="section-title" style={{ marginTop: '1.1rem' }}>
                Externalities coverage by dimension
              </h3>
              <p className="section-help">
                Every searchable risk dimension is listed. Empty dimensions show as{' '}
                <code>news-PEP = 0</code> (and similar) — not omitted.
              </p>
              {(dossier.externality_coverage?.length ?? 0) === 0 ? (
                <p className="muted">Coverage not available for this run — regenerate dossier.</p>
              ) : (
                <div className="coverage-grid">
                  <div>
                    <h4 className="coverage-scope">Company</h4>
                    <ul className="coverage-list">
                      {dossier.externality_coverage!
                        .filter((c) => c.scope === 'company')
                        .map((c) => (
                          <li
                            key={c.theme_id}
                            className={
                              c.hit_count > 0 ? 'coverage-hit' : 'coverage-zero'
                            }
                          >
                            <code>{c.summary}</code>
                            <span>{c.label}</span>
                            {!c.searched && (
                              <em className="muted"> · not queried this run</em>
                            )}
                          </li>
                        ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="coverage-scope">CEO (person themes)</h4>
                    <ul className="coverage-list">
                      {dossier.externality_coverage!
                        .filter((c) => c.scope === 'person')
                        .map((c) => (
                          <li
                            key={c.theme_id}
                            className={
                              c.hit_count > 0 ? 'coverage-hit' : 'coverage-zero'
                            }
                          >
                            <code>{c.summary}</code>
                            <span>{c.label}</span>
                            {!c.searched && (
                              <em className="muted"> · not queried this run</em>
                            )}
                          </li>
                        ))}
                    </ul>
                  </div>
                </div>
              )}

              <h3 className="section-title" style={{ marginTop: '1.1rem' }}>
                Grounded news by dimension
              </h3>
              <p className="section-help">
                Articles with URL + quote, grouped under the externality theme that found them.
              </p>
              {dossier.adverse_media.length === 0 ? (
                <p className="muted">No grounded media signals returned.</p>
              ) : (
                <div className="media-by-theme">
                  {Object.entries(
                    dossier.adverse_media.reduce<
                      Record<string, typeof dossier.adverse_media>
                    >((acc, item) => {
                      const key =
                        item.externality_theme_id ||
                        item.externality_theme_label ||
                        'untagged'
                      if (!acc[key]) acc[key] = []
                      acc[key].push(item)
                      return acc
                    }, {}),
                  ).map(([themeKey, items]) => {
                    const cover = dossier.externality_coverage?.find(
                      (c) => c.theme_id === themeKey,
                    )
                    const title =
                      cover?.summary ||
                      items[0]?.externality_theme_label ||
                      themeKey
                    return (
                      <div key={themeKey} className="theme-news-block">
                        <h4>
                          {title}
                          {cover ? (
                            <span className="muted"> · {cover.label}</span>
                          ) : null}
                        </h4>
                        <div className="media-list">
                          {items.map((item) => (
                            <article
                              key={`${item.source_url}-${item.headline}`}
                              className="media-card"
                            >
                              <div className="media-top">
                                <strong>{item.headline}</strong>
                                <span className={`sev ${item.severity.toLowerCase()}`}>
                                  {item.severity} · {item.risk_category}
                                  {item.subject_type === 'person'
                                    ? ` · ${item.subject_name ?? 'person'}`
                                    : ''}
                                </span>
                              </div>
                              <blockquote>“{item.verbatim_quote}”</blockquote>
                              <a
                                href={item.source_url}
                                target="_blank"
                                rel="noreferrer"
                              >
                                {item.source_name} · open article
                              </a>
                            </article>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </section>

            {dossier.ai_analysis && (
              <section className="ai-panel">
                <div className="section-head">
                  <h3 className="section-title">Analyst brief for your review</h3>
                  {dossier.ai_analysis.prompt_trace && (
                    <button
                      type="button"
                      className="btn btn-ghost"
                      title="See what we sent to the model and what it returned"
                      onClick={() =>
                        setPromptViewer({
                          title: `AI exchange · Analyst · ${dossier.company_name}`,
                          trace: dossier.ai_analysis!.prompt_trace!,
                        })
                      }
                    >
                      View AI exchange
                    </button>
                  )}
                </div>
                <p className="ai-meta">
                  Draft confidence {dossier.ai_analysis.confidence_0_to_100}/100 ·
                  policy alignment: {dossier.ai_analysis.recommendation_alignment}
                </p>
                <p>{dossier.ai_analysis.executive_brief}</p>
                <div className="grid-2">
                  <article className="card">
                    <h3>Supported findings</h3>
                    <ul className="plain-list">
                      {dossier.ai_analysis.supported_findings.map((f) => (
                        <li key={f}>{f}</li>
                      ))}
                    </ul>
                  </article>
                  <article className="card">
                    <h3>Residual risks</h3>
                    <ul className="plain-list">
                      {dossier.ai_analysis.residual_risks.map((f) => (
                        <li key={f}>{f}</li>
                      ))}
                    </ul>
                  </article>
                </div>
              </section>
            )}

            <p className="disclaimer">{dossier.disclaimer}</p>

            <section className="final-brief-panel">
              <div className="section-head">
                <h3 className="section-title">Final AI recommendation dialogue</h3>
                {finalBrief?.prompt_trace && (
                  <button
                    type="button"
                    className="btn btn-ghost"
                    title="See what we sent to the model and what it returned"
                    onClick={() =>
                      setPromptViewer({
                        title: `AI exchange · Final brief · ${dossier.company_name}`,
                        trace: finalBrief.prompt_trace!,
                      })
                    }
                  >
                    View AI exchange
                  </button>
                )}
              </div>
              <p className="section-help">
                LLM drafts a final brief: connects logically the news and the hard API
                facts of the company. It cannot change Approved / Escalate / Rejected.
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={onFinalBrief}
                disabled={briefLoading}
              >
                {briefLoading ? 'Drafting grounded brief…' : 'Generate final recommendation'}
              </button>
              {finalBrief && (
                <article className="card" style={{ marginTop: '1rem' }}>
                  <h3>{finalBrief.recommendation_headline}</h3>
                  <p className="muted">
                    Locked policy: {finalBrief.policy_recommendation.replace(/_/g, ' ')} ·
                    confidence {finalBrief.confidence_0_to_100}/100 ·{' '}
                    {finalBrief.model_provider}
                    {finalBrief.human_review_required ? ' · human review required' : ''}
                  </p>
                  <p>{finalBrief.rationale_for_partnerships}</p>
                  <h4>Evidence</h4>
                  <ul className="plain-list">
                    {finalBrief.evidence_bullets.map((b) => (
                      <li key={b}>{b}</li>
                    ))}
                  </ul>
                  <h4>Cited rules</h4>
                  <p>{finalBrief.cited_rule_ids.join(', ') || '—'}</p>
                  <h4>Open questions</h4>
                  <ul className="plain-list">
                    {finalBrief.open_questions.map((q) => (
                      <li key={q}>{q}</li>
                    ))}
                  </ul>
                </article>
              )}
            </section>

            <details className="tech-notes">
              <summary>Sources & prototype notes (for reviewers)</summary>
              <div className="grid-2" style={{ marginTop: '0.85rem' }}>
                <article className="card">
                  <h3>Sources</h3>
                  <ul className="plain-list">
                    {dossier.sources.map((s) => (
                      <li key={s}>
                        <code>{s}</code>
                      </li>
                    ))}
                  </ul>
                </article>
                <article className="card">
                  <h3>Corners cut in this demo</h3>
                  <ul className="plain-list muted">
                    {response?.cut_corners.map((c) => (
                      <li key={c}>{c}</li>
                    ))}
                  </ul>
                  {dossier.ai_analysis && (
                    <p className="muted" style={{ marginTop: '0.75rem' }}>
                      Engine: {dossier.ai_analysis.model_provider}
                    </p>
                  )}
                </article>
              </div>
            </details>
          </main>
        )}
      </div>
      )}
      {promptViewer && (
        <AiPromptViewer
          title={promptViewer.title}
          trace={promptViewer.trace}
          onClose={() => setPromptViewer(null)}
        />
      )}
    </>
  )
}
