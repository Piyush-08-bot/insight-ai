import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Box, Text } from 'ink';
import figures from 'figures';
import { useTheme } from '../theme.js';
import { getConfig } from '../config.js';
export function StatusBar({ sessionId, messageCount = 0 }) {
    const theme = useTheme();
    const config = getConfig();
    return (_jsxs(Box, { flexDirection: "column", children: [_jsx(Box, { children: _jsx(Text, { color: theme.borderHex, children: '─'.repeat(44) }) }), _jsxs(Box, { flexDirection: "row", gap: 2, children: [_jsx(Box, { children: _jsxs(Text, { color: theme.dimHex, children: [figures.pointer, " ", config.model] }) }), _jsx(Text, { color: theme.borderHex, children: "\u2502" }), _jsx(Box, { children: _jsxs(Text, { color: theme.dimHex, children: [figures.star, " ", config.theme] }) }), _jsx(Text, { color: theme.borderHex, children: "\u2502" }), _jsx(Box, { children: _jsxs(Text, { color: theme.dimHex, children: [figures.info, " ", messageCount, " msgs"] }) })] })] }));
}
//# sourceMappingURL=StatusBar.js.map