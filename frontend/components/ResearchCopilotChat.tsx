'use client';

import { Brain, User, BookOpen, GitBranch, Lightbulb } from 'lucide-react';
import { clsx } from 'clsx';
import type { CopilotMessage } from '@/lib/types';
import AgentStatusTracker from './AgentStatusTracker';
import type { AgentEvent } from '@/lib/types';
import type { SSEStatus } from '@/lib/hooks/useSSE';

interface Props {
  messages: CopilotMessage[];
  status: SSEStatus;
  events: AgentEvent[];
}

function AssistantBubble({ msg }: { msg: CopilotMessage }) {
  return (
    <div className="flex items-start gap-3">
      <div className="shrink-0 size-8 rounded-full bg-sky-500/20 flex items-center justify-center">
        <Brain size={16} className="text-sky-400" />
      </div>
      <div className="flex-1 space-y-3 max-w-3xl">
        <div className="glass p-4">
          <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{msg.content}</p>
          <p className="text-xs text-gray-600 mt-2">{new Date(msg.timestamp).toLocaleTimeString()}</p>
        </div>

        {msg.papers && msg.papers.length > 0 && (
          <div className="glass p-3">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2 flex items-center gap-1">
              <BookOpen size={11} /> {msg.papers.length} Papers Analyzed
            </p>
            <ul className="space-y-1">
              {msg.papers.slice(0, 3).map(p => (
                <li key={p.id} className="text-xs text-gray-400">· {p.title} ({p.year})</li>
              ))}
              {msg.papers.length > 3 && (
                <li className="text-xs text-gray-600">+ {msg.papers.length - 3} more</li>
              )}
            </ul>
          </div>
        )}

        {msg.gaps && msg.gaps.length > 0 && (
          <div className="glass p-3">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2 flex items-center gap-1">
              <GitBranch size={11} /> {msg.gaps.length} Research Gaps Found
            </p>
            <ul className="space-y-1">
              {msg.gaps.slice(0, 2).map(g => (
                <li key={g.id} className="text-xs text-gray-400">· {g.gap_description.slice(0, 100)}…</li>
              ))}
            </ul>
          </div>
        )}

        {msg.hypotheses && msg.hypotheses.length > 0 && (
          <div className="glass p-3">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2 flex items-center gap-1">
              <Lightbulb size={11} /> {msg.hypotheses.length} Hypotheses Generated
            </p>
            <ul className="space-y-1">
              {msg.hypotheses.slice(0, 2).map(h => (
                <li key={h.id} className="text-xs text-gray-400">· {h.hypothesis.slice(0, 100)}…</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function UserBubble({ msg }: { msg: CopilotMessage }) {
  return (
    <div className="flex items-start gap-3 justify-end">
      <div className="glass p-3 max-w-lg">
        <p className="text-sm text-gray-200">{msg.content}</p>
        <p className="text-xs text-gray-600 mt-1 text-right">{new Date(msg.timestamp).toLocaleTimeString()}</p>
      </div>
      <div className="shrink-0 size-8 rounded-full bg-white/10 flex items-center justify-center">
        <User size={16} className="text-gray-400" />
      </div>
    </div>
  );
}

export default function ResearchCopilotChat({ messages, status, events }: Props) {
  return (
    <div className="space-y-6">
      {messages.map((msg, i) =>
        msg.role === 'user'
          ? <UserBubble key={i} msg={msg} />
          : <AssistantBubble key={i} msg={msg} />
      )}
      {(status === 'connecting' || status === 'streaming') && (
        <div className="flex items-start gap-3">
          <div className="shrink-0 size-8 rounded-full bg-sky-500/20 flex items-center justify-center">
            <Brain size={16} className="text-sky-400" />
          </div>
          <div className="flex-1 max-w-sm">
            <AgentStatusTracker status={status} events={events} />
          </div>
        </div>
      )}
    </div>
  );
}
