/**
 * useOllamaStatus — Non-blocking Ollama health check hook
 */
interface OllamaStatus {
    checking: boolean;
    running: boolean;
    model?: string;
}
export declare function useOllamaStatus(): OllamaStatus;
export {};
//# sourceMappingURL=useOllamaStatus.d.ts.map