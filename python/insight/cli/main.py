"""CLI entry point for INsight."""

import os
import sys
from pathlib import Path

# Add project root to sys.path for robust local imports
root_path = str(Path(__file__).resolve().parent.parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import click
import httpx
import threading
from typing import List, Optional

import warnings
warnings.filterwarnings("ignore")

import logging
logging.getLogger("langchain").setLevel(logging.ERROR)
logging.getLogger("pydantic").setLevel(logging.ERROR)

# Also set environment variables to suppress some library noise
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.simplefilter("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HTTP_LOG_LEVEL"] = "error"

# Silence specific library loggers
for logger_name in ["transformers", "huggingface_hub", "absl", "urllib3", "chromadb", "langchain", "langchain_core"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

# ─── CLI Imports ────────────────────────────────────────────────
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.theme import Theme
from rich.prompt import Prompt
from rich.text import Text
from rich.tree import Tree
from rich.live import Live # Added Live import

# Claude-like premium theme
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "user": "bold #F4A261",  # Warm user color
    "ai": "bold #A56EFF",    # Deep AI purple
    "highlight": "bold cyan",
    "muted": "dim default"
})

# Global console
console = Console(theme=custom_theme)

def get_api_key(provider: str, manual_key: Optional[str] = None) -> Optional[str]:
    """
    Get the API key for a provider with the following fallback priority:
    1.  Manual Override (CLI flag)
    2.  Project-level .env
    3.  Global Config (~/.insight/config.json)
    """
    # 1. CLI Flag
    if manual_key:
        return manual_key
    
    # 2. .env (Usually happens automatically if providers load it, but we check here)
    env_vars = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY"
    }
    env_name = env_vars.get(provider.lower())
    if env_name and os.getenv(env_name):
        return os.getenv(env_name)
        
    # 3. Database (Remote Supabase)
    from insight.database.manager import db_manager
    from insight.database.models import User
    
    if getattr(db_manager, "SessionLocal", None):
        try:
            with next(db_manager.get_session()) as session:
                if session:
                    # For now, we assume a single 'admin' user or the first user in the DB
                    # In a full multi-user app, we would use the authenticated user's ID
                    user = session.query(User).filter_by(username="admin").first()
                    if user and user.api_keys and provider.lower() in user.api_keys:
                        return user.api_keys[provider.lower()]
        except Exception:
            pass

    # 4. Global Config File (Fallback)
    from insight.utils.config_manager import ConfigManager
    cm = ConfigManager()
    return cm.get_key(provider)


def set_provider_env(provider: str, api_key: Optional[str]):
    """Inject the key into the environment session."""
    if not api_key: return
    env_vars = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY"
    }
    env_name = env_vars.get(provider.lower())
    if env_name:
        os.environ[env_name] = api_key


def prewarm_model(provider: str, model: Optional[str] = None):
    """
    Background thread to warm up the Ollama model (silent request).
    """
    try:
        # Silently trigger a load
        if provider == "ollama":
            httpx.post("http://localhost:11434/api/generate",
                       json={"model": model or "qwen2.5-coder:latest", "prompt": ""},
                       timeout=0.1)
    except Exception:
        pass # Ignore timeouts/errors


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """✨ INsight - Professional AI Code Analyst"""
    # Initialize Database Schema if DATABASE_URL is present
    from insight.database.manager import db_manager
    try:
        db_manager.init_db()
    except Exception as e:
        # Don't crash if DB is unreachable, just log it
        pass


# ─── Analyze Command ────────────────────────────────────────────

@cli.command()
@click.argument('path', default='.', type=click.Path(exists=True))
@click.option('--embedding', type=click.Choice(['ollama', 'openai', 'google']), default='ollama', help='Provider for embeddings')
@click.option('--model', help='Embedding model name override')
@click.option('--persist-dir', '-d', default='./chroma_db',
              help='Vector store directory')
@click.option('--chunking', type=click.Choice(['chars', 'ast']), default='ast', help='Chunking strategy (default: ast)')
@click.option('--api-key', '-k', default=None, help='Direct API key override')
@click.option('--append', is_flag=True, help='Append to existing index instead of clearing')
def analyze(path, embedding, model, api_key, persist_dir, chunking, append):
    """Analyze a codebase and create a specialized vector index."""
    console.print(Panel(
        f"[highlight]Analyzing Workspace:[/highlight] {path}",
        title="[ai]✦ INsight Engine[/ai]",
        border_style="cyan"
    ))

    from insight.ingestion import load_codebase
    from insight.vectorstore import create_vector_store, load_vector_store

    # ✦ Clean slate logic
    if not append and os.path.exists(persist_dir):
        with console.status("[info]Cleaning existing index...[/info]"):
            vs_old = load_vector_store(persist_dir)
            if vs_old:
                vs_old.clear()
        console.print("[dim]Existing index cleared.[/dim]")
    
    # Default file types for analysis
    default_file_types = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb', '.php', '.c', '.cpp', '.h', '.hpp', '.cs', '.swift', '.kt', '.rs', '.vue', '.svelte', '.html', '.css', '.scss', '.less', '.json', '.yaml', '.yml', '.xml', '.sh', '.bash', '.zsh', '.ps1', '.md', '.txt']
    documents = load_codebase(path, default_file_types)

    if not documents:
        console.print("[error]⨯ No supported source code files found![/error]")
        return

    console.print(f"[success]✓[/success] Ingested {len(documents)} raw files")
    
    # ✦ Visual Tree
    console.print("\n[highlight]Project Structure:[/highlight]")
    console.print(_generate_project_tree(path))

    with console.status("[info]Chunking and generating embeddings...[/info]", spinner="bouncingBar"):
        vs = create_vector_store(
            documents,
            persist_directory=persist_dir,
            embedding_provider=embedding,
            embedding_model=model, # Pass model to vector store
            chunking_strategy=chunking
        )

    stats = vs.get_collection_stats()
    console.print(f"[success]✓[/success] Generated {stats.get('total_vectors', 0)} semantic vectors")
    
    console.print("\n[info]Analysis complete. You can now chat with your code:[/info]")
    console.print("  [highlight]insight chat[/highlight]")


# ─── Chat Command ───────────────────────────────────────────────

@cli.command()
@click.option('--persist-dir', '-d', default='./chroma_db', help='Vector store directory')
@click.option('--provider', '-p', type=click.Choice(['ollama', 'openai', 'anthropic', 'google', 'groq']), default='ollama',
              help='LLM provider')
@click.option('--model', '-m', default=None, help='Model name override')
@click.option('--api-key', '-k', default=None, help='Direct API key override')
@click.option('--stream', is_flag=True, help='Output raw JSON stream for UI consumption')
@click.argument('query', required=False)
def chat(persist_dir, provider, model, api_key, stream, query):
    """Chat interactively with your codebase."""
    from insight.vectorstore import load_vector_store
    from insight.chains.conversational_chain import chat as do_chat

    # Resolve and inject API key
    resolved_key = get_api_key(provider, api_key)
    set_provider_env(provider, resolved_key)

    vs = load_vector_store(persist_dir)
    if not vs:
        console.print("[error]⨯ Workspace not indexed.[/error]")
        console.print("Please run [highlight]insight analyze <path>[/highlight] first.")
        return

    # Single query mode
    if query:
        from insight.chains.conversational_chain import stream_chat
        
        if stream:
            # JSON streaming mode for Node.js bridge
            for chunk in stream_chat(vs, question=query, llm_provider=provider, llm_model=model):
                import json
                print(json.dumps(chunk), flush=True)
            return

        console.print(f"\n[ai]✦ INsight[/ai]")
        full_response: str = ""
        sources: List[str] = [] 
        with Live(Panel("", title="✦ INsight", border_style="cyan"), 
                    console=console, refresh_per_second=10) as live:
            for chunk in stream_chat(vs, question=query, llm_provider=provider, llm_model=model):
                if "token" in chunk:
                    full_response += str(chunk["token"])
                    live.update(Panel(Markdown(full_response + "▌"), title="✦ INsight", border_style="cyan"))
                elif "sources" in chunk:
                    sources = chunk["sources"]
            
        live.update(Panel(Markdown(full_response), title="✦ INsight", border_style="cyan"))
        _print_sources(sources)
        return

    # Interactive mode
    console.print(Panel(
        "[muted]Type your question below. Type 'exit' to quit.[/muted]",
        title="[bold cyan]✦ INsight CLI Chat[/bold cyan]",
        border_style="magenta"
    ))

    # Phase 2: Pre-warm in background
    threading.Thread(target=prewarm_model, args=(provider, model,), daemon=True).start()
    console.print("[dim]✦ Warming up model for near-instant response...[/dim]")

    session_id = None
    while True:
        try:
            console.print() # Spacer
            question = Prompt.ask("[user]O You[/user]")

            if question.lower() in ['exit', 'quit', 'q']:
                break

            if not question.strip():
                continue

            from insight.chains.conversational_chain import stream_chat
            
            console.print(f"\n[ai]✦ INsight[/ai]")
            with Live(Markdown("▌"), refresh_per_second=15, console=console) as live:
                full_text: str = ""
                sources: List[str] = []
                for chunk in stream_chat(
                    vs, question=question,
                    session_id=session_id,
                    llm_provider=provider,
                    llm_model=model
                ):
                    if "status" in chunk:
                        live.update(Panel(f"[bold cyan]✦[/bold cyan] [italic]{chunk['status']}[/italic]", border_style="dim"))
                        continue
                    if "token" in chunk:
                        full_text += str(chunk["token"])
                        live.update(Markdown(full_text + "▌"))
                    elif "sources" in chunk:
                        sources = chunk["sources"]
                    elif "session_id" in chunk:
                        session_id = chunk["session_id"]
                
                live.update(Markdown(full_text)) # Final update
            
            _print_sources(sources)

        except KeyboardInterrupt:
            break
        except Exception as e:
            _handle_llm_error(e, provider, model)
            
    console.print("\n[muted]Session ended.[/muted]")


# ─── Analysis Commands ──────────────────────────────────────────

@cli.command()
@click.argument('project_path', type=click.Path(exists=True), required=False)
@click.option('--persist-dir', '-d', default='./chroma_db')
@click.option('--provider', '-p', type=click.Choice(['ollama', 'openai', 'anthropic', 'google', 'groq']), default='ollama')
@click.option('--model', '-m', default=None)
@click.option('--api-key', '-k', default=None, help='Direct API key override')
@click.option('--output', '-o', default=None, help='Save report to file (.md)')
def overview(project_path, persist_dir, provider, model, api_key, output):
    """Generate a high-level project overview."""
    _run_analysis("overview", project_path, persist_dir, provider, model, api_key, output)


@cli.command()
@click.argument('project_path', type=click.Path(exists=True), required=False)
@click.option('--persist-dir', '-d', default='./chroma_db')
@click.option('--provider', '-p', type=click.Choice(['ollama', 'openai', 'anthropic', 'google', 'groq']), default='ollama')
@click.option('--model', '-m', default=None)
@click.option('--api-key', '-k', default=None, help='Direct API key override')
@click.option('--output', '-o', default=None, help='Save report to file (.md)')
def learn(project_path, persist_dir, provider, model, api_key, output):
    """Generate a step-by-step learning path for the code."""
    _run_analysis("learning", project_path, persist_dir, provider, model, api_key, output)


@cli.command()
@click.argument('project_path', type=click.Path(exists=True), required=False)
@click.option('--persist-dir', '-d', default='./chroma_db')
@click.option('--provider', '-p', type=click.Choice(['ollama', 'openai', 'anthropic', 'google', 'groq']), default='ollama')
@click.option('--model', '-m', default=None)
@click.option('--api-key', '-k', default=None, help='Direct API key override')
@click.option('--output', '-o', default=None, help='Save report to file (.md)')
def architecture(project_path, persist_dir, provider, model, api_key, output):
    """Analyze the architecture and design patterns."""
    _run_analysis("architecture", project_path, persist_dir, provider, model, api_key, output)


@cli.command()
@click.argument('project_path', type=click.Path(exists=True), required=False)
@click.option('--persist-dir', '-d', default='./chroma_db')
@click.option('--provider', '-p', type=click.Choice(['ollama', 'openai', 'anthropic', 'google', 'groq']), default='ollama')
@click.option('--model', '-m', default=None)
@click.option('--api-key', '-k', default=None, help='Direct API key override')
@click.option('--output', '-o', default=None, help='Save report to file (.md)')
def deps(project_path, persist_dir, provider, model, api_key, output):
    """Map out all internal and external dependencies."""
    vs = _ensure_vectorstore(project_path, persist_dir)
    if vs:
        console.print("\n[highlight]Detected Dependency Map:[/highlight]")
        console.print(_generate_dependency_visual(vs))
        console.print()
        
    _run_analysis("dependencies", project_path, persist_dir, provider, model, api_key, output)


@cli.command()
@click.argument('project_path', type=click.Path(exists=True), required=False)
@click.option('--persist-dir', '-d', default='./chroma_db')
@click.option('--provider', '-p', type=click.Choice(['ollama', 'openai', 'anthropic', 'google', 'groq']), default='ollama')
@click.option('--model', '-m', default=None)
@click.option('--api-key', '-k', default=None, help='Direct API key override')
@click.option('--output', '-o', default=None, help='Save report to file (.md)')
def report(project_path, persist_dir, provider, model, api_key, output):
    """Generate a full master report (all analysis combined)."""
    # Resolve and inject API key
    resolved_key = get_api_key(provider, api_key)
    set_provider_env(provider, resolved_key)
    
    vs = _ensure_vectorstore(project_path, persist_dir)
    if not vs:
        return

    from insight.chains import run_full_report

    console.print(Panel("[highlight]Compiling Master Project Report[/highlight]", border_style="cyan"))

    with console.status("[info]Generating comprehensive analysis (this may take a minute)...[/info]", spinner="bouncingBar"):
        results = run_full_report(vs, llm_provider=provider, llm_model=model)

    full_md: str = ""
    for analysis_type, data in results.items():
        title = analysis_type.replace("_", " ").title()
        full_md += f"# ❖ {title}\n\n{data['result']}\n\n"
        
        console.print(f"\n[ai]✦ {title}[/ai]")
        console.print(Panel(Markdown(data['result']), border_style="dim", padding=(1,2)))
        _print_sources(data.get('sources', []))

    if output:
        _save_to_file(output, full_md)


# ─── Stories Command ─────────────────────────────────────────────

@cli.command(name="stories")
@click.argument('project_path', type=click.Path(exists=True), required=False)
@click.option('--persist-dir', '-d', default='./chroma_db')
@click.option('--provider', '-p', type=click.Choice(['ollama', 'openai', 'anthropic', 'google', 'groq']), default='ollama')
@click.option('--model', '-m', default=None)
@click.option('--api-key', '-k', default=None, help='Direct API key override')
@click.option('--output', '-o', default=None, help='Save story to file (.md)')
def stories(project_path, persist_dir, provider, model, api_key, output):
    """📖 Generate a full 8-chapter project story — the single most powerful codebase analysis."""
    _run_stories(project_path, persist_dir, provider, model, api_key, output)


@cli.command(name="story")
@click.argument('project_path', type=click.Path(exists=True), required=False)
@click.option('--persist-dir', '-d', default='./chroma_db')
@click.option('--provider', '-p', type=click.Choice(['ollama', 'openai', 'anthropic', 'google', 'groq']), default='ollama')
@click.option('--model', '-m', default=None)
@click.option('--api-key', '-k', default=None, help='Direct API key override')
@click.option('--output', '-o', default=None, help='Save story to file (.md)')
def story(project_path, persist_dir, provider, model, api_key, output):
    """📖 Alias for 'stories'."""
    _run_stories(project_path, persist_dir, provider, model, api_key, output)


def _run_stories(project_path, persist_dir, provider, model, api_key=None, output=None):
    """Internal runner for stories/story."""
    from insight.vectorstore import load_vector_store
    from insight.chains.analysis_chains import run_stories

    vs = _ensure_vectorstore(project_path, persist_dir)
    if not vs:
        return

    # Cinematic header
    console.print("\n")
    console.print(Panel(
        "[bold #A56EFF]📖 INsight Project Story Generator[/bold #A56EFF]\n"
        "[dim]Weaving together architecture, modules, flows, and learning paths\n"
        "into one comprehensive developer narrative...[/dim]",
        border_style="bright_magenta",
        padding=(1, 4)
    ))

    from rich.prompt import Prompt
    
    # Mode Selection
    console.print("\n[bold #A56EFF]✦ Choose Your Story Mode:[/bold #A56EFF]")
    console.print("[dim]1.[/dim] [bold white]Detailed Technical Pass[/bold white] [dim](12 Chapters — Deep technical audit)[/dim]")
    console.print("[dim]2.[/dim] [bold white]Architect's Mental Model[/bold white] [dim](12 Phases — Layered flows & 'Why')[/dim]")
    
    choice = Prompt.ask(
        "\n[ai]Select mode (1 or 2)[/ai]",
        choices=["1", "2"],
        default="2"
    )
    
    mode_name = "Detailed" if choice == "1" else "Architect"
    mode_arg = "detailed" if choice == "1" else "architect"

    # Resolve and inject API key for stories
    resolved_key = get_api_key(provider, api_key)
    set_provider_env(provider, resolved_key)

    with console.status(
        f"[ai]✧ Synthesizing your {mode_name} Story (v3.2)...[/ai]",
        spinner="bouncingBar"
    ):
        result = run_stories(
            vs,
            project_path=project_path,
            llm_provider=provider,
            llm_model=model,
            mode=mode_arg,
            markdown_style=bool(output)
        )

    story_text: str = result.get("result", "")
    sources: List[str] = result.get("sources", [])

    if output:
        # For file output, we write RAW content (no headers, no footers, no CLI junk)
        _save_to_file(output, story_text, append_footer=False)
    else:
        # For terminal, we show the visual UI
        console.print(Panel(
            Markdown(story_text),
            title="[bold #A56EFF]✦ Codebase Story (v3.0)[/bold #A56EFF]",
            border_style="bright_magenta",
            padding=(1, 2)
        ))
        _print_sources(sources)
        
        # Suggest the export command with timestamp
        import datetime
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        suggested = f"insight_story_{ts}.md"
        console.print(
            f"\n[dim]💡 Tip: Export this handbook with [bold]--output {suggested}[/bold][/dim]"
        )


# ─── Doctor Command ─────────────────────────────────────────────

@cli.command()
def doctor():
    """Diagnostic tool for system health and dependencies."""
    console.print(Panel("[highlight]System Diagnostics[/highlight]", border_style="cyan"))

    checks = []

    # Python
    import sys
    checks.append(("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", "[success]✓[/success]"))

    # Vector DB
    try:
        import chromadb
        checks.append(("Vector Engine (Chroma)", getattr(chromadb, '__version__', 'ready'), "[success]✓[/success]"))
    except ImportError:
        checks.append(("Vector Engine (Chroma)", "missing", "[error]⨯[/error]"))

    # Ollama
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code == 200:
            models = r.json().get('models', [])
            if models:
                model_names = [m['name'] for m in models[:3]]
                checks.append(("Local AI (Ollama)", f"running ({', '.join(model_names)})", "[success]✓[/success]"))
            else:
                checks.append(("Local AI (Ollama)", "running (no models installed!)", "[warning]![/warning]"))
        else:
            checks.append(("Local AI (Ollama)", "not responding", "[warning]![/warning]"))
    except Exception:
        checks.append(("Local AI (Ollama)", "not running/installed", "[error]⨯[/error]"))

    table = Table(box=None, header_style="dim", padding=(0, 2))
    table.add_column("Component")
    table.add_column("Status")
    table.add_column("State", justify="center")

    for name, status, icon in checks:
        table.add_row(name, status, icon)

    console.print("")
    console.print(table)
    console.print("")


@cli.command()
@click.option('--force', is_flag=True, help='Force reinstall of dependencies')
def setup(force):
    """🏠 Initial setup: Pull models and verify environment."""
    console.print(Panel("[highlight]INsight Welcome & Setup[/highlight]", border_style="bright_magenta"))
    
    # 1. Check Ollama
    with console.status("[info]Checking for Ollama...[/info]"):
        import subprocess
        try:
            subprocess.run(["ollama", "--version"], capture_output=True, check=True)
            console.print("[success]✓[/success] Ollama is installed")
        except:
            console.print("[error]⨯ Ollama not found.[/error]")
            console.print("Please install from: https://ollama.com\n")
            return

    # 2. Pull model
    console.print("[info]Recommended Model:[/info] qwen2.5-coder:latest (7B)")
    if click.confirm("Do you want to pull the recommended model now?"):
        console.print("[dim]Pulling model (this may take a few minutes)...[/dim]")
        try:
            # Use unbuffered output for the pull
            import subprocess
            process = subprocess.Popen(["ollama", "pull", "qwen2.5-coder:latest"], 
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if process.stdout is not None:
                for line in process.stdout:
                    console.print(f"  [muted]{line.strip()}[/muted]", end="\r")
            process.wait()
            console.print("\n[success]✓[/success] Model ready!")
        except Exception as e:
            console.print(f"\n[error]⨯ Failed to pull model: {e}[/error]")

    # 3. Final instructions
    console.print("\n[success]✅ Setup complete![/success]")
    console.print("Try running: [highlight]insight analyze .[/highlight]")


# ─── Visual Helpers ─────────────────────────────────────────────

def _generate_project_tree(project_path):
    """Generate a visual project tree using rich.tree."""
    import os
    
    canonical_path = os.path.abspath(project_path)
    base_name = os.path.basename(canonical_path) or canonical_path
    tree = Tree(f"📁 [highlight]{base_name}[/highlight]")
    
    exclude_dirs = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', '.gemini'}
    include_exts = {'.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.json'}
    
    # Simple limit to avoid massive trees
    MAX_FILES = 40
    files_count = 0
    
    def add_to_tree(path, parent_node):
        nonlocal files_count
        if files_count >= MAX_FILES: return
        
        try:
            # Sort items: dirs first, then files
            items = sorted(os.listdir(path))
            dirs = [i for i in items if os.path.isdir(os.path.join(path, i)) and i not in exclude_dirs]
            files = [i for i in items if os.path.isfile(os.path.join(path, i)) and any(i.endswith(ext) for ext in include_exts)]
            
            for d in dirs:
                branch = parent_node.add(f"📁 {d}", style="cyan")
                add_to_tree(os.path.join(path, d), branch)
                    
            for f in files:
                if files_count < MAX_FILES:
                    parent_node.add(f"📄 {f}", style="muted")
                    files_count += 1
                else:
                    parent_node.add("...", style="dim")
                    break
        except Exception:
            pass

    add_to_tree(canonical_path, tree)
    return tree


def _generate_dependency_visual(vs):
    """Generate a visual dependency summary from vectorstore metadata."""
    from collections import Counter
    import os

    # Extract all imports from metadata
    all_docs = vs.get_all_documents()
    external_deps: List[str] = []
    internal_links: List[str] = []

    for doc in all_docs:
        # Imports are stored as comma-sep strings in metadata by our parsers
        imports_str: str = doc.metadata.get('imports', '')
        if not imports_str: continue
        
        file_path: str = doc.metadata.get('source', 'unknown')
        file_name: str = os.path.basename(file_path)
        
        imports = [i.strip() for i in imports_str.split(',') if i.strip()]
        for imp in imports:
            # Simple heuristic: if it contains a '.', it's often internal or a sub-module
            if imp.startswith('.') or any(x in imp for x in ['insight', 'src', 'app', 'core']):
                internal_links.append(f"{file_name} ➔ {imp}")
            else:
                # Take the base package name (e.g., 'langchain.chains' -> 'langchain')
                base_pkg = imp.split('.')[0]
                external_deps.append(base_pkg)

    # Build Top External Table
    top_ext = Counter(external_deps).most_common(8)
    table = Table(title="[highlight]Top External Packages[/highlight]", box=None, header_style="bold cyan")
    table.add_column("Package", style="magenta")
    table.add_column("Usage Count", justify="right", style="dim")
    
    for pkg, count in top_ext:
        table.add_row(pkg, str(count))

    return table


# ─── Helpers ────────────────────────────────────────────────────

def _ensure_vectorstore(project_path, persist_dir):
    """Load existing vector store or analyze project first."""
    from insight.vectorstore import load_vector_store
    from pathlib import Path

    if Path(persist_dir).exists():
        vs = load_vector_store(persist_dir)
        if vs: return vs

    if project_path:
        console.print(f"[warning]No existing index found. Analyzing workspace first...[/warning]")
        from insight.ingestion import load_codebase
        from insight.vectorstore import create_vector_store

        with console.status("[info]Parsing codebase...[/info]"):
            documents = load_codebase(project_path)
        if not documents:
            console.print("[error]⨯ No supported source code files found![/error]")
            return None

        with console.status("[info]Indexing...[/info]"):
            vs = create_vector_store(documents, persist_directory=persist_dir)
        return vs

    console.print("[error]⨯ Workspace not indexed.[/error]")
    console.print("Please run [highlight]insight analyze <path>[/highlight] first.")
    return None


def _run_analysis(analysis_type, project_path, persist_dir, provider, model, api_key=None, output_file=None):
    """Run a specific analysis type and format nicely."""
    # Resolve and inject API key
    resolved_key = get_api_key(provider, api_key)
    set_provider_env(provider, resolved_key)

    vs = _ensure_vectorstore(project_path, persist_dir)
    if not vs: return

    from insight.chains import run_analysis

    title = analysis_type.replace("_", " ").title()
    
    # ✦ Visual Tree for Overview
    if analysis_type == "overview" and project_path:
        console.print("\n[highlight]Workspace Context:[/highlight]")
        console.print(_generate_project_tree(project_path))
        console.print()

    try:
        with console.status(f"[info]Synthesizing {title.lower()}...[/info]", spinner="bouncingBar"):
            result = run_analysis(vs, analysis_type=analysis_type, llm_provider=provider, llm_model=model)

        console.print(f"\n[ai]✦ {title}[/ai]")
        console.print(Panel(Markdown(result['result']), border_style="dim", padding=(1, 2)))
        _print_sources(result.get('sources', []))

        if output_file:
            content = f"# {title}\n\n{result['result']}"
            _save_to_file(output_file, content)
            
    except Exception as e:
        _handle_llm_error(e, provider, model)


def _handle_llm_error(e, provider, model=None):
    """Provide helpful error messages for LLM failures."""
    err_str = str(e).lower()
    
    if "model_not_found" in err_str or "404" in err_str:
        console.print(f"\n[error]⨯ AI Model Error:[/error] The model '{model or 'default'}' was not found.")
        console.print(f"[info]Tip:[/info] Try a different model or use the new default: [highlight]-m gpt-4o-mini[/highlight]")
    elif "invalid_api_key" in err_str or "401" in err_str:
        console.print(f"\n[error]⨯ Authentication Error:[/error] Your {provider.upper()} API key is invalid.")
        console.print(f"[info]Tip:[/info] Check your [highlight].env[/highlight] file.")
    elif "rate_limit" in err_str or "429" in err_str:
        console.print(f"\n[error]⨯ Rate Limit Reached:[/error] {provider.upper()} is throttling requests.")
        console.print(f"[info]Action:[/info] I've already reduced context and tried 2 retries, but the API is still blocked.")
        console.print(f"[info]Tip:[/info] Use [highlight]gpt-4o-mini[/highlight] (it has 10x higher limits) or run locally with [highlight]-p ollama[/highlight].")
    elif "413" in err_str or "request too large" in err_str or "tpm" in err_str:
        console.print(f"\n[error]⨯ Token Limit Exceeded:[/error] The request is too large for {provider.upper()}'s current tier.")
        console.print(f"[info]Tip:[/info] This usually happens with Groq's free tier. Try [highlight]-p ollama[/highlight] for full depth, or use a smaller project for stories.")
    else:
        console.print(f"\n[error]⨯ AI Error:[/error] {str(e)}")


def _save_to_file(filepath, content, append_footer=True):
    """Save markdown content to a file."""
    try:
        import os
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            if append_footer:
                f.write("\n\n---\n*Generated by INsight AI Engine*")
            
        console.print(f"\n[success]✓[/success] Report successfully exported to: [highlight]{filepath}[/highlight]")
    except Exception as e:
        console.print(f"\n[error]⨯ Failed to save file: {str(e)}[/error]")


def _print_sources(sources):
    """Print source citations seamlessly."""
    if sources:
        console.print("  [muted]Referenced Files:[/muted]")
        for source in sources[:5]:
            # Just show filename rather than absolute path if possible
            import os
            name = os.path.basename(source)
            console.print(f"  [muted]• {name}[/muted]")


@cli.group()
def config():
    """Manage global INsight configuration (API keys, themes, etc)."""
    pass

@config.command(name="set-key")
@click.argument('provider', type=click.Choice(['openai', 'anthropic', 'google', 'groq']))
@click.argument('key')
def set_key(provider, key):
    """Save an API key globally in your home directory."""
    from insight.utils.config_manager import ConfigManager
    cm = ConfigManager()
    cm.set_key(provider, key)
    console.print(f"[success]✓[/success] Global [highlight]{provider}[/highlight] API key saved to ~/.insight/config.json")

@config.command(name="list")
def list_keys():
    """List all globally configured providers."""
    from insight.utils.config_manager import ConfigManager
    cm = ConfigManager()
    keys = cm.list_keys()
    if not keys:
        console.print("[warning]No global keys configured.[/warning]")
        return
        
    table = Table(title="Global API Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Provider", style="highlight")
    table.add_column("Saved Key", style="muted")
    
    for provider, masked in keys.items():
        table.add_row(provider, masked)
    
    console.print(table)

@config.command(name="remove")
@click.argument('provider')
def remove_key(provider):
    """Delete a specific API key from the global config."""
    from insight.utils.config_manager import ConfigManager
    cm = ConfigManager()
    cm.remove_key(provider)
    console.print(f"[success]✓[/success] Removed [highlight]{provider}[/highlight] key.")

@config.command(name="clear")
def clear_config():
    """Wipe all global configuration settings."""
    if click.confirm("Are you sure you want to clear ALL global keys?"):
        from insight.utils.config_manager import ConfigManager
        cm = ConfigManager()
        cm.clear()
        console.print("[success]✓[/success] Global configuration cleared.")


if __name__ == "__main__":
    cli()
