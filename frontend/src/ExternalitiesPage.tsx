import { useEffect, useState } from 'react'
import { fetchExternalities } from './api'
import type { ExternalitiesDocument, ExternalityTheme } from './types/dossier'

function ThemeCard({
  theme,
  accent,
}: {
  theme: ExternalityTheme
  accent: string
}) {
  return (
    <article className="card">
      <div className="rule-id" style={{ color: accent }}>
        {theme.label}
      </div>
      <p className="muted">{theme.description}</p>
      <p>
        <strong>Code:</strong> <code>{theme.news_code ?? theme.id}</code>
      </p>
      <p>
        <strong>Query OR:</strong> <code>{theme.query_or}</code>
      </p>
    </article>
  )
}

export default function ExternalitiesPage() {
  const [doc, setDoc] = useState<ExternalitiesDocument | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchExternalities()
      .then(setDoc)
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load externalities'),
      )
  }, [])

  return (
    <div className="page">
      <header className="hero">
        <h1>Externalities</h1>
        <p className="lede">
          For NorthBank Partnerships: open-web risk dimensions we search on trusted news
          domains — then report every dimension as <code>news-Code = N</code> (including{' '}
          <code>= 0</code>). This feeds Research evidence. It does{' '}
          <strong>not</strong> set Approved / Escalate / Rejected (that is Criteria /
          policy).
        </p>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="callout-deterministic">
        <h3>Search logic in this mockup</h3>
        <p>
          Live search is intentionally limited to <strong>company legal name + CEO</strong>{' '}
          (board, UBOs and investors are out of scope for the demo). Each theme becomes one
          DuckDuckGo query; results are filtered to allowlisted domains; a hit needs article
          URL + verbatim quote.
        </p>
        <p className="muted">
          Query shape:{' '}
          <code>&quot;Northvolt AB&quot; (bankruptcy OR insolvency OR …)</code> for the
          company, and{' '}
          <code>
            &quot;CEO Name&quot; (fraud OR embezzlement OR &quot;money laundering&quot; OR
            …)
          </code>{' '}
          for person themes (fraud/crime themes may add a company hint). Keywords inside a
          theme are OR’d together — not one separate search per synonym.
        </p>
      </section>

      {doc && (
        <>
          <section className="grid-2">
            <article className="card">
              <h3>How this feeds Research</h3>
              <p className="muted" style={{ margin: 0 }}>
                {doc.how_it_feeds_research}
              </p>
              <ul className="plain-list" style={{ marginTop: '0.75rem' }}>
                <li>Coverage list shows every theme, including zeros (e.g. news-PEP = 0).</li>
                <li>Zero ≠ cleared — only “no grounded hit in this run”.</li>
                <li>AI may connect news ↔ hard facts; classification stays locked.</li>
              </ul>
            </article>
            <article className="card">
              <h3>Mockup search budget</h3>
              <ul className="plain-list">
                <li>
                  <strong>Who</strong>: company name + CEO only
                </li>
                <li>Company themes: {doc.search_budget.company_theme_queries}</li>
                <li>CEO / person themes: {doc.search_budget.person_theme_queries}</li>
                <li>
                  Typical live queries ≈ company themes + CEO themes (parallel workers)
                </li>
                <li>
                  Articles kept in dossier: up to ~
                  {doc.search_budget.dossier_top_n_articles}+ with theme diversity
                </li>
                <li>
                  <strong>Not searched live</strong>: board, UBOs, outside investors
                </li>
              </ul>
            </article>
          </section>

          <section className="grid-2">
            <article className="card">
              <h3>Demo story for reviewers</h3>
              <ol className="plain-list" style={{ paddingLeft: '1.1rem' }}>
                <li>Fan out company themes on the legal name.</li>
                <li>Fan out person themes on the CEO.</li>
                <li>Keep only trusted-domain URL + quote hits.</li>
                <li>
                  Show coverage (news-Legal = N, news-PEP = 0, …) in the dossier.
                </li>
              </ol>
            </article>
            <article className="card">
              <h3>Guardrails</h3>
              <ul className="plain-list">
                <li>No invented headlines — mock fallback only if live returns nothing</li>
                <li>Homonym risk on person names remains (human review)</li>
                <li>Externalities ≠ classification engine (see Criteria)</li>
                <li>Human review before any commercial commitment</li>
              </ul>
            </article>
          </section>

          <section>
            <h3 className="section-title">Company externalities</h3>
            <p className="section-help">
              Searched as <code>&quot;Company name&quot; (theme OR-terms)</code> — legal,
              fraud, financial distress, regulatory, environmental, etc.
            </p>
            <div className="rules-list">
              {doc.company.map((t) => (
                <ThemeCard key={t.id} theme={t} accent="var(--purple)" />
              ))}
            </div>
          </section>

          <section>
            <h3 className="section-title">Person externalities (CEO only in this mockup)</h3>
            <p className="section-help">
              Searched as <code>&quot;CEO name&quot; (theme OR-terms)</code>. Themes below
              are the person risk dimensions (PEP, fraud, sanctions, litigation…). Board /
              UBO fan-out can be added later without changing Criteria.
            </p>
            <div className="rules-list">
              {doc.person.map((t) => (
                <ThemeCard key={t.id} theme={t} accent="var(--cautious)" />
              ))}
            </div>
          </section>

          <p className="disclaimer">{doc.purpose}</p>
        </>
      )}
    </div>
  )
}
