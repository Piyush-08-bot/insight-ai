import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Chat — Full-screen conversational UI with streaming, command palette, and history.
 */
import React, { useState, useCallback, useMemo } from 'react';
import { Box, Text, useApp, useInput } from 'ink';
import TextInput from 'ink-text-input';
import figures from 'figures';
import { Header } from './Header.js';
import { MessageBubble } from './MessageBubble.js';
import { StatusBar } from './StatusBar.js';
import { CommandPalette } from './CommandPalette.js';
import { useTheme } from '../theme.js';
import { useStreaming } from '../hooks/useStreaming.js';
import { useInputHistory } from '../hooks/useInputHistory.js';
import { setTheme, getConfig } from '../config.js';
import { getThemeNames } from '../theme.js';
export function Chat({ provider = 'ollama', model, persistDir, initialQuery }) {
    const { exit } = useApp();
    const theme = useTheme();
    const streaming = useStreaming();
    const history = useInputHistory();
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([
        {
            id: 'system-0',
            role: 'system',
            content: 'Session started',
            timestamp: new Date(),
        },
    ]);
    const [showPalette, setShowPalette] = useState(false);
    const [paletteIndex, setPaletteIndex] = useState(0);
    const [exitPending, setExitPending] = useState(false);
    // ─── Commands ──────────────────────────────────────────────
    const commands = useMemo(() => [
        { name: 'help', description: 'Show available commands', action: () => addSystemMsg('Type a question to chat, /theme to switch themes, /clear to reset') },
        { name: 'clear', description: 'Clear chat history', action: () => setMessages([{ id: `sys-${Date.now()}`, role: 'system', content: 'Chat cleared', timestamp: new Date() }]) },
        { name: 'theme', args: 'name', description: 'Switch theme (forest/light/aurora)', action: () => { } },
        { name: 'exit', description: 'Exit INsight', action: () => exit() },
        { name: 'model', args: 'name', description: 'Show or set LLM model', action: () => addSystemMsg(`Current model: ${getConfig().model}`) },
    ], []);
    function addSystemMsg(content) {
        setMessages((prev) => [...prev, {
                id: `sys-${Date.now()}`,
                role: 'system',
                content,
                timestamp: new Date(),
            }]);
    }
    // ─── Submit Handler ────────────────────────────────────────
    const handleSubmit = useCallback((value) => {
        const trimmed = value.trim();
        if (!trimmed)
            return;
        // Close palette if open
        setShowPalette(false);
        // Handle commands
        if (trimmed.startsWith('/')) {
            const parts = trimmed.slice(1).split(' ');
            const cmdName = parts[0]?.toLowerCase();
            const cmdArg = parts.slice(1).join(' ');
            if (cmdName === 'theme') {
                const validThemes = getThemeNames();
                if (cmdArg && validThemes.includes(cmdArg)) {
                    setTheme(cmdArg);
                    addSystemMsg(`Theme switched to ${cmdArg}`);
                }
                else {
                    addSystemMsg(`Available themes: ${validThemes.join(', ')}`);
                }
            }
            else {
                const cmd = commands.find((c) => c.name === cmdName);
                if (cmd)
                    cmd.action();
                else
                    addSystemMsg(`Unknown command: /${cmdName}`);
            }
            setInput('');
            history.addEntry(trimmed);
            return;
        }
        // Add user message
        const userMsg = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: trimmed,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMsg]);
        history.addEntry(trimmed);
        setInput('');
        // Start streaming response
        const assistantId = `asst-${Date.now()}`;
        setMessages((prev) => [...prev, {
                id: assistantId,
                role: 'assistant',
                content: '',
                isStreaming: true,
                subSteps: [
                    { label: 'Retrieving context', status: 'active' },
                    { label: 'Researching codebase', status: 'pending' },
                    { label: 'Synthesizing answer', status: 'pending' },
                ],
                timestamp: new Date(),
            }]);
        streaming.startStream(trimmed, { provider, model, persistDir });
    }, [provider, model, persistDir, commands, history, streaming]);
    // Update the last assistant message with streaming state
    const subStepsKey = JSON.stringify(streaming.subSteps.map(s => s.status));
    React.useEffect(() => {
        if (streaming.content || streaming.isStreaming) {
            setMessages((prev) => {
                const msgs = [...prev];
                const lastAsst = msgs.findLastIndex((m) => m.role === 'assistant');
                if (lastAsst >= 0) {
                    msgs[lastAsst] = {
                        ...msgs[lastAsst],
                        content: streaming.content,
                        isStreaming: streaming.isStreaming,
                        subSteps: streaming.subSteps,
                        elapsed: streaming.elapsed ?? undefined,
                    };
                }
                return msgs;
            });
        }
    }, [streaming.content, streaming.isStreaming, subStepsKey, streaming.elapsed]);
    // ─── Keyboard Input ────────────────────────────────────────
    useInput((ch, key) => {
        // Ctrl+C double-press
        if (key.ctrl && ch === 'c') {
            if (streaming.isStreaming) {
                streaming.cancelStream();
                return;
            }
            if (exitPending) {
                exit();
                return;
            }
            setExitPending(true);
            addSystemMsg('Press Ctrl+C again to exit');
            setTimeout(() => setExitPending(false), 2000);
            return;
        }
        // Escape — cancel stream
        if (key.escape) {
            if (streaming.isStreaming)
                streaming.cancelStream();
            if (showPalette)
                setShowPalette(false);
            return;
        }
        // Slash — open palette
        if (ch === '/' && !input && !showPalette) {
            setShowPalette(true);
            setInput('/');
            return;
        }
        // Arrow up/down — history
        if (key.upArrow && !showPalette) {
            setInput(history.navigateUp());
            return;
        }
        if (key.downArrow && !showPalette) {
            setInput(history.navigateDown());
            return;
        }
        // Palette navigation
        if (showPalette && key.upArrow) {
            setPaletteIndex((i) => Math.max(0, i - 1));
            return;
        }
        if (showPalette && key.downArrow) {
            setPaletteIndex((i) => i + 1);
            return;
        }
    });
    // Handle initial query
    React.useEffect(() => {
        if (initialQuery) {
            handleSubmit(initialQuery);
        }
    }, []);
    return (_jsxs(Box, { flexDirection: "column", height: "100%", children: [_jsx(Header, { provider: provider, model: model }), _jsx(Box, { flexDirection: "column", flexGrow: 1, gap: 1, paddingX: 1, children: messages.map((msg) => (_jsx(MessageBubble, { message: msg }, msg.id))) }), showPalette && (_jsx(CommandPalette, { commands: commands, filter: input, selectedIndex: paletteIndex, onSelect: (cmd) => {
                    setShowPalette(false);
                    setInput('');
                    cmd.action();
                }, onClose: () => {
                    setShowPalette(false);
                    setInput('');
                } })), _jsxs(Box, { flexDirection: "column", children: [_jsx(Box, { paddingX: 1, children: _jsx(Text, { color: theme.borderHex, children: '─'.repeat(56) }) }), _jsxs(Box, { paddingX: 1, children: [_jsx(Box, { marginRight: 1, children: _jsx(Text, { color: theme.primaryHex, bold: true, children: "\u276F" }) }), _jsx(TextInput, { value: input, onChange: setInput, onSubmit: handleSubmit, placeholder: streaming.isStreaming ? 'Waiting for response...' : 'Ask about your code...' })] }), _jsx(Box, { paddingX: 1, children: _jsx(Text, { color: theme.borderHex, children: '─'.repeat(56) }) }), _jsxs(Box, { paddingX: 1, gap: 2, children: [_jsxs(Text, { color: theme.secondaryHex, children: [figures.star, " ", provider.charAt(0).toUpperCase() + provider.slice(1), " ", model ? `(${model})` : ''] }), _jsx(Text, { color: theme.dimHex, children: "/  commands" }), _jsx(Text, { color: theme.dimHex, children: "\u2191\u2193  history" }), _jsx(Text, { color: theme.dimHex, children: "esc  cancel" })] })] }), _jsx(StatusBar, { sessionId: streaming.sessionId, messageCount: messages.filter((m) => m.role !== 'system').length })] }));
}
//# sourceMappingURL=Chat.js.map