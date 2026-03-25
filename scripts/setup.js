/**
 * Postinstall script — runs after `npm install -g insight-ai`.
 * Sets up Python venv and installs dependencies automatically.
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const PACKAGE_DIR = path.resolve(__dirname, '..');
const VENV_DIR = path.join(PACKAGE_DIR, '.venv');
const PYTHON_DIR = path.join(PACKAGE_DIR, 'python');

console.log('\n🔍 INsight — Setting up AI engine...\n');

// 1. Find Python
let pythonCmd = null;
for (const cmd of ['python3', 'python']) {
    try {
        const version = execSync(`${cmd} --version`, { encoding: 'utf-8' }).trim();
        const match = version.match(/(\d+)\.(\d+)/);
        if (match && parseInt(match[1]) >= 3 && parseInt(match[2]) >= 9) {
            pythonCmd = cmd;
            console.log(`✅ Found ${version}`);
            break;
        }
    } catch { }
}

if (!pythonCmd) {
    console.log('⚠️  Python 3.9+ not found. Run `insight setup` after installing Python.');
    console.log('   Download: https://www.python.org/downloads/\n');
    process.exit(0); // Don't fail npm install
}

// 2. Create venv
if (!fs.existsSync(VENV_DIR)) {
    console.log('📦 Creating virtual environment...');
    try {
        execSync(`${pythonCmd} -m venv "${VENV_DIR}"`, { stdio: 'pipe' });
        console.log('✅ Virtual environment created');
    } catch (err) {
        console.log('⚠️  Could not create venv. Run `insight setup` manually.');
        process.exit(0);
    }
}

// 3. Install Python package
const isWin = process.platform === 'win32';
const pip = isWin
    ? path.join(VENV_DIR, 'Scripts', 'pip')
    : path.join(VENV_DIR, 'bin', 'pip');

console.log('📥 Installing AI engine (this may take 1-2 minutes)...');
try {
    execSync(`"${pip}" install -e "${PYTHON_DIR}" --quiet 2>&1`, {
        stdio: 'pipe',
        timeout: 300000
    });
    console.log('✅ AI engine installed');
} catch (err) {
    console.log('⚠️  Some dependencies failed. Run `insight setup` to retry.');
}

console.log('\n✅ INsight ready! Run: insight --help');
console.log('   First time? Run: insight setup\n');
