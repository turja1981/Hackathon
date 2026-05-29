'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, ArrowRight } from 'lucide-react';
import type { ReasoningStep } from '@/lib/types';

interface Props {
  steps: ReasoningStep[];
  hypothesis: string;
}

export default function ReasoningPath({ steps, hypothesis }: Props) {
  const [expanded, setExpanded] = useState(false);

  if (steps.length === 0) return null;

  return (
    <div className="glass p-4">
      <button
        className="w-full flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wide"
        onClick={() => setExpanded(v => !v)}
      >
        <span>Reasoning Path ({steps.length} steps)</span>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {expanded && (
        <div className="mt-4 space-y-3">
          {steps.map((step, i) => (
            <div key={i} className="flex items-start gap-3">
              <div className="shrink-0 flex flex-col items-center">
                <div className="size-6 rounded-full bg-sky-500/20 flex items-center justify-center text-sky-400 text-xs font-bold">
                  {i + 1}
                </div>
                {i < steps.length - 1 && (
                  <div className="w-px h-8 bg-white/10 mt-1" />
                )}
              </div>
              <div className="flex-1 pb-2">
                <p className="text-xs font-medium text-sky-300">{step.paper_title}</p>
                <p className="text-xs text-gray-300 mt-0.5">{step.finding}</p>
                <p className="text-xs text-gray-600 mt-0.5 italic">{step.relevance}</p>
              </div>
            </div>
          ))}
          <div className="flex items-center gap-2 pt-2 border-t border-white/10">
            <ArrowRight size={12} className="text-yellow-400 shrink-0" />
            <p className="text-xs text-yellow-300 italic">{hypothesis.slice(0, 120)}…</p>
          </div>
        </div>
      )}
    </div>
  );
}
