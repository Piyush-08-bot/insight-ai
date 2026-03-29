import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';
import figures from 'figures';
import { useTheme } from '../theme.js';
import { RenderMarkdown } from '../markdown.js';
export function MessageBubble({ message }) {
    const theme = useTheme();
    // ─── System messages ─────────────────────────────────────
    if (message.role === 'system') {
        return (_jsx(Box, { marginY: 0, justifyContent: "center", children: _jsxs(Text, { color: theme.dimHex, children: ["\u2500\u2500\u2500 ", message.content, " \u2500\u2500\u2500"] }) }));
    }
    // ─── User messages ───────────────────────────────────────
    if (message.role === 'user') {
        return (_jsxs(Box, { flexDirection: "column", marginTop: 1, children: [_jsxs(Box, { flexDirection: "row", children: [_jsx(Text, { color: theme.infoHex, children: "\u25CF" }), _jsx(Text, { color: theme.infoHex, bold: true, children: " You  " }), _jsx(Text, { color: theme.dimHex, children: '─'.repeat(50) })] }), _jsx(Box, { marginLeft: 3, children: _jsx(Text, { wrap: "wrap", children: message.content }) })] }));
    }
    // ─── Assistant messages ──────────────────────────────────
    return (_jsxs(Box, { flexDirection: "column", marginTop: 1, children: [_jsxs(Box, { flexDirection: "row", children: [_jsx(Text, { color: theme.primaryHex, children: "\u25C6" }), _jsxs(Text, { color: theme.primaryHex, bold: true, children: [' ', "INsight", '  '] }), _jsx(Text, { color: theme.dimHex, children: '─'.repeat(48) })] }), message.subSteps && message.subSteps.length > 0 && (_jsxs(Box, { flexDirection: "column", marginLeft: 3, marginTop: 1, children: [message.subSteps.map((step, i) => (_jsxs(Box, { flexDirection: "row", gap: 1, children: [step.status === 'active' ? (_jsx(Text, { color: theme.primaryHex, children: _jsx(Spinner, { type: "dots" }) })) : step.status === 'done' ? (_jsx(Text, { color: theme.successHex, children: figures.tick })) : step.status === 'error' ? (_jsx(Text, { color: theme.errorHex, children: figures.cross })) : (_jsx(Text, { color: theme.dimHex, children: "\u2591" })), _jsx(Text, { color: step.status === 'done'
                                    ? theme.dimHex
                                    : step.status === 'active'
                                        ? undefined
                                        : theme.dimHex, children: step.label })] }, i))), message.content && (_jsx(Box, { marginTop: 0, children: _jsx(Text, { color: theme.dimHex, children: '─'.repeat(36) }) }))] })), message.content && (_jsx(Box, { marginLeft: 3, marginTop: 0, flexDirection: "column", children: _jsx(RenderMarkdown, { text: message.content, theme: theme, isStreaming: message.isStreaming }) })), message.isStreaming && !message.content && (_jsx(Box, { marginLeft: 3, marginTop: 0, children: _jsx(Text, { color: theme.primaryHex, children: "\u258C" }) })), !message.isStreaming && message.content && message.elapsed !== undefined && (_jsxs(Box, { marginLeft: 3, marginTop: 1, children: [_jsxs(Text, { color: theme.successHex, children: [figures.tick, " Complete"] }), _jsxs(Text, { color: theme.dimHex, children: ["  (", message.elapsed.toFixed(1), "s)"] })] }))] }));
}
//# sourceMappingURL=MessageBubble.js.map