/**
 * StatusBar — Bottom bar showing session info, model, and theme.
 */

import React from 'react';
import { Box, Text } from 'ink';
import figures from 'figures';
import { useTheme } from '../theme.js';
import { getConfig } from '../config.js';

interface Props {
  sessionId?: string | null;
  messageCount?: number;
}

export function StatusBar({ sessionId, messageCount = 0 }: Props): React.ReactElement {
  const theme = useTheme();
  const config = getConfig();

  return (
    <Box flexDirection="column">
      <Box>
        <Text color={theme.borderHex}>{'─'.repeat(44)}</Text>
      </Box>
      <Box flexDirection="row" gap={2}>
        {/* Model */}
        <Box>
          <Text color={theme.dimHex}>
            {figures.pointer} {config.model}
          </Text>
        </Box>

        <Text color={theme.borderHex}>│</Text>

        {/* Theme */}
        <Box>
          <Text color={theme.dimHex}>
            {figures.star} {config.theme}
          </Text>
        </Box>

        <Text color={theme.borderHex}>│</Text>

        {/* Session */}
        <Box>
          <Text color={theme.dimHex}>
            {figures.info} {messageCount} msgs
          </Text>
        </Box>
      </Box>
    </Box>
  );
}
