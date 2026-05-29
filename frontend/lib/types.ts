// ---------------------------------------------------------------------------
// Domain types
// ---------------------------------------------------------------------------

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  journal?: string;
  year?: number;
  doi?: string;
  abstract: string;
  keywords: string[];
  publication_date?: string;
  score?: number;
  rerank_score?: number;
}

export interface ReasoningStep {
  paper_id: string;
  paper_title: string;
  finding: string;
  relevance: string;
}

export interface EvidenceScore {
  overall_score: number;
  supporting_papers_count: number;
  recency_score: number;
  agreement_score: number;
  citation_impact_score: number;
  label: 'Strong' | 'Moderate' | 'Weak';
}

export interface ResearchGap {
  id: string;
  gap_description: string;
  area: string;
  opportunity_level: 'High' | 'Medium' | 'Low';
  missing_connections: string[];
  suggested_experiments: string[];
  novelty_score: number;
  related_paper_ids: string[];
}

export interface CopilotMessage {
  role: 'user' | 'assistant';
  content: string;
  papers?: Paper[];
  gaps?: ResearchGap[];
  hypotheses?: Hypothesis[];
  timestamp: string;
}

export interface Hypothesis {
  id: string;
  hypothesis: string;
  rationale: string;
  experiments: string[];
  novelty_score: number;
  impact_area: string;
  supporting_paper_ids: string[];
  reasoning_path?: ReasoningStep[];
  evidence_score?: EvidenceScore;
  critic_challenge?: string;
}

// ---------------------------------------------------------------------------
// API request / response types
// ---------------------------------------------------------------------------

export interface SearchRequest {
  query: string;
  max_results?: number;
  use_semantic?: boolean;
}

export interface SearchResponse {
  query: string;
  papers: Paper[];
  total: number;
  job_id?: string;
}

export interface SummarizeRequest {
  query: string;
  paper_ids?: string[];
  max_papers?: number;
}

export interface HypothesizeRequest {
  query: string;
  paper_ids?: string[];
  num_hypotheses?: number;
  focus_area?: string;
}

export interface JobStartResponse {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  stream_url: string;
}

export interface JobResult {
  job_id: string;
  status: string;
  result?: {
    type: 'search' | 'summarize' | 'hypothesize' | 'gaps';
    query: string;
    papers?: Paper[];
    total?: number;
    summary?: string;
    key_findings?: string[];
    citations?: Citation[];
    papers_used?: Paper[];
    hypotheses?: Hypothesis[];
    context_summary?: string;
    research_gaps?: ResearchGap[];
    papers_analyzed?: number;
    kpi_metrics?: KpiMetrics;
  };
  error?: string;
}

export interface IngestRequest {
  papers: Omit<Paper, 'id' | 'score' | 'rerank_score'>[];
}

export interface Citation {
  paper_id: string;
  paper_title: string;
  claim: string;
}

export interface KpiMetrics {
  processing_time_ms: number;
  processing_time_label: string;
  time_reduction_pct: number;
  time_saved_label: string;
  kpi_target_met: boolean;
  avg_novelty_score?: number;
  avg_novelty_pct?: number;
  novelty_target_met?: boolean;
  gap_count?: number;
  gap_target_met?: boolean;
  gap_detection_rate?: number;
}

export interface AdoptionMetrics {
  papers_processed: number;
  hypotheses_generated: number;
  gaps_identified: number;
  queries_total: number;

}

export type AgentName = 'orchestrator' | 'search' | 'ranker' | 'summarizer' | 'hypothesis' | 'gap_detector' | 'critic';

export interface FeedbackRequest {
  job_id: string;
  item_id: string;
  feedback_type: 'accept' | 'reject' | 'flag';
  accuracy_rating?: number;  // 1-10 for KPI 2
  comment?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  llm_configured: boolean;
  vector_store_loaded: boolean;
  paper_count: number;
  mock_mode: boolean;
}

// ---------------------------------------------------------------------------
// SSE / streaming types
// ---------------------------------------------------------------------------

export interface AgentEvent {
  agent: AgentName;
  status: 'running' | 'completed' | 'failed';
  message: string;
  data?: Record<string, unknown>;
  timestamp?: string;
}

export interface SSEDoneEvent {
  job_id: string;
  status: string;
  result?: JobResult['result'];
  error?: string;
}
