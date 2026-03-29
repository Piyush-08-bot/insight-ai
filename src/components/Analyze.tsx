/**
 * Analyze — Codebase analysis with live progress and stats.
 */

import React, { useState, useEffect, useRef } from 'react';
import { Box, Text, useApp } from 'ink';
import Spinner from 'ink-spinner';
import figures from 'figures';

import { Header } from './Header.js';
import { useTheme } from '../theme.js';
import { runAnalyze, isVenvReady } from '../python-bridge.js';
import type { AnalyzeProgress } from '../types.js';

interface Props {
  projectPath: string;
  provider?: string;
  model?: string;
  persistDir?: string;
  fileTypes?: string;
  embedding?: string;
}

export function Analyze({ projectPath, provider, model, persistDir, fileTypes, embedding }: Props): React.ReactElement {
  const { exit } = useApp();
  const theme = useTheme();

  const [status, setStatus] = useState<string>('Starting analysis...');
  const [lines, setLines] = useState<string[]>([]);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const startTime = useRef(Date.now());

  useEffect(() => {
    const timer = setInterval(() => {
      if (!done) setElapsed((Date.now() - startTime.current) / 1000);
    }, 100);
    return () => clearInterval(timer);
  }, [done]);

  useEffect(() => {
    if (!isVenvReady()) {
      setError('Python environment not ready. Run: insight setup');
      return;
    }

    runAnalyze(
      projectPath,
      { provider, model, persistDir, fileTypes, embedding },
      (progress: AnalyzeProgress) => {
        setStatus(progress.status);
        setLines((prev) => [...prev, progress.status]);
        if (progress.done) setDone(true);
      },
      () => {
        setDone(true);
        setElapsed((Date.now() - startTime.current) / 1000);
      },
      (err: Error) => {
        setError(err.message);
      },
    );
  }, []);

  return (
    <Box flexDirection="column">
      <Header />

      <Box flexDirection="column" paddingX={1} gap={0}>
        {/* Title */}
        <Box marginBottom={1}>
          <Text color={theme.primaryHex} bold>
            {figures.pointer} Analyzing: {projectPath}
          </Text>
        </Box>

        {/* Progress */}
        {!done && !error && (
          <Box flexDirection="row" gap={1}>
            <Text color={theme.infoHex}><Spinner type="dots" /></Text>
            <Text color={theme.dimHex}>{status}</Text>
          </Box>
        )}

        {/* Log lines (last 8) */}
        <Box flexDirection="column" marginLeft={2} marginTop={1}>
          {lines.slice(-8).map((line, i) => (
            <Text key={i} color={theme.dimHex}>  {line}</Text>
          ))}
        </Box>

        {/* Error */}
        {error && (
          <Box marginTop={1}>
            <Text color={theme.errorHex}>{figures.cross} Error: {error}</Text>
          </Box>
        )}

        {/* Done */}
        {done && !error && (
          <Box flexDirection="column" marginTop={1}>
            <Text color={theme.successHex} bold>
              {figures.tick} Done in {elapsed.toFixed(1)}s
            </Text>
            <Box marginTop={1}>
              <Text color={theme.dimHex}>
                Run `insight chat` to start asking questions about your code.
              </Text>
            </Box>
          </Box>
        )}

        {/* Timer */}
        {!done && !error && (
          <Box marginTop={1}>
            <Text color={theme.dimHex}>{elapsed.toFixed(1)}s elapsed</Text>
          </Box>
        )}
      </Box>
    </Box>
  );
}
