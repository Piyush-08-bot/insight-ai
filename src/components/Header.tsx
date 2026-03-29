/**
 * Header — Premium ASCII art header with themed styling.
 * Shows the INSIGHT logo, version, model info, and Ollama status.
 */

import React from 'react';
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

interface HeaderProps {
  provider?: string;
  model?: string;
}

export function Header({ provider = 'ollama', model }: HeaderProps): React.ReactElement {
  const theme = useTheme();
  const ollama = useOllamaStatus();

  return (
    <Box flexDirection="column" marginBottom={1}>
      {/* Logo */}
      <Box flexDirection="column" alignItems="center">
        {ASCII_LOGO.map((line, i) => (
          <Text key={i} color={theme.primaryHex} bold>{line}</Text>
        ))}
      </Box>

      {/* Tagline */}
      <Box justifyContent="center" marginTop={0}>
        <Text color={theme.dimHex}>
          {'✨'} AI-Powered Code Intelligence Engine
        </Text>
      </Box>

      {/* Status bar */}
      <Box marginTop={1} justifyContent="center" gap={2}>
        {/* Dynamic Provider status */}
        <Box>
          {provider === 'ollama' ? (
            ollama.checking ? (
              <Text color={theme.dimHex}><Spinner type="dots" /> Checking Ollama...</Text>
            ) : ollama.running ? (
              <Text color={theme.successHex}>
                {figures.tick} Ollama {ollama.model ? `(${ollama.model})` : ''}
              </Text>
            ) : (
              <Text color={theme.warningHex}>
                {figures.warning} Ollama offline
              </Text>
            )
          ) : (
            <Text color={theme.secondaryHex}>
              {figures.star} {provider.charAt(0).toUpperCase() + provider.slice(1)} {model ? `(${model})` : ''}
            </Text>
          )}
        </Box>

        <Text color={theme.borderHex}>│</Text>

        {/* Version */}
        <Text color={theme.dimHex}>v1.0.0</Text>
      </Box>

      {/* Separator */}
      <Box marginTop={1} justifyContent="center">
        <Text color={theme.borderHex}>
          {'─'.repeat(44)}
        </Text>
      </Box>
    </Box>
  );
}
