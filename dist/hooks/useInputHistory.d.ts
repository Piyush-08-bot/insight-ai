/**
 * useInputHistory — Bash-like input history with ↑/↓ navigation
 */
interface InputHistory {
    history: string[];
    index: number;
    navigateUp: () => string;
    navigateDown: () => string;
    addEntry: (entry: string) => void;
    reset: () => void;
}
export declare function useInputHistory(maxSize?: number): InputHistory;
export {};
//# sourceMappingURL=useInputHistory.d.ts.map