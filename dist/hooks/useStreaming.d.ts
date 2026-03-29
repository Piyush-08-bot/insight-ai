/**
 * useStreaming — Manages streaming state for Python bridge output
 */
import type { SubStep } from '../types.js';
interface StreamingState {
    isStreaming: boolean;
    content: string;
    sources: string[];
    sessionId: string | null;
    subSteps: SubStep[];
    error: string | null;
    elapsed: number | null;
}
interface UseStreamingReturn extends StreamingState {
    startStream: (question: string, options?: {
        provider?: string;
        model?: string;
        persistDir?: string;
    }) => void;
    cancelStream: () => void;
}
export declare function useStreaming(): UseStreamingReturn;
export {};
//# sourceMappingURL=useStreaming.d.ts.map