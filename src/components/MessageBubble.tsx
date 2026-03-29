/**
 * MessageBubble — Premium chat message with role indicator, sub-steps,
 * and beautifully rendered AI output using the smart markdown renderer.
 */

import React from 'react';
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';
import figures from 'figures';
import type { Message } from '../types.js';
import { useTheme } from '../theme.js';
import { RenderMarkdown } from '../markdown.js';

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props): React.ReactElement {
  const theme = useTheme();

  // ─── System messages ─────────────────────────────────────
  if (message.role === 'system') {
    return (
      <Box marginY={0} justifyContent="center">
        <Text color={theme.dimHex}>─── {message.content} ───</Text>
      </Box>
    );
  }

  // ─── User messages ───────────────────────────────────────
  if (message.role === 'user') {
    return (
      <Box flexDirection="column" marginTop={1}>
        <Box flexDirection="row">
          <Text color={theme.infoHex}>●</Text>
          <Text color={theme.infoHex} bold> You  </Text>
          <Text color={theme.dimHex}>{'─'.repeat(50)}</Text>
        </Box>
        <Box marginLeft={3}>
          <Text wrap="wrap">{message.content}</Text>
        </Box>
      </Box>
    );
  }

  // ─── Assistant messages ──────────────────────────────────
  return (
    <Box flexDirection="column" marginTop={1}>
      {/* Role header with separator */}
      <Box flexDirection="row">
        <Text color={theme.primaryHex}>◆</Text>
        <Text color={theme.primaryHex} bold>
          {' '}
          INsight{'  '}
        </Text>
        <Text color={theme.dimHex}>{'─'.repeat(48)}</Text>
      </Box>

      {/* Sub-steps — ALWAYS visible if present */}
      {message.subSteps && message.subSteps.length > 0 && (
        <Box flexDirection="column" marginLeft={3} marginTop={1}>
          {message.subSteps.map((step, i) => (
            <Box key={i} flexDirection="row" gap={1}>
              {step.status === 'active' ? (
                <Text color={theme.primaryHex}>
                  <Spinner type="dots" />
                </Text>
              ) : step.status === 'done' ? (
                <Text color={theme.successHex}>{figures.tick}</Text>
              ) : step.status === 'error' ? (
                <Text color={theme.errorHex}>{figures.cross}</Text>
              ) : (
                <Text color={theme.dimHex}>░</Text>
              )}
              <Text
                color={
                  step.status === 'done'
                    ? theme.dimHex
                    : step.status === 'active'
                      ? undefined
                      : theme.dimHex
                }
              >
                {step.label}
              </Text>
            </Box>
          ))}
          {/* Separator between sub-steps and content */}
          {message.content && (
            <Box marginTop={0}>
              <Text color={theme.dimHex}>{'─'.repeat(36)}</Text>
            </Box>
          )}
        </Box>
      )}

      {/* Content — rendered with smart markdown detector */}
      {message.content && (
        <Box marginLeft={3} marginTop={0} flexDirection="column">
          <RenderMarkdown
            text={message.content}
            theme={theme}
            isStreaming={message.isStreaming}
          />
        </Box>
      )}

      {/* Streaming cursor when no content yet */}
      {message.isStreaming && !message.content && (
        <Box marginLeft={3} marginTop={0}>
          <Text color={theme.primaryHex}>▌</Text>
        </Box>
      )}

      {/* Completion indicator */}
      {!message.isStreaming && message.content && message.elapsed !== undefined && (
        <Box marginLeft={3} marginTop={1}>
          <Text color={theme.successHex}>{figures.tick} Complete</Text>
          <Text color={theme.dimHex}>  ({message.elapsed.toFixed(1)}s)</Text>
        </Box>
      )}
    </Box>
  );
}
