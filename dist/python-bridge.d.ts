/**
 * INsight CLI — Python Bridge
 *
 * Spawns the Python CLI and streams output for real-time rendering.
 * Handles both JSON-streaming (chat) and line-streaming (analyze).
 */
import { type ChildProcess } from 'child_process';
import type { StreamChunk, AnalyzeProgress } from './types.js';
declare const PACKAGE_DIR: string;
declare const PYTHON_DIR: string;
declare const VENV_DIR: string;
export declare function getPythonExe(): string;
export declare function checkOllamaStatus(): Promise<{
    running: boolean;
    model?: string;
}>;
export declare function runPythonDirect(args: string[]): ChildProcess;
export declare function streamChat(question: string, options: {
    provider?: string;
    model?: string;
    persistDir?: string;
} | undefined, onChunk: (chunk: StreamChunk) => void, onDone: () => void, onError: (err: Error) => void): ChildProcess;
export declare function runAnalyze(projectPath: string, options: {
    provider?: string;
    model?: string;
    persistDir?: string;
    fileTypes?: string;
    embedding?: string;
} | undefined, onProgress: (progress: AnalyzeProgress) => void, onDone: () => void, onError: (err: Error) => void): ChildProcess;
export declare function isVenvReady(): boolean;
export { PACKAGE_DIR, PYTHON_DIR, VENV_DIR };
//# sourceMappingURL=python-bridge.d.ts.map