'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { FileText, Loader2 } from 'lucide-react';
import SearchBar from '@/components/SearchBar';
import PaperCard from '@/components/PaperCard';
import AgentStatusTracker from '@/components/AgentStatusTracker';
import { api } from '@/lib/api';
import { useSSE } from '@/lib/hooks/useSSE';
import type { Paper } from '@/lib/types';

function SearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || '';

  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [currentQuery, setCurrentQuery] = useState(initialQuery);
  const { status, events, result, start } = useSSE();

  const runSearch = async (q: string) => {
    setLoading(true);
    setSearched(true);
    setPapers([]);
    setCurrentQuery(q);
    router.replace(`/search?q=${encodeURIComponent(q)}`, { scroll: false });

    try {
      // Fast synchronous search (no LLM)
      const res = await api.search({ query: q, max_results: 10 });
      setPapers(res.papers);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  // If query param is present on mount, auto-search
  useEffect(() => {
    if (initialQuery) runSearch(initialQuery);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Use SSE result papers if available (LLM-reranked)
  const displayPapers = (result?.papers ?? papers) as Paper[];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-100 mb-4">Search Papers</h1>
        <SearchBar onSearch={runSearch} loading={loading} initialValue={currentQuery} />
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        {/* Sidebar: agent tracker */}
        {status !== 'idle' && (
          <aside className="lg:col-span-1">
            <AgentStatusTracker status={status} events={events} />
          </aside>
        )}

        {/* Results */}
        <div className={status !== 'idle' ? 'lg:col-span-3' : 'lg:col-span-4'}>
          {loading && (
            <div className="flex items-center gap-2 text-gray-400">
              <Loader2 size={18} className="animate-spin" />
              Searching…
            </div>
          )}

          {searched && !loading && displayPapers.length === 0 && (
            <div className="text-center py-16 text-gray-500">
              <FileText size={40} className="mx-auto mb-3 opacity-30" />
              <p>No papers found for &quot;{currentQuery}&quot;</p>
            </div>
          )}

          {displayPapers.length > 0 && (
            <div className="space-y-3">
              <p className="text-sm text-gray-500">
                {displayPapers.length} result{displayPapers.length !== 1 ? 's' : ''} for &ldquo;{currentQuery}&rdquo;
              </p>
              {displayPapers.map(p => (
                <PaperCard key={p.id} paper={p} showScore />
              ))}
            </div>
          )}
        </div>
      </div>
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
