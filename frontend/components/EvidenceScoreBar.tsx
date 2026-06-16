'use client';

import { clsx } from 'clsx';
import type { EvidenceScore } from '@/lib/types';

interface Props {
  score: EvidenceScore;
}

const COMPONENTS = [
  { key: 'supporting_papers_count', label: 'Supporting Papers', weight: '30%', format: (v: number) => `${v} papers`, max: 10 },
  { key: 'recency_score', label: 'Recency', weight: '20%', format: (v: number) => `${Math.round(v * 100)}%`, max: 1 },
  { key: 'agreement_score', label: 'Literature Agreement', weight: '30%', format: (v: number) => `${Math.round(v * 100)}%`, max: 1 },
  { key: 'citation_impact_score', label: 'Citation Impact', weight: '20%', format: (v: number) => `${Math.round(v * 100)}%`, max: 1 },
] as const;

export default function EvidenceScoreBar({ score }: Props) {
  const overall = score.overall_score;
  const overallColor = overall >= 75 ? 'text-green-400' : overall >= 50 ? 'text-yellow-400' : 'text-red-400';
  const barColor = overall >= 75 ? 'bg-green-500' : overall >= 50 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div className="glass p-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Evidence Score</p>
        <div className="flex items-center gap-2">
          <span className={clsx('text-lg font-bold', overallColor)}>{Math.round(overall)}/100</span>
          <span className={clsx(
            'text-xs px-1.5 py-0.5 rounded font-medium',
            score.label === 'Strong' ? 'bg-green-500/20 text-green-400' :
            score.label === 'Moderate' ? 'bg-yellow-500/20 text-yellow-400' :
            'bg-red-500/20 text-red-400'
          )}>
            {score.label}
          </span>
        </div>
      </div>

      {/* Overall bar */}
      <div className="h-2 rounded-full bg-white/5">
        <div className={clsx('h-full rounded-full transition-all', barColor)} style={{ width: `${overall}%` }} />
      </div>

      {/* Component bars */}
      <div className="space-y-2">
        {COMPONENTS.map(({ key, label, weight, format, max }) => {
          const raw = score[key] as number;
          const pct = Math.round((raw / max) * 100);
          return (
            <div key={key} className="flex items-center gap-2 text-xs">
              <span className="text-gray-600 w-36 shrink-0">{label}</span>
              <div className="flex-1 h-1 rounded-full bg-white/5">
                <div className="h-full rounded-full bg-sky-500/60" style={{ width: `${Math.min(pct, 100)}%` }} />
              </div>
              <span className="text-gray-400 w-12 text-right">{format(raw)}</span>
              <span className="text-gray-700 w-8 text-right">{weight}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
