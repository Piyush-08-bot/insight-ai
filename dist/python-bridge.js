/**
 * INsight CLI — Python Bridge
 *
 * Spawns the Python CLI and streams output for real-time rendering.
 * Handles both JSON-streaming (chat) and line-streaming (analyze).
 */
import { spawn, execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PACKAGE_DIR = path.resolve(__dirname, '..');
const PYTHON_DIR = path.join(PACKAGE_DIR, 'python');
const VENV_DIR = path.join(PACKAGE_DIR, '.venv');
// ─── Python Executable Discovery ───────────────────────────────
export function getPythonExe() {
    const isWin = process.platform === 'win32';
    const venvPython = isWin
        ? path.join(VENV_DIR, 'Scripts', 'python.exe')
        : path.join(VENV_DIR, 'bin', 'python');
    if (fs.existsSync(venvPython))
        return venvPython;
    for (const cmd of ['python3', 'python']) {
        try {
            execSync(`${cmd} --version`, { stdio: 'ignore' });
            return cmd;
        }
        catch { /* skip */ }
    }
    throw new Error('Python not found. Run: insight setup');
}
// ─── Environment ───────────────────────────────────────────────
function getPythonEnv() {
    return {
        ...process.env,
        PYTHONPATH: PYTHON_DIR,
        PYTHONUNBUFFERED: '1',
        PYTHONWARNINGS: 'ignore',
        TRANSFORMERS_VERBOSITY: 'error',
        HF_HUB_DISABLE_SYMLINKS_WARNING: '1',
    };
}
// ─── Check Ollama Status ───────────────────────────────────────
export async function checkOllamaStatus() {
    try {
        const response = await fetch('http://localhost:11434/api/tags', {
            signal: AbortSignal.timeout(2000),
        });
        if (response.ok) {
            const data = await response.json();
            const models = data.models || [];
            const qwen = models.find((m) => m.name.includes('qwen'));
            return { running: true, model: qwen?.name || models[0]?.name };
        }
        return { running: false };
    }
    catch {
        return { running: false };
    }
}
// ─── Run Python Command (fire & forget with stdio inherit) ─────
export function runPythonDirect(args) {
    const pythonExe = getPythonExe();
    return spawn(pythonExe, ['-W', 'ignore', '-m', 'insight.cli.main', ...args], {
        cwd: process.cwd(),
        stdio: 'inherit',
        env: getPythonEnv(),
    });
}
// ─── Stream Python Chat Output ─────────────────────────────────
export function streamChat(question, options = {}, onChunk, onDone, onError) {
    const pythonExe = getPythonExe();
    const args = ['-W', 'ignore', '-m', 'insight.cli.main', 'chat', '--stream', question];
    if (options.provider)
        args.push('--provider', options.provider);
    if (options.model)
        args.push('--model', options.model);
    if (options.persistDir)
        args.push('--persist-dir', options.persistDir);
    const proc = spawn(pythonExe, args, {
        cwd: process.cwd(),
        env: getPythonEnv(),
        stdio: ['pipe', 'pipe', 'pipe'],
    });
    let buffer = '';
    proc.stdout?.on('data', (data) => {
        buffer += data.toString();
        // Try to parse line-by-line as JSON
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed)
                continue;
            try {
                const chunk = JSON.parse(trimmed);
                onChunk(chunk);
            }
            catch {
                // Not JSON — ignore known library noise
                if (trimmed.includes('UserWarning') || trimmed.includes('Pydantic') || trimmed.includes('DeprecationWarning')) {
                    return;
                }
                // Treat as raw token
                onChunk({ token: trimmed });
            }
        }
    });
    proc.stderr?.on('data', (data) => {
        const text = data.toString().trim();
        // Filter out Python warnings — only report real errors
        if (text && !text.startsWith('WARNING') && !text.includes('UserWarning')) {
            onError(new Error(text));
        }
    });
    proc.on('close', () => {
        // Flush remaining buffer
        if (buffer.trim()) {
            try {
                const chunk = JSON.parse(buffer.trim());
                onChunk(chunk);
            }
            catch {
                onChunk({ token: buffer.trim() });
            }
        }
        onDone();
    });
    return proc;
}
// ─── Run Analyze ───────────────────────────────────────────────
export function runAnalyze(projectPath, options = {}, onProgress, onDone, onError) {
    const pythonExe = getPythonExe();
    const args = ['-W', 'ignore', '-m', 'insight.cli.main', 'analyze', projectPath];
    if (options.persistDir)
        args.push('--persist-dir', options.persistDir);
    if (options.fileTypes)
        args.push('--file-types', options.fileTypes);
    if (options.embedding)
        args.push('--embedding', options.embedding);
    const proc = spawn(pythonExe, args, {
        cwd: process.cwd(),
        env: getPythonEnv(),
        stdio: ['pipe', 'pipe', 'pipe'],
    });
    proc.stdout?.on('data', (data) => {
        const text = data.toString();
        for (const line of text.split('\n')) {
            const trimmed = line.trim();
            if (!trimmed)
                continue;
            // Parse status messages
            if (trimmed.includes('Processing')) {
                onProgress({ status: trimmed });
            }
            else if (trimmed.includes('✅') || trimmed.includes('✂️')) {
                onProgress({ status: trimmed, done: true });
            }
            else {
                onProgress({ status: trimmed });
            }
        }
    });
    proc.stderr?.on('data', (data) => {
        const text = data.toString().trim();
        if (text && !text.startsWith('WARNING') && !text.includes('UserWarning')) {
            onError(new Error(text));
        }
    });
    proc.on('close', onDone);
    return proc;
}
// ─── Utility ───────────────────────────────────────────────────
export function isVenvReady() {
    return fs.existsSync(VENV_DIR);
}
export { PACKAGE_DIR, PYTHON_DIR, VENV_DIR };
//# sourceMappingURL=python-bridge.js.map