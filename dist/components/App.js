import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * App — Root component that routes to Chat, Analyze, or Setup.
 */
import { useState, useEffect } from 'react';
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';
import figures from 'figures';
import { Chat } from './Chat.js';
import { Header } from './Header.js';
import { useTheme } from '../theme.js';
import { runPythonDirect } from '../python-bridge.js';
export function App({ command, args, flags }) {
    const theme = useTheme();
    // ─── Demo Mode ──────────────────────────────────────────────
    if (flags.demo) {
        return _jsx(DemoMode, { flags: flags });
    }
    // ─── Route by command ──────────────────────────────────────
    switch (command) {
        case 'chat':
            return (_jsx(Chat, { provider: flags.provider, model: flags.model, persistDir: flags.persistDir, initialQuery: args[0] }));
        case 'analyze':
        case 'overview':
        case 'learn':
        case 'architecture':
        case 'deps':
        case 'stories':
        case 'report':
        case 'doctor':
        case 'setup':
            // These commands use Python's Rich CLI for rendering
            return _jsx(PythonPassthrough, { command: command, args: args, flags: flags });
        default:
            return _jsx(PythonPassthrough, { command: command, args: args, flags: flags });
    }
}
// ─── Python Passthrough ─────────────────────────────────────────
// Renders header, then spawns Python for commands not yet ported to Ink
function PythonPassthrough({ command, args, flags }) {
    const theme = useTheme();
    useEffect(() => {
        const cliArgs = [command, ...args];
        if (flags.provider)
            cliArgs.push('--provider', flags.provider);
        if (flags.model)
            cliArgs.push('--model', flags.model);
        if (flags.persistDir)
            cliArgs.push('--persist-dir', flags.persistDir);
        if (flags.output)
            cliArgs.push('--output', flags.output);
        const proc = runPythonDirect(cliArgs);
        proc.on('close', (code) => {
            process.exit(code ?? 0);
        });
        proc.on('error', () => {
            process.exit(1);
        });
    }, []);
    // Render nothing — let Python's Rich CLI own the terminal
    return (_jsx(Box, { children: _jsx(Text, { color: theme.dimHex, children: " " }) }));
}
// ─── Demo Mode ──────────────────────────────────────────────────
function DemoMode({ flags }) {
    const theme = useTheme();
    const [phase, setPhase] = useState(0);
    const [demoText, setDemoText] = useState('');
    const demoResponse = `## Project Overview

**INsight** is an AI-powered code intelligence engine that uses RAG (Retrieval-Augmented Generation) to analyze and understand codebases.

### Key Components
- **Ingestion Layer** — Parses code with AST, extracts metadata
- **Vector Store** — ChromaDB for semantic search
- **RAG Pipeline** — LangChain chains for Q&A, analysis, stories
- **CLI Interface** — Rich terminal UI with streaming responses

### Tech Stack
Python, LangChain, ChromaDB, Ollama, FastAPI, React Ink`;
    useEffect(() => {
        // Phase 0: Show header (instant)
        // Phase 1: Simulate analyze
        const timer1 = setTimeout(() => setPhase(1), 1500);
        // Phase 2: Simulate chat
        const timer2 = setTimeout(() => setPhase(2), 4000);
        // Phase 3: Stream response
        const timer3 = setTimeout(() => {
            setPhase(3);
            let i = 0;
            const streamTimer = setInterval(() => {
                if (i < demoResponse.length) {
                    setDemoText(demoResponse.slice(0, i + 3));
                    i += 3;
                }
                else {
                    clearInterval(streamTimer);
                    setPhase(4);
                }
            }, 15);
        }, 5500);
        return () => {
            clearTimeout(timer1);
            clearTimeout(timer2);
            clearTimeout(timer3);
        };
    }, []);
    return (_jsxs(Box, { flexDirection: "column", children: [_jsx(Header, { provider: flags.provider, model: flags.model }), _jsxs(Box, { flexDirection: "column", paddingX: 1, gap: 1, children: [phase >= 1 && (_jsx(Box, { flexDirection: "column", children: _jsxs(Box, { gap: 1, children: [phase === 1 ? (_jsx(Text, { color: theme.infoHex, children: _jsx(Spinner, { type: "dots" }) })) : (_jsx(Text, { color: theme.successHex, children: figures.tick })), _jsxs(Text, { color: phase > 1 ? theme.dimHex : theme.primaryHex, children: ["Analyzing codebase... ", phase > 1 ? '42 files indexed in 3.2s' : ''] })] }) })), phase >= 2 && (_jsxs(Box, { paddingX: 1, gap: 2, children: [flags.provider && (_jsxs(Text, { color: theme.secondaryHex, children: [figures.star, " ", flags.provider.charAt(0).toUpperCase() + flags.provider.slice(1), " ", flags.model ? `(${flags.model})` : ''] })), _jsx(Text, { color: theme.dimHex, children: "/  commands" })] })), phase >= 3 && (_jsxs(Box, { flexDirection: "column", marginTop: 1, children: [_jsxs(Box, { gap: 1, children: [_jsxs(Text, { color: theme.primaryHex, bold: true, children: ['✨', " INsight"] }), phase === 3 && _jsx(Text, { color: theme.dimHex, children: _jsx(Spinner, { type: "dots" }) }), phase === 4 && _jsxs(Text, { color: theme.successHex, children: [figures.tick, " 4.2s"] })] }), _jsx(Box, { marginLeft: 2, marginTop: 0, children: _jsxs(Text, { wrap: "wrap", children: [demoText, phase === 3 ? '▌' : ''] }) })] })), phase >= 4 && (_jsx(Box, { marginTop: 2, justifyContent: "center", children: _jsx(Text, { color: theme.dimHex, children: "\u2500\u2500\u2500 Demo complete. Run `insight analyze` to try it for real! \u2500\u2500\u2500" }) }))] })] }));
}
//# sourceMappingURL=App.js.map