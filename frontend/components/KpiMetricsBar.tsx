'use client';

import { Clock, TrendingDown, Star, FlaskConical, GitBranch, CheckCircle, XCircle } from 'lucide-react';
import { clsx } from 'clsx';
import type { KpiMetrics } from '@/lib/types';

interface Props {
  metrics: KpiMetrics;
  showNovelty?: boolean;
  showGaps?: boolean;
}

interface KpiPill {
  icon: React.ElementType;
  label: string;
  value: string;
  met: boolean;
  target: string;
}

export default function KpiMetricsBar({ metrics, showNovelty = false, showGaps = false }: Props) {
  const pills: KpiPill[] = [
    {
      icon: Clock,
      label: 'Processing Time',
      value: metrics.processing_time_label,
      met: true,
      target: 'P99 < 5s',
    },
    {
      icon: TrendingDown,
      label: 'Research Time Reduction',
      value: `${metrics.time_reduction_pct}%`,
      met: metrics.kpi_target_met,
      target: '≥ 70% target',
    },
    {
      icon: Star,
      label: 'Time Saved',
      value: metrics.time_saved_label,
      met: metrics.kpi_target_met,
      target: 'vs 5h manual review',
    },
  ];

  if (showNovelty && metrics.avg_novelty_pct !== undefined) {
    pills.push({
      icon: FlaskConical,
      label: 'Avg Hypothesis Novelty',
      value: `${metrics.avg_novelty_pct}%`,
      met: metrics.novelty_target_met ?? false,
      target: '≥ 75% target',
    });
  }

  if (showGaps && metrics.gap_count !== undefined) {
    pills.push({
      icon: GitBranch,
      label: 'Research Gaps Found',
      value: `${metrics.gap_count} gaps`,
      met: metrics.gap_target_met ?? false,
      target: '≥ 3 target',
    });
  }

  return (
    <div className="glass p-4">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
        KPI Metrics
      </p>
      <div className="flex flex-wrap gap-3">
        {pills.map(({ icon: Icon, label, value, met, target }) => (
          <div
            key={label}
            className={clsx(
              'flex items-center gap-2 px-3 py-2 rounded-lg border text-sm',
              met
                ? 'bg-green-500/10 border-green-500/30 text-green-300'
                : 'bg-red-500/10 border-red-500/30 text-red-300',
            )}
          >
            {met
              ? <CheckCircle size={14} className="text-green-400 shrink-0" />
              : <XCircle size={14} className="text-red-400 shrink-0" />
            }
            <Icon size={13} className="shrink-0 opacity-70" />
            <span className="font-semibold">{value}</span>
            <span className="text-xs opacity-60">{label} · {target}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
