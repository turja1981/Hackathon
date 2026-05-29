'use client';

import { useState, useRef, useCallback } from 'react';
import {
  Upload, Plus, Trash2, CheckCircle, AlertCircle,
  Loader2, FileJson, X, FileUp,
} from 'lucide-react';
import { api } from '@/lib/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Mode = 'upload' | 'manual';

interface PaperPayload {
  title: string;
  abstract: string;
  authors: string[];
  journal?: string;
  year?: number;
  doi?: string;
  keywords: string[];
  publication_date?: string;
}

interface ParsedFile {
  name: string;
  papers: PaperPayload[];
  error?: string;
}

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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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

function parseJsonToPapers(text: string): PaperPayload[] {
  const data: unknown = JSON.parse(text);

  let raw: unknown[];
  if (Array.isArray(data)) {
    raw = data;
  } else if (data !== null && typeof data === 'object' && 'papers' in data) {
    const d = data as Record<string, unknown>;
    raw = Array.isArray(d.papers) ? d.papers : [];
  } else {
    throw new Error('Expected a JSON array or {"papers": [...]}');
  }

  return raw
    .map((item: unknown) => {
      const p = item as Record<string, unknown>;
      const authors = Array.isArray(p.authors)
        ? (p.authors as string[])
        : typeof p.authors === 'string'
        ? p.authors.split(',').map((a: string) => a.trim()).filter(Boolean)
        : [];
      const keywords = Array.isArray(p.keywords)
        ? (p.keywords as string[])
        : typeof p.keywords === 'string'
        ? p.keywords.split(',').map((k: string) => k.trim()).filter(Boolean)
        : [];
      return {
        title: String(p.title ?? ''),
        abstract: String(p.abstract ?? ''),
        authors,
        keywords,
        journal: p.journal ? String(p.journal) : undefined,
        year: p.year ? Number(p.year) : undefined,
        doi: p.doi ? String(p.doi) : undefined,
        publication_date: p.publication_date ? String(p.publication_date) : undefined,
      } satisfies PaperPayload;
    })
    .filter(p => p.title.trim() && p.abstract.trim());
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function IngestPage() {
  const [mode, setMode] = useState<Mode>('upload');

  // Upload mode
  const [parsedFiles, setParsedFiles] = useState<ParsedFile[]>([]);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Manual mode
  const [papers, setPapers] = useState<PaperForm[]>([emptyPaper()]);

  // Shared
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // -------------------------------------------------------------------------
  // File handling
  // -------------------------------------------------------------------------

  const processFiles = useCallback(async (files: FileList | File[]) => {
    const jsonFiles = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.json'));
    if (jsonFiles.length === 0) return;

    const results: ParsedFile[] = await Promise.all(
      jsonFiles.map(async file => {
        try {
          const text = await file.text();
          const parsed = parseJsonToPapers(text);
          return { name: file.name, papers: parsed };
        } catch (err) {
          return {
            name: file.name,
            papers: [],
            error: err instanceof Error ? err.message : 'Parse failed',
          };
        }
      }),
    );

    setParsedFiles(prev => [...prev, ...results]);
    setResult(null);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      processFiles(e.dataTransfer.files);
    },
    [processFiles],
  );

  const onFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) processFiles(e.target.files);
    e.target.value = '';
  };

  const removeFile = (idx: number) =>
    setParsedFiles(prev => prev.filter((_, i) => i !== idx));

  const totalPapers = parsedFiles.reduce((s, f) => s + f.papers.length, 0);

  const handleFileIngest = async () => {
    const allPapers = parsedFiles.flatMap(f => f.papers);
    if (!allPapers.length) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await api.ingest({ papers: allPapers });
      setResult({
        type: 'success',
        message: `✓ ${res.ingested_count} paper(s) ingested from ${parsedFiles.length} file(s).`,
      });
      setParsedFiles([]);
    } catch (err) {
      setResult({ type: 'error', message: `Error: ${err instanceof Error ? err.message : 'Unknown'}` });
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------------------------------------
  // Manual form
  // -------------------------------------------------------------------------

  const update = (idx: number, field: keyof PaperForm, value: unknown) =>
    setPapers(prev => prev.map((p, i) => (i === idx ? { ...p, [field]: value } : p)));

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const valid = papers.filter(p => p.title.trim() && p.abstract.trim());
    if (!valid.length) return;
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
      setResult({ type: 'success', message: `✓ ${res.ingested_count} paper(s) ingested.` });
      setPapers([emptyPaper()]);
    } catch (err) {
      setResult({ type: 'error', message: `Error: ${err instanceof Error ? err.message : 'Unknown'}` });
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100 mb-2 flex items-center gap-2">
          <FileUp size={22} className="text-green-400" />
          Ingest Papers
        </h1>
        <p className="text-gray-500 text-sm">
          Add research papers to the vector store. Abstracts are embedded and indexed for semantic search.
        </p>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 p-1 bg-white/5 rounded-lg w-fit">
        {(['upload', 'manual'] as Mode[]).map(m => (
          <button
            key={m}
            onClick={() => { setMode(m); setResult(null); }}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              mode === m
                ? 'bg-green-600 text-white shadow'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {m === 'upload' ? 'Upload JSON Files' : 'Manual Entry'}
          </button>
        ))}
      </div>

      {/* Result banner */}
      {result && (
        <div
          className={`glass p-4 flex items-center gap-3 ${
            result.type === 'success'
              ? 'border-green-500/30 text-green-400'
              : 'border-red-500/30 text-red-400'
          }`}
        >
          {result.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          {result.message}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* UPLOAD MODE                                                         */}
      {/* ------------------------------------------------------------------ */}
      {mode === 'upload' && (
        <div className="space-y-4">
          {/* Drop zone */}
          <div
            role="button"
            tabIndex={0}
            onClick={() => fileInputRef.current?.click()}
            onKeyDown={e => e.key === 'Enter' && fileInputRef.current?.click()}
            onDrop={onDrop}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            className={`card border-2 border-dashed cursor-pointer transition-all text-center py-14 select-none ${
              dragging
                ? 'border-green-400/80 bg-green-900/10 scale-[1.01]'
                : 'border-white/10 hover:border-green-500/40 hover:bg-white/[0.02]'
            }`}
          >
            <FileJson size={40} className="mx-auto mb-3 text-green-500 opacity-80" />
            <p className="text-sm font-semibold text-gray-200">
              Drop JSON files here, or click to browse
            </p>
            <p className="text-xs text-gray-500 mt-2 leading-relaxed">
              Accepts <code className="text-gray-400">[{'{...}'}, ...]</code> or{' '}
              <code className="text-gray-400">{'{"papers": [{...}]}'}</code>
              <br />
              Multiple files supported &middot; Fields: title, abstract, authors, journal, year, doi, keywords
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              multiple
              className="hidden"
              onChange={onFileInput}
            />
          </div>

          {/* Parsed files */}
          {parsedFiles.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Selected files
              </h3>
              {parsedFiles.map((f, i) => (
                <div
                  key={i}
                  className={`card flex items-center gap-3 ${f.error ? 'border-red-500/30' : 'border-green-500/20'}`}
                >
                  <FileJson
                    size={20}
                    className={f.error ? 'text-red-400 shrink-0' : 'text-green-400 shrink-0'}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-200 truncate">{f.name}</p>
                    {f.error ? (
                      <p className="text-xs text-red-400">Error: {f.error}</p>
                    ) : (
                      <p className="text-xs text-gray-500">
                        {f.papers.length} paper{f.papers.length !== 1 ? 's' : ''} ready to ingest
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => removeFile(i)}
                    className="text-gray-600 hover:text-red-400 transition-colors shrink-0"
                    aria-label="Remove file"
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}

              {/* Summary + action */}
              <div className="flex items-center justify-between pt-2 border-t border-white/5">
                <span className="text-sm text-gray-400">
                  {totalPapers} paper{totalPapers !== 1 ? 's' : ''} across {parsedFiles.length} file{parsedFiles.length !== 1 ? 's' : ''}
                </span>
                <button
                  onClick={handleFileIngest}
                  disabled={loading || totalPapers === 0}
                  className="btn-primary flex items-center gap-2 disabled:opacity-50"
                >
                  {loading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
                  {loading ? 'Ingesting…' : `Ingest ${totalPapers} Paper${totalPapers !== 1 ? 's' : ''}`}
                </button>
              </div>
            </div>
          )}

          {/* Hint when empty */}
          {parsedFiles.length === 0 && (
            <p className="text-xs text-gray-600 text-center">
              The JSON file should match the format of{' '}
              <code className="text-gray-500">sample_papers.json</code> — an array of paper objects.
            </p>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* MANUAL MODE                                                         */}
      {/* ------------------------------------------------------------------ */}
      {mode === 'manual' && (
        <form onSubmit={handleManualSubmit} className="space-y-6">
          {papers.map((paper, idx) => (
            <div key={idx} className="card space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-400">Paper {idx + 1}</h3>
                {papers.length > 1 && (
                  <button
                    type="button"
                    onClick={() => setPapers(prev => prev.filter((_, i) => i !== idx))}
                    className="text-red-400 hover:text-red-300 transition-colors"
                  >
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
                    value={paper.journal}
                    onChange={e => update(idx, 'journal', e.target.value)}
                    placeholder="Nature, Cell, NEJM…"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Year</label>
                  <input
                    type="number"
                    className="input"
                    value={paper.year}
                    onChange={e => update(idx, 'year', parseInt(e.target.value))}
                    min="1900"
                    max="2030"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">DOI</label>
                  <input
                    className="input"
                    value={paper.doi}
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
            <button
              type="button"
              onClick={() => setPapers(prev => [...prev, emptyPaper()])}
              className="btn-secondary flex items-center gap-2 text-sm"
            >
              <Plus size={14} /> Add Another Paper
            </button>
            <button
              type="submit"
              className="btn-primary flex items-center gap-2"
              disabled={loading}
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
              {loading
                ? 'Ingesting…'
                : `Ingest ${papers.length} Paper${papers.length !== 1 ? 's' : ''}`}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
