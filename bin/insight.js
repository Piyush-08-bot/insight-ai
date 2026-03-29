#!/usr/bin/env node

/**
 * INsight CLI — Launcher
 *
 * This is the npm bin entry point. It launches the compiled
 * TypeScript CLI or falls back to tsx for development.
 */

import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import { existsSync } from 'fs';
import { resolve, dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const DIST_CLI = resolve(__dirname, '..', 'dist', 'cli.js');
const SRC_CLI = resolve(__dirname, '..', 'src', 'cli.tsx');

// Prefer compiled dist if available, otherwise use tsx for dev
if (existsSync(DIST_CLI)) {
  // Run compiled version
  const proc = spawn('node', [DIST_CLI, ...process.argv.slice(2)], {
    stdio: 'inherit',
    cwd: process.cwd(),
  });
  proc.on('close', (code) => process.exit(code || 0));
} else if (existsSync(SRC_CLI)) {
  // Dev mode: run via tsx
  const proc = spawn('npx', ['tsx', SRC_CLI, ...process.argv.slice(2)], {
    stdio: 'inherit',
    cwd: process.cwd(),
  });
  proc.on('close', (code) => process.exit(code || 0));
} else {
  console.error('❌ INsight CLI not built. Run: npm run build');
  process.exit(1);
}
