/**
 * CommandPalette — Slash-command popup with live filtering.
 */

import React, { useState, useMemo } from 'react';
import { Box, Text, useInput } from 'ink';
import figures from 'figures';
import { useTheme } from '../theme.js';
import type { Command } from '../types.js';

interface Props {
  commands: Command[];
  filter: string;
  selectedIndex: number;
  onSelect: (cmd: Command) => void;
  onClose: () => void;
}

export function CommandPalette({ commands, filter, selectedIndex, onSelect, onClose }: Props): React.ReactElement {
  const theme = useTheme();

  const filtered = useMemo(() => {
    const query = filter.replace(/^\//, '').toLowerCase();
    if (!query) return commands;
    return commands.filter((c) =>
      c.name.toLowerCase().includes(query) ||
      c.description.toLowerCase().includes(query)
    );
  }, [commands, filter]);

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor={theme.primaryHex}
      paddingX={1}
      marginBottom={1}
    >
      {/* Header */}
      <Box marginBottom={0}>
        <Text color={theme.primaryHex} bold>
          {figures.pointer} Commands
        </Text>
        <Text color={theme.dimHex}> (type to filter, Enter to select, Esc to close)</Text>
      </Box>

      {/* Command list */}
      {filtered.length === 0 ? (
        <Text color={theme.dimHex}>No matching commands</Text>
      ) : (
        filtered.map((cmd, i) => (
          <Box key={cmd.name} flexDirection="row" gap={1}>
            <Text color={i === selectedIndex ? theme.primaryHex : theme.dimHex}>
              {i === selectedIndex ? figures.pointer : ' '}
            </Text>
            <Text color={i === selectedIndex ? theme.primaryHex : theme.secondaryHex} bold>
              /{cmd.name}
            </Text>
            {cmd.args && (
              <Text color={theme.dimHex}>&lt;{cmd.args}&gt;</Text>
            )}
            <Text color={theme.dimHex}> — {cmd.description}</Text>
          </Box>
        ))
      )}
    </Box>
  );
}
