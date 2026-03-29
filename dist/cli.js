#!/usr/bin/env node
/**
 * INsight CLI — Entry Point
 *
 * Parses arguments and renders the React Ink UI.
 */
import { render } from 'ink';
import React from 'react';
import { App } from './components/App.js';
import { setTheme } from './config.js';
// ─── Parse Arguments ───────────────────────────────────────────
const rawArgs = process.argv.slice(2);
// Extract flags
const flags = {};
const positional = [];
let i = 0;
while (i < rawArgs.length) {
    const arg = rawArgs[i];
    if (arg === '--demo') {
        flags.demo = true;
        i++;
    }
    else if (arg === '--help' || arg === '-h') {
        showHelp();
        process.exit(0);
    }
    else if (arg === '--version') {
        console.log('1.0.0');
        process.exit(0);
    }
    else if (arg === '-p' || arg === '--provider') {
        flags.provider = rawArgs[++i] || 'ollama';
        i++;
    }
    else if (arg === '-m' || arg === '--model') {
        flags.model = rawArgs[++i] || '';
        i++;
    }
    else if (arg === '-d' || arg === '--persist-dir') {
        flags.persistDir = rawArgs[++i] || './chroma_db';
        i++;
    }
    else if (arg === '-f' || arg === '--file-types') {
        flags.fileTypes = rawArgs[++i] || '';
        i++;
    }
    else if (arg === '-e' || arg === '--embedding') {
        flags.embedding = rawArgs[++i] || 'local';
        i++;
    }
    else if (arg === '-o' || arg === '--output') {
        flags.output = rawArgs[++i] || '';
        i++;
    }
    else if (arg === '--theme') {
        const themeName = rawArgs[++i] || 'forest';
        setTheme(themeName);
        i++;
    }
    else if (arg.startsWith('-')) {
        // Unknown flag, skip
        i++;
    }
    else {
        positional.push(arg);
        i++;
    }
}
const command = positional[0] || 'chat';
const cmdArgs = positional.slice(1);
// ─── Render ────────────────────────────────────────────────────
render(React.createElement(App, {
    command,
    args: cmdArgs,
    flags: {
        provider: flags.provider,
        model: flags.model,
        persistDir: flags.persistDir,
        fileTypes: flags.fileTypes,
        embedding: flags.embedding,
        output: flags.output,
        demo: flags.demo,
    },
}));
// ─── Help ──────────────────────────────────────────────────────
function showHelp() {
    // Use dynamic import to avoid issues when just showing help
    const helpText = `
  ╦╔╗╔╔═╗╦╔═╗╦ ╦╔╦╗
  ║║║║╚═╗║║ ╦╠═╣ ║ 
  ╩╝╚╝╚═╝╩╚═╝╩ ╩ ╩ 

  ✨ AI-Powered Code Intelligence Engine v1.0.0

USAGE
  insight <command> [options]

COMMANDS
  chat                  Interactive chat with your codebase
  analyze <path>        Analyze a codebase (ingest → chunk → embed → index)
  setup                 First-time setup wizard
  overview [path]       Generate a project overview
  learn [path]          Generate a learning path
  architecture [path]   Analyze code architecture
  deps [path]           Map out all dependencies
  stories [path]        📖 Generate full 8-chapter project story
  report [path]         Full analysis report (all types)
  doctor                Check system health

OPTIONS
  -p, --provider        LLM provider: ollama (free) or openai
  -m, --model           Model name
  -d, --persist-dir     Vector store directory (default: ./chroma_db)
  -f, --file-types      File types to analyze
  -e, --embedding       Embedding provider: local or openai
  -o, --output          Save output to file
  --theme               Set theme: forest | light | aurora
  --demo                Run demo showcase
  --help, -h            Show this help
  --version             Show version

EXAMPLES
  insight analyze ./my-project     Analyze your project
  insight chat                     Start chatting about your code
  insight --demo                   See a demo
  insight chat --theme aurora      Chat with aurora theme
`;
    console.log(helpText);
}
//# sourceMappingURL=cli.js.map