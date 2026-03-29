/**
 * markdown.tsx — Smart Line Detector + Styled Renderer
 *
 * Detects what type of content each line is and renders it beautifully.
 * Implements a waterfall detector: first match wins, fallback to plain text.
 * All colors flow through the Theme object — zero hardcoded colors.
 */

import React from 'react';
import { Box, Text, useStdout } from 'ink';
import type { Theme } from './types.js';

// ─── Inline Transforms ─────────────────────────────────────────

/**
 * Apply inline markdown transforms: **bold**, `code`, *italic*
 * Returns an array of React elements for a single line.
 */
function renderInline(text: string, theme: Theme): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  // Combined regex: bold, inline code, or plain text
  const regex = /(\*\*(.+?)\*\*|`([^`]+?)`)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    // Push text before match
    if (match.index > lastIndex) {
      nodes.push(<Text key={key++}>{text.slice(lastIndex, match.index)}</Text>);
    }

    if (match[2]) {
      // **bold** → theme.primary + bold
      nodes.push(
        <Text key={key++} color={theme.primaryHex} bold>
          {match[2]}
        </Text>
      );
    } else if (match[3]) {
      // `code` → theme.code
      nodes.push(
        <Text key={key++} color={theme.infoHex} dimColor>
          {match[3]}
        </Text>
      );
    }

    lastIndex = match.index + match[0].length;
  }

  // Push remaining text
  if (lastIndex < text.length) {
    nodes.push(<Text key={key++}>{text.slice(lastIndex)}</Text>);
  }

  if (nodes.length === 0) {
    nodes.push(<Text key={0}>{text}</Text>);
  }

  return nodes;
}

// ─── Code Block Keyword Highlighter ─────────────────────────────

function highlightCode(line: string, theme: Theme): React.ReactNode {
  const comments = /(#.*$|\/\/.*$)/g;

  // Simple approach: split by keywords and colorize
  const parts: React.ReactNode[] = [];
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
    parts.push(
      <Text key={key++} color={theme.dimHex}>
        {commentText}
      </Text>
    );
    return <Text>{parts}</Text>;
  }

  parts.push(...highlightKeywords(remaining, theme, key));
  return <Text>{parts}</Text>;
}

function highlightKeywords(
  text: string,
  theme: Theme,
  startKey: number
): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const keywords =
    /\b(def|class|import|from|return|if|else|elif|for|while|in|not|and|or|try|except|finally|with|as|yield|async|await|const|let|var|function|export|interface|type|extends|implements|new|this|self|True|False|None|null|undefined|true|false)\b/g;
  let lastIdx = 0;
  let match: RegExpExecArray | null;
  let key = startKey;

  while ((match = keywords.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(<Text key={key++}>{text.slice(lastIdx, match.index)}</Text>);
    }
    parts.push(
      <Text key={key++} color={theme.primaryHex}>
        {match[0]}
      </Text>
    );
    lastIdx = match.index + match[0].length;
  }

  if (lastIdx < text.length) {
    parts.push(<Text key={key++}>{text.slice(lastIdx)}</Text>);
  }

  return parts;
}

// ─── Line Type Detector ─────────────────────────────────────────

type LineType =
  | 'phase_header'
  | 'code_fence_open'
  | 'code_fence_close'
  | 'heading'
  | 'bullet'
  | 'numbered'
  | 'horizontal_rule'
  | 'tree_line'
  | 'key_value'
  | 'empty'
  | 'plain';

interface DetectedLine {
  type: LineType;
  raw: string;
  // Extracted data
  headingLevel?: number;
  headingText?: string;
  phaseNumber?: number;
  phaseTitle?: string;
  codeLang?: string;
  bulletText?: string;
  bulletIndent?: number;
  numberValue?: string;
  numberText?: string;
  keyText?: string;
  valueText?: string;
}

function detectLineType(line: string): DetectedLine {
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
      phaseNumber: parseInt(phaseMatch[1] || phaseMatch[2]!),
      phaseTitle: phaseMatch[3]!.trim(),
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
      headingLevel: headingMatch[1]!.length,
      headingText: headingMatch[2]!,
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
      bulletIndent: bulletMatch[1]!.length,
      bulletText: bulletMatch[2]!,
    };
  }

  // 7. Numbered item: 1. text
  const numberedMatch = trimmed.match(/^(\d+)\.\s+(.+)/);
  if (numberedMatch) {
    return {
      type: 'numbered',
      raw: line,
      numberValue: numberedMatch[1]!,
      numberText: numberedMatch[2]!,
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
      keyText: kvMatch[1]!,
      valueText: kvMatch[2]!,
    };
  }

  // 10. Plain text (fallback)
  return { type: 'plain', raw: line };
}

// ─── Render Content Block ───────────────────────────────────────

interface ContentBlock {
  type: 'phase' | 'code' | 'lines';
  phaseNumber?: number;
  phaseTitle?: string;
  codeLang?: string;
  lines: string[];
}

/**
 * Parse raw text into content blocks (phases, code blocks, regular lines)
 */
function parseIntoBlocks(text: string): ContentBlock[] {
  const rawLines = text.split('\n');
  const blocks: ContentBlock[] = [];
  let currentBlock: ContentBlock = { type: 'lines', lines: [] };
  let inCodeBlock = false;

  for (const line of rawLines) {
    const detected = detectLineType(line);

    if (inCodeBlock) {
      if (detected.type === 'code_fence_close') {
        // Close code block
        blocks.push(currentBlock);
        currentBlock = { type: 'lines', lines: [] };
        inCodeBlock = false;
      } else {
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

function PhaseBlock({
  phaseNumber,
  phaseTitle,
  lines,
  theme,
  isStreaming,
  columns,
}: {
  phaseNumber: number;
  phaseTitle: string;
  lines: string[];
  theme: Theme;
  isStreaming: boolean;
  columns: number;
}): React.ReactElement {
  const content = lines.join('\n').trim();
  return (
    <Box
      flexDirection="column"
      marginTop={1}
      borderStyle="round"
      borderColor={theme.borderHex}
      paddingX={1}
    >
      {/* Title overlapping border (conceptually) */}
      <Box position="absolute" marginTop={-1} marginLeft={1}>
          <Text backgroundColor="black">
            <Text color={theme.dimHex}> PHASE {phaseNumber} </Text>
            <Text color={theme.primaryHex} bold>
              {phaseTitle.slice(0, Math.max(0, columns - 30))}
            </Text>
          </Text>
      </Box>

      {/* Phase content */}
      {content && (
        <Box flexDirection="column" paddingY={0}>
          <StyledLines text={content} theme={theme} />
        </Box>
      )}

      {isStreaming && (
        <Box>
          <Text color={theme.primaryHex}>▌</Text>
        </Box>
      )}
    </Box>
  );
}

function CodeBlock({
  lang,
  lines,
  theme,
}: {
  lang: string;
  lines: string[];
  theme: Theme;
}): React.ReactElement {
  return (
    <Box
      flexDirection="column"
      marginTop={1}
      marginBottom={1}
      borderStyle="single"
      borderColor={theme.dimHex}
      paddingX={1}
    >
      <Box position="absolute" marginTop={-1} marginLeft={1}>
        <Text backgroundColor="black">
          <Text color={theme.infoHex}> {lang || 'code'} </Text>
        </Text>
      </Box>

      {/* Code lines */}
      <Box flexDirection="column">
        {lines.map((line, i) => (
          <Box key={i}>
            <Box flexGrow={1}>{highlightCode(line, theme)}</Box>
          </Box>
        ))}
      </Box>
    </Box>
  );
}

/**
 * Render styled lines — applies the detection waterfall to each line
 */
function StyledLines({
  text,
  theme,
}: {
  text: string;
  theme: Theme;
}): React.ReactElement {
  const lines = text.split('\n');

  return (
    <Box flexDirection="column">
      {lines.map((line, i) => {
        const detected = detectLineType(line);

        switch (detected.type) {
          case 'empty':
            return <Box key={i} height={1} />;

          case 'heading':
            return (
              <Box key={i} marginTop={1} marginBottom={0}>
                <Text color={theme.primaryHex} bold underline>
                  {detected.headingText}
                </Text>
              </Box>
            );

          case 'bullet':
            return (
              <Box key={i} marginLeft={detected.bulletIndent ?? 0}>
                <Text color={theme.primaryHex}>{'›'} </Text>
                <Text wrap="wrap">{renderInline(detected.bulletText!, theme)}</Text>
              </Box>
            );

          case 'numbered':
            return (
              <Box key={i}>
                <Text color={theme.primaryHex}>{detected.numberValue}. </Text>
                <Text wrap="wrap">
                  {renderInline(detected.numberText!, theme)}
                </Text>
              </Box>
            );

          case 'horizontal_rule':
            return (
              <Box key={i} paddingY={0}>
                <Text color={theme.dimHex}>{'─'.repeat(20)}</Text>
              </Box>
            );

          case 'tree_line':
            return (
              <Box key={i}>
                <Text>
                  {line.split('').map((ch, ci) =>
                    '├└│─┌┐┘┤┬┴┼'.includes(ch) ? (
                      <Text key={ci} color={theme.primaryHex}>
                        {ch}
                      </Text>
                    ) : (
                      <Text key={ci}>{ch}</Text>
                    )
                  )}
                </Text>
              </Box>
            );

          case 'key_value':
            return (
              <Box key={i}>
                <Text color={theme.secondaryHex}>{detected.keyText}: </Text>
                <Text color={theme.primaryHex}>{detected.valueText}</Text>
              </Box>
            );

          case 'plain':
          default:
            return (
              <Box key={i}>
                <Text wrap="wrap">{renderInline(line, theme)}</Text>
              </Box>
            );
        }
      })}
    </Box>
  );
}

// ─── Main Export: renderMarkdown ─────────────────────────────────

/**
 * Renders raw AI output text as beautiful styled React elements.
 * Handles phases, code blocks, headings, bullets, bold, inline code,
 * and falls back to plain styled text for anything else.
 */
export function RenderMarkdown({
  text,
  theme,
  isStreaming = false,
}: {
  text: string;
  theme: Theme;
  isStreaming?: boolean;
}): React.ReactElement {
  const { stdout } = useStdout();
  const columns = stdout?.columns || 80;

  if (!text.trim()) {
    if (isStreaming) {
      return (
        <Box marginLeft={2}>
          <Text color={theme.primaryHex}>▌</Text>
        </Box>
      );
    }
    return <Box />;
  }

  const blocks = parseIntoBlocks(text);

  return (
    <Box flexDirection="column" width={Math.max(20, columns - 10)}>
      {blocks.map((block, i) => {
        const isLastBlock = i === blocks.length - 1;

        switch (block.type) {
          case 'phase':
            return (
              <PhaseBlock
                key={i}
                phaseNumber={block.phaseNumber ?? 0}
                phaseTitle={block.phaseTitle ?? ''}
                lines={block.lines}
                theme={theme}
                isStreaming={isStreaming && isLastBlock}
                columns={columns}
              />
            );

          case 'code':
            return (
              <CodeBlock
                key={i}
                lang={block.codeLang ?? ''}
                lines={block.lines}
                theme={theme}
              />
            );

          case 'lines':
          default: {
            const content = block.lines.join('\n');
            if (!content.trim()) return <Box key={i} />;
            return (
              <Box key={i} flexDirection="column" marginLeft={0}>
                <StyledLines text={content} theme={theme} />
                {isStreaming && isLastBlock && (
                  <Text color={theme.primaryHex}>▌</Text>
                )}
              </Box>
            );
          }
        }
      })}
    </Box>
  );
}

export { StyledLines, renderInline };
