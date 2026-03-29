/**
 * useInputHistory — Bash-like input history with ↑/↓ navigation
 */

import { useState, useCallback } from 'react';

interface InputHistory {
  history: string[];
  index: number;
  navigateUp: () => string;
  navigateDown: () => string;
  addEntry: (entry: string) => void;
  reset: () => void;
}

export function useInputHistory(maxSize: number = 50): InputHistory {
  const [history, setHistory] = useState<string[]>([]);
  const [index, setIndex] = useState<number>(-1);

  const addEntry = useCallback((entry: string) => {
    if (!entry.trim()) return;
    setHistory((prev) => {
      const next = [entry, ...prev.filter((h) => h !== entry)];
      return next.length > maxSize ? next.slice(0, maxSize) : next;
    });
    setIndex(-1);
  }, [maxSize]);

  const navigateUp = useCallback((): string => {
    const newIndex = Math.min(index + 1, history.length - 1);
    setIndex(newIndex);
    return history[newIndex] || '';
  }, [history, index]);

  const navigateDown = useCallback((): string => {
    const newIndex = Math.max(index - 1, -1);
    setIndex(newIndex);
    return newIndex === -1 ? '' : (history[newIndex] || '');
  }, [history, index]);

  const reset = useCallback(() => {
    setIndex(-1);
  }, []);

  return { history, index, navigateUp, navigateDown, addEntry, reset };
}
