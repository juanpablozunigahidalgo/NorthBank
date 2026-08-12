# NorthBank — Partner Research Assistant

A first-pass research dossier for **digital banks** that need to screen prospective merchants and business partners faster — without turning risk ownership over to a black-box model.

Live demo: [northbank.onrender.com](https://northbank.onrender.com)  
Presentation: [Google Slides](https://docs.google.com/presentation/d/1d7r9RzV4AM9B-kEuWIRP_STTzmXZwU7fJ_fBbRjwmNw/edit?usp=sharing)

---

## The problem (in the abstract)

Before a bank deepens a commercial relationship, someone still has to answer the same questions:

- Who owns and controls this company?
- What does financial health look like (statements, credit posture, payment behaviour)?
- Are there external red flags — adverse media, litigation, PEP / sanctions-adjacent exposure, unusual ownership?
- Is this a candidate to progress, escalate to compliance, or decline at first pass?

Today that work is often **manual KYB-style research**: registries, bureaus, tax validity, news and watchlist-adjacent checks across disconnected tools. It is slow, uneven, and expensive to scale. As digital banks grow merchant and credit-adjacent volumes, that hour-per-counterparty becomes a **cost-to-serve** problem — under the same regulatory expectation that humans remain accountable for decisions that affect credit risk and partner onboarding.

---

## What this prototype demonstrates

NorthBank shows a practical split that regulated institutions can live with **today**, while preparing for **tomorrow**:

| Layer | Role |
|---|---|
| **Deterministic policy** | Classification (Approved / Escalate / Rejected) from numbers and if→then criteria — bureau-style scores, registry status, VAT validity, PEP flags, media severity. Same inputs → same gate. |
| **Automated externalities** | Multidimensional open-web search (fraud, financial distress, regulatory, environmental, PEP, etc.) with trusted-domain URLs and verbatim quotes — including explicit zeros (`news-PEP = 0` ≠ cleared). |
| **AI reflection** | Connects hard facts with grounded news; surfaces evident vs non-evident risk and investigation areas. **Cannot** change the classification. |
| **Human-in-the-loop** | Assisted draft only. Commercial and compliance judgment stay with people. |

In short: **automate retrieval and structuring; keep decision rights with the bank.**

---

## Why banks should care now

Regulators still require meaningful human intervention for high-stakes KYB / credit-adjacent decisions. That will not disappear overnight. But cost pressure and improving model reliability are moving the trust frontier. Institutions that wait until automation is “fully allowed” rebuild under stress. Institutions that **fabricate the infrastructure now** — deterministic connectors to financial/registry sources, auditable news fan-out, grounded reflection, evaluation and override patterns — can raise automation later **along a path they already operate**.

This project is that skeleton: not a chatbot that approves counterparties, but a **repeatable research fabric** for partner and merchant first-pass screening.

---

## What’s in the dossier

1. General data — ownership, legal status, key people  
2. Financial health — revenue / EBITDA trend signals  
3. External red flags — coverage by risk dimension + grounded articles  
4. Classification — deterministic recommendation  
5. AI reflection — narrative that binds facts to evidence  

Explore **Criteria** (rule matrix) and **Externalities** (search taxonomy) in the live UI.

---

## Stack (prototype)

- **Backend:** Python, FastAPI, deterministic policy engine, DuckDuckGo + trust filter, optional LLM narrative (e.g. Groq)  
- **Frontend:** React + Vite  
- **Deploy:** single Docker service (API + UI)

Cut corners are intentional and labelled (mock bureau/registry payloads where live contracts are not wired). The architecture is what transfers to production APIs and private LLM paths.

---

## Run locally

```bash
# API
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # set GROQ_API_KEY if you want live narrative
uvicorn main:app --host 127.0.0.1 --port 8000

# UI (another terminal)
cd frontend
npm install
npm run dev
```

UI: http://127.0.0.1:5173 · API health: http://127.0.0.1:8000/health

---

## Recommendation (v1)

**Fully assisted draft with mandatory human review** — not straight-through processing.

That is the honest posture for KYB and credit-adjacent partner screening under current rules. It is also how a digital bank builds the option to automate further when cost, model quality, and supervisory trust allow — without gambling decision rights on an unconstrained LLM.
