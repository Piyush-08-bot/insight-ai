import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';
import { useTheme } from '../theme.js';
import { useOllamaStatus } from '../hooks/useOllamaStatus.js';
import figures from 'figures';
const ASCII_LOGO = [
    '  ╦╔╗╔╔═╗╦╔═╗╦ ╦╔╦╗',
    '  ║║║║╚═╗║║ ╦╠═╣ ║ ',
    '  ╩╝╚╝╚═╝╩╚═╝╩ ╩ ╩ ',
];
export function Header({ provider = 'ollama', model }) {
    const theme = useTheme();
    const ollama = useOllamaStatus();
    return (_jsxs(Box, { flexDirection: "column", marginBottom: 1, children: [_jsx(Box, { flexDirection: "column", alignItems: "center", children: ASCII_LOGO.map((line, i) => (_jsx(Text, { color: theme.primaryHex, bold: true, children: line }, i))) }), _jsx(Box, { justifyContent: "center", marginTop: 0, children: _jsxs(Text, { color: theme.dimHex, children: ['✨', " AI-Powered Code Intelligence Engine"] }) }), _jsxs(Box, { marginTop: 1, justifyContent: "center", gap: 2, children: [_jsx(Box, { children: provider === 'ollama' ? (ollama.checking ? (_jsxs(Text, { color: theme.dimHex, children: [_jsx(Spinner, { type: "dots" }), " Checking Ollama..."] })) : ollama.running ? (_jsxs(Text, { color: theme.successHex, children: [figures.tick, " Ollama ", ollama.model ? `(${ollama.model})` : ''] })) : (_jsxs(Text, { color: theme.warningHex, children: [figures.warning, " Ollama offline"] }))) : (_jsxs(Text, { color: theme.secondaryHex, children: [figures.star, " ", provider.charAt(0).toUpperCase() + provider.slice(1), " ", model ? `(${model})` : ''] })) }), _jsx(Text, { color: theme.borderHex, children: "\u2502" }), _jsx(Text, { color: theme.dimHex, children: "v1.0.0" })] }), _jsx(Box, { marginTop: 1, justifyContent: "center", children: _jsx(Text, { color: theme.borderHex, children: '─'.repeat(44) }) })] }));
}
//# sourceMappingURL=Header.js.map