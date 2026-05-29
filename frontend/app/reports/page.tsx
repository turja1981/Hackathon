'use client';

import { useEffect, useState, useCallback } from 'react';
import { ShieldCheck, Eye, BarChart3, AlertTriangle, CheckCircle, XCircle, Loader2, RefreshCw, type LucideIcon } from 'lucide-react';
import { clsx } from 'clsx';
import { api } from '@/lib/api';
import type { PIIReport, RAGASReport, GuardrailReport } from '@/lib/types';

type TabId = 'pii' | 'ragas' | 'guardrails';

const TABS: { id: TabId; label: string; icon: LucideIcon }[] = [
  { id: 'pii', label: 'PII Masking', icon: Eye },
  { id: 'ragas', label: 'RAG Evaluation', icon: BarChart3 },
  { id: 'guardrails', label: 'Responsible AI', icon: ShieldCheck },
];

function scoreLabel(score: number): { label: string; color: string } {
  if (score >= 0.85) return { label: 'Excellent', color: 'text-green-400' };
  if (score >= 0.70) return { label: 'Good', color: 'text-yellow-400' };
  return { label: 'Fair', color: 'text-orange-400' };
}

function ScoreCard({ label, value, subtitle }: { label: string; value: number; subtitle?: string }) {
  const pct = Math.round(value * 100);
  const { label: qualityLabel, color } = scoreLabel(value);
  return (
    <div className="glass p-5 rounded-xl flex flex-col gap-2">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={clsx('text-4xl font-bold', color)}>{pct}%</p>
      <p className={clsx('text-sm font-medium', color)}>{qualityLabel}</p>
      {subtitle && <p className="text-xs text-gray-600">{subtitle}</p>}
    </div>
  );
}

function StatCard({ label, value, color = 'text-gray-100' }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="glass p-4 rounded-xl flex flex-col gap-1">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={clsx('text-3xl font-bold', color)}>{value}</p>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="text-center py-16 text-gray-600">
      <BarChart3 size={40} className="mx-auto mb-3 opacity-30" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return ts;
  }
}

// ─── PII Tab ──────────────────────────────────────────────────────────────────

function PIITab({ data }: { data: PIIReport | null }) {
  if (!data) return <EmptyState message="Loading PII data..." />;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Queries Scanned" value={data.total_queries_scanned} />
        <StatCard
          label="Queries With PII"
          value={data.queries_with_pii}
          color={data.queries_with_pii > 0 ? 'text-orange-400' : 'text-green-400'}
        />
        <StatCard
          label="PII Rate"
          value={`${data.pii_rate_pct}%`}
          color={data.pii_rate_pct > 10 ? 'text-red-400' : data.pii_rate_pct > 0 ? 'text-yellow-400' : 'text-green-400'}
        />
        <StatCard
          label="Backend"
          value={data.backend === 'presidio' ? 'Presidio' : data.backend === 'regex' ? 'Regex' : data.backend}
          color={data.backend === 'presidio' ? 'text-sky-400' : 'text-yellow-400'}
        />
      </div>

      {Object.keys(data.entity_type_counts).length > 0 && (
        <div className="glass p-5 rounded-xl">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Entity Type Distribution</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(data.entity_type_counts)
              .sort((a, b) => b[1] - a[1])
              .map(([type, count]) => (
                <span
                  key={type}
                  className="px-2.5 py-1 rounded-full text-xs font-medium bg-orange-500/15 text-orange-300 border border-orange-500/20"
                >
                  {type} <span className="font-bold">{count}</span>
                </span>
              ))}
          </div>
        </div>
      )}

      {data.recent_events.length === 0 ? (
        <EmptyState message="Run a search to generate PII evaluation data" />
      ) : (
        <div className="glass rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-white/10">
            <h3 className="text-sm font-semibold text-gray-300">Recent Events (last 20)</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="text-left px-4 py-2.5 text-gray-500 font-medium">Time</th>
                  <th className="text-left px-4 py-2.5 text-gray-500 font-medium">Query Preview</th>
                  <th className="text-center px-4 py-2.5 text-gray-500 font-medium">PII Types</th>
                  <th className="text-center px-4 py-2.5 text-gray-500 font-medium">Masked?</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_events.map((ev, i) => (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/2">
                    <td className="px-4 py-2.5 text-gray-500 text-xs whitespace-nowrap">{formatTime(ev.timestamp)}</td>
                    <td className="px-4 py-2.5 text-gray-300 max-w-xs truncate">{ev.query_preview}</td>
                    <td className="px-4 py-2.5 text-center">
                      {ev.entity_types.length === 0 ? (
                        <span className="text-gray-600 text-xs">none</span>
                      ) : (
                        <div className="flex flex-wrap gap-1 justify-center">
                          {ev.entity_types.map(t => (
                            <span key={t} className="px-1.5 py-0.5 rounded text-xs bg-orange-500/10 text-orange-300">{t}</span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-center">
                      {ev.masked ? (
                        <span className="inline-flex items-center gap-1 text-xs text-orange-400">
                          <AlertTriangle size={12} /> Masked
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs text-green-400">
                          <CheckCircle size={12} /> Clean
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── RAGAS Tab ────────────────────────────────────────────────────────────────

function RAGASTab({ data }: { data: RAGASReport | null }) {
  if (!data) return <EmptyState message="Loading RAGAS data..." />;

  const hasScores = data.total_evaluations > 0;

  return (
    <div className="space-y-6">
      {!hasScores ? (
        <EmptyState message="Run a search or summarize query to generate RAG evaluation data" />
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <ScoreCard label="Faithfulness" value={data.avg_scores.faithfulness} subtitle="Claims grounded in context" />
            <ScoreCard label="Answer Relevancy" value={data.avg_scores.answer_relevancy} subtitle="How relevant to the query" />
            <ScoreCard label="Context Precision" value={data.avg_scores.context_precision} subtitle="Retrieved paper relevance" />
            <ScoreCard label="Overall Score" value={data.avg_scores.overall} subtitle="Weighted composite" />
          </div>

          <div className="glass p-4 rounded-xl flex items-center gap-3">
            <BarChart3 size={16} className="text-sky-400 shrink-0" />
            <p className="text-sm text-gray-400">
              Based on <span className="text-sky-400 font-semibold">{data.total_evaluations}</span> evaluations using LLM-as-judge scoring
            </p>
          </div>

          <div className="glass rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-white/10">
              <h3 className="text-sm font-semibold text-gray-300">Recent Evaluations (last 20)</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left px-4 py-2.5 text-gray-500 font-medium">Time</th>
                    <th className="text-left px-4 py-2.5 text-gray-500 font-medium">Query</th>
                    <th className="text-center px-4 py-2.5 text-gray-500 font-medium">Faith.</th>
                    <th className="text-center px-4 py-2.5 text-gray-500 font-medium">Ans. Rel.</th>
                    <th className="text-center px-4 py-2.5 text-gray-500 font-medium">Ctx. Prec.</th>
                    <th className="text-center px-4 py-2.5 text-gray-500 font-medium">Overall</th>
                    <th className="text-center px-4 py-2.5 text-gray-500 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_evals.map((ev, i) => (
                    <tr key={i} className="border-b border-white/5 hover:bg-white/2">
                      <td className="px-4 py-2.5 text-gray-500 text-xs whitespace-nowrap">{formatTime(ev.timestamp)}</td>
                      <td className="px-4 py-2.5 text-gray-300 max-w-xs truncate">{ev.query_preview}</td>
                      {[ev.faithfulness, ev.answer_relevancy, ev.context_precision, ev.overall_score].map((v, j) => {
                        const { color } = scoreLabel(v);
                        return (
                          <td key={j} className={clsx('px-4 py-2.5 text-center font-semibold', color)}>
                            {Math.round(v * 100)}%
                          </td>
                        );
                      })}
                      <td className="px-4 py-2.5 text-center">
                        <span className={clsx(
                          'text-xs px-2 py-0.5 rounded-full border',
                          ev.status === 'evaluated' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                          ev.status === 'mock' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                          'bg-gray-500/10 text-gray-400 border-gray-500/20'
                        )}>
                          {ev.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Guardrails Tab ───────────────────────────────────────────────────────────

function GuardrailsTab({ data }: { data: GuardrailReport | null }) {
  if (!data) return <EmptyState message="Loading guardrail data..." />;

  const hasData = data.total_validations > 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Validations" value={data.total_validations} />
        <StatCard
          label="Pass Rate"
          value={`${data.pass_rate_pct}%`}
          color={data.pass_rate_pct >= 90 ? 'text-green-400' : data.pass_rate_pct >= 70 ? 'text-yellow-400' : 'text-red-400'}
        />
        <StatCard label="Passed" value={data.passed ?? 0} color="text-green-400" />
        <StatCard label="Failed" value={data.failed ?? 0} color={data.failed > 0 ? 'text-red-400' : 'text-gray-400'} />
      </div>

      {!hasData ? (
        <EmptyState message="Run a summarize query to generate guardrail validation data" />
      ) : (
        <>
          {Object.keys(data.violation_breakdown).length > 0 && (
            <div className="glass p-5 rounded-xl">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">Violation Breakdown</h3>
              <div className="space-y-2">
                {Object.entries(data.violation_breakdown)
                  .sort((a, b) => b[1] - a[1])
                  .map(([violation, count]) => (
                    <div key={violation} className="flex items-center justify-between">
                      <span className="text-sm text-gray-400">{violation}</span>
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-500/15 text-red-400 border border-red-500/20">
                        {count}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          <div className="glass rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-white/10">
              <h3 className="text-sm font-semibold text-gray-300">Recent Validations (last 20)</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left px-4 py-2.5 text-gray-500 font-medium">Time</th>
                    <th className="text-left px-4 py-2.5 text-gray-500 font-medium">Agent</th>
                    <th className="text-left px-4 py-2.5 text-gray-500 font-medium">Query</th>
                    <th className="text-center px-4 py-2.5 text-gray-500 font-medium">Status</th>
                    <th className="text-left px-4 py-2.5 text-gray-500 font-medium">Violations</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_events.map((ev, i) => (
                    <tr key={i} className="border-b border-white/5 hover:bg-white/2">
                      <td className="px-4 py-2.5 text-gray-500 text-xs whitespace-nowrap">{formatTime(ev.timestamp)}</td>
                      <td className="px-4 py-2.5 text-gray-400 text-xs">{ev.agent}</td>
                      <td className="px-4 py-2.5 text-gray-300 max-w-xs truncate">{ev.query_preview}</td>
                      <td className="px-4 py-2.5 text-center">
                        {ev.passed ? (
                          <span className="inline-flex items-center gap-1 text-xs text-green-400">
                            <CheckCircle size={12} /> Pass
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs text-red-400">
                            <XCircle size={12} /> Fail
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2.5">
                        {ev.violations.length === 0 ? (
                          <span className="text-gray-600 text-xs">none</span>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {ev.violations.map((v, vi) => (
                              <span key={vi} className="px-1.5 py-0.5 rounded text-xs bg-red-500/10 text-red-300 border border-red-500/15">
                                {v.split(':')[0]}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<TabId>('pii');
  const [piiData, setPiiData] = useState<PIIReport | null>(null);
  const [ragasData, setRagasData] = useState<RAGASReport | null>(null);
  const [guardrailData, setGuardrailData] = useState<GuardrailReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [pii, ragas, guard] = await Promise.allSettled([
        api.getPIIReport(),
        api.getRAGASReport(),
        api.getGuardrailReport(),
      ]);
      if (pii.status === 'fulfilled') setPiiData(pii.value);
      if (ragas.status === 'fulfilled') setRagasData(ragas.value);
      if (guard.status === 'fulfilled') setGuardrailData(guard.value);
      setLastRefresh(new Date());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30_000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-2">
            <ShieldCheck className="text-sky-400" size={24} />
            Responsible AI Reports
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            PII masking audit, RAG pipeline quality scores, and guardrail validations. Auto-refreshes every 30s.
          </p>
        </div>
        <button
          onClick={fetchAll}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-gray-400 hover:text-gray-200 hover:bg-white/5 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          {lastRefresh ? `Updated ${lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Refresh'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/10">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={clsx(
              'flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px',
              activeTab === id
                ? 'border-sky-400 text-sky-400'
                : 'border-transparent text-gray-500 hover:text-gray-300',
            )}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {loading && !piiData && !ragasData && !guardrailData ? (
          <div className="flex items-center justify-center py-20 text-gray-500 gap-2">
            <Loader2 size={18} className="animate-spin" />
            Loading reports…
          </div>
        ) : (
          <>
            {activeTab === 'pii' && <PIITab data={piiData} />}
            {activeTab === 'ragas' && <RAGASTab data={ragasData} />}
            {activeTab === 'guardrails' && <GuardrailsTab data={guardrailData} />}
          </>
        )}
      </div>
    </div>
  );
}
