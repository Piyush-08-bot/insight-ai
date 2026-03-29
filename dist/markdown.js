import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Box, Text, useStdout } from 'ink';
// ─── Inline Transforms ─────────────────────────────────────────
/**
 * Apply inline markdown transforms: **bold**, `code`, *italic*
 * Returns an array of React elements for a single line.
 */
function renderInline(text, theme) {
    const nodes = [];
    // Combined regex: bold, inline code, or plain text
    const regex = /(\*\*(.+?)\*\*|`([^`]+?)`)/g;
    let lastIndex = 0;
    let match;
    let key = 0;
    while ((match = regex.exec(text)) !== null) {
        // Push text before match
        if (match.index > lastIndex) {
            nodes.push(_jsx(Text, { children: text.slice(lastIndex, match.index) }, key++));
        }
        if (match[2]) {
            // **bold** → theme.primary + bold
            nodes.push(_jsx(Text, { color: theme.primaryHex, bold: true, children: match[2] }, key++));
        }
        else if (match[3]) {
            // `code` → theme.code
            nodes.push(_jsx(Text, { color: theme.infoHex, dimColor: true, children: match[3] }, key++));
        }
        lastIndex = match.index + match[0].length;
    }
    // Push remaining text
    if (lastIndex < text.length) {
        nodes.push(_jsx(Text, { children: text.slice(lastIndex) }, key++));
    }
    if (nodes.length === 0) {
        nodes.push(_jsx(Text, { children: text }, 0));
    }
    return nodes;
}
// ─── Code Block Keyword Highlighter ─────────────────────────────
function highlightCode(line, theme) {
    const comments = /(#.*$|\/\/.*$)/g;
    // Simple approach: split by keywords and colorize
    const parts = [];
    let remaining = line;
    let key = 0;
    // Check for comment first
    const commentMatch = remaining.match(comments);
    if (commentMatch && commentMatch.index !== undefined) {
        const beforeComment = remaining.slice(0, commentMatch.index);
        const commentText = commentMatch[0];
        remaining = beforeComment;
        // Process beforeComment for keywords, then add comment
        parts.push(...highlightKeywords(remaining, theme, key));
        key += 100;
        parts.push(_jsx(Text, { color: theme.dimHex, children: commentText }, key++));
        return _jsx(Text, { children: parts });
    }
    parts.push(...highlightKeywords(remaining, theme, key));
    return _jsx(Text, { children: parts });
}
function highlightKeywords(text, theme, startKey) {
    const parts = [];
    const keywords = /\b(def|class|import|from|return|if|else|elif|for|while|in|not|and|or|try|except|finally|with|as|yield|async|await|const|let|var|function|export|interface|type|extends|implements|new|this|self|True|False|None|null|undefined|true|false)\b/g;
    let lastIdx = 0;
    let match;
    let key = startKey;
    while ((match = keywords.exec(text)) !== null) {
        if (match.index > lastIdx) {
            parts.push(_jsx(Text, { children: text.slice(lastIdx, match.index) }, key++));
        }
        parts.push(_jsx(Text, { color: theme.primaryHex, children: match[0] }, key++));
        lastIdx = match.index + match[0].length;
    }
    if (lastIdx < text.length) {
        parts.push(_jsx(Text, { children: text.slice(lastIdx) }, key++));
    }
    return parts;
}
function detectLineType(line) {
    const trimmed = line.trim();
    // Empty line
    if (!trimmed) {
        return { type: 'empty', raw: line };
    }
    // 1. Phase header variations: [PHASE N], Phase N: Title, Phase N - Title
    const phaseMatch = trimmed.match(/^(?:\[?PHASE\s+(\d+)\]?|PHASE\s+(\d+))[:\s-]*(.+)/i);
    if (phaseMatch) {
        return {
            type: 'phase_header',
            raw: line,
            phaseNumber: parseInt(phaseMatch[1] || phaseMatch[2]),
            phaseTitle: phaseMatch[3].trim(),
        };
    }
    // 2. Code fence open: ```lang
    const codeFenceOpen = trimmed.match(/^```(\w*)$/);
    if (codeFenceOpen && trimmed.length > 2) {
        return {
            type: 'code_fence_open',
            raw: line,
            codeLang: codeFenceOpen[1] || '',
        };
    }
    // 3. Code fence close: ```
    if (trimmed === '```') {
        return { type: 'code_fence_close', raw: line };
    }
    // 4. Heading: # ## ###
    const headingMatch = trimmed.match(/^(#{1,3})\s+(.+)/);
    if (headingMatch) {
        return {
            type: 'heading',
            raw: line,
            headingLevel: headingMatch[1].length,
            headingText: headingMatch[2],
        };
    }
    // 5. Horizontal rule
    if (/^[-=─]{3,}$/.test(trimmed) || /^[─━═]{3,}$/.test(trimmed)) {
        return { type: 'horizontal_rule', raw: line };
    }
    // 6. Bullet item: - text or * text (with optional indent)
    const bulletMatch = line.match(/^(\s*)[*\-•›]\s+(.+)/);
    if (bulletMatch) {
        return {
            type: 'bullet',
            raw: line,
            bulletIndent: bulletMatch[1].length,
            bulletText: bulletMatch[2],
        };
    }
    // 7. Numbered item: 1. text
    const numberedMatch = trimmed.match(/^(\d+)\.\s+(.+)/);
    if (numberedMatch) {
        return {
            type: 'numbered',
            raw: line,
            numberValue: numberedMatch[1],
            numberText: numberedMatch[2],
        };
    }
    // 8. Tree line: contains ├ └ │ followed by text
    if (/^[\s│├└─┌┐┘┤┬┴┼]+\w/.test(trimmed)) {
        return { type: 'tree_line', raw: line };
    }
    // 9. Key:Value line (only if it looks structured, not prose with colons)
    const kvMatch = trimmed.match(/^([A-Z][\w\s]{0,25}):\s+(.+)/);
    if (kvMatch && !trimmed.includes('.') && trimmed.length < 80) {
        return {
            type: 'key_value',
            raw: line,
            keyText: kvMatch[1],
            valueText: kvMatch[2],
        };
    }
    // 10. Plain text (fallback)
    return { type: 'plain', raw: line };
}
/**
 * Parse raw text into content blocks (phases, code blocks, regular lines)
 */
function parseIntoBlocks(text) {
    const rawLines = text.split('\n');
    const blocks = [];
    let currentBlock = { type: 'lines', lines: [] };
    let inCodeBlock = false;
    for (const line of rawLines) {
        const detected = detectLineType(line);
        if (inCodeBlock) {
            if (detected.type === 'code_fence_close') {
                // Close code block
                blocks.push(currentBlock);
                currentBlock = { type: 'lines', lines: [] };
                inCodeBlock = false;
            }
            else {
                currentBlock.lines.push(line);
            }
            continue;
        }
        if (detected.type === 'code_fence_open') {
            // Save any pending lines
            if (currentBlock.lines.length > 0) {
                blocks.push(currentBlock);
            }
            currentBlock = {
                type: 'code',
                codeLang: detected.codeLang,
                lines: [],
            };
            inCodeBlock = true;
            continue;
        }
        if (detected.type === 'phase_header') {
            // Save any pending lines
            if (currentBlock.lines.length > 0) {
                blocks.push(currentBlock);
            }
            currentBlock = {
                type: 'phase',
                phaseNumber: detected.phaseNumber,
                phaseTitle: detected.phaseTitle,
                lines: [],
            };
            continue;
        }
        // Default: add to current block
        currentBlock.lines.push(line);
    }
    // Flush remaining
    if (currentBlock.lines.length > 0) {
        blocks.push(currentBlock);
    }
    return blocks;
}
// ─── React Components for Each Block Type ───────────────────────
function PhaseBlock({ phaseNumber, phaseTitle, lines, theme, isStreaming, columns, }) {
    const content = lines.join('\n').trim();
    return (_jsxs(Box, { flexDirection: "column", marginTop: 1, borderStyle: "round", borderColor: theme.borderHex, paddingX: 1, children: [_jsx(Box, { position: "absolute", marginTop: -1, marginLeft: 1, children: _jsxs(Text, { backgroundColor: "black", children: [_jsxs(Text, { color: theme.dimHex, children: [" PHASE ", phaseNumber, " "] }), _jsx(Text, { color: theme.primaryHex, bold: true, children: phaseTitle.slice(0, Math.max(0, columns - 30)) })] }) }), content && (_jsx(Box, { flexDirection: "column", paddingY: 0, children: _jsx(StyledLines, { text: content, theme: theme }) })), isStreaming && (_jsx(Box, { children: _jsx(Text, { color: theme.primaryHex, children: "\u258C" }) }))] }));
}
function CodeBlock({ lang, lines, theme, }) {
    return (_jsxs(Box, { flexDirection: "column", marginTop: 1, marginBottom: 1, borderStyle: "single", borderColor: theme.dimHex, paddingX: 1, children: [_jsx(Box, { position: "absolute", marginTop: -1, marginLeft: 1, children: _jsx(Text, { backgroundColor: "black", children: _jsxs(Text, { color: theme.infoHex, children: [" ", lang || 'code', " "] }) }) }), _jsx(Box, { flexDirection: "column", children: lines.map((line, i) => (_jsx(Box, { children: _jsx(Box, { flexGrow: 1, children: highlightCode(line, theme) }) }, i))) })] }));
}
/**
 * Render styled lines — applies the detection waterfall to each line
 */
function StyledLines({ text, theme, }) {
    const lines = text.split('\n');
    return (_jsx(Box, { flexDirection: "column", children: lines.map((line, i) => {
            const detected = detectLineType(line);
            switch (detected.type) {
                case 'empty':
                    return _jsx(Box, { height: 1 }, i);
                case 'heading':
                    return (_jsx(Box, { marginTop: 1, marginBottom: 0, children: _jsx(Text, { color: theme.primaryHex, bold: true, underline: true, children: detected.headingText }) }, i));
                case 'bullet':
                    return (_jsxs(Box, { marginLeft: detected.bulletIndent ?? 0, children: [_jsxs(Text, { color: theme.primaryHex, children: ['›', " "] }), _jsx(Text, { wrap: "wrap", children: renderInline(detected.bulletText, theme) })] }, i));
                case 'numbered':
                    return (_jsxs(Box, { children: [_jsxs(Text, { color: theme.primaryHex, children: [detected.numberValue, ". "] }), _jsx(Text, { wrap: "wrap", children: renderInline(detected.numberText, theme) })] }, i));
                case 'horizontal_rule':
                    return (_jsx(Box, { paddingY: 0, children: _jsx(Text, { color: theme.dimHex, children: '─'.repeat(20) }) }, i));
                case 'tree_line':
                    return (_jsx(Box, { children: _jsx(Text, { children: line.split('').map((ch, ci) => '├└│─┌┐┘┤┬┴┼'.includes(ch) ? (_jsx(Text, { color: theme.primaryHex, children: ch }, ci)) : (_jsx(Text, { children: ch }, ci))) }) }, i));
                case 'key_value':
                    return (_jsxs(Box, { children: [_jsxs(Text, { color: theme.secondaryHex, children: [detected.keyText, ": "] }), _jsx(Text, { color: theme.primaryHex, children: detected.valueText })] }, i));
                case 'plain':
                default:
                    return (_jsx(Box, { children: _jsx(Text, { wrap: "wrap", children: renderInline(line, theme) }) }, i));
            }
        }) }));
}
// ─── Main Export: renderMarkdown ─────────────────────────────────
/**
 * Renders raw AI output text as beautiful styled React elements.
 * Handles phases, code blocks, headings, bullets, bold, inline code,
 * and falls back to plain styled text for anything else.
 */
export function RenderMarkdown({ text, theme, isStreaming = false, }) {
    const { stdout } = useStdout();
    const columns = stdout?.columns || 80;
    if (!text.trim()) {
        if (isStreaming) {
            return (_jsx(Box, { marginLeft: 2, children: _jsx(Text, { color: theme.primaryHex, children: "\u258C" }) }));
        }
        return _jsx(Box, {});
    }
    const blocks = parseIntoBlocks(text);
    return (_jsx(Box, { flexDirection: "column", width: Math.max(20, columns - 10), children: blocks.map((block, i) => {
            const isLastBlock = i === blocks.length - 1;
            switch (block.type) {
                case 'phase':
                    return (_jsx(PhaseBlock, { phaseNumber: block.phaseNumber ?? 0, phaseTitle: block.phaseTitle ?? '', lines: block.lines, theme: theme, isStreaming: isStreaming && isLastBlock, columns: columns }, i));
                case 'code':
                    return (_jsx(CodeBlock, { lang: block.codeLang ?? '', lines: block.lines, theme: theme }, i));
                case 'lines':
                default: {
                    const content = block.lines.join('\n');
                    if (!content.trim())
                        return _jsx(Box, {}, i);
                    return (_jsxs(Box, { flexDirection: "column", marginLeft: 0, children: [_jsx(StyledLines, { text: content, theme: theme }), isStreaming && isLastBlock && (_jsx(Text, { color: theme.primaryHex, children: "\u258C" }))] }, i));
                }
            }
        }) }));
}
export { StyledLines, renderInline };
//# sourceMappingURL=markdown.js.map