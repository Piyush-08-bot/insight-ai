"""FastAPI application for INsight AI Service."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
from pathlib import Path

# Add project root to sys.path for robust local imports
root_path = str(Path(__file__).resolve().parent.parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="INsight AI Service",
    description="AI-powered code understanding service using LangChain and RAG",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Models ────────────────────────────────────

class AnalyzeRequest(BaseModel):
    project_path: str
    file_types: Optional[List[str]] = [".py", ".js", ".ts", ".jsx", ".tsx"]
    embedding_provider: Optional[str] = "local"

class AnalyzeResponse(BaseModel):
    project_id: str
    status: str
    documents_count: int
    chunks_count: int
    message: str

class QueryRequest(BaseModel):
    project_id: str
    question: str
    llm_provider: Optional[str] = "ollama"
    llm_model: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]

class ChatRequest(BaseModel):
    project_id: str
    question: str
    session_id: Optional[str] = None
    llm_provider: Optional[str] = "ollama"
    llm_model: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[str]

class AnalysisRequest(BaseModel):
    project_id: str
    analysis_type: str  # overview, learning, architecture, dependencies
    llm_provider: Optional[str] = "ollama"
    llm_model: Optional[str] = None

class AnalysisResponse(BaseModel):
    analysis_type: str
    result: str
    sources: List[str]


# ─── State ──────────────────────────────────────────────────────

# In-memory project store (maps project_id → VectorStoreManager)
_projects = {}


def _get_vectorstore(project_id: str):
    """Get or load a project's vector store."""
    if project_id in _projects:
        return _projects[project_id]

    from insight.vectorstore import load_vector_store
    persist_dir = f"./data/{project_id}"
    vs = load_vector_store(persist_dir)
    if vs:
        _projects[project_id] = vs
    return vs


# ─── Health ─────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "INsight AI Service",
        "status": "running",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "ollama": _check_ollama(),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
    }


def _check_ollama() -> str:
    """Check if Ollama is running."""
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=2)
        return "running" if r.status_code == 200 else "not responding"
    except Exception:
        return "not running"


# ─── Analyze ────────────────────────────────────────────────────

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_project(request: AnalyzeRequest):
    """Analyze a codebase: ingest → chunk → embed → index."""
    try:
        import uuid
        from insight.ingestion import load_codebase
        from insight.vectorstore import create_vector_store

        if not os.path.exists(request.project_path):
            raise HTTPException(status_code=400, detail="Project path does not exist")

        # Load documents
        documents = load_codebase(request.project_path, request.file_types)
        if not documents:
            raise HTTPException(status_code=400, detail="No documents found")

        # Generate project ID
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        persist_dir = f"./data/{project_id}"

        # Create vector store
        vs_manager = create_vector_store(
            documents,
            persist_directory=persist_dir,
            embedding_provider=request.embedding_provider or "local"
        )

        # Cache
        _projects[project_id] = vs_manager

        stats = vs_manager.get_collection_stats()

        return AnalyzeResponse(
            project_id=project_id,
            status="completed",
            documents_count=len(documents),
            chunks_count=stats.get('total_vectors', 0),
            message=f"Successfully analyzed {len(documents)} files"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Query ──────────────────────────────────────────────────────

@app.post("/api/query", response_model=QueryResponse)
async def query_codebase(request: QueryRequest):
    """Single question about the codebase (no memory)."""
    try:
        from insight.chains import create_qa_chain

        vs = _get_vectorstore(request.project_id)
        if not vs:
            raise HTTPException(status_code=404, detail=f"Project not found: {request.project_id}")

        qa_chain = create_qa_chain(
            vs,
            llm_provider=request.llm_provider or "ollama",
            llm_model=request.llm_model,
        )

        result = qa_chain({"query": request.question})

        source_set = set(doc.metadata.get('source', 'unknown') for doc in result.get('source_documents', []))
        sources = [str(s) for i, s in enumerate(sorted(list(source_set))) if i < 5]

        return QueryResponse(answer=result['result'], sources=sources)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Chat (with memory) ────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_codebase(request: ChatRequest):
    """Conversational chat with memory — supports follow-up questions."""
    try:
        from insight.chains import chat as insight_chat

        vs = _get_vectorstore(request.project_id)
        if not vs:
            raise HTTPException(status_code=404, detail=f"Project not found: {request.project_id}")

        result = insight_chat(
            vs,
            question=request.question,
            session_id=request.session_id,
            llm_provider=request.llm_provider or "ollama",
            llm_model=request.llm_model,
        )

        return ChatResponse(
            session_id=str(result["session_id"]),
            answer=str(result["answer"]),
            sources=list(result["sources"]),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/{session_id}")
async def clear_chat_session(session_id: str):
    """Clear a chat session."""
    from insight.chains import clear_session
    if clear_session(session_id):
        return {"message": f"Session {session_id} cleared"}
    raise HTTPException(status_code=404, detail="Session not found")


# ─── Specialized Analysis ──────────────────────────────────────

@app.post("/api/analysis", response_model=AnalysisResponse)
async def run_analysis_endpoint(request: AnalysisRequest):
    """Run a specialized analysis (overview, learning, architecture, dependencies)."""
    try:
        from insight.chains import run_analysis

        vs = _get_vectorstore(request.project_id)
        if not vs:
            raise HTTPException(status_code=404, detail=f"Project not found: {request.project_id}")

        result = run_analysis(
            vs,
            analysis_type=request.analysis_type,
            llm_provider=request.llm_provider or "ollama",
            llm_model=request.llm_model,
        )

        return AnalysisResponse(
            analysis_type=result["analysis_type"],
            result=result["result"],
            sources=result["sources"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Project Management ────────────────────────────────────────

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project's vector store."""
    try:
        import shutil
        persist_dir = f"./data/{project_id}"

        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)
            _projects.pop(project_id, None)
            return {"message": f"Project {project_id} deleted"}

        raise HTTPException(status_code=404, detail="Project not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects")
async def list_projects():
    """List all analyzed projects."""
    import os
    data_dir = "./data"
    if not os.path.exists(data_dir):
        return {"projects": []}

    projects = [
        d for d in os.listdir(data_dir)
        if os.path.isdir(os.path.join(data_dir, d)) and d.startswith("proj_")
    ]
    return {"projects": projects}


# ─── Run ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
