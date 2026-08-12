# NorthBank Partner Research Assistant — Case Write-up (~1 page)

**Candidate:** Juan Pablo Zúñiga Hidalgo  
**Case:** Applied AI Analyst — Sales & Partner Research Assistant  
**Live demo:** https://northbank.onrender.com

---

## 1. Why this problem matters now (bank context)

NorthBank is scaling as a regulated Nordic challenger (Sweden, Norway, Finland; EU expansion stated as priority). Public signals point to the same operating pressure: grow merchants and end-users while keeping **cost-to-serve** competitive in a digital market where automation sets the pace.

NorthBank's CEO (Q2 2025 public commentary) framed AI pragmatically: *“scalability through AI… where it truly adds value”*, with priority on **internal capabilities and process acceleration**, not customer-facing gimmicks. Engineering messaging (AWS / cloud-only journey) already emphasises automation for compliance-adjacent work (e.g. AML-style screening) and product velocity. Job scopes for **Applied AI Analyst** and **AI Engineer** reinforce the mandate: find bottlenecks, prototype with controls, prefer **assisted or partial automation** over unsupervised decisions in regulated flows.

Partnerships research fits that mandate tightly. Today, evaluating a prospective merchant/partner takes ~**1 hour** of manual lookups across registries, credit sources, news and sanctions-style checks, with uneven depth. As merchant volume grows (public figures on the order of thousands of merchants / hundreds of thousands of end-users), that manual hour becomes a **throughput and margin problem**: more deals to screen without linear hiring, while residual risk must still be governed.

**Hypothesis:** a first-pass research dossier that compresses lookups into minutes — without pretending to replace compliance judgment — improves Partnerships capacity and protects operating leverage during expansion.

---

## 2. Use case (v1)

| | |
|---|---|
| **User** | NorthBank Partnerships (first serious conversation before a deal) |
| **Input** | Prospective partner company name |
| **Output** | Structured dossier: ownership/legal, financial health signal, external red flags, **deterministic** Classification-Recommendation (Approved / Escalate to compliance / Rejected), plus an AI reflection that connects hard facts with grounded news |
| **Out of scope (v1)** | Auto-approval of deals; live World-Check; production Creditsafe/VIES contracts; board/investor deep-dive beyond CEO; full sanctions graph; unsupervised policy changes by an LLM |

---

## 3. Approach — what should be deterministic vs what AI is for

**Deterministic gates (numbers + if→then criteria).**  
Approval/escalation/rejection must not be an LLM “opinion”. In Nordics, the spine of partner screening is obtainable from financial/registry-style sources (e.g. Creditsafe-shaped bureau opinion, Allabolag/Roaring-shaped company registry & statements, EU VIES VAT validity, status codes such as bankruptcy/reconstruction, PEP indicators, connected bankruptcies). The prototype encodes these as explicit rules (Criteria page): same inputs → same class, before any model call.

**Automated multidimensional “externalities”.**  
Adverse media is not one Google search. Risk themes — fraud / money laundering, litigation, environmental, regulatory, political/PEP, cyber, etc. — can be **fan-out queried** for the company legal name and (in this mockup) the CEO, filtered to trusted domains, requiring URL + verbatim quote, and reported as coverage including zeros (`news-PEP = 0` ≠ cleared). That turns “internet research” into a repeatable pipeline.

**AI as the connecting brain — not the judge.**  
The valuable GenAI step is reflection: connect registry/bureau facts with grounded news, separate evident vs non-evident risk, and leave investigation areas for humans. Classification stays locked. This matches NorthBank’s stated AI posture (support strategy; internal leverage) and banking control expectations.

---

## 4. Feasibility, risks, controls

| Obtainable now | Hard / later | Failure modes |
|---|---|---|
| Public registries & VAT checks (API or mock) | Live PEP/sanctions providers | Hallucinated numbers/owners/news |
| Bureau-style credit signals | Full ownership graphs | Homonyms / wrong entity |
| Trusted-domain news with quotes | Real-time global media completeness | Stale filings; “no hit” ≠ clean |

**Controls in the prototype:** policy engine owns the class; LLM cannot change it; sources and unsure flags surfaced; human review required; cut corners labelled (mock bureau/registry where live keys unavailable).

---

## 5. Success metrics & acceptance

- **Time:** first-pass dossier in **&lt; 5 minutes** median (vs ~60 min manual).  
- **Coverage:** ownership + finance + externality coverage (incl. explicit zeros) + sources.  
- **Control:** 0% of runs where LLM alters Approved/Escalate/Rejected.  
- **Quality (pilot):** Partnerships rates ≥80% of drafts “useful to start judgment”; critical false “Approved” on known hard-fail cases = 0 in gold set.  
- **Adoption:** used before first serious partner conversation in pilot segment.

---

## 6. Recommendation & future vision

**Today — fully assisted draft with mandatory human review.**  
Regulation and governance still require a human in the loop for decisions that can affect counterparties and the bank’s risk profile. Automate **retrieval and structuring**; keep **decision rights** with Partnerships/Compliance. That is the correct v1 posture — and it is also how you *prepare* for what comes next.

**Tomorrow — cost pressure + rising model reliability will push the trust frontier.**  
In a few years — perhaps sooner than many banks plan for — operating margins will force more of the partner-screening workflow onto machines. At the same time, foundation models will fail less often, grounding and evaluation will tighten hallucinations, and supervisors will increasingly accept **well-controlled** AI-assisted decisions. Banks that wait until that moment to “bolt on AI” will rebuild from scratch under stress. Banks that **start fabricating the infrastructure now** will already own: (1) deterministic connectors to Nordic financial institutions and registries; (2) a multidimensional, auditable internet/news search fabric (externalities with sources and zeros); (3) a reflection layer that binds hard data to external evidence; and (4) evaluation, logging, and human-override patterns that can later be relaxed *deliberately* as risk appetite and model quality allow — not overnight, and not without evidence.

**How this prototype synchronises with that future.**  
NorthBank is not “a chatbot that approves merchants.” It is a **skeleton of that future stack**: policy engine for institutional numbers/criteria; automated company (+ CEO) web research as a productised pipeline; LLM as connector, not silent judge; explicit coverage and unsure flags. Each production step — live Creditsafe/Allabolag-class APIs, VIES, licensed PEP/media, Bedrock/private LLM for residency, gold-set regression, board/UBO fan-out — plugs into the same architecture. When regulation and trust catch up, the bank does not invent a new process; it **raises automation along a path it already operates**, with measurable quality gates.

That is the strategic bet: build today the infrastructure that lets deterministic financial data and automated external analysis converge into a progressively more reliable view of a prospective partner — so cost pressure is met with capability, not with panic hiring or uncontrolled GenAI.
