/**
 * Setup — First-time setup wizard with step-by-step flow.
 */

import React, { useState, useEffect } from 'react';
import { Box, Text, useApp } from 'ink';
import SelectInput from 'ink-select-input';
import Spinner from 'ink-spinner';
import figures from 'figures';

import { Header } from './Header.js';
import { useTheme, getThemeNames, getTheme } from '../theme.js';
import { setTheme, setModel, setConfig } from '../config.js';
import { checkOllamaStatus, isVenvReady, runPythonDirect } from '../python-bridge.js';
import type { ThemeName } from '../types.js';

type SetupStep = 'provider' | 'ollama-check' | 'model' | 'theme' | 'doctor' | 'done';

export function Setup(): React.ReactElement {
  const { exit } = useApp();
  const theme = useTheme();

  const [step, setStep] = useState<SetupStep>('provider');
  const [provider, setProvider] = useState('ollama');
  const [ollamaStatus, setOllamaStatus] = useState<{ running: boolean; model?: string } | null>(null);
  const [selectedModel, setSelectedModel] = useState('qwen2.5-coder:latest');
  const [doctorResults, setDoctorResults] = useState<string[]>([]);

  // ─── Provider Selection ────────────────────────────────────
  const providerItems = [
    { label: `${figures.star} Ollama (Free, Local, Recommended)`, value: 'ollama' },
    { label: `${figures.pointer} OpenAI (Paid, Cloud)`, value: 'openai' },
  ];

  // ─── Model Selection ──────────────────────────────────────
  const modelItems = [
    { label: `${figures.star} qwen2.5-coder:latest (Recommended)`, value: 'qwen2.5-coder:latest' },
    { label: '  llama3.2:latest', value: 'llama3.2:latest' },
    { label: '  codellama:latest', value: 'codellama:latest' },
    { label: '  mistral:latest', value: 'mistral:latest' },
  ];

  // ─── Theme Selection ──────────────────────────────────────
  const themeItems = getThemeNames().map((name) => {
    const t = getTheme(name);
    const labels: Record<string, string> = {
      forest: `🌲 Forest — Green-on-black (Hero identity)`,
      light: `☀️  Light — Clean day mode`,
      aurora: `🌌 Aurora — Vibrant neon`,
    };
    return { label: labels[name] || name, value: name };
  });

  // ─── Check Ollama on step change ──────────────────────────
  useEffect(() => {
    if (step === 'ollama-check') {
      checkOllamaStatus().then((status) => {
        setOllamaStatus(status);
        setTimeout(() => setStep('model'), 1500);
      });
    }
  }, [step]);

  // ─── Doctor check ─────────────────────────────────────────
  useEffect(() => {
    if (step === 'doctor') {
      const results: string[] = [];
      // Python
      results.push(isVenvReady() ? `${figures.tick} Python environment ready` : `${figures.cross} Python not configured`);
      // Ollama
      results.push(ollamaStatus?.running ? `${figures.tick} Ollama running` : `${figures.warning} Ollama not detected`);
      // Model
      results.push(`${figures.tick} Model: ${selectedModel}`);
      setDoctorResults(results);
      setTimeout(() => setStep('done'), 2000);
    }
  }, [step]);

  return (
    <Box flexDirection="column">
      <Header />

      <Box flexDirection="column" paddingX={2} gap={1}>
        {/* Progress indicator */}
        <Box marginBottom={1}>
          {(['provider', 'ollama-check', 'model', 'theme', 'doctor', 'done'] as SetupStep[]).map((s, i) => (
            <React.Fragment key={s}>
              <Text color={
                step === s ? theme.primaryHex :
                  (['provider', 'ollama-check', 'model', 'theme', 'doctor', 'done'].indexOf(step) > i ? theme.successHex : theme.dimHex)
              }>
                {['provider', 'ollama-check', 'model', 'theme', 'doctor', 'done'].indexOf(step) > i ? figures.tick : (step === s ? figures.pointer : figures.circle)}
              </Text>
              {i < 5 && <Text color={theme.dimHex}> ─ </Text>}
            </React.Fragment>
          ))}
        </Box>

        {/* Step 1: Provider */}
        {step === 'provider' && (
          <Box flexDirection="column">
            <Text color={theme.primaryHex} bold>Step 1: Choose AI Provider</Text>
            <Box marginTop={1}>
              <SelectInput
                items={providerItems}
                onSelect={(item) => {
                  setProvider(item.value);
                  setStep(item.value === 'ollama' ? 'ollama-check' : 'model');
                }}
              />
            </Box>
          </Box>
        )}

        {/* Step 2: Ollama Check */}
        {step === 'ollama-check' && (
          <Box flexDirection="column">
            <Text color={theme.primaryHex} bold>Step 2: Checking Ollama</Text>
            <Box marginTop={1} gap={1}>
              {ollamaStatus === null ? (
                <>
                  <Text color={theme.infoHex}><Spinner type="dots" /></Text>
                  <Text color={theme.dimHex}>Connecting to Ollama...</Text>
                </>
              ) : ollamaStatus.running ? (
                <Text color={theme.successHex}>{figures.tick} Ollama is running!</Text>
              ) : (
                <Box flexDirection="column">
                  <Text color={theme.warningHex}>{figures.warning} Ollama not detected</Text>
                  <Text color={theme.dimHex}>  Install: https://ollama.com/download</Text>
                </Box>
              )}
            </Box>
          </Box>
        )}

        {/* Step 3: Model */}
        {step === 'model' && (
          <Box flexDirection="column">
            <Text color={theme.primaryHex} bold>Step 3: Choose Model</Text>
            <Box marginTop={1}>
              <SelectInput
                items={modelItems}
                onSelect={(item) => {
                  setSelectedModel(item.value);
                  setModel(item.value);
                  setStep('theme');
                }}
              />
            </Box>
          </Box>
        )}

        {/* Step 4: Theme */}
        {step === 'theme' && (
          <Box flexDirection="column">
            <Text color={theme.primaryHex} bold>Step 4: Choose Theme</Text>
            <Box marginTop={1}>
              <SelectInput
                items={themeItems}
                onSelect={(item) => {
                  setTheme(item.value as ThemeName);
                  setStep('doctor');
                }}
              />
            </Box>
          </Box>
        )}

        {/* Step 5: Doctor */}
        {step === 'doctor' && (
          <Box flexDirection="column">
            <Text color={theme.primaryHex} bold>Step 5: System Check</Text>
            <Box flexDirection="column" marginTop={1} marginLeft={2}>
              {doctorResults.map((r, i) => (
                <Text key={i}>{r}</Text>
              ))}
              {doctorResults.length === 0 && (
                <Box gap={1}>
                  <Text color={theme.infoHex}><Spinner type="dots" /></Text>
                  <Text color={theme.dimHex}>Running diagnostics...</Text>
                </Box>
              )}
            </Box>
          </Box>
        )}

        {/* Done */}
        {step === 'done' && (
          <Box flexDirection="column" gap={1}>
            <Text color={theme.successHex} bold>
              {figures.tick} Setup Complete!
            </Text>
            <Box flexDirection="column" marginLeft={2}>
              <Text color={theme.dimHex}>Next steps:</Text>
              <Text>  1. <Text color={theme.primaryHex}>insight analyze ./your-project</Text></Text>
              <Text>  2. <Text color={theme.primaryHex}>insight chat</Text></Text>
              <Text>  3. <Text color={theme.primaryHex}>insight stories</Text></Text>
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  );
}
