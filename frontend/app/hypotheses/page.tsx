'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Lightbulb, Loader2 } from 'lucide-react';
import SearchBar from '@/components/SearchBar';
import HypothesisPanel from '@/components/HypothesisPanel';
import AgentStatusTracker from '@/components/AgentStatusTracker';
import { api } from '@/lib/api';
import { useSSE } from '@/lib/hooks/useSSE';
import type { Hypothesis } from '@/lib/types';

function HypothesesContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const initialPaperIds = searchParams.get('paperIds')?.split(',').filter(Boolean) ?? [];

  const [query, setQuery] = useState(initialQuery);
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const { status, events, result, start } = useSSE();

  const hypotheses = (result as { hypotheses?: Hypothesis[] } | null)?.hypotheses ?? [];
  const contextSummary = (result as { context_summary?: string } | null)?.context_summary ?? '';

  const handleGenerate = async (q: string) => {
    setQuery(q);
    setSubmitted(true);
    const job = await api.hypothesize({
      query: q,
      paper_ids: initialPaperIds.length > 0 ? initialPaperIds : undefined,
      num_hypotheses: 3,
    });
    setJobId(job.job_id);
    start(job.job_id);
  };

  useEffect(() => {
    if (initialQuery && !submitted) {
      handleGenerate(initialQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isLoading = status === 'connecting' || status === 'streaming';

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-100 mb-2 flex items-center gap-2">
          <Lightbulb className="text-yellow-400" size={24} />
          Hypothesis Explorer
        </h1>
        <p className="text-gray-500 text-sm mb-5">
          Enter a research topic to generate novel, testable hypotheses with AI.
        </p>
        <SearchBar
          onSearch={handleGenerate}
          loading={isLoading}
          placeholder='e.g. "gut microbiome and cancer immunotherapy"'
          initialValue={query}
        />
      </div>

      {submitted && (
        <div className="grid lg:grid-cols-4 gap-6">
          {/* Agent tracker sidebar */}
          <aside className="lg:col-span-1">
            <AgentStatusTracker status={status} events={events} />
          </aside>

          {/* Hypotheses */}
          <div className="lg:col-span-3 space-y-4">
            {isLoading && hypotheses.length === 0 && (
              <div className="flex items-center gap-2 text-gray-400">
                <Loader2 size={18} className="animate-spin" />
                Generating hypotheses…
              </div>
            )}

            {contextSummary && (
              <div className="glass p-4 text-sm text-gray-400 leading-relaxed">
                <span className="font-semibold text-gray-300">Context: </span>
                {contextSummary.slice(0, 300)}…
              </div>
            )}

            {hypotheses.length > 0 && (
              <>
                <p className="text-sm text-gray-500">{hypotheses.length} hypotheses generated for &ldquo;{query}&rdquo;</p>
                {hypotheses.map((h, i) => (
                  <HypothesisPanel key={h.id} hypothesis={h} jobId={jobId ?? undefined} index={i} />
                ))}
              </>
            )}

            {status === 'done' && hypotheses.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <Lightbulb size={36} className="mx-auto mb-3 opacity-30" />
                <p>No hypotheses generated. Try a different query.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {!submitted && (
        <div className="text-center py-16 space-y-3 text-gray-600">
          <Lightbulb size={48} className="mx-auto opacity-20" />
          <p className="text-lg">Enter a research topic above to generate hypotheses</p>
          <p className="text-sm">Try: &ldquo;CRISPR gene editing for neurodegeneration&rdquo;</p>
        </div>
      )}
    </div>
  );
}

export default function HypothesesPage() {
  return (
    <Suspense fallback={<div className="text-gray-400 py-8 text-center">Loading…</div>}>
      <HypothesesContent />
    </Suspense>
  );
}
