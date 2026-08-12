# Applied AI Analyst — Technical Case Study

## Case: Sales & Partner Research Assistant

### Business Context

NorthBank's Partnerships team regularly evaluates prospective merchant and business partners before moving forward with a deal. Before a first serious conversation, someone on the team needs to answer questions like:

- Who owns and controls this company? What's its legal structure?
- What do we know about its financial health (revenue, credit history, payment behaviour)?
- Are there any red flags — negative news, litigation, sanctions or PEP (Politically Exposed Person) exposure, unusual ownership patterns?
- Is this a company we should be excited about, cautious about, or need to escalate to compliance before proceeding?

Today, this research is done manually: someone searches company registries, credit reference sources, news, and sanctions lists across several separate tools, then writes up a summary. It typically takes **1 hour per company**, and the quality and depth vary a lot depending on who does it and how much time they have.

The Partnerships team has asked whether AI could automatically produce a first-pass research dossier, so their people can spend their time on judgment and relationship-building instead of manual lookups.

---

### Your Assignment

Treat this the way you would a real opportunity that lands on your desk. We're less interested in a polished tool and much more interested in how you think and how you work.

1. **Analyse the problem.** Based on the context above, define the use case clearly: who is the user, what do they need as input and output, and — importantly — what should be explicitly out of scope for a first version?

2. **Assess feasibility, data readiness and risk.** What information is realistically obtainable (public registries, news, financial data), what isn't, and where would an AI system be prone to getting things wrong (outdated data, hallucination, confusing similarly-named companies, unverifiable claims)? What controls or disclaimers would a real version of this need, given the output could influence a business decision?

3. **Build a lightweight prototype.** Given a company (name, or a short profile), your prototype should produce a structured research dossier covering at minimum: legal/ownership structure, a financial health signal, and a risk/compliance signal (e.g. adverse media, sanctions-type flags). It should indicate its sources and flag anything it's unsure about or couldn't verify — don't just produce a confident-sounding wall of text.

4. **Define success metrics and acceptance criteria.** How would you know this is actually good enough to save the team time without introducing new risk?

5. **Make a recommendation.** Should this be a fully assisted draft that always needs human review, a partially automated workflow, or something else? Justify it.

You're free to use any AI tools, models, or tech stack you're comfortable with (Claude, Claude Code, Cursor, ChatGPT, Bedrock, Python, TypeScript, notebooks, whatever gets you there) — there's no "correct" stack.

---

### Scope & Constraints

- Use only publicly available information about real companies, or a fictional sample pack. Do not attempt to access any real internal NorthBank or customer data — you won't have access to any, and none is needed for this exercise.
- This is a prototype to demonstrate your approach, not a production-grade compliance tool. It's fine (and expected) to cut corners — just be explicit about which corners you cut and why.
- Be thoughtful about how you handle information that could be reputationally sensitive about real companies — if that's a concern, feel free to demo primarily with a fictional pack.

---

### Deliverables

We're not expecting a finished product — we're expecting clear thinking, sound prioritisation, and a prototype that demonstrates the core value convincingly.

1. A short (**≈1 page**) write-up covering your use case definition, feasibility/risk assessment, and automation recommendation.
2. A working prototype you can demo live.
3. A short presentation (slides optional) for the technical interview covering: your understanding of the problem, your approach, a live demo, key risks/limitations, success metrics, and your recommendation for next steps toward production.
