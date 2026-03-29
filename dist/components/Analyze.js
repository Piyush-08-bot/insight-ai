import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Analyze — Codebase analysis with live progress and stats.
 */
import { useState, useEffect, useRef } from 'react';
import { Box, Text, useApp } from 'ink';
import Spinner from 'ink-spinner';
import figures from 'figures';
import { Header } from './Header.js';
import { useTheme } from '../theme.js';
import { runAnalyze, isVenvReady } from '../python-bridge.js';
export function Analyze({ projectPath, provider, model, persistDir, fileTypes, embedding }) {
    const { exit } = useApp();
    const theme = useTheme();
    const [status, setStatus] = useState('Starting analysis...');
    const [lines, setLines] = useState([]);
    const [done, setDone] = useState(false);
    const [error, setError] = useState(null);
    const [elapsed, setElapsed] = useState(0);
    const startTime = useRef(Date.now());
    useEffect(() => {
        const timer = setInterval(() => {
            if (!done)
                setElapsed((Date.now() - startTime.current) / 1000);
        }, 100);
        return () => clearInterval(timer);
    }, [done]);
    useEffect(() => {
        if (!isVenvReady()) {
            setError('Python environment not ready. Run: insight setup');
            return;
        }
        runAnalyze(projectPath, { provider, model, persistDir, fileTypes, embedding }, (progress) => {
            setStatus(progress.status);
            setLines((prev) => [...prev, progress.status]);
            if (progress.done)
                setDone(true);
        }, () => {
            setDone(true);
            setElapsed((Date.now() - startTime.current) / 1000);
        }, (err) => {
            setError(err.message);
        });
    }, []);
    return (_jsxs(Box, { flexDirection: "column", children: [_jsx(Header, {}), _jsxs(Box, { flexDirection: "column", paddingX: 1, gap: 0, children: [_jsx(Box, { marginBottom: 1, children: _jsxs(Text, { color: theme.primaryHex, bold: true, children: [figures.pointer, " Analyzing: ", projectPath] }) }), !done && !error && (_jsxs(Box, { flexDirection: "row", gap: 1, children: [_jsx(Text, { color: theme.infoHex, children: _jsx(Spinner, { type: "dots" }) }), _jsx(Text, { color: theme.dimHex, children: status })] })), _jsx(Box, { flexDirection: "column", marginLeft: 2, marginTop: 1, children: lines.slice(-8).map((line, i) => (_jsxs(Text, { color: theme.dimHex, children: ["  ", line] }, i))) }), error && (_jsx(Box, { marginTop: 1, children: _jsxs(Text, { color: theme.errorHex, children: [figures.cross, " Error: ", error] }) })), done && !error && (_jsxs(Box, { flexDirection: "column", marginTop: 1, children: [_jsxs(Text, { color: theme.successHex, bold: true, children: [figures.tick, " Done in ", elapsed.toFixed(1), "s"] }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { color: theme.dimHex, children: "Run `insight chat` to start asking questions about your code." }) })] })), !done && !error && (_jsx(Box, { marginTop: 1, children: _jsxs(Text, { color: theme.dimHex, children: [elapsed.toFixed(1), "s elapsed"] }) }))] })] }));
}
//# sourceMappingURL=Analyze.js.map