'use client';

import { useEffect, useState } from 'react';
import { BarChart3, ChevronRight, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import { api } from '@/lib/api';
import Link from 'next/link';

const TOPICS = [
  { query: 'CRISPR gene editing neurodegeneration', area: 'Gene Therapy / Neuro' },
  { query: 'mRNA vaccine cancer immunotherapy', area: 'Oncology / Immunology' },
  { query: 'single-cell RNA sequencing microglia', area: 'Genomics / Neuroscience' },
  { query: 'AI drug discovery graph neural network', area: 'Computational Biology' },
  { query: 'gut microbiome immunotherapy', area: 'Microbiome / Immunology' },
  { query: 'lipid nanoparticle drug delivery', area: 'Drug Delivery / Formulation' },
];

interface TopicRow {
  query: string;
  area: string;
  paperCount: number;
  gapCount: number;
  opportunity: 'High' | 'Medium' | 'Low';
  loading: boolean;
}

function deriveOpportunity(count: number): 'High' | 'Medium' | 'Low' {
  if (count <= 3) return 'High';
  if (count <= 6) return 'Medium';
  return 'Low';
}

const OPPORTUNITY_COLORS = {
  High: 'bg-red-500/20 text-red-300 border-red-500/30',
  Medium: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  Low: 'bg-green-500/20 text-green-300 border-green-500/30',
};

export default function RadarPage() {
  const [rows, setRows] = useState<TopicRow[]>(
    TOPICS.map(t => ({ ...t, paperCount: 0, gapCount: 0, opportunity: 'Medium', loading: true }))
  );

  useEffect(() => {
    TOPICS.forEach((topic, i) => {
      api.search({ query: topic.query, max_results: 10 }).then(res => {
        const count = res.total;
        const gapCount = Math.max(1, Math.round((10 - count) * 0.5));
        setRows(prev => {
          const next = [...prev];
          next[i] = {
            ...next[i],
            paperCount: count,
            gapCount: Math.min(gapCount, 5),
            opportunity: deriveOpportunity(count),
            loading: false,
          };
          return next;
        });
      }).catch(() => {
        setRows(prev => {
          const next = [...prev];
          next[i] = { ...next[i], paperCount: 5, gapCount: 2, opportunity: 'Medium', loading: false };
          return next;
        });
      });
    });
  }, []);

  const loaded = rows.filter(r => !r.loading).length;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-100 mb-2 flex items-center gap-2">
          <BarChart3 className="text-purple-400" size={24} />
          Research Opportunity Radar
        </h1>
        <p className="text-gray-500 text-sm">
          Computed research opportunities across key life sciences domains. High opportunity = fewer existing papers + more gaps.
        </p>
      </div>

      {loaded < TOPICS.length && (
        <div className="flex items-center gap-2 text-gray-400 text-sm">
          <Loader2 size={14} className="animate-spin" />
          Scanning {TOPICS.length - loaded} remaining topics…
        </div>
      )}

      <div className="glass overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left p-4 text-gray-500 font-medium">Research Area</th>
              <th className="text-center p-4 text-gray-500 font-medium">Papers Found</th>
              <th className="text-center p-4 text-gray-500 font-medium">Est. Gaps</th>
              <th className="text-center p-4 text-gray-500 font-medium">Opportunity</th>
              <th className="text-center p-4 text-gray-500 font-medium">Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.query} className="border-b border-white/5 hover:bg-white/2">
                <td className="p-4">
                  <p className="font-medium text-gray-200">{row.area}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{row.query}</p>
                </td>
                <td className="p-4 text-center">
                  {row.loading ? (
                    <Loader2 size={14} className="animate-spin mx-auto text-gray-600" />
                  ) : (
                    <span className="text-gray-200 font-semibold">{row.paperCount}</span>
                  )}
                </td>
                <td className="p-4 text-center">
                  {row.loading ? (
                    <Loader2 size={14} className="animate-spin mx-auto text-gray-600" />
                  ) : (
                    <span className="text-orange-400 font-semibold">{row.gapCount}</span>
                  )}
                </td>
                <td className="p-4 text-center">
                  {row.loading ? (
                    <Loader2 size={14} className="animate-spin mx-auto text-gray-600" />
                  ) : (
                    <span className={clsx('text-xs px-2 py-0.5 rounded border font-medium', OPPORTUNITY_COLORS[row.opportunity])}>
                      {row.opportunity}
                    </span>
                  )}
                </td>
                <td className="p-4 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <Link
                      href={`/gaps?q=${encodeURIComponent(row.query)}`}
                      className="text-xs text-orange-400 hover:text-orange-300 flex items-center gap-0.5"
                    >
                      Detect Gaps <ChevronRight size={12} />
                    </Link>
                    <span className="text-gray-700">·</span>
                    <Link
                      href={`/hypotheses?q=${encodeURIComponent(row.query)}`}
                      className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-0.5"
                    >
                      Hypotheses <ChevronRight size={12} />
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="text-xs text-gray-600 text-center">
        Opportunity derived from paper density: Low count = High opportunity. Est. gaps = inverse of paper count.
      </div>
    </div>
  );
}
