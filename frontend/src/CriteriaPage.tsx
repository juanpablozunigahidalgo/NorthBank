import { useEffect, useState } from 'react'
import { fetchPolicyRules } from './api'
import type { PolicyRulesDocument } from './types/dossier'

export default function CriteriaPage() {
  const [doc, setDoc] = useState<PolicyRulesDocument | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPolicyRules()
      .then(setDoc)
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load rules'),
      )
  }, [])

  const escalate = doc?.rules.filter((r) => r.then.includes('ESCALATE')) ?? []
  const rejected = doc?.rules.filter((r) => r.then.includes('REJECTED')) ?? []
  const approved = doc?.rules.filter((r) => r.then.includes('APPROVED')) ?? []

  return (
    <div className="page criteria-page">
      <header className="hero">
        <h1>How we evaluate partners</h1>
        <p className="lede">
          For NorthBank Partnerships: the Classification-Recommendation is a{' '}
          <strong>deterministic</strong> first-pass — pure numbers and pure if→then
          criteria. AI never chooses Approved / Escalate / Rejected; it only explains
          evidence already in the pack. A human always decides commercially.
        </p>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="callout-deterministic">
        <h3>Logic in one sentence</h3>
        <p>
          Same inputs → same class. Rules fire on registry status, Creditsafe score/band,
          VIES VAT validity, compliance flags (PEP, auditor, connected bankruptcies), and
          grounded media severity — <strong>before</strong> any LLM call.
        </p>
        {doc?.logic_summary && <p className="muted">{doc.logic_summary}</p>}
      </section>

      <section className="grid-2">
        <article className="card">
          <h3>Classification-Recommendation (3 outputs)</h3>
          <p className="muted" style={{ marginTop: 0 }}>
            Engine output only — reproducible bank-style gates for this mockup.
          </p>
          <ul className="plain-list">
            <li>
              <strong>Approved</strong> — clean first-pass; no reject/escalate rules
            </li>
            <li>
              <strong>Escalate to compliance</strong> — grey zone (PEP, mid credit,
              medium news)
            </li>
            <li>
              <strong>Rejected</strong> — hard fail (bankruptcy/reconstruction, invalid
              VAT, very weak credit, critical news)
            </li>
          </ul>
        </article>
        <article className="card">
          <h3>What runs the class (not AI)</h3>
          <ul className="plain-list">
            <li>
              <strong>Pure numbers</strong> — credit score / band, pepCount, connected
              bankruptcies, media severity ranks
            </li>
            <li>
              <strong>Pure criteria</strong> — status codes (e.g. bankruptcy), VAT
              valid/invalid, missing auditor, critical vs medium news
            </li>
            <li>
              <strong>AI afterwards</strong> — connects those facts with grounded news and
              flags investigation areas; never invents scores or flips the class
            </li>
            <li>
              <strong>Human-in-the-loop</strong> — required before any commercial
              commitment
            </li>
          </ul>
        </article>
      </section>

      <section className="grid-2">
        <article className="card">
          <h3>Demo story for reviewers</h3>
          <ol className="plain-list" style={{ paddingLeft: '1.1rem' }}>
            <li>Gather hard facts (registry, Creditsafe, VIES, flags).</li>
            <li>Gather grounded news (Externalities → company + CEO).</li>
            <li>
              Policy engine sets Approved / Escalate / Rejected (this page’s rules).
            </li>
            <li>AI drafts narrative only — locked class stays locked.</li>
          </ol>
        </article>
        <article className="card">
          <h3>What this mockup is / is not</h3>
          <ul className="plain-list">
            <li>
              <strong>Is</strong> — a first-pass Partnerships assistant with transparent
              gates
            </li>
            <li>
              <strong>Is not</strong> — live World-Check, live Creditsafe/VIES, or
              auto-approval of a deal
            </li>
            <li>
              LLM may change recommendation:{' '}
              <strong>{String(doc?.llm_may_change_recommendation ?? false)}</strong>
            </li>
          </ul>
        </article>
      </section>

      <section>
        <h3 className="section-title">Rejected (hard fails)</h3>
        <p className="section-help">
          Deterministic hard fails — if any of these fire, class = Rejected.
        </p>
        <div className="rules-list">
          {rejected.map((r) => (
            <article key={r.id} className="card rule-card escalate-rule">
              <div className="rule-id">{r.id}</div>
              <p>
                <strong>If</strong> {r.if}
              </p>
              <p>
                <strong>Then</strong> {r.then}
              </p>
              <p className="muted">{r.why}</p>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h3 className="section-title">Escalate to compliance (grey zone)</h3>
        <p className="section-help">
          Deterministic grey zone — numbers/flags that need human compliance judgment.
        </p>
        <div className="rules-list">
          {escalate.map((r) => (
            <article key={r.id} className="card rule-card cautious-rule">
              <div className="rule-id">{r.id}</div>
              <p>
                <strong>If</strong> {r.if}
              </p>
              <p>
                <strong>Then</strong> {r.then}
              </p>
              <p className="muted">{r.why}</p>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h3 className="section-title">Approved</h3>
        <p className="section-help">
          Deterministic clean pass — only if no reject/escalate rule fired.
        </p>
        <div className="rules-list">
          {approved.map((r) => (
            <article key={r.id} className="card rule-card proceed-rule">
              <div className="rule-id">{r.id}</div>
              <p>
                <strong>If</strong> {r.if}
              </p>
              <p>
                <strong>Then</strong> {r.then}
              </p>
              <p className="muted">{r.why}</p>
            </article>
          ))}
        </div>
      </section>

      {doc && (
        <p className="disclaimer">
          Policy v{doc.version}. Human-in-the-loop: {String(doc.human_in_the_loop)}. LLM may
          change recommendation: {String(doc.llm_may_change_recommendation)}. {doc.future_agents}
        </p>
      )}
    </div>
  )
}
