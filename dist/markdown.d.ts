/**
 * markdown.tsx — Smart Line Detector + Styled Renderer
 *
 * Detects what type of content each line is and renders it beautifully.
 * Implements a waterfall detector: first match wins, fallback to plain text.
 * All colors flow through the Theme object — zero hardcoded colors.
 */
import React from 'react';
import type { Theme } from './types.js';
/**
 * Apply inline markdown transforms: **bold**, `code`, *italic*
 * Returns an array of React elements for a single line.
 */
declare function renderInline(text: string, theme: Theme): React.ReactNode[];
/**
 * Render styled lines — applies the detection waterfall to each line
 */
declare function StyledLines({ text, theme, }: {
    text: string;
    theme: Theme;
}): React.ReactElement;
/**
 * Renders raw AI output text as beautiful styled React elements.
 * Handles phases, code blocks, headings, bullets, bold, inline code,
 * and falls back to plain styled text for anything else.
 */
export declare function RenderMarkdown({ text, theme, isStreaming, }: {
    text: string;
    theme: Theme;
    isStreaming?: boolean;
}): React.ReactElement;
export { StyledLines, renderInline };
//# sourceMappingURL=markdown.d.ts.map