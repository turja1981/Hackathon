'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  Brain, Search, Lightbulb, BookOpen, Zap, ChevronRight,
  GitBranch, ShieldCheck, BarChart3, Users, CheckCircle, XCircle, Clock,
} from 'lucide-react';
import SearchBar from '@/components/SearchBar';
import { api } from '@/lib/api';
import type { HealthResponse, AdoptionMetrics } from '@/lib/types';

const FEATURED_QUERIES = [
  'CRISPR gene editing neurodegeneration',
  'mRNA cancer vaccine immunotherapy',
  'single-cell sequencing microglia',
  'AI drug discovery graph neural network',
  'gut microbiome immunotherapy response',
];

const CAPABILITIES = [
  { icon: Search, title: 'Semantic Search', desc: 'FAISS vector search over hundreds of papers with LLM reranking.', color: 'text-sky-400' },
  { icon: BookOpen, title: 'AI Summarization', desc: 'Multi-paper summaries with citation grounding — no hallucinations.', color: 'text-purple-400' },
  { icon: GitBranch, title: 'Gap Detection', desc: 'Identify unexplored research connections and high-value white spaces.', color: 'text-orange-400' },
  { icon: Lightbulb, title: 'Hypothesis Generation', desc: 'Novel, testable research directions with novelty scoring.', color: 'text-yellow-400' },
  { icon: ShieldCheck, title: 'Evidence Scoring', desc: 'Weighted evidence strength: recency, consensus, citation impact.', color: 'text-green-400' },
  { icon: Brain, title: 'Reasoning Paths', desc: 'Transparent step-by-step chain linking papers → findings → hypothesis.', color: 'text-pink-400' },
  { icon: Zap, title: 'Research Copilot', desc: 'Conversational AI assistant for open-ended research questions.', color: 'text-cyan-400' },
];

const KPI_CARDS = [
  { label: 'Research Time Reduction', value: '≥ 70%', target: '5h → 45min', color: 'border-sky-500/30 bg-sky-500/5' },
  { label: 'Summary Accuracy', value: '≥ 8.5/10', target: 'Expert-validated', color: 'border-purple-500/30 bg-purple-500/5' },
  { label: 'Hallucination Rate', value: '< 3%', target: 'Citation-grounded', color: 'border-green-500/30 bg-green-500/5' },
  { label: 'Hypothesis Novelty', value: '≥ 75%', target: 'Novelty score', color: 'border-yellow-500/30 bg-yellow-500/5' },
  { label: 'Gap Detection Rate', value: '> 75%', target: '3-5 gaps per query', color: 'border-orange-500/30 bg-orange-500/5' },
  { label: 'Evidence Score', value: '≥ 80/100', target: 'Strong evidence', color: 'border-pink-500/30 bg-pink-500/5' },
  { label: 'User Adoption', value: '> 50/day', target: 'Active queries', color: 'border-cyan-500/30 bg-cyan-500/5' },
];

const COMPARISON = [
  { feature: 'Semantic Search', pubmed: false, semantic: true, elicit: true, chatgpt: false, biomind: true },
  { feature: 'AI Summarization', pubmed: false, semantic: false, elicit: true, chatgpt: true, biomind: true },
  { feature: 'Cross-Paper Reasoning', pubmed: false, semantic: false, elicit: false, chatgpt: false, biomind: true },
  { feature: 'Research Gap Detection', pubmed: false, semantic: false, elicit: false, chatgpt: false, biomind: true },
  { feature: 'Evidence Scoring', pubmed: false, semantic: false, elicit: false, chatgpt: false, biomind: true },
  { feature: 'Hypothesis Generation', pubmed: false, semantic: false, elicit: false, chatgpt: false, biomind: true },
  { feature: 'Explainable Reasoning Path', pubmed: false, semantic: false, elicit: false, chatgpt: false, biomind: true },
  { feature: 'Citation Grounding', pubmed: false, semantic: true, elicit: true, chatgpt: false, biomind: true },
];

const Check = () => <CheckCircle size={14} className="text-green-400 mx-auto" />;
const Cross = () => <XCircle size={14} className="text-gray-700 mx-auto" />;

export default function HomePage() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [adoption, setAdoption] = useState<AdoptionMetrics | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => null);
    api.getAdoptionMetrics().then(setAdoption).catch(() => null);
  }, []);

  const handleSearch = (q: string) => router.push(`/search?q=${encodeURIComponent(q)}`);

  return (
    <div className="space-y-16">
      {/* Hero */}
      <section className="text-center space-y-6 pt-8">
        <div className="inline-flex items-center gap-2 badge bg-sky-500/10 text-sky-400 border border-sky-500/20 px-3 py-1 text-sm">
          <Brain size={14} />
          AI Research Discovery Platform
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold leading-tight text-white">
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-purple-400">
            BioMind AI
          </span>
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
          From information retrieval to autonomous scientific discovery.
          Cross-paper reasoning · Gap detection · Evidence scoring · Explainable hypotheses.
        </p>

        {health && (
          <div className="flex justify-center gap-3 text-xs flex-wrap">
            <span className={`badge ${health.vector_store_loaded ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
              {health.vector_store_loaded ? '✓' : '✗'} {health.paper_count} papers indexed
            </span>
            <span className={`badge ${health.llm_configured ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'}`}>
              {health.llm_configured ? '✓ LLM connected' : '⚡ Demo mode'}
            </span>
            <span className="badge bg-sky-500/10 text-sky-400 border-sky-500/20">v{health.version}</span>
          </div>
        )}

        <SearchBar onSearch={handleSearch} className="max-w-2xl mx-auto" />

        <div className="flex flex-wrap justify-center gap-2">
          {FEATURED_QUERIES.map(q => (
            <button key={q} onClick={() => handleSearch(q)}
              className="badge bg-white/5 text-gray-400 border border-white/10 hover:border-sky-500/40 hover:text-sky-300 transition-all cursor-pointer px-3 py-1 text-xs">
              {q}
            </button>
          ))}
        </div>
      </section>

      {/* Executive Impact */}
      <section>
        <h2 className="text-xl font-semibold text-gray-300 text-center mb-6">Executive Impact</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { icon: Clock, before: '5 hours', after: '45 minutes', label: 'Research Time', color: 'text-sky-400' },
            { icon: BookOpen, before: '20 papers', after: '500+ papers', label: 'Simultaneous Analysis', color: 'text-purple-400' },
            { icon: Zap, before: 'Weeks', after: 'Minutes', label: 'Discovery Time', color: 'text-yellow-400' },
            { icon: BarChart3, before: 'Manual review', after: '≥ 8.5/10 accuracy', label: 'AI-Validated', color: 'text-green-400' },
          ].map(({ icon: Icon, before, after, label, color }) => (
            <div key={label} className="card text-center space-y-2">
              <Icon size={20} className={`mx-auto ${color}`} />
              <p className="text-xs text-gray-600 line-through">{before}</p>
              <p className="text-lg font-bold text-white">{after}</p>
              <p className="text-xs text-gray-500">{label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Live adoption metrics */}
      {adoption && (
        <section className="glass p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Users size={14} /> Live Platform Metrics
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            {[
              { label: 'Papers Processed', value: adoption.papers_processed },
              { label: 'Hypotheses Generated', value: adoption.hypotheses_generated },
              { label: 'Gaps Identified', value: adoption.gaps_identified },
              { label: 'Total Queries', value: adoption.queries_total },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-2xl font-bold text-sky-400">{value.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">{label}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* KPI grid */}
      <section>
        <h2 className="text-xl font-semibold text-gray-300 text-center mb-6">7 Production KPIs</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {KPI_CARDS.map(({ label, value, target, color }) => (
            <div key={label} className={`card border ${color} space-y-1`}>
              <p className="text-xs text-gray-500">{label}</p>
              <p className="text-xl font-bold text-white">{value}</p>
              <p className="text-xs text-gray-600">{target}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Capabilities */}
      <section>
        <h2 className="text-xl font-semibold text-gray-300 text-center mb-8">Platform Capabilities</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {CAPABILITIES.map(({ icon: Icon, title, desc, color }) => (
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
      <section className="grid sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {[
          { href: '/search', label: 'Search Papers', desc: 'Semantic vector search', icon: Search, iconClass: 'bg-sky-500/10 text-sky-400' },
          { href: '/gaps', label: 'Discover Gaps', desc: 'Find research white spaces', icon: GitBranch, iconClass: 'bg-orange-500/10 text-orange-400' },
          { href: '/hypotheses', label: 'Generate Hypotheses', desc: 'AI-powered research directions', icon: Lightbulb, iconClass: 'bg-purple-500/10 text-purple-400' },
          { href: '/copilot', label: 'Research Copilot', desc: 'Conversational AI assistant', icon: Brain, iconClass: 'bg-cyan-500/10 text-cyan-400' },
        ].map(({ href, label, desc, icon: Icon, iconClass }) => (
          <a key={href} href={href} className="card flex items-center gap-4 hover:scale-[1.01] group">
            <div className={`p-3 rounded-xl ${iconClass}`}><Icon size={22} /></div>
            <div className="flex-1">
              <p className="font-semibold text-gray-200">{label}</p>
              <p className="text-xs text-gray-500">{desc}</p>
            </div>
            <ChevronRight size={16} className="text-gray-600 group-hover:text-gray-400 transition-colors" />
          </a>
        ))}
      </section>

      {/* Competitive comparison */}
      <section>
        <h2 className="text-xl font-semibold text-gray-300 text-center mb-6">Competitive Positioning</h2>
        <div className="glass overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left p-3 text-gray-500 font-medium">Feature</th>
                <th className="text-center p-3 text-gray-500 font-medium">PubMed</th>
                <th className="text-center p-3 text-gray-500 font-medium">Semantic Scholar</th>
                <th className="text-center p-3 text-gray-500 font-medium">Elicit</th>
                <th className="text-center p-3 text-gray-500 font-medium">ChatGPT</th>
                <th className="text-center p-3 text-sky-400 font-bold">BioMind AI</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON.map(({ feature, pubmed, semantic, elicit, chatgpt, biomind }) => (
                <tr key={feature} className="border-b border-white/5 hover:bg-white/2">
                  <td className="p-3 text-gray-300">{feature}</td>
                  <td className="p-3">{pubmed ? <Check /> : <Cross />}</td>
                  <td className="p-3">{semantic ? <Check /> : <Cross />}</td>
                  <td className="p-3">{elicit ? <Check /> : <Cross />}</td>
                  <td className="p-3">{chatgpt ? <Check /> : <Cross />}</td>
                  <td className="p-3 bg-sky-500/5">{biomind ? <Check /> : <Cross />}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
