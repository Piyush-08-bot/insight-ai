/**
 * useInputHistory — Bash-like input history with ↑/↓ navigation
 */
import { useState, useCallback } from 'react';
export function useInputHistory(maxSize = 50) {
    const [history, setHistory] = useState([]);
    const [index, setIndex] = useState(-1);
    const addEntry = useCallback((entry) => {
        if (!entry.trim())
            return;
        setHistory((prev) => {
            const next = [entry, ...prev.filter((h) => h !== entry)];
            return next.length > maxSize ? next.slice(0, maxSize) : next;
        });
        setIndex(-1);
    }, [maxSize]);
    const navigateUp = useCallback(() => {
        const newIndex = Math.min(index + 1, history.length - 1);
        setIndex(newIndex);
        return history[newIndex] || '';
    }, [history, index]);
    const navigateDown = useCallback(() => {
        const newIndex = Math.max(index - 1, -1);
        setIndex(newIndex);
        return newIndex === -1 ? '' : (history[newIndex] || '');
    }, [history, index]);
    const reset = useCallback(() => {
        setIndex(-1);
    }, []);
    return { history, index, navigateUp, navigateDown, addEntry, reset };
}
//# sourceMappingURL=useInputHistory.js.map