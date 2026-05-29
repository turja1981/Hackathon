'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { AgentEvent, JobResult, SSEDoneEvent } from '../types';
import { api } from '../api';

export type SSEStatus = 'idle' | 'connecting' | 'streaming' | 'done' | 'error';

interface UseSSEState {
  status: SSEStatus;
  events: AgentEvent[];
  result: JobResult['result'] | null;
  error: string | null;
}

export function useSSE() {
  const [state, setState] = useState<UseSSEState>({
    status: 'idle',
    events: [],
    result: null,
    error: null,
  });
  const esRef = useRef<EventSource | null>(null);

  const close = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
  }, []);

  const start = useCallback((jobId: string) => {
    close();
    setState({ status: 'connecting', events: [], result: null, error: null });

    const es = new EventSource(api.streamUrl(jobId));
    esRef.current = es;

    es.addEventListener('connected', () => {
      setState(s => ({ ...s, status: 'streaming' }));
    });

    es.addEventListener('agent_update', (e: MessageEvent) => {
      try {
        const event: AgentEvent = JSON.parse(e.data);
        setState(s => ({ ...s, events: [...s.events, event] }));
      } catch {
        // malformed event – ignore
      }
    });

    es.addEventListener('done', (e: MessageEvent) => {
      try {
        const done: SSEDoneEvent = JSON.parse(e.data);
        setState(s => ({
          ...s,
          status: done.error ? 'error' : 'done',
          result: done.result ?? null,
          error: done.error ?? null,
        }));
      } catch {
        setState(s => ({ ...s, status: 'done' }));
      }
      es.close();
    });

    es.onerror = () => {
      setState(s => ({ ...s, status: 'error', error: 'Stream connection lost.' }));
      es.close();
    };
  }, [close]);

  // Clean up on unmount
  useEffect(() => () => close(), [close]);

  return { ...state, start, close };
}
