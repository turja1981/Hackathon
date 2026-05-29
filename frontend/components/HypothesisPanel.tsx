'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, ThumbsUp, ThumbsDown, Flag, FlaskConical } from 'lucide-react';
import { clsx } from 'clsx';
import type { Hypothesis } from '@/lib/types';
import { api } from '@/lib/api';

interface Props {
  hypothesis: Hypothesis;
  jobId?: string;
  index: number;
}

export default function HypothesisPanel({ hypothesis, jobId, index }: Props) {
  const [expanded, setExpanded] = useState(index === 0);
  const [feedback, setFeedback] = useState<'accept' | 'reject' | 'flag' | null>(null);

  const noveltyPct = Math.round(hypothesis.novelty_score * 100);
  const noveltyColor =
    noveltyPct >= 85 ? 'text-green-400' : noveltyPct >= 65 ? 'text-yellow-400' : 'text-red-400';

  const sendFeedback = async (type: 'accept' | 'reject' | 'flag') => {
    setFeedback(type);
    if (jobId) {
      await api.feedback({ job_id: jobId, item_id: hypothesis.id, feedback_type: type }).catch(() => null);
    }
  };

  return (
    <div className={clsx('card transition-all', expanded && 'ring-1 ring-sky-500/30')}>
      {/* Header */}
      <button
        className="w-full text-left flex items-start gap-3"
        onClick={() => setExpanded(v => !v)}
      >
        <div className="shrink-0 flex size-7 items-center justify-center rounded-full bg-sky-500/20 text-sky-400 text-xs font-bold mt-0.5">
          {index + 1}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-100 leading-snug pr-6">{hypothesis.hypothesis}</p>
          <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <FlaskConical size={11} />
              {hypothesis.impact_area}
            </span>
            <span className={clsx('font-semibold', noveltyColor)}>
              {noveltyPct}% novelty
            </span>
          </div>
        </div>
        {expanded ? <ChevronUp size={16} className="text-gray-500 shrink-0 mt-1" /> : <ChevronDown size={16} className="text-gray-500 shrink-0 mt-1" />}
      </button>

      {/* Novelty bar */}
      <div className="mt-3 h-1.5 rounded-full bg-white/5">
        <div
          className={clsx('h-full rounded-full transition-all', noveltyPct >= 85 ? 'bg-green-500' : noveltyPct >= 65 ? 'bg-yellow-500' : 'bg-red-500')}
          style={{ width: `${noveltyPct}%` }}
        />
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="mt-4 space-y-4 border-t border-white/10 pt-4">
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Rationale</h4>
            <p className="text-sm text-gray-300 leading-relaxed">{hypothesis.rationale}</p>
          </div>

          {hypothesis.experiments.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Proposed Experiments
              </h4>
              <ol className="space-y-1.5">
                {hypothesis.experiments.map((exp, i) => (
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

          {/* Human-in-the-loop feedback */}
          <div className="flex items-center gap-3 pt-1">
            <span className="text-xs text-gray-600">Rate this hypothesis:</span>
            <button
              onClick={() => sendFeedback('accept')}
              className={clsx('flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border transition-all',
                feedback === 'accept' ? 'bg-green-500/20 border-green-500 text-green-400' : 'border-white/20 text-gray-500 hover:border-green-500/50 hover:text-green-400'
              )}
            >
              <ThumbsUp size={11} /> Accept
            </button>
            <button
              onClick={() => sendFeedback('reject')}
              className={clsx('flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border transition-all',
                feedback === 'reject' ? 'bg-red-500/20 border-red-500 text-red-400' : 'border-white/20 text-gray-500 hover:border-red-500/50 hover:text-red-400'
              )}
            >
              <ThumbsDown size={11} /> Reject
            </button>
            <button
              onClick={() => sendFeedback('flag')}
              className={clsx('flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border transition-all',
                feedback === 'flag' ? 'bg-yellow-500/20 border-yellow-500 text-yellow-400' : 'border-white/20 text-gray-500 hover:border-yellow-500/50 hover:text-yellow-400'
              )}
            >
              <Flag size={11} /> Flag
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
