"""
Specialized Analysis Chains for INsight.

Each chain uses the same vector store but with different prompts
and retrieval strategies to produce different types of analysis.
"""

import sys
from pathlib import Path

# Add project root to sys.path for robust local imports
root_path = str(Path(__file__).resolve().parent.parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import os
import re
from typing import List, Dict, Any, Optional

try:
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate
except ImportError:
    from langchain_classic.chains import RetrievalQA
    from langchain_classic.prompts import PromptTemplate

from langchain_core.documents import Document
from insight.chains.qa_chain import get_llm
from insight.utils.fs_scanner import FilesystemScanner
from rich.console import Console

console = Console()


# ─── Shared Constraints ───────────────────────────────────────

INSIGHT_CORE_CONSTRAINTS = """You are INSIGHT — a high-fidelity documentation engine.
Strictly follow these VISUAL HIERARCHY rules:
1. USE MARKDOWN: Use `#`, `##`, and `###` for clear section nesting.
2. USE BULLETS: Use `-` for key points and `1.` for sequences.
3. CODE CITATIONS: Use `backticks` for every file and function name.
4. BOLD KEYWORDS: Use **bold** for major architectural components.
5. NO BOX DRAWING: Do NOT attempt to draw your own boxes or ASCII art.
6. RESPONSIVE: Keep descriptions concise to avoid excessive terminal wrapping."""

# ─── Prompt Templates ───────────────────────────────────────────

OVERVIEW_PROMPT = INSIGHT_CORE_CONSTRAINTS + """Provide a high-fidelity project overview based on the provided codebase.

Code context:
{context}

Question: {question}

Format your response using this structure:
1. **Executive Summary** — The "elevator pitch" of what this project is and does.
2. **Core Tech Stack** — Specific languages, frameworks, and critical libraries used.
3. **High-Level Layout** — Map the major directories to their functional roles.
4. **Primary Components** — The most important modules and their responsibilities.
5. **Execution Entry Points** — Where the system starts (e.g., main scripts, APIs).
6. **Data Lifecycle** — How information is ingested, processed, and outputted.

IMPORTANT: Cite actual `filenames` and `function_names`. Do NOT use ASCII boxes.

Overview:"""


LEARNING_PATH_PROMPT = INSIGHT_CORE_CONSTRAINTS + """You are a senior mentor guiding a new developer through this specific codebase. 

Code context:
{context}

Question: {question}

Create a structured learning path with these sections:
1. **The Ground Zero** — The very first file(s) to open and why they are foundational.
2. **Architectural Concepts** — Key patterns (e.g., RAG, Middleware) the developer must grasp.
3. **Step-by-Step Curriculum** — A numbered list of files/modules to study in logical order.
4. **Mission-Critical Functions** — The 3-5 most important functions to understand deeply.
5. **Developer Gotchas** — Non-obvious traps or unique patterns in this project.
6. **Knowledge Check Tasks** — Small coding exercises to prove understanding.

Reference specific `files` and `functions` throughout. Do NOT use ASCII boxes.

Learning Path:"""


ARCHITECTURE_PROMPT = INSIGHT_CORE_CONSTRAINTS + """You are a senior software architect. Analyze the provided codebase and extract its structural DNA.

Code context:
{context}

Question: {question}

Provide a deep-dive architecture report using this exact structure:

1. **Architecture Overview** — Describe the high-level pattern (e.g., MVC, Microservices, Event-Driven).
2. **Layered Analysis** — Identify the layers (e.g., ai-service, backend-api, frontend-ui) and their specific roles.
3. **Core Modules** — List the most critical files/folders and how they anchor the system.
4. **Data Flow & Logic** — Trace how a request moves from an endpoint (e.g., /chat) to the AI engine.
5. **Key Design Patterns** — Identify patterns like Factory, Singleton, or Middleware actually present in the code.
6. **Technical Strengths** — What parts of this architecture are built to scale or remain secure?
7. **Architect's Roadmap** — Recommendations for future decoupling or performance tuning.

IMPORTANT: Do NOT use ASCII art. Use bold text, lists, and code blocks only.

Architecture Analysis:"""


DEPENDENCY_PROMPT = INSIGHT_CORE_CONSTRAINTS + """Map the structural dependencies of this codebase with high precision.

Code context:
{context}

Question: {question}

Provide a comprehensive dependency audit:
1. **External Ecosystem** — Major third-party packages and where they anchor the project.
2. **Internal Module Map** — How the main folders/modules depend on each other.
3. **Critical Import Chains** — The most frequent or important import patterns.
4. **Foundation Modules** — The most-imported files that form the base of the app.
5. **Isolated Leaf Modules** — Modules that have zero internal dependencies.
6. **Structural Risks** — Circular dependencies or excessive coupling detected.

Use hierarchy lists and `file_paths`. Do NOT use ASCII boxes.

Dependency Analysis:"""


STORIES_PROMPT = """You are INSIGHT — an elite software chronicler. Tell the definitive story of this project.

⚠️ CRITICAL ANTI-HALLUCINATION MANDATE ⚠️
You MUST base EVERYTHING on the CODE CONTEXT below. No generic guesses.

CODE CONTEXT (THE PROJECT):
{context}

Question: {question}

Write the "Project Story" using these high-fidelity Phase headers:

### Phase 1: THE BIG PICTURE
- What does THIS project specifically do? (cite `filenames`)
- What major problem is it solving in the real world?

### Phase 2: ARCHTECTURE & FLOW
- What is the structural DNA (e.g., MVC, Layered)?
- Describe the logic flow from user input to result (cite `functions`).

### Phase 3: THE HEART OF THE SYSTEM
- Identify the 3 most critical modules/files.
- Explain why the project would collapse without them.

### Phase 4: DEVELOPER JOURNEY
- The "Golden Path" of learning this system.
- Start at File A and move to File Z.

### Phase 5: ROADMAP & EVOLUTION
- Technical strengths detected in the code.
- Potential technical debt or recommended optimizations.

IMPORTANT: Use Markdown headers and bold lists. Do NOT attempt ASCII art or diagrams.

Project Story:"""


# ─── Chain Creation ─────────────────────────────────────────────

def _create_analysis_chain(
    vectorstore_manager,
    prompt_template: str,
    llm_provider: str = "ollama",
    llm_model: Optional[str] = None,
    k: int = 10,
    temperature: float = 0.3
) -> RetrievalQA:
    """Create a specialized analysis chain."""
    llm = get_llm(provider=llm_provider, model=llm_model, temperature=temperature)
    retriever = vectorstore_manager.as_retriever(k=k)

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        verbose=False,
        chain_type_kwargs={"prompt": prompt}
    )


def run_analysis(
    vectorstore_manager,
    analysis_type: str,
    llm_provider: str = "ollama",
    llm_model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run a specialized analysis on the codebase.

    Args:
        vectorstore_manager: VectorStoreManager instance
        analysis_type: "overview", "learning", "architecture", or "dependencies"
        llm_provider: "ollama" (free) or "openai" (paid)
        llm_model: Model name override

    Returns:
        Dict with: analysis_type, result, sources
    """
    # Dynamic K based on provider (Save tokens on Cloud APIs, use more for Local)
    is_local = llm_provider == "ollama"
    
    configs = {
        "overview": {
            "prompt": OVERVIEW_PROMPT,
            "question": "Provide a complete project overview.",
            "k": 15 if is_local else 6,
        },
        "learning": {
            "prompt": LEARNING_PATH_PROMPT,
            "question": "Create a step-by-step learning path for this codebase.",
            "k": 15 if is_local else 6,
        },
        "architecture": {
            "prompt": ARCHITECTURE_PROMPT,
            "question": "Analyze the architecture of this project.",
            "k": 12 if is_local else 5,
        },
        "dependencies": {
            "prompt": DEPENDENCY_PROMPT,
            "question": "Map out all dependencies in this project.",
            "k": 12 if is_local else 5,
        },
    }

    if analysis_type not in configs:
        raise ValueError(f"Unknown analysis type: {analysis_type}. Choose from: {list(configs.keys())}")

    config = configs[analysis_type]
    prompt_val: str = str(config["prompt"])
    k_val: int = int(config["k"])

    chain = _create_analysis_chain(
        vectorstore_manager,
        prompt_template=prompt_val,
        llm_provider=llm_provider,
        llm_model=llm_model,
        k=k_val,
    )

    with console.status(f"[info]Synthesizing {analysis_type.replace('_', ' ')}...[/info]"):
        result = chain.invoke({"query": config["question"]})

    sources = list(set(
        doc.metadata.get('source', 'unknown')
        for doc in result.get('source_documents', [])
    ))

    return {
        "analysis_type": analysis_type,
        "result": result.get("result", ""),
        "sources": sources,
    }


def run_full_report(
    vectorstore_manager,
    llm_provider: str = "ollama",
    llm_model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run all analysis types and return a complete report.

    Returns:
        Dict with all 4 analysis results
    """
    report = {}
    analysis_types = ["overview", "learning", "architecture", "dependencies"]

    for analysis_type in analysis_types:
        import logging
        logging.getLogger(__name__).info(f"  📊 Running {analysis_type} analysis...")
        report[analysis_type] = run_analysis(
            vectorstore_manager,
            analysis_type=analysis_type,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

    return report


def run_stories(
    vectorstore_manager,
    project_path: Optional[str] = None,
    llm_provider: str = "ollama",
    llm_model: Optional[str] = None,
    mode: str = "architect",
    markdown_style: bool = False,
) -> Dict[str, Any]:
    """
    Generate the Deterministic Codebase Story (v3.2).
    Supports 'detailed' (12-chapter technical) and 'architect' (12-phase layered) modes.
    """
    import os
    
    llm = get_llm(provider=llm_provider, model=llm_model, temperature=0.0)
    
    # 1. Mandatory Context Validation
    # Check if we have documents in the vector store
    try:
        doc_count = vectorstore_manager.collection.count()
        if doc_count == 0:
            return {
                "result": "Unable to generate story: codebase context not properly loaded.",
                "sources": []
            }
    except Exception:
        pass

    # 2. Conservative Root Detection
    try:
        if project_path and os.path.exists(project_path):
            root = os.path.abspath(project_path)
        else:
            root = os.getcwd()
            home = os.path.expanduser("~")
            current = root
            for _ in range(3):
                if os.path.exists(os.path.join(current, ".git")):
                    root = current
                    break
                parent = os.path.dirname(current)
                if parent == current or parent == home or parent == "/": break
                current = parent
        fs_context = FilesystemScanner.scan_directory(root, max_depth=3)
    except Exception as e:
        fs_context = f"Structural info unavailable: {e}"

    # 3. Define Mode-Specific Chapters
    if mode == "architect":
        # Phase-based Architectural Story (v6.0)
        chapters = [
            {
                "id": 1, "title": "THE BIG PICTURE (MENTAL MODEL)",
                "search": "project purpose, mission, problem solved, audience",
                "prompt": "What is this system REALLY? Explain the core mental model in simple terms for a new engineer."
            },
            {
                "id": 2, "title": "SYSTEM LAYERS (ARCHITECTURE VIEW)",
                "search": "high level architecture, interface, orchestration, intelligence, storage layers",
                "prompt": "Break the system into Layers: Interface (CLI), Orchestration (Backend/Bridge), Intelligence (AI Service), Storage (Vector DB). Define responsibility and key files for each."
            },
            {
                "id": 3, "title": "CORE EXECUTION FLOW (TRACE)",
                "search": "main entry point, execution flow, request path, bridge interaction",
                "prompt": "Explain ONE COMPLETE FLOW (e.g., a story command run). User -> CLI -> Bridge -> Python -> DB -> Response. Step-by-step trace."
            },
            {
                "id": 4, "title": "FOLDER & MODULE DEEP DIVE",
                "search": "project structure, module responsibilities, interaction between directories",
                "prompt": "Explain the role of each primary directory. How do modules interact? Focus on modularity and separation of concerns."
            },
            {
                "id": 5, "title": "CORE LOGIC & IMPORTANT FUNCTIONS",
                "search": "critical functions, heart of system, business logic, key classes",
                "prompt": "Identify the most important functions/classes. What do they do? Why are they the 'heart' of the system code-wise?"
            },
            {
                "id": 6, "title": "DATA FLOW & STATE",
                "search": "data movement, input output processing, state storage, memory management",
                "prompt": "How data moves across the system. Input -> Processing -> Storage -> Output. Where is state (DB/Cache) managed?"
            },
            {
                "id": 7, "title": "DESIGN DECISIONS (WHY LAYER)",
                "search": "architecture rationale, tech stack choices, why node python bridge",
                "prompt": "Explain THE WHY. Why this architecture? Why Node+Python? Why Vector DB? Infer carefully from implementation clues."
            },
            {
                "id": 8, "title": "NON-OBVIOUS / HIDDEN LOGIC",
                "search": "complex parts, performance tricks, edge cases, tricky logic",
                "prompt": "Expose non-obvious logic, tricky edge cases, or optimizations (like width calculations) that a dev might miss."
            },
            {
                "id": 9, "title": "END-TO-END STORY (SIMPLIFIED)",
                "search": "summary story, end to end narrative",
                "prompt": "Re-explain the FULL system as an intuitive, clean story: 'When a user does X -> happens Y -> result Z'."
            },
            {
                "id": 10, "title": "HOW TO MODIFY / EXTEND",
                "search": "extension points, adding features, codebase modification guide",
                "prompt": "Developer Guide: Where to go in the code to add a feature, fix a bug, or change system behavior."
            },
            {
                "id": 11, "title": "RISKS & LIMITATIONS",
                "search": "technical debt, performance bottlenecks, scaling risks, known limitations",
                "prompt": "Senior Audit: Identify performance risks, technical debt, scaling issues, or missing pieces in the current codebase."
            },
            {
                "id": 12, "title": "FINAL SUMMARY (DNA)",
                "search": "core value proposition, technical highlights, project overview summary",
                "prompt": "10-15 bullet points capturing the entire system's technical DNA and unique value."
            }
        ]
    else:
        # Standard Technical Chapters (v3.1)
        chapters = [
            {
                "id": 1, "title": "BIG PICTURE",
                "search": "project purpose, mission, primary objective, README overview, main folder",
                "prompt": "Define the core problem and solution. Reference key files that embody the project mission."
            },
            {
                "id": 2, "title": "ARCHITECTURE & DESIGN",
                "search": "architecture pattern, design decisions, tech stack, function calls, class relationships, logic flow",
                "prompt": "Identify the architecture pattern. Map it to REAL files. Describe the Dependency Graph (function → function flows)."
            },
            {
                "id": 3, "title": "CORE MODULES & COMPONENTS",
                "search": "main directories, entry point files, business logic modules, controllers, services",
                "prompt": "Focus on 3-4 primary technical blocks. Describe folder-level responsibility and primary entry-point file for each."
            },
            {
                "id": 4, "title": "END-TO-END EXECUTION TRACE",
                "search": "request flow, data path, main functions lifecycle, process flow, execution trace",
                "prompt": "Trace ONE primary system request (e.g., API call or command). Step-by-step flow across files with exact function names."
            },
            {
                "id": 5, "title": "API CONTRACTS",
                "search": "router, controllers, API routes, express routes, endpoints, app.get, app.post, request body",
                "prompt": "Extract all available API routes. Show endpoint, expected body/params, and response format."
            },
            {
                "id": 6, "title": "DATABASE LAYER",
                "search": "schema.prisma, database models, migrations, prisma client, table relationships, entity definitions",
                "prompt": "Extract the Prisma schema or primary database models. Show relationships (e.g., One-to-Many) clearly."
            },
            {
                "id": 7, "title": "KEY FUNCTIONS & CLASSES",
                "search": "main classes, critical functions, heart of project, complex logic, core algorithms",
                "prompt": "List the Top 5 technical hearts. Explain code-level WHY they define the system behavior."
            },
            {
                "id": 8, "title": "CODE QUALITY ANALYSIS",
                "search": "TODOs, validation logic, error handling, try-catch, technical debt, code smells",
                "prompt": "Perform a senior-level audit. Detect tight coupling, missing validation, or poor error handling. Cite files."
            },
            {
                "id": 9, "title": "REFACTOR SUGGESTIONS",
                "search": "complexity, technical debt, refactoring needs, code cleanup, optimization",
                "prompt": "Provide ACTIONABLE file-level improvements. Show small example fixes for specific code found."
            },
            {
                "id": 10, "title": "DEVELOPER LEARNING PATH",
                "search": "getting started, setup, learning sequence, how it works, developer guide",
                "prompt": "Exact file reading order for a new dev. Highlight the 'Aha!' moment files."
            },
            {
                "id": 11, "title": "CHANGE IMPACT GUIDE",
                "search": "imports, exports, dependency ripple, core utilities, shared types, cross-module dependencies",
                "prompt": "Dependency ripple effects: If File X is changed, what breaks in File Y? Map the blast radius."
            },
            {
                "id": 12, "title": "SYSTEM RISKS",
                "search": "security, performance, scalability, bottleneck, vulnerabilities, edge cases",
                "prompt": "Analyze technical risks: Potential scalability issues, security gaps, or performance bottlenecks."
            }
        ]

    full_story = ""
    all_sources = set()

    # Draconian Grounding Rules
    RULES = """🚨 CRITICAL QUALITY RULES:
1. NO GENERIC OUTPUT: Do NOT explain common folder structures. Only THIS codebase.
2. NO HALLUCINATION: If info is not found, say "Not found in the current codebase".
3. NO RANDOM CODE: Do NOT dump code blocks. Only reference file/function names.
4. MARKDOWN-FIRST: Use headers (###), bold text, and lists.
5. NO ASCII ART: Do NOT attempt to draw boxes or diagrams.
6. CITE SOURCE: Mention real `file_names` and `function_names`.
"""

    for i, ch in enumerate(chapters):
        ch_num = i + 1
        
        # UI/File formatting bifurcation
        if markdown_style:
            header = f"## {ch['title']}"
            ch_id_str = f"SECTION {ch_num}"
        else:
            header = f"═══════════════════════════════════════════════\nPhase {ch_num}: {ch['title']}\n═══════════════════════════════════════════════"
            ch_id_str = f"Phase {ch_num}"
            print(f"  🧵 Weaving {ch['title']}...", flush=True)

        retriever = vectorstore_manager.as_retriever(k=20)
        
        prompt_tmpl = f"""{RULES}
You are a senior software engineer generating a REAL, GROUNDED "Codebase Story".
You are writing {ch_id_str} focusing on "{ch['title']}".

INSTRUCTIONS:
{ch['prompt']}

CODE CONTEXT:
{{context}}

PROJECT STRUCTURE:
{fs_context}

Chapter Output:
{header}"""

        prompt = PromptTemplate(template=prompt_tmpl, input_variables=["context", "question"])

        chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        
        res = chain.invoke({"query": ch['search']})
        content = res.get('result', '').strip()
        
        # Ensure we start with the header if the LLM forgot or repeated it
        if not content.startswith("#"):
            full_story += f"{header}\n{content}\n\n"
        else:
            full_story += f"{content}\n\n"
        
        for doc in res.get("source_documents", []):
            all_sources.add(doc.metadata.get('source', 'unknown'))

    return {
        "result": full_story.strip(),
        "sources": sorted(list(all_sources)),
    }
