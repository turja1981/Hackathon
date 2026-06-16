'use client';

import { ShieldCheck, ShieldAlert, Eye, BarChart3, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { clsx } from 'clsx';
import type { ResponsibleAIReport } from '@/lib/types';

interface Props {
  report: ResponsibleAIReport;
}

function ScoreBar({ label, value, weight }: { label: string; value: number; weight: string }) {
  const pct = Math.round(value * 100);
  const color = pct >= 85 ? 'bg-green-500' : pct >= 70 ? 'bg-yellow-500' : 'bg-orange-500';
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-gray-500 w-36 shrink-0">{label}</span>
      <div className="flex-1 bg-white/5 rounded-full h-1.5 overflow-hidden">
        <div className={clsx('h-full rounded-full transition-all', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-gray-300 w-8 text-right">{pct}%</span>
      <span className="text-gray-600 w-14 text-right">{weight}</span>
    </div>
  );
}

export default function AnswerMetricsPanel({ report }: Props) {
  const [expanded, setExpanded] = useState(false);

  const guardrail = report.guardrail_report;
  const pii = report.pii_report;
  const ragas = report.ragas_evaluation;

  const hasData = guardrail || pii || ragas;
  if (!hasData) return null;

  const guardPassed = guardrail?.passed ?? true;
  const piiEntities = pii?.entities ?? [];
  const piiDetected = piiEntities.length > 0;
  const ragsScore = ragas?.overall_score;

  return (
    <div className="mt-3 rounded-xl border border-white/8 bg-white/[0.02] overflow-hidden">
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-white/[0.03] transition-colors"
      >
        <div className="flex items-center gap-2 flex-1">
          {/* Guardrail badge */}
          {guardrail && (
            <span className={clsx(
              'inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium',
              guardPassed ? 'bg-green-500/15 text-green-400' : 'bg-red-500/15 text-red-400',
            )}>
              {guardPassed
                ? <ShieldCheck size={11} />
                : <ShieldAlert size={11} />}
              {guardPassed ? 'Guardrails OK' : `${guardrail.violations.length} violation${guardrail.violations.length !== 1 ? 's' : ''}`}
            </span>
          )}

          {/* PII badge */}
          {pii && (
            <span className={clsx(
              'inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium',
              piiDetected ? 'bg-yellow-500/15 text-yellow-400' : 'bg-gray-500/15 text-gray-400',
            )}>
              <Eye size={11} />
              {piiDetected ? `PII: ${piiEntities.length} masked` : 'No PII'}
            </span>
          )}

          {/* RAGAS badge */}
          {ragas && ragsScore !== undefined && (
            <span className={clsx(
              'inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium',
              ragsScore >= 0.85 ? 'bg-green-500/15 text-green-400'
                : ragsScore >= 0.70 ? 'bg-yellow-500/15 text-yellow-400'
                : 'bg-orange-500/15 text-orange-400',
            )}>
              <BarChart3 size={11} />
              RAG: {Math.round(ragsScore * 100)}%
            </span>
          )}
        </div>

        <span className="text-gray-600 text-xs">Traceability</span>
        {expanded ? <ChevronUp size={13} className="text-gray-600" /> : <ChevronDown size={13} className="text-gray-600" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-white/5 pt-3">
          {/* Guardrail details */}
          {guardrail && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                <ShieldCheck size={11} /> Responsible AI Guardrails
                <span className={clsx('ml-2 font-bold', guardPassed ? 'text-green-400' : 'text-red-400')}>
                  {guardPassed ? '✓ Passed' : '✗ Failed'}
                </span>
              </p>
              <div className="grid grid-cols-2 gap-1.5">
                {Object.entries(guardrail.checks).map(([check, passed]) => (
                  <div key={check} className="flex items-center gap-1.5 text-xs">
                    <span className={passed ? 'text-green-400' : 'text-red-400'}>{passed ? '✓' : '✗'}</span>
                    <span className="text-gray-400 capitalize">{check.replace(/_/g, ' ')}</span>
                  </div>
                ))}
              </div>
              {guardrail.violations.length > 0 && (
                <div className="mt-2 space-y-0.5">
                  {guardrail.violations.map((v, i) => (
                    <p key={i} className="text-xs text-red-400 flex items-start gap-1">
                      <ShieldAlert size={11} className="mt-0.5 shrink-0" /> {v}
                    </p>
                  ))}
                </div>
              )}
              {guardrail.pii_in_output > 0 && (
                <p className="mt-1.5 text-xs text-yellow-400 flex items-center gap-1">
                  <Eye size={11} /> {guardrail.pii_in_output} PII entity{guardrail.pii_in_output !== 1 ? 'ies' : ''} detected in output
                </p>
              )}
            </div>
          )}

          {/* PII details */}
          {pii && piiDetected && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                <Eye size={11} /> PII Masking
                <span className="text-xs text-gray-600 font-normal ml-1">via {pii.backend}</span>
              </p>
              <p className="text-xs text-yellow-400">
                {piiEntities.length} {piiEntities.length === 1 ? 'entity' : 'entities'} detected and masked:{' '}
                {Array.from(new Set(piiEntities.map(e => e.entity_type))).join(', ')}
              </p>
            </div>
          )}

          {/* RAGAS scores */}
          {ragas && ragas.status !== 'pending' && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                <BarChart3 size={11} /> RAG Quality Evaluation
              </p>
              <div className="space-y-1.5">
                <ScoreBar label="Faithfulness" value={ragas.faithfulness} weight="40%" />
                <ScoreBar label="Answer Relevancy" value={ragas.answer_relevancy} weight="35%" />
                <ScoreBar label="Context Precision" value={ragas.context_precision} weight="25%" />
                <div className="border-t border-white/5 pt-1.5 mt-1.5">
                  <ScoreBar label="Overall Score" value={ragas.overall_score} weight="" />
                </div>
              </div>
            </div>
          )}
          {ragas && ragas.status === 'pending' && (
            <p className="text-xs text-gray-600">RAG evaluation running in background…</p>
          )}
        </div>
      )}
    </div>
  );
}
