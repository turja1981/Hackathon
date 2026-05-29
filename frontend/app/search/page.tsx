'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { FileText, Loader2 } from 'lucide-react';
import SearchBar from '@/components/SearchBar';
import PaperCard from '@/components/PaperCard';
import AnswerMetricsPanel from '@/components/AnswerMetricsPanel';
import { api } from '@/lib/api';
import type { Paper, ResponsibleAIReport } from '@/lib/types';

function SearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || '';

  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [currentQuery, setCurrentQuery] = useState(initialQuery);
  const [responsibleAI, setResponsibleAI] = useState<ResponsibleAIReport | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const runSearch = async (q: string) => {
    setLoading(true);
    setSearched(true);
    setPapers([]);
    setResponsibleAI(null);
    setErrorMsg(null);
    setCurrentQuery(q);
    router.replace(`/search?q=${encodeURIComponent(q)}`, { scroll: false });

    try {
      const res = await api.search({ query: q, max_results: 10 });
      setPapers(res.papers);
      if (res.responsible_ai) setResponsibleAI(res.responsible_ai);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialQuery) runSearch(initialQuery);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-100 mb-4">Search Papers</h1>
        <SearchBar onSearch={runSearch} loading={loading} initialValue={currentQuery} />
      </div>

      {errorMsg && (
        <div className="glass border-red-500/30 p-4 text-red-400 text-sm rounded-xl">
          {errorMsg}
        </div>
      )}

      {papers.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              {papers.length} result{papers.length !== 1 ? 's' : ''} for &ldquo;{currentQuery}&rdquo;
            </p>
          </div>

          {/* PII + RAGAS traceability panel */}
          {responsibleAI && <AnswerMetricsPanel report={responsibleAI} />}

          {papers.map(p => (
            <PaperCard key={p.id} paper={p} showScore />
          ))}
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-2 text-gray-400">
          <Loader2 size={18} className="animate-spin" />
          Searching…
        </div>
      )}

      {searched && !loading && papers.length === 0 && !errorMsg && (
        <div className="text-center py-16 text-gray-500">
          <FileText size={40} className="mx-auto mb-3 opacity-30" />
          <p>No papers found for &quot;{currentQuery}&quot;</p>
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="text-gray-400 py-8 text-center">Loading…</div>}>
      <SearchContent />
    </Suspense>
  );
}
