'use client';

import { useState, useRef, useEffect } from 'react';
import { Brain, Send, Loader2 } from 'lucide-react';
import ResearchCopilotChat from '@/components/ResearchCopilotChat';
import { api } from '@/lib/api';
import { useSSE } from '@/lib/hooks/useSSE';
import type { CopilotMessage, Paper, ResearchGap, Hypothesis } from '@/lib/types';

const SUGGESTIONS = [
  'What do we know about gut microbiome and cancer immunotherapy?',
  'What are the key gaps in CRISPR gene therapy for neurodegeneration?',
  'Generate hypotheses for mRNA vaccines in autoimmune diseases',
  'Summarize recent advances in spatial transcriptomics',
];

export default function CopilotPage() {
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [input, setInput] = useState('');
  const { status, events, result, start, close } = useSSE();
  const bottomRef = useRef<HTMLDivElement>(null);
  const pendingQuery = useRef('');

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, status]);

  useEffect(() => {
    if (status === 'done' && result && pendingQuery.current) {
      const r = result as {
        summary?: string; context_summary?: string;
        papers_used?: Paper[]; research_gaps?: ResearchGap[];
        hypotheses?: Hypothesis[];
      };
      const content = r.summary || r.context_summary || 'Analysis complete. See details below.';
      const assistantMsg: CopilotMessage = {
        role: 'assistant',
        content,
        papers: r.papers_used,
        gaps: r.research_gaps,
        hypotheses: r.hypotheses,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev: CopilotMessage[]) => [...prev, assistantMsg]);
      pendingQuery.current = '';
    }
  }, [status, result]);

  const handleSend = async (msg?: string) => {
    const text = (msg ?? input).trim();
    if (!text || status === 'connecting' || status === 'streaming') return;

    close();
    setInput('');
    pendingQuery.current = text;

    setMessages((prev: CopilotMessage[]) => [...prev, {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }]);

    const job = await api.copilot({ message: text });
    start(job.job_id);
  };

  const isLoading = status === 'connecting' || status === 'streaming';

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] max-h-[900px]">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-2">
          <Brain className="text-cyan-400" size={24} />
          Research Copilot
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Ask anything about life sciences research. Auto-detects intent: summarize, gap detection, or hypotheses.
        </p>
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && !isLoading && (
          <div className="text-center py-16 space-y-6">
            <Brain size={48} className="mx-auto text-cyan-400 opacity-30" />
            <p className="text-gray-500">Ask a research question to get started</p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => handleSend(s)}
                  className="text-xs px-3 py-1.5 rounded-full border border-white/10 text-gray-400 hover:border-cyan-500/40 hover:text-cyan-300 transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <ResearchCopilotChat messages={messages} status={status} events={events} />
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-white/10 pt-4">
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Ask a research question… (Enter to send, Shift+Enter for newline)"
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-gray-200 placeholder-gray-600 resize-none focus:outline-none focus:border-cyan-500/50 min-h-[52px] max-h-32"
            rows={1}
            disabled={isLoading}
          />
          <button
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
            className="btn-primary px-4 flex items-center gap-2 self-end disabled:opacity-50"
          >
            {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            {isLoading ? 'Thinking…' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
