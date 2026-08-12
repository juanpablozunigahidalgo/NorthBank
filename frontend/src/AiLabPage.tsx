import { useEffect, useState } from 'react'
import { fetchAiLab } from './api'
import type { AiLabDocument, ResearchDossier } from './types/dossier'

type Props = {
  dossier: ResearchDossier | null
  companyQuery: string
}

export default function AiLabPage({ dossier, companyQuery }: Props) {
  const [doc, setDoc] = useState<AiLabDocument | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const company = dossier?.company_name || companyQuery.trim() || undefined
    fetchAiLab(company)
      .then(setDoc)
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load AI lab'),
      )
      .finally(() => setLoading(false))
  }, [dossier?.company_name, companyQuery])

  const connected = doc?.stack.connected === true

  return (
    <div className="page">
      <header className="hero">
        <h1>AI Lab</h1>
        <p className="lede">
          Narrative layer only. Classification stays locked. Here you see the model, the
          system prompts, and — when a dossier exists — the full evidence pack sent to the
          model.
        </p>
      </header>

      {loading && <p className="muted">Loading prompt lab…</p>}
      {error && <div className="error">{error}</div>}

      {doc && (
        <>
          <section className="grid-2">
            <article className="card">
              <h3>Connection</h3>
              <p>
                <strong>{doc.stack.ux_label}</strong>
              </p>
              <dl>
                <dt>Provider</dt>
                <dd>{doc.stack.ai_provider}</dd>
                <dt>Model</dt>
                <dd>
                  <code>{doc.stack.ai_model}</code>
                </dd>
                <dt>Status</dt>
                <dd>{connected ? 'Connected' : 'Disconnected'}</dd>
              </dl>
            </article>
            <article className="card">
              <h3>How to connect a cheap / free model</h3>
              <ul className="plain-list">
                <li>
                  <strong>Groq (recommended free tier):</strong>{' '}
                  <a
                    href={doc.stack.how_to_connect?.groq_free_tier?.split(' — ')[0]}
                    target="_blank"
                    rel="noreferrer"
                  >
                    console.groq.com
                  </a>{' '}
                  → create API key → set <code>GROQ_API_KEY</code> in{' '}
                  <code>backend/.env</code> → restart API
                </li>
                <li>
                  <strong>Anthropic:</strong> set <code>ANTHROPIC_API_KEY</code>
                </li>
                <li>
                  <strong>Cursor:</strong> {doc.stack.how_to_connect?.cursor_note}
                </li>
              </ul>
              {!connected && (
                <p className="muted" style={{ marginBottom: 0 }}>
                  {doc.when_disconnected}
                </p>
              )}
            </article>
          </section>

          <p className="disclaimer">{doc.classification_note}</p>

          <section>
            <h3 className="section-title">Partnerships reflection task</h3>
            <pre className="prompt-block">{doc.prompts.partnerships_reflection_task}</pre>
          </section>

          <section>
            <h3 className="section-title">Final brief · system prompt</h3>
            <pre className="prompt-block">{doc.prompts.final_brief_system}</pre>
          </section>

          <section>
            <h3 className="section-title">Analyst · system prompt</h3>
            <pre className="prompt-block">{doc.prompts.analyst_system}</pre>
          </section>

          <section>
            <h3 className="section-title">
              Full user message {doc.has_live_dossier ? '(live dossier pack)' : ''}
            </h3>
            {doc.has_live_dossier && doc.live_user_message ? (
              <pre className="prompt-block prompt-block-lg">{doc.live_user_message}</pre>
            ) : (
              <article className="card">
                <p className="muted" style={{ margin: 0 }}>
                  Build a dossier in Research first, then reopen AI Lab to see the full
                  evidence pack JSON the model would receive (
                  {doc.prompts.final_brief_user_message_template}).
                </p>
              </article>
            )}
          </section>
        </>
      )}
    </div>
  )
}
