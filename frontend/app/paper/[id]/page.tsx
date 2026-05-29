'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, BookOpen, Loader2, Lightbulb } from 'lucide-react';
import Link from 'next/link';
import PaperCard from '@/components/PaperCard';
import SummaryVisualization from '@/components/SummaryVisualization';
import AgentStatusTracker from '@/components/AgentStatusTracker';
import { api } from '@/lib/api';
import { useSSE } from '@/lib/hooks/useSSE';
import type { Paper } from '@/lib/types';

export default function PaperDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [paper, setPaper] = useState<Paper | null>(null);
  const [summaryTriggered, setSummaryTriggered] = useState(false);
  const { status, events, result, start } = useSSE();

  useEffect(() => {
    api.getPaper(id).then(setPaper).catch(() => null);
  }, [id]);

  const handleSummarize = async () => {
    if (!paper) return;
    setSummaryTriggered(true);
    const job = await api.summarize({ query: paper.title, paper_ids: [paper.id] });
    start(job.job_id);
  };

  const summaryResult = result as { summary?: string; key_findings?: string[]; papers_used?: Paper[] } | null;

  return (
    <div className="space-y-6">
      <Link href="/search" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-300 transition-colors">
        <ArrowLeft size={14} /> Back to search
      </Link>

      {!paper && (
        <div className="flex items-center gap-2 text-gray-400">
          <Loader2 size={18} className="animate-spin" /> Loading paper…
        </div>
      )}

      {paper && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <PaperCard paper={paper} />

            {/* Full abstract */}
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                <BookOpen size={14} />
                Full Abstract
              </h3>
              <p className="text-gray-300 leading-relaxed text-sm">{paper.abstract}</p>
            </div>

            {/* Summary section */}
            {!summaryTriggered ? (
              <button onClick={handleSummarize} className="btn-primary flex items-center gap-2">
                <Lightbulb size={16} /> Generate AI Summary
              </button>
            ) : (
              <AgentStatusTracker status={status} events={events} />
            )}

            {summaryResult?.summary && (
              <SummaryVisualization
                summary={summaryResult.summary}
                keyFindings={summaryResult.key_findings ?? []}
              />
            )}
          </div>

          <aside className="space-y-4">
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Metadata</h3>
              <dl className="space-y-2 text-sm">
                {paper.journal && (
                  <>
                    <dt className="text-gray-600">Journal</dt>
                    <dd className="text-gray-300">{paper.journal}</dd>
                  </>
                )}
                {paper.year && (
                  <>
                    <dt className="text-gray-600 mt-2">Year</dt>
                    <dd className="text-gray-300">{paper.year}</dd>
                  </>
                )}
                {paper.authors.length > 0 && (
                  <>
                    <dt className="text-gray-600 mt-2">Authors</dt>
                    <dd className="text-gray-300">{paper.authors.join(', ')}</dd>
                  </>
                )}
              </dl>
            </div>

            <div className="card">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Generate Hypotheses</h3>
              <p className="text-xs text-gray-500 mb-3">
                Use this paper as context to generate novel research directions.
              </p>
              <Link
                href={`/hypotheses?paperIds=${paper.id}&q=${encodeURIComponent(paper.title)}`}
                className="btn-secondary w-full text-center text-sm"
              >
                Generate Hypotheses →
              </Link>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
