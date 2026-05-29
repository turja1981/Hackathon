'use client';

import { CheckCircle, Circle, Loader2, XCircle } from 'lucide-react';
import { clsx } from 'clsx';
import type { AgentEvent, AgentName } from '@/lib/types';
import type { SSEStatus } from '@/lib/hooks/useSSE';

const AGENT_LABELS: Record<AgentName, string> = {
  orchestrator: 'Orchestrator',
  search: 'Search Agent',
  ranker: 'Ranker Agent',
  summarizer: 'Summary Agent',
  hypothesis: 'Hypothesis Agent',
};

const AGENT_ORDER: AgentName[] = ['orchestrator', 'search', 'ranker', 'summarizer', 'hypothesis'];

interface Props {
  status: SSEStatus;
  events: AgentEvent[];
}

export default function AgentStatusTracker({ status, events }: Props) {
  if (status === 'idle') return null;

  const activeAgents = new Set(events.map(e => e.agent));
  const lastByAgent: Record<string, AgentEvent> = {};
  for (const ev of events) lastByAgent[ev.agent] = ev;

  return (
    <div className="glass p-4 space-y-1">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
        Agent Pipeline
      </p>
      {AGENT_ORDER.map(agent => {
        const lastEvent = lastByAgent[agent];
        const isActive = status === 'streaming' && events.at(-1)?.agent === agent;
        const isDone = activeAgents.has(agent) && !isActive && status !== 'error';
        const isFailed = status === 'error' && activeAgents.has(agent);

        return (
          <div key={agent} className="flex items-start gap-3 py-1.5">
            <div className="mt-0.5 shrink-0">
              {isFailed ? (
                <XCircle size={16} className="text-red-400" />
              ) : isDone ? (
                <CheckCircle size={16} className="text-green-400" />
              ) : isActive ? (
                <Loader2 size={16} className="text-sky-400 animate-spin" />
              ) : (
                <Circle size={16} className="text-gray-700" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className={clsx('text-sm font-medium', isActive ? 'text-sky-300' : isDone ? 'text-gray-300' : 'text-gray-600')}>
                {AGENT_LABELS[agent]}
              </p>
              {lastEvent && (
                <p className="text-xs text-gray-500 truncate mt-0.5">{lastEvent.message}</p>
              )}
            </div>
          </div>
        );
      })}

      {status === 'done' && (
        <p className="text-xs text-green-400 font-medium pt-2 border-t border-white/5">
          ✓ Pipeline completed
        </p>
      )}
      {status === 'error' && (
        <p className="text-xs text-red-400 pt-2 border-t border-white/5">
          Pipeline encountered an error
        </p>
      )}
    </div>
  );
}
