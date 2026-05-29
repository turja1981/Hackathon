'use client';

import { Lightbulb } from 'lucide-react';

interface Props {
  summary: string;
  keyFindings: string[];
}

export default function SummaryVisualization({ summary, keyFindings }: Props) {
  return (
    <div className="space-y-4">
      {/* Summary prose */}
      <div className="glass p-5">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
          AI-Generated Summary
        </h3>
        <div className="prose prose-invert prose-sm max-w-none">
          {summary.split('\n\n').map((para, i) => (
            <p key={i} className="text-gray-300 leading-relaxed mb-3 last:mb-0">
              {para}
            </p>
          ))}
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
    </div>
  );
}
