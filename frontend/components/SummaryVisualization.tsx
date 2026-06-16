'use client';

import { useState } from 'react';
import { Lightbulb, BookOpen, Star } from 'lucide-react';
import { clsx } from 'clsx';
import type { Citation } from '@/lib/types';
import { api } from '@/lib/api';

interface Props {
  summary: string;
  keyFindings: string[];
  citations?: Citation[];
  jobId?: string;
}

export default function SummaryVisualization({ summary, keyFindings, citations = [], jobId }: Props) {
  const [rating, setRating] = useState<number | null>(null);
  const [hovered, setHovered] = useState<number | null>(null);
  const [rated, setRated] = useState(false);

  const handleRate = async (score: number) => {
    if (rated) return;
    setRating(score);
    setRated(true);
    if (jobId) {
      await api.feedback({
        job_id: jobId,
        item_id: 'summary',
        feedback_type: 'accept',
        accuracy_rating: score,  // KPI 2: 1-10 accuracy rating
      }).catch(() => null);
    }
  };

  const displayRating = hovered ?? rating;

  return (
    <div className="space-y-4">
      {/* Summary prose */}
      <div className="glass p-5">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
          AI-Generated Summary
        </h3>
        <div className="space-y-3">
          {summary.split('\n\n').map((para, i) => (
            <p key={i} className="text-gray-300 leading-relaxed text-sm">{para}</p>
          ))}
        </div>

        {/* KPI 2: Summary Accuracy Rating (1-10) */}
        <div className="mt-5 pt-4 border-t border-white/10">
          <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
            <Star size={11} />
            Rate summary accuracy (KPI target ≥ 8.5 / 10):
          </p>
          <div className="flex items-center gap-1">
            {Array.from({ length: 10 }, (_, i) => i + 1).map(score => (
              <button
                key={score}
                disabled={rated}
                onClick={() => handleRate(score)}
                onMouseEnter={() => !rated && setHovered(score)}
                onMouseLeave={() => setHovered(null)}
                className={clsx(
                  'w-7 h-7 rounded text-xs font-semibold transition-all',
                  displayRating !== null && score <= displayRating
                    ? score >= 9 ? 'bg-green-500 text-white'
                      : score >= 7 ? 'bg-yellow-500 text-white'
                      : 'bg-red-500 text-white'
                    : 'bg-white/5 text-gray-600 hover:bg-white/15',
                  rated && 'cursor-default',
                )}
              >
                {score}
              </button>
            ))}
            {rated && rating !== null && (
              <span className={clsx(
                'ml-2 text-xs font-semibold',
                rating >= 9 ? 'text-green-400' : rating >= 7 ? 'text-yellow-400' : 'text-red-400'
              )}>
                {rating}/10 · {rating >= 8.5 ? '✓ Target met' : '✗ Below target (8.5)'}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Key findings */}
      {keyFindings.length > 0 && (
        <div className="glass p-5">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
            <Lightbulb size={14} className="text-yellow-400" />
            Key Findings
          </h3>
          <ul className="space-y-2">
            {keyFindings.map((finding, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-gray-300">
                <span className="mt-1 shrink-0 size-2 rounded-full bg-sky-500" />
                {finding}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* KPI 3: Citations / Grounding (hallucination prevention) */}
      {citations.length > 0 && (
        <div className="glass p-5">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
            <BookOpen size={14} className="text-sky-400" />
            Sources &amp; Grounding
            <span className="badge bg-green-500/10 text-green-400 border-green-500/20 text-xs ml-1">
              ✓ {citations.length} citations · Hallucination prevention active
            </span>
          </h3>
          <ul className="space-y-2">
            {citations.map((c, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-gray-400">
                <span className="shrink-0 mt-0.5 font-semibold text-sky-500">[{i + 1}]</span>
                <span>
                  <span className="text-gray-300 font-medium">{c.paper_title}</span>
                  {c.claim && <span className="text-gray-500"> — {c.claim}</span>}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
