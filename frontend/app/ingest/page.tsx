'use client';

import { useState } from 'react';
import { Upload, Plus, Trash2, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
// Use string for authors/keywords in form state for easier text input
interface PaperForm {
  title: string;
  abstract: string;
  authors: string;
  journal: string;
  year: number;
  doi: string;
  keywords: string;
  publication_date: string;
}

const emptyPaper = (): PaperForm => ({
  title: '',
  abstract: '',
  authors: '',
  journal: '',
  year: new Date().getFullYear(),
  doi: '',
  keywords: '',
  publication_date: '',
});

export default function IngestPage() {
  const [papers, setPapers] = useState<PaperForm[]>([emptyPaper()]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const update = (idx: number, field: keyof PaperForm, value: unknown) => {
    setPapers(prev => prev.map((p, i) => (i === idx ? { ...p, [field]: value } : p)));
  };

  const addPaper = () => setPapers(prev => [...prev, emptyPaper()]);
  const removePaper = (idx: number) => setPapers(prev => prev.filter((_, i) => i !== idx));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const valid = papers.filter(p => p.title.trim() && p.abstract.trim());
    if (valid.length === 0) return;

    setLoading(true);
    setResult(null);
    try {
      const res = await api.ingest({
        papers: valid.map(p => ({
          title: p.title,
          abstract: p.abstract,
          authors: p.authors.split(',').map(a => a.trim()).filter(Boolean),
          keywords: p.keywords.split(',').map(k => k.trim()).filter(Boolean),
          journal: p.journal || undefined,
          year: p.year || undefined,
          doi: p.doi || undefined,
          publication_date: p.publication_date || undefined,
        })),
      });
      setResult({ type: 'success', message: `✓ ${res.ingested_count} paper(s) ingested successfully.` });
      setPapers([emptyPaper()]);
    } catch (err) {
      setResult({ type: 'error', message: `Error: ${err instanceof Error ? err.message : 'Unknown error'}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100 mb-2 flex items-center gap-2">
          <Upload size={22} className="text-green-400" />
          Ingest Papers
        </h1>
        <p className="text-gray-500 text-sm">
          Add research papers to the vector store. Abstracts are embedded and indexed for semantic search.
        </p>
      </div>

      {result && (
        <div className={`glass p-4 flex items-center gap-3 ${result.type === 'success' ? 'border-green-500/30 text-green-400' : 'border-red-500/30 text-red-400'}`}>
          {result.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          {result.message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {papers.map((paper, idx) => (
          <div key={idx} className="card space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-400">Paper {idx + 1}</h3>
              {papers.length > 1 && (
                <button type="button" onClick={() => removePaper(idx)} className="text-red-400 hover:text-red-300 transition-colors">
                  <Trash2 size={14} />
                </button>
              )}
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className="block text-xs text-gray-500 mb-1">Title *</label>
                <input
                  className="input"
                  value={paper.title}
                  onChange={e => update(idx, 'title', e.target.value)}
                  placeholder="Paper title"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Authors (comma-separated)</label>
                <input
                  className="input"
                  value={paper.authors}
                  onChange={e => update(idx, 'authors', e.target.value)}
                  placeholder="Smith J.A., Chen L."
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Journal</label>
                <input
                  className="input"
                  value={paper.journal ?? ''}
                  onChange={e => update(idx, 'journal', e.target.value)}
                  placeholder="Nature, Cell, NEJM…"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Year</label>
                <input
                  type="number"
                  className="input"
                  value={paper.year ?? ''}
                  onChange={e => update(idx, 'year', parseInt(e.target.value))}
                  min="1900"
                  max="2030"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">DOI</label>
                <input
                  className="input"
                  value={paper.doi ?? ''}
                  onChange={e => update(idx, 'doi', e.target.value)}
                  placeholder="10.1038/…"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs text-gray-500 mb-1">Abstract *</label>
                <textarea
                  className="input h-28 resize-none"
                  value={paper.abstract}
                  onChange={e => update(idx, 'abstract', e.target.value)}
                  placeholder="Paste the paper abstract here…"
                  required
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs text-gray-500 mb-1">Keywords (comma-separated)</label>
                <input
                  className="input"
                  value={paper.keywords}
                  onChange={e => update(idx, 'keywords', e.target.value)}
                  placeholder="CRISPR, gene therapy, neurons…"
                />
              </div>
            </div>
          </div>
        ))}

        <div className="flex gap-3">
          <button type="button" onClick={addPaper} className="btn-secondary flex items-center gap-2 text-sm">
            <Plus size={14} /> Add Another Paper
          </button>
          <button type="submit" className="btn-primary flex items-center gap-2" disabled={loading}>
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
            {loading ? 'Ingesting…' : `Ingest ${papers.length} Paper${papers.length !== 1 ? 's' : ''}`}
          </button>
        </div>
      </form>
    </div>
  );
}
