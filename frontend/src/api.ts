import type {
  AiLabDocument,
  ExternalitiesDocument,
  FinalRecommendationBrief,
  PolicyRulesDocument,
  ResearchResponse,
} from './types/dossier'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `Request failed (${res.status})`)
  }
  return (await res.json()) as T
}

export async function fetchCompanies(): Promise<string[]> {
  const data = await getJson<{ companies: string[] }>(`${API_BASE}/api/companies`)
  return data.companies
}

export async function fetchResearch(company: string): Promise<ResearchResponse> {
  return getJson(
    `${API_BASE}/api/research?company=${encodeURIComponent(company)}`,
  )
}

export async function fetchFinalBrief(
  company: string,
): Promise<FinalRecommendationBrief> {
  return getJson(
    `${API_BASE}/api/research/final-brief?company=${encodeURIComponent(company)}`,
  )
}

export async function fetchPolicyRules(): Promise<PolicyRulesDocument> {
  return getJson(`${API_BASE}/api/policy-rules`)
}

export async function fetchExternalities(): Promise<ExternalitiesDocument> {
  return getJson(`${API_BASE}/api/externalities`)
}

export async function fetchAiConfig(): Promise<{
  ai_provider: string
  ai_model: string
  connected?: boolean
  ux_label?: string
  note?: string
}> {
  return getJson(`${API_BASE}/api/ai-config`)
}

export async function fetchAiLab(company?: string): Promise<AiLabDocument> {
  const q = company?.trim()
    ? `?company=${encodeURIComponent(company.trim())}`
    : ''
  return getJson(`${API_BASE}/api/ai-lab${q}`)
}
