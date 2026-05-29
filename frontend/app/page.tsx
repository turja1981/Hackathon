'use client';

import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { FlaskConical, Search, Lightbulb, BookOpen, Zap, ChevronRight } from 'lucide-react';
import SearchBar from '@/components/SearchBar';
import { api } from '@/lib/api';
import type { HealthResponse } from '@/lib/types';

const FEATURED_QUERIES = [
  'CRISPR gene editing neurodegeneration',
  'mRNA cancer vaccine immunotherapy',
  'single-cell sequencing microglia',
  'AI drug discovery graph neural network',
  'gut microbiome immunotherapy response',
];

const FEATURES = [
  {
    icon: Search,
    title: 'Semantic Search',
    desc: 'FAISS-powered vector search over hundreds of papers with LLM reranking for precision.',
    color: 'text-sky-400',
  },
  {
    icon: BookOpen,
    title: 'AI Summarization',
    desc: 'Multi-paper summaries with key findings extraction, powered by GPT-4o / Gemini 1.5.',
    color: 'text-purple-400',
  },
  {
    icon: Lightbulb,
    title: 'Hypothesis Generation',
    desc: 'Novel, testable research hypotheses with experimental designs and novelty scoring.',
    color: 'text-yellow-400',
  },
  {
    icon: Zap,
    title: 'Multi-Agent Pipeline',
    desc: 'LangGraph orchestrates Orchestrator → Search → Ranker → Summary → Hypothesis agents.',
    color: 'text-green-400',
  },
];

export default function HomePage() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => null);
  }, []);

  const handleSearch = (q: string) => {
    router.push(`/search?q=${encodeURIComponent(q)}`);
  };

  return (
    <div className="space-y-16">
      {/* Hero */}
      <section className="text-center space-y-6 pt-8">
        <div className="inline-flex items-center gap-2 badge bg-sky-500/10 text-sky-400 border border-sky-500/20 px-3 py-1 text-sm">
          <FlaskConical size={14} />
          Life Sciences AI Research Assistant
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold leading-tight text-white">
          Accelerate Discovery with{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-purple-400">
            Multi-Agent AI
          </span>
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
          Search thousands of life sciences papers, get instant AI-powered summaries, and generate
          novel research hypotheses — all in under 5 seconds.
        </p>

        {/* Status indicator */}
        {health && (
          <div className="flex justify-center gap-3 text-xs flex-wrap">
            <span className={`badge ${health.vector_store_loaded ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
              {health.vector_store_loaded ? '✓' : '✗'} {health.paper_count} papers indexed
            </span>
            <span className={`badge ${health.llm_configured ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'}`}>
              {health.llm_configured ? '✓ LLM connected' : '⚡ Demo mode (no API key)'}
            </span>
            <span className="badge bg-sky-500/10 text-sky-400 border-sky-500/20">
              v{health.version}
            </span>
          </div>
        )}

        <SearchBar onSearch={handleSearch} className="max-w-2xl mx-auto" />

        {/* Featured queries */}
        <div className="flex flex-wrap justify-center gap-2">
          {FEATURED_QUERIES.map(q => (
            <button
              key={q}
              onClick={() => handleSearch(q)}
              className="badge bg-white/5 text-gray-400 border border-white/10 hover:border-sky-500/40 hover:text-sky-300 transition-all cursor-pointer px-3 py-1 text-xs"
            >
              {q}
            </button>
          ))}
        </div>
      </section>

      {/* Features grid */}
      <section>
        <h2 className="text-xl font-semibold text-gray-300 text-center mb-8">Platform Capabilities</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURES.map(({ icon: Icon, title, desc, color }) => (
            <div key={title} className="card space-y-3">
              <div className={`${color} p-2 rounded-lg bg-current/10 w-fit`}>
                <Icon size={20} className={color} />
              </div>
              <h3 className="font-semibold text-gray-200">{title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Quick actions */}
      <section className="grid sm:grid-cols-3 gap-4">
        {[
          { href: '/search', label: 'Search Papers', desc: 'Explore our indexed corpus', icon: Search, iconClass: 'bg-sky-500/10 text-sky-400' },
          { href: '/hypotheses', label: 'Generate Hypotheses', desc: 'AI-powered research directions', icon: Lightbulb, iconClass: 'bg-purple-500/10 text-purple-400' },
          { href: '/ingest', label: 'Add Papers', desc: 'Expand the knowledge base', icon: BookOpen, iconClass: 'bg-green-500/10 text-green-400' },
        ].map(({ href, label, desc, icon: Icon, iconClass }) => (
          <a
            key={href}
            href={href}
            className="card flex items-center gap-4 hover:scale-[1.01] group"
          >
            <div className={`p-3 rounded-xl ${iconClass}`}>
              <Icon size={22} />
            </div>
            <div className="flex-1">
              <p className="font-semibold text-gray-200">{label}</p>
              <p className="text-xs text-gray-500">{desc}</p>
            </div>
            <ChevronRight size={16} className="text-gray-600 group-hover:text-gray-400 transition-colors" />
          </a>
        ))}
      </section>
    </div>
  );
}
