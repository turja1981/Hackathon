'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, AlertTriangle, FlaskConical } from 'lucide-react';
import { clsx } from 'clsx';
import type { ResearchGap } from '@/lib/types';

interface Props {
  gap: ResearchGap;
  index: number;
}

const OPPORTUNITY_COLORS = {
  High: 'bg-red-500/20 text-red-300 border-red-500/30',
  Medium: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  Low: 'bg-green-500/20 text-green-300 border-green-500/30',
};

export default function ResearchGapCard({ gap, index }: Props) {
  const [expanded, setExpanded] = useState(index === 0);
  const noveltyPct = Math.round(gap.novelty_score * 100);

  return (
    <div className={clsx('card transition-all', expanded && 'ring-1 ring-orange-500/30')}>
      <button className="w-full text-left flex items-start gap-3" onClick={() => setExpanded(v => !v)}>
        <div className="shrink-0 flex size-7 items-center justify-center rounded-full bg-orange-500/20 text-orange-400 text-xs font-bold mt-0.5">
          {index + 1}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-100 leading-snug pr-6">{gap.gap_description}</p>
          <div className="flex flex-wrap items-center gap-2 mt-1.5">
            <span className="text-xs text-gray-500">{gap.area}</span>
            <span className={clsx('text-xs px-1.5 py-0.5 rounded border font-medium', OPPORTUNITY_COLORS[gap.opportunity_level])}>
              {gap.opportunity_level} Opportunity
            </span>
            <span className="text-xs text-orange-400 font-semibold">{noveltyPct}% novelty</span>
          </div>
        </div>
        {expanded ? <ChevronUp size={16} className="text-gray-500 shrink-0 mt-1" /> : <ChevronDown size={16} className="text-gray-500 shrink-0 mt-1" />}
      </button>

      {/* Novelty bar */}
      <div className="mt-3 h-1.5 rounded-full bg-white/5">
        <div className="h-full rounded-full bg-orange-500" style={{ width: `${noveltyPct}%` }} />
      </div>

      {expanded && (
        <div className="mt-4 space-y-4 border-t border-white/10 pt-4">
          {gap.missing_connections.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                <AlertTriangle size={11} /> Missing Connections
              </h4>
              <ul className="space-y-1">
                {gap.missing_connections.map((c, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="mt-1.5 shrink-0 size-1.5 rounded-full bg-orange-500" />
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {gap.suggested_experiments.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                <FlaskConical size={11} /> Suggested Experiments
              </h4>
              <ol className="space-y-1.5">
                {gap.suggested_experiments.map((exp, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="shrink-0 size-5 rounded-full bg-white/10 flex items-center justify-center text-xs text-gray-400 font-medium">
                      {i + 1}
                    </span>
                    {exp}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
