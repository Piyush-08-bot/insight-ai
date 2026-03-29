/**
 * useStreaming — Manages streaming state for Python bridge output
 */
import { useState, useCallback, useRef } from 'react';
import { streamChat } from '../python-bridge.js';
export function useStreaming() {
    const [state, setState] = useState({
        isStreaming: false,
        content: '',
        sources: [],
        sessionId: null,
        subSteps: [],
        error: null,
        elapsed: null,
    });
    const procRef = useRef(null);
    const startTimeRef = useRef(0);
    const startStream = useCallback((question, options = {}) => {
        startTimeRef.current = Date.now();
        setState({
            isStreaming: true,
            content: '',
            sources: [],
            sessionId: null,
            subSteps: [
                { label: 'Retrieving context', status: 'active' },
                { label: 'Researching codebase', status: 'pending' },
                { label: 'Synthesizing answer', status: 'pending' },
            ],
            error: null,
            elapsed: null,
        });
        procRef.current = streamChat(question, options, (chunk) => {
            setState((prev) => {
                const next = { ...prev };
                if (chunk.status) {
                    // Update sub-steps based on status
                    const steps = [...prev.subSteps];
                    if (chunk.status.includes('Retrieving')) {
                        steps[0] = { ...steps[0], status: 'active' };
                    }
                    else if (chunk.status.includes('Researching')) {
                        steps[0] = { ...steps[0], status: 'done' };
                        steps[1] = { ...steps[1], status: 'active' };
                    }
                    else if (chunk.status.includes('Synthesizing')) {
                        steps[0] = { ...steps[0], status: 'done' };
                        steps[1] = { ...steps[1], status: 'done' };
                        steps[2] = { ...steps[2], status: 'active' };
                    }
                    next.subSteps = steps;
                }
                if (chunk.token) {
                    next.content = prev.content + chunk.token;
                    // Once tokens flow, mark synthesis as active
                    const steps = [...next.subSteps];
                    steps[0] = { ...steps[0], status: 'done' };
                    steps[1] = { ...steps[1], status: 'done' };
                    steps[2] = { ...steps[2], status: 'active' };
                    next.subSteps = steps;
                }
                if (chunk.sources)
                    next.sources = chunk.sources;
                if (chunk.session_id)
                    next.sessionId = chunk.session_id;
                if (chunk.final) {
                    const steps = next.subSteps.map((s) => ({ ...s, status: 'done' }));
                    next.subSteps = steps;
                    next.isStreaming = false;
                    next.elapsed = (Date.now() - startTimeRef.current) / 1000;
                }
                if (chunk.error) {
                    next.error = chunk.error;
                    next.isStreaming = false;
                }
                return next;
            });
        }, () => {
            setState((prev) => ({
                ...prev,
                isStreaming: false,
                elapsed: prev.elapsed ?? (Date.now() - startTimeRef.current) / 1000,
                subSteps: prev.subSteps.map((s) => ({ ...s, status: 'done' })),
            }));
        }, (err) => {
            setState((prev) => ({
                ...prev,
                isStreaming: false,
                error: err.message,
            }));
        });
    }, []);
    const cancelStream = useCallback(() => {
        procRef.current?.kill();
        setState((prev) => ({
            ...prev,
            isStreaming: false,
            subSteps: prev.subSteps.map((s) => s.status === 'active' ? { ...s, status: 'error' } : s),
        }));
    }, []);
    return { ...state, startStream, cancelStream };
}
//# sourceMappingURL=useStreaming.js.map