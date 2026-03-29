/**
 * useOllamaStatus — Non-blocking Ollama health check hook
 */
import { useState, useEffect } from 'react';
import { checkOllamaStatus } from '../python-bridge.js';
export function useOllamaStatus() {
    const [status, setStatus] = useState({
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
//# sourceMappingURL=useOllamaStatus.js.map