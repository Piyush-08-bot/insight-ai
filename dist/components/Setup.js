import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
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
import { setTheme, setModel } from '../config.js';
import { checkOllamaStatus, isVenvReady } from '../python-bridge.js';
export function Setup() {
    const { exit } = useApp();
    const theme = useTheme();
    const [step, setStep] = useState('provider');
    const [provider, setProvider] = useState('ollama');
    const [ollamaStatus, setOllamaStatus] = useState(null);
    const [selectedModel, setSelectedModel] = useState('qwen2.5-coder:latest');
    const [doctorResults, setDoctorResults] = useState([]);
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
        const labels = {
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
            const results = [];
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
    return (_jsxs(Box, { flexDirection: "column", children: [_jsx(Header, {}), _jsxs(Box, { flexDirection: "column", paddingX: 2, gap: 1, children: [_jsx(Box, { marginBottom: 1, children: ['provider', 'ollama-check', 'model', 'theme', 'doctor', 'done'].map((s, i) => (_jsxs(React.Fragment, { children: [_jsx(Text, { color: step === s ? theme.primaryHex :
                                        (['provider', 'ollama-check', 'model', 'theme', 'doctor', 'done'].indexOf(step) > i ? theme.successHex : theme.dimHex), children: ['provider', 'ollama-check', 'model', 'theme', 'doctor', 'done'].indexOf(step) > i ? figures.tick : (step === s ? figures.pointer : figures.circle) }), i < 5 && _jsx(Text, { color: theme.dimHex, children: " \u2500 " })] }, s))) }), step === 'provider' && (_jsxs(Box, { flexDirection: "column", children: [_jsx(Text, { color: theme.primaryHex, bold: true, children: "Step 1: Choose AI Provider" }), _jsx(Box, { marginTop: 1, children: _jsx(SelectInput, { items: providerItems, onSelect: (item) => {
                                        setProvider(item.value);
                                        setStep(item.value === 'ollama' ? 'ollama-check' : 'model');
                                    } }) })] })), step === 'ollama-check' && (_jsxs(Box, { flexDirection: "column", children: [_jsx(Text, { color: theme.primaryHex, bold: true, children: "Step 2: Checking Ollama" }), _jsx(Box, { marginTop: 1, gap: 1, children: ollamaStatus === null ? (_jsxs(_Fragment, { children: [_jsx(Text, { color: theme.infoHex, children: _jsx(Spinner, { type: "dots" }) }), _jsx(Text, { color: theme.dimHex, children: "Connecting to Ollama..." })] })) : ollamaStatus.running ? (_jsxs(Text, { color: theme.successHex, children: [figures.tick, " Ollama is running!"] })) : (_jsxs(Box, { flexDirection: "column", children: [_jsxs(Text, { color: theme.warningHex, children: [figures.warning, " Ollama not detected"] }), _jsx(Text, { color: theme.dimHex, children: "  Install: https://ollama.com/download" })] })) })] })), step === 'model' && (_jsxs(Box, { flexDirection: "column", children: [_jsx(Text, { color: theme.primaryHex, bold: true, children: "Step 3: Choose Model" }), _jsx(Box, { marginTop: 1, children: _jsx(SelectInput, { items: modelItems, onSelect: (item) => {
                                        setSelectedModel(item.value);
                                        setModel(item.value);
                                        setStep('theme');
                                    } }) })] })), step === 'theme' && (_jsxs(Box, { flexDirection: "column", children: [_jsx(Text, { color: theme.primaryHex, bold: true, children: "Step 4: Choose Theme" }), _jsx(Box, { marginTop: 1, children: _jsx(SelectInput, { items: themeItems, onSelect: (item) => {
                                        setTheme(item.value);
                                        setStep('doctor');
                                    } }) })] })), step === 'doctor' && (_jsxs(Box, { flexDirection: "column", children: [_jsx(Text, { color: theme.primaryHex, bold: true, children: "Step 5: System Check" }), _jsxs(Box, { flexDirection: "column", marginTop: 1, marginLeft: 2, children: [doctorResults.map((r, i) => (_jsx(Text, { children: r }, i))), doctorResults.length === 0 && (_jsxs(Box, { gap: 1, children: [_jsx(Text, { color: theme.infoHex, children: _jsx(Spinner, { type: "dots" }) }), _jsx(Text, { color: theme.dimHex, children: "Running diagnostics..." })] }))] })] })), step === 'done' && (_jsxs(Box, { flexDirection: "column", gap: 1, children: [_jsxs(Text, { color: theme.successHex, bold: true, children: [figures.tick, " Setup Complete!"] }), _jsxs(Box, { flexDirection: "column", marginLeft: 2, children: [_jsx(Text, { color: theme.dimHex, children: "Next steps:" }), _jsxs(Text, { children: ["  1. ", _jsx(Text, { color: theme.primaryHex, children: "insight analyze ./your-project" })] }), _jsxs(Text, { children: ["  2. ", _jsx(Text, { color: theme.primaryHex, children: "insight chat" })] }), _jsxs(Text, { children: ["  3. ", _jsx(Text, { color: theme.primaryHex, children: "insight stories" })] })] })] }))] })] }));
}
//# sourceMappingURL=Setup.js.map