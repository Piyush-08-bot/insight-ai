/**
 * App — Root component that routes to Chat, Analyze, or Setup.
 */

import React, { useState, useEffect } from 'react';
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';
import figures from 'figures';

import { Chat } from './Chat.js';
import { Analyze } from './Analyze.js';
import { Setup } from './Setup.js';
import { Header } from './Header.js';
import { useTheme } from '../theme.js';
import { runPythonDirect } from '../python-bridge.js';

interface Props {
  command: string;
  args: string[];
  flags: {
    provider?: string;
    model?: string;
    persistDir?: string;
    fileTypes?: string;
    embedding?: string;
    output?: string;
    demo?: boolean;
    theme?: string;
  };
}

export function App({ command, args, flags }: Props): React.ReactElement {
  const theme = useTheme();

  // ─── Demo Mode ──────────────────────────────────────────────
  if (flags.demo) {
    return <DemoMode flags={flags} />;
  }

  // ─── Route by command ──────────────────────────────────────
  switch (command) {
    case 'chat':
      return (
        <Chat
          provider={flags.provider}
          model={flags.model}
          persistDir={flags.persistDir}
          initialQuery={args[0]}
        />
      );

    case 'analyze':
    case 'overview':
    case 'learn':
    case 'architecture':
    case 'deps':
    case 'stories':
    case 'report':
    case 'doctor':
    case 'setup':
      // These commands use Python's Rich CLI for rendering
      return <PythonPassthrough command={command} args={args} flags={flags} />;

    default:
      return <PythonPassthrough command={command} args={args} flags={flags} />;
  }
}

// ─── Python Passthrough ─────────────────────────────────────────
// Renders header, then spawns Python for commands not yet ported to Ink

function PythonPassthrough({ command, args, flags }: Props): React.ReactElement {
  const theme = useTheme();

  useEffect(() => {
    const cliArgs = [command, ...args];
    if (flags.provider) cliArgs.push('--provider', flags.provider);
    if (flags.model) cliArgs.push('--model', flags.model);
    if (flags.persistDir) cliArgs.push('--persist-dir', flags.persistDir);
    if (flags.output) cliArgs.push('--output', flags.output);

    const proc = runPythonDirect(cliArgs);
    proc.on('close', (code) => {
      process.exit(code ?? 0);
    });
    proc.on('error', () => {
      process.exit(1);
    });
  }, []);

  // Render nothing — let Python's Rich CLI own the terminal
  return (
    <Box>
      <Text color={theme.dimHex}> </Text>
    </Box>
  );
}

// ─── Demo Mode ──────────────────────────────────────────────────

function DemoMode({ flags }: { flags: Props['flags'] }): React.ReactElement {
  const theme = useTheme();
  const [phase, setPhase] = useState(0);
  const [demoText, setDemoText] = useState('');

  const demoResponse = `## Project Overview

**INsight** is an AI-powered code intelligence engine that uses RAG (Retrieval-Augmented Generation) to analyze and understand codebases.

### Key Components
- **Ingestion Layer** — Parses code with AST, extracts metadata
- **Vector Store** — ChromaDB for semantic search
- **RAG Pipeline** — LangChain chains for Q&A, analysis, stories
- **CLI Interface** — Rich terminal UI with streaming responses

### Tech Stack
Python, LangChain, ChromaDB, Ollama, FastAPI, React Ink`;

  useEffect(() => {
    // Phase 0: Show header (instant)
    // Phase 1: Simulate analyze
    const timer1 = setTimeout(() => setPhase(1), 1500);
    // Phase 2: Simulate chat
    const timer2 = setTimeout(() => setPhase(2), 4000);
    // Phase 3: Stream response
    const timer3 = setTimeout(() => {
      setPhase(3);
      let i = 0;
      const streamTimer = setInterval(() => {
        if (i < demoResponse.length) {
          setDemoText(demoResponse.slice(0, i + 3));
          i += 3;
        } else {
          clearInterval(streamTimer);
          setPhase(4);
        }
      }, 15);
    }, 5500);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, []);

  return (
    <Box flexDirection="column">
      <Header provider={flags.provider} model={flags.model} />

      <Box flexDirection="column" paddingX={1} gap={1}>
        {/* Phase 1: Analyze */}
        {phase >= 1 && (
          <Box flexDirection="column">
            <Box gap={1}>
              {phase === 1 ? (
                <Text color={theme.infoHex}><Spinner type="dots" /></Text>
              ) : (
                <Text color={theme.successHex}>{figures.tick}</Text>
              )}
              <Text color={phase > 1 ? theme.dimHex : theme.primaryHex}>
                Analyzing codebase... {phase > 1 ? '42 files indexed in 3.2s' : ''}
              </Text>
            </Box>
          </Box>
        )}

        {/* Phase 2: User question */}
        {phase >= 2 && (
          <Box paddingX={1} gap={2}>
            {flags.provider && (
              <Text color={theme.secondaryHex}>
                {figures.star} {flags.provider.charAt(0).toUpperCase() + flags.provider.slice(1)} {flags.model ? `(${flags.model})` : ''}
              </Text>
            )}
          <Text color={theme.dimHex}>/  commands</Text>
          </Box>
        )}

        {/* Phase 3: Streaming response */}
        {phase >= 3 && (
          <Box flexDirection="column" marginTop={1}>
            <Box gap={1}>
              <Text color={theme.primaryHex} bold>{'✨'} INsight</Text>
              {phase === 3 && <Text color={theme.dimHex}><Spinner type="dots" /></Text>}
              {phase === 4 && <Text color={theme.successHex}>{figures.tick} 4.2s</Text>}
            </Box>
            <Box marginLeft={2} marginTop={0}>
              <Text wrap="wrap">{demoText}{phase === 3 ? '▌' : ''}</Text>
            </Box>
          </Box>
        )}

        {/* Phase 4: Done */}
        {phase >= 4 && (
          <Box marginTop={2} justifyContent="center">
            <Text color={theme.dimHex}>
              ─── Demo complete. Run `insight analyze` to try it for real! ───
            </Text>
          </Box>
        )}
      </Box>
    </Box>
  );
}
