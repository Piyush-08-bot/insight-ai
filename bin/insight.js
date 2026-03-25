#!/usr/bin/env node

/**
 * INsight CLI - npm wrapper for the Python AI engine.
 * 
 * This script dispatches commands to the Python CLI tool.
 * Python + venv are managed automatically via postinstall.
 */

const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const PACKAGE_DIR = path.resolve(__dirname, '..');
const PYTHON_DIR = path.join(PACKAGE_DIR, 'python');
const VENV_DIR = path.join(PACKAGE_DIR, '.venv');

// ─── Determine Python executable ───────────────────────────────

function getPythonExe() {
    const isWin = process.platform === 'win32';
    const venvPython = isWin
        ? path.join(VENV_DIR, 'Scripts', 'python.exe')
        : path.join(VENV_DIR, 'bin', 'python');

    if (fs.existsSync(venvPython)) {
        return venvPython;
    }

    // Fallback: try system python
    for (const cmd of ['python3', 'python']) {
        try {
            execSync(`${cmd} --version`, { stdio: 'ignore' });
            return cmd;
        } catch { }
    }

    console.error('❌ Python not found!');
    console.error('   Install Python 3.9+ or run: insight setup');
    process.exit(1);
}

// ─── Built-in commands ─────────────────────────────────────────

const args = process.argv.slice(2);
const command = args[0];

if (command === 'setup') {
    runSetup();
} else if (command === '--help' || command === '-h' || !command) {
    showHelp();
} else {
    // Pass everything to Python CLI
    runPython(args);
}

// ─── Run Python CLI ────────────────────────────────────────────

function runPython(args) {
    const pythonExe = getPythonExe();

    // Check if venv exists
    if (!fs.existsSync(VENV_DIR)) {
        console.log('⚠️  First run detected. Setting up...\n');
        runSetup(() => {
            executePython(getPythonExe(), args);
        });
        return;
    }

    executePython(pythonExe, args);
}

function executePython(pythonExe, args) {
    const proc = spawn(pythonExe, ['-W', 'ignore', '-m', 'insight.cli.main', ...args], {
        cwd: process.cwd(),  // Use USER's working directory (critical for chroma_db path resolution)
        stdio: 'inherit',
        env: {
            ...process.env,
            PYTHONPATH: PYTHON_DIR,  // Keep the package importable from anywhere
            PYTHONUNBUFFERED: '1',
            PYTHONWARNINGS: 'ignore',
            TRANSFORMERS_VERBOSITY: 'error',
            HF_HUB_DISABLE_SYMLINKS_WARNING: '1'
        }
    });

    proc.on('error', (err) => {
        if (err.code === 'ENOENT') {
            console.error('❌ Python not found. Run: insight setup');
        } else {
            console.error(`❌ Error: ${err.message}`);
        }
        process.exit(1);
    });

    proc.on('close', (code) => {
        process.exit(code || 0);
    });
}

// ─── Setup ─────────────────────────────────────────────────────

function runSetup(callback) {
    console.log('🔧 INsight Setup\n');

    // 1. Check Python
    let pythonCmd = null;
    for (const cmd of ['python3', 'python']) {
        try {
            const version = execSync(`${cmd} --version`, { encoding: 'utf-8' }).trim();
            console.log(`✅ ${version}`);
            pythonCmd = cmd;
            break;
        } catch { }
    }

    if (!pythonCmd) {
        console.error('❌ Python 3.9+ is required.');
        console.error('   Install from: https://www.python.org/downloads/');
        process.exit(1);
    }

    // 2. Create venv
    if (!fs.existsSync(VENV_DIR)) {
        console.log('\n📦 Creating virtual environment...');
        try {
            execSync(`${pythonCmd} -m venv "${VENV_DIR}"`, { stdio: 'inherit' });
            console.log('✅ Virtual environment created');
        } catch (err) {
            console.error('❌ Failed to create venv:', err.message);
            process.exit(1);
        }
    } else {
        console.log('✅ Virtual environment exists');
    }

    // 3. Install Python dependencies
    const isWin = process.platform === 'win32';
    const pip = isWin
        ? path.join(VENV_DIR, 'Scripts', 'pip')
        : path.join(VENV_DIR, 'bin', 'pip');

    console.log('\n📥 Installing Python dependencies (this may take a minute)...');
    try {
        execSync(`"${pip}" install -e "${PYTHON_DIR}" --quiet`, {
            stdio: 'inherit',
            timeout: 300000 // 5 min timeout
        });
        console.log('✅ Dependencies installed');
    } catch (err) {
        console.error('❌ Failed to install dependencies:', err.message);
        console.error('   Try manually: pip install -e python/');
        process.exit(1);
    }

    // 4. Check Ollama
    console.log('\n🤖 Checking Ollama...');
    try {
        execSync('ollama --version', { stdio: 'ignore' });
        console.log('✅ Ollama is installed');

        // Check if a model is available
        try {
            const models = execSync('ollama list', { encoding: 'utf-8' });
            if (models.includes('qwen')) {
                console.log('✅ LLM model found');
            } else {
                console.log('⚠️  No LLM model found. Run: ollama pull qwen2.5-coder');
            }
        } catch { }
    } catch {
        console.log('⚠️  Ollama not found (needed for free AI).');
        console.log('   Install: https://ollama.com/download');
        console.log('   Then run: ollama pull qwen2.5-coder');
    }

    console.log('\n✅ Setup complete! Run: insight --help\n');

    if (callback) callback();
}

// ─── Help ──────────────────────────────────────────────────────

function showHelp() {
    console.log(`
   ___ _  _ ___ ___ ___  _  _ _____ 
  |_ _| \\| / __|_ _/ __|| || |_   _|
   | || .\` \\__ \\| | (_ || __ | | |  
  |___|_|\\_|___/___\\___||_||_| |_|  

  ✨ AI-Powered Code Intelligence Engine

USAGE
  insight <command> [options]

COMMANDS
  analyze <path>        Analyze a codebase (ingest → chunk → embed → index)
  chat                  Chat with your codebase (with memory)
  overview [path]       Generate a project overview
  learn [path]          Generate a learning path for the codebase
  architecture [path]   Analyze the code architecture
  deps [path]           Map out all dependencies
  stories [path]        📖 Generate a full 8-chapter project story (most powerful)
  report [path]         Generate a full analysis report (all types)
  doctor                Check system health (Python, Ollama, etc.)
  setup                 Install/repair Python dependencies

OPTIONS
  -p, --provider        LLM provider: ollama (free, default) or openai
  -m, --model           Model name override
  -d, --persist-dir     Vector store directory (default: ./chroma_db)
  -f, --file-types      File types to analyze (default: .py .js .ts .jsx .tsx)
  -e, --embedding       Embedding provider: local (free, default) or openai
  -o, --output          Save report to file
  --help, -h            Show this help
  --version             Show version

EXAMPLES
  insight analyze ./my-project       Analyze a MERN project
  insight chat                       Chat about the analyzed code
  insight overview                   Get a project overview
  insight report -o report.md        Full report saved to file
  insight chat -p openai             Use OpenAI GPT-4 (paid)

FIRST TIME?
  1. insight setup                   Install dependencies
  2. ollama pull qwen2.5-coder       Download free LLM
  3. insight analyze ./your-project  Analyze your code
  4. insight chat                    Start chatting!
`);
}
