/**
 * useOllamaStatus — Non-blocking Ollama health check hook
 */

import { useState, useEffect } from 'react';
import { checkOllamaStatus } from '../python-bridge.js';

interface OllamaStatus {
  checking: boolean;
  running: boolean;
  model?: string;
}

export function useOllamaStatus(): OllamaStatus {
  const [status, setStatus] = useState<OllamaStatus>({
    checking: true,
    running: false,
  });

  useEffect(() => {
    checkOllamaStatus().then((result) => {
      setStatus({
        checking: false,
        running: result.running,
        model: result.model,
      });
    }).catch(() => {
      setStatus({ checking: false, running: false });
    });
  }, []);

  return status;
}
