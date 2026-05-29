import type {
  AdoptionMetrics,
  FeedbackRequest,
  GuardrailReport,
  HealthResponse,
  HypothesizeRequest,
  IngestRequest,
  JobResult,
  JobStartResponse,
  PIIReport,
  RAGASReport,
  SearchRequest,
  SearchResponse,
  SummarizeRequest,
} from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>('/api/v1/health'),

  search: (body: SearchRequest) =>
    request<SearchResponse>('/api/v1/search', { method: 'POST', body: JSON.stringify(body) }),

  searchAsync: (body: SearchRequest) =>
    request<JobStartResponse>('/api/v1/search/async', { method: 'POST', body: JSON.stringify(body) }),

  summarize: (body: SummarizeRequest) =>
    request<JobStartResponse>('/api/v1/summarize', { method: 'POST', body: JSON.stringify(body) }),

  hypothesize: (body: HypothesizeRequest) =>
    request<JobStartResponse>('/api/v1/hypothesize', { method: 'POST', body: JSON.stringify(body) }),

  getJob: (jobId: string) =>
    request<JobResult>(`/api/v1/jobs/${jobId}`),

  ingest: (body: IngestRequest) =>
    request<{ ingested_count: number; paper_ids: string[] }>('/api/v1/ingest', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getPaper: (paperId: string) =>
    request<import('./types').Paper>(`/api/v1/papers/${paperId}`),

  listPapers: (limit = 20, offset = 0) =>
    request<{ papers: import('./types').Paper[]; total: number }>(`/api/v1/papers?limit=${limit}&offset=${offset}`),

  feedback: (body: FeedbackRequest) =>
    request<{ status: string }>('/api/v1/feedback', { method: 'POST', body: JSON.stringify(body) }),

  detectGaps: (body: { query: string; max_gaps?: number }) =>
    request<JobStartResponse>('/api/v1/gaps', { method: 'POST', body: JSON.stringify(body) }),

  copilot: (body: { message: string; conversation_history?: { role: string; content: string }[] }) =>
    request<JobStartResponse & { detected_intent: string }>('/api/v1/copilot', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getAdoptionMetrics: () =>
    request<AdoptionMetrics>('/api/v1/metrics/adoption'),

  streamUrl: (jobId: string) => `${BASE_URL}/api/v1/stream/${jobId}`,

  getPIIReport: () => request<PIIReport>('/api/v1/reports/pii'),
  getRAGASReport: () => request<RAGASReport>('/api/v1/reports/ragas'),
  getGuardrailReport: () => request<GuardrailReport>('/api/v1/reports/guardrails'),
  getReportsSummary: () => request<{ pii: object; ragas: object; guardrails: object }>('/api/v1/reports/summary'),
};
