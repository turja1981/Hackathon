'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { GitBranch, Loader2 } from 'lucide-react';
import SearchBar from '@/components/SearchBar';
import ResearchGapCard from '@/components/ResearchGapCard';
import AgentStatusTracker from '@/components/AgentStatusTracker';
import KpiMetricsBar from '@/components/KpiMetricsBar';
import { api } from '@/lib/api';
import { useSSE } from '@/lib/hooks/useSSE';
import type { ResearchGap, KpiMetrics } from '@/lib/types';

function GapsContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || '';

  const [query, setQuery] = useState(initialQuery);
  const [submitted, setSubmitted] = useState(false);
  const { status, events, result, start } = useSSE();

  const gaps = (result as { research_gaps?: ResearchGap[] } | null)?.research_gaps ?? [];
  const kpiMetrics = (result as { kpi_metrics?: KpiMetrics } | null)?.kpi_metrics ?? null;

  const handleDetect = async (q: string) => {
    setQuery(q);
    setSubmitted(true);
    const job = await api.detectGaps({ query: q, max_gaps: 5 });
    start(job.job_id);
  };

  useEffect(() => {
    if (initialQuery && !submitted) {
      handleDetect(initialQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isLoading = status === 'connecting' || status === 'streaming';

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-100 mb-2 flex items-center gap-2">
          <GitBranch className="text-orange-400" size={24} />
          Research Gap Discovery
        </h1>
        <p className="text-gray-500 text-sm mb-5">
          Identify unexplored research connections and high-value white spaces in the literature.
        </p>
        <SearchBar
          onSearch={handleDetect}
          loading={isLoading}
          placeholder='e.g. "CRISPR neurodegeneration treatment"'
          initialValue={query}
        />
      </div>

      {submitted && (
        <div className="grid lg:grid-cols-4 gap-6">
          <aside className="lg:col-span-1">
            <AgentStatusTracker status={status} events={events} />
          </aside>

          <div className="lg:col-span-3 space-y-4">
            {isLoading && gaps.length === 0 && (
              <div className="flex items-center gap-2 text-gray-400">
                <Loader2 size={18} className="animate-spin" />
                Analyzing literature for research gaps…
              </div>
            )}

            {kpiMetrics && (
              <KpiMetricsBar metrics={kpiMetrics} showGaps />
            )}

            {gaps.length > 0 && (
              <>
                <p className="text-sm text-gray-500">
                  {gaps.length} research gaps identified for &ldquo;{query}&rdquo;
                </p>
                {gaps.map((g, i) => (
                  <ResearchGapCard key={g.id} gap={g} index={i} />
                ))}
              </>
            )}

            {status === 'done' && gaps.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <GitBranch size={36} className="mx-auto mb-3 opacity-30" />
                <p>No gaps found. Try a more specific research topic.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {!submitted && (
        <div className="text-center py-16 space-y-3 text-gray-600">
          <GitBranch size={48} className="mx-auto opacity-20" />
          <p className="text-lg">Enter a research topic to discover unexplored opportunities</p>
          <p className="text-sm">Try: &ldquo;pancreatic cancer immunotherapy combination therapy&rdquo;</p>
        </div>
      )}
    </div>
  );
}

export default function GapsPage() {
  return (
    <Suspense fallback={<div className="text-gray-400 py-8 text-center">Loading…</div>}>
      <GapsContent />
    </Suspense>
  );
}
