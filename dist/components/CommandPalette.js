import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
/**
 * CommandPalette — Slash-command popup with live filtering.
 */
import { useMemo } from 'react';
import { Box, Text } from 'ink';
import figures from 'figures';
import { useTheme } from '../theme.js';
export function CommandPalette({ commands, filter, selectedIndex, onSelect, onClose }) {
    const theme = useTheme();
    const filtered = useMemo(() => {
        const query = filter.replace(/^\//, '').toLowerCase();
        if (!query)
            return commands;
        return commands.filter((c) => c.name.toLowerCase().includes(query) ||
            c.description.toLowerCase().includes(query));
    }, [commands, filter]);
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: theme.primaryHex, paddingX: 1, marginBottom: 1, children: [_jsxs(Box, { marginBottom: 0, children: [_jsxs(Text, { color: theme.primaryHex, bold: true, children: [figures.pointer, " Commands"] }), _jsx(Text, { color: theme.dimHex, children: " (type to filter, Enter to select, Esc to close)" })] }), filtered.length === 0 ? (_jsx(Text, { color: theme.dimHex, children: "No matching commands" })) : (filtered.map((cmd, i) => (_jsxs(Box, { flexDirection: "row", gap: 1, children: [_jsx(Text, { color: i === selectedIndex ? theme.primaryHex : theme.dimHex, children: i === selectedIndex ? figures.pointer : ' ' }), _jsxs(Text, { color: i === selectedIndex ? theme.primaryHex : theme.secondaryHex, bold: true, children: ["/", cmd.name] }), cmd.args && (_jsxs(Text, { color: theme.dimHex, children: ["<", cmd.args, ">"] })), _jsxs(Text, { color: theme.dimHex, children: [" \u2014 ", cmd.description] })] }, cmd.name))))] }));
}
//# sourceMappingURL=CommandPalette.js.map