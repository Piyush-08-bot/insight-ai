"""
Vector Store Management for INsight.

Handles embedding generation (OpenAI, HuggingFace local),
vector database operations (Chroma), and retrieval.

KEY CHANGE: Collections are now scoped per user + project using
the identity system, ensuring complete data isolation.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import hashlib
import json
import logging

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from insight.vectorstore.graph_manager import GraphManager

logger = logging.getLogger(__name__)

load_dotenv()


class EmbeddingProvider:
    """Factory for creating embedding models."""

    @staticmethod
    def create(provider: str = "local", **kwargs) -> Embeddings:
        """
        Create an embedding model.

        Args:
            provider: "local" (free, default) or "openai" (paid)
        """
        if provider == "openai":
            return EmbeddingProvider.create_openai(**kwargs)
        elif provider == "google":
            return EmbeddingProvider.create_google(**kwargs)
        else:
            return EmbeddingProvider.create_local(**kwargs)

    @staticmethod
    def create_google(
        model: str = "models/text-embedding-004",
        api_key: Optional[str] = None
    ) -> Embeddings:
        """Create Google Generative AI embeddings (paid/free-tier)."""
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model=model,
            google_api_key=api_key or os.getenv("GOOGLE_API_KEY")
        )

    @staticmethod
    def create_openai(
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None
    ) -> Embeddings:
        """Create OpenAI embeddings (paid)."""
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=model,
            openai_api_key=api_key or os.getenv("OPENAI_API_KEY")
        )

    @staticmethod
    def create_local(
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu"
    ) -> Embeddings:
        """Create local HuggingFace embeddings (free, no API key needed)."""
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
        # Brute-force silence for model loading (tqdm, HF logs, etc.)
        with open(os.devnull, 'w') as fnull:
            with redirect_stdout(fnull), redirect_stderr(fnull):
                return HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs={'device': device},
                    encode_kwargs={'normalize_embeddings': True}
                )


class VectorStoreManager:
    """
    Manages Chroma vector store operations.

    Features:
    - User-scoped collections (each user+project gets isolated data)
    - Batch indexing
    - Persistence and loading
    - Similarity search, MMR search
    - Retriever creation for chains
    """

    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: Optional[str] = None,
        embedding_provider: str = "local",
        embedding_model: Optional[str] = None,
        user_id: Optional[str] = None,
        project_path: Optional[str] = None,
    ):
        self.persist_directory = Path(persist_directory)
        self.user_id = user_id
        self.project_path = project_path
        
        # ─── User-Scoped Collection Name ────────────────────────
        if collection_name:
            # Explicit collection name provided (e.g., from test or migration)
            self.collection_name = collection_name
        elif user_id and project_path:
            # Auto-generate scoped name from user + project
            from insight.identity import get_scoped_collection_name
            self.collection_name = get_scoped_collection_name(project_path, user_id)
        else:
            # Fallback for backward compatibility (single-user / dev mode)
            self.collection_name = "codebase_vectors"
        
        # Build embedding kwargs
        embed_kwargs = {}
        if embedding_model:
            if embedding_provider == "openai":
                embed_kwargs["model"] = embedding_model
            else:
                embed_kwargs["model_name"] = embedding_model
                
        self.embeddings = EmbeddingProvider.create(embedding_provider, **embed_kwargs)
        self.vectorstore = self._load_or_create()
        
        # Load graph
        graph_path = self.persist_directory / "code_graph.json"
        self.graph = GraphManager(persist_path=str(graph_path) if graph_path.exists() else None)

    def _load_or_create(self) -> Chroma:
        """Load existing vector store (local or remote)."""
        chroma_host = os.getenv("CHROMA_HOST")
        chroma_port = os.getenv("CHROMA_PORT", "8000")

        if chroma_host:
            # Remote Mode using HttpClient
            import chromadb
            try:
                # chromadb >= 0.6.x: Use Settings for configuration
                from chromadb.config import Settings
                settings = Settings(
                    chroma_api_impl="chromadb.api.fastapi.FastAPI",
                    anonymized_telemetry=False,
                )
                client = chromadb.HttpClient(
                    host=chroma_host,
                    port=int(chroma_port),
                    settings=settings,
                )
            except (TypeError, ImportError, AttributeError):
                # Fallback for older/newer chromadb versions
                client = chromadb.HttpClient(
                    host=chroma_host,
                    port=int(chroma_port),
                )
            
            logger.info(f"Connected to remote ChromaDB at {chroma_host}:{chroma_port}, "
                        f"collection: {self.collection_name}")
            
            return Chroma(
                client=client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
        else:
            # Local Persistent Mode
            try:
                if self.persist_directory.exists():
                    return Chroma(
                        persist_directory=str(self.persist_directory),
                        embedding_function=self.embeddings,
                        collection_name=self.collection_name
                    )
            except Exception as e:
                logger.warning(f"Could not load existing store: {e}")

            return Chroma(
                embedding_function=self.embeddings,
                persist_directory=str(self.persist_directory),
                collection_name=self.collection_name
            )

    def index_documents(
        self,
        documents: List[Document],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> None:
        """Index documents in batches."""
        if not documents:
            logger.warning("No documents to index!")
            return

        total = len(documents)
        indexed = 0

        for i in range(0, total, batch_size):
            batch = [documents[j] for j in range(i, min(i + batch_size, len(documents)))]
            
            # Filter out chunks already in cache
            new_chunks, cache = self._filter_cached_chunks(batch)
            
            if new_chunks:
                self.vectorstore.add_documents(new_chunks)
                self._update_cache(new_chunks, cache)
                indexed += len(new_chunks)
        
        logger.info(f"Indexing complete. Processed {total} chunks, added {indexed} new vectors "
                     f"to collection '{self.collection_name}'.")
            
    def _get_chunk_hash(self, doc: Document) -> str:
        """Generate a stable hash for a document chunk."""
        return hashlib.md5(f"{doc.page_content}{doc.metadata.get('source', '')}".encode()).hexdigest()

    def _filter_cached_chunks(self, chunks: List[Document]) -> Tuple[List[Document], Dict[str, bool]]:
        """Filter out chunks that are already indexed and present in the local cache."""
        cache_path = self.persist_directory / ".insight_embed_cache.json"
        cache = {}
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cache = json.load(f)
            except Exception:
                pass

        new_chunks = [c for c in chunks if self._get_chunk_hash(c) not in cache]
        return new_chunks, cache

    def _update_cache(self, chunks: List[Document], cache: Dict[str, bool]) -> None:
        """Update the local embedding cache with new chunk hashes."""
        for c in chunks:
            cache[self._get_chunk_hash(c)] = True
            
        cache_path = self.persist_directory / ".insight_embed_cache.json"
        try:
            with open(cache_path, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            logger.error(f"Failed to save embedding cache: {e}")

    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Basic similarity search."""
        return self.vectorstore.similarity_search(
            query=query, k=k, filter=filter_dict
        )

    def search_with_scores(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """Similarity search with relevance scores."""
        return self.vectorstore.similarity_search_with_score(
            query=query, k=k, filter=filter_dict
        )

    def mmr_search(
        self,
        query: str,
        k: int = 5,
        fetch_k: int = 20,
        lambda_mult: float = 0.5
    ) -> List[Document]:
        """Maximum Marginal Relevance search for diverse results."""
        return self.vectorstore.max_marginal_relevance_search(
            query=query, k=k, fetch_k=fetch_k, lambda_mult=lambda_mult
        )

    def search_with_graph(
        self,
        query: str,
        k: int = 5,
        graph_depth: int = 1
    ) -> List[Document]:
        """
        Extended search that follows code graph relationships.
        1. Find k similar chunks.
        2. Find files related to those chunks via graph.
        3. Retrieve high-level info from those related files.
        """
        initial_docs = self.search(query, k=k)
        if not self.graph or not self.graph.graph.nodes:
            return initial_docs
            
        # Follow graph edges from initial results
        related_files = set()
        for doc in initial_docs:
            source = doc.metadata.get('source')
            if source:
                related_files.update(self.graph.get_related_files(source, depth=graph_depth))
                
        # Supplement with 'Context Clips' from related files
        extra_docs = []
        rel_files = sorted(list(related_files))
        for rel_file in rel_files[:3]:  # Limit to avoid context bloat
            rel_docs = self.search(f"Overview of {rel_file}", k=1, filter_dict={"source": str(rel_file)})
            if rel_docs:
                extra_docs.append(rel_docs[0])
                
        return initial_docs + extra_docs

    def as_retriever(self, search_type: str = "similarity", k: int = 5):
        """Get a retriever for use in LangChain chains."""
        return self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k}
        )

    def get_high_level_context(self, limit: int = 5) -> str:
        """
        Retrieve content from high-level project files (README, package.json, etc.)
        to provide a 'Project Dossier' context.
        """
        priority_files = [
            "README.md", "package.json", "setup.py", "pyproject.toml",
            "main.py", "app.py", "index.js", "server.js", "__init__.py"
        ]
        
        context_parts = []
        for filename in priority_files:
            try:
                docs = self.vectorstore.similarity_search(
                    query=f"File content of {filename}",
                    k=1,
                    filter={"source": {"$like": f"%{filename}"}}
                )
                if docs:
                    content = docs[0].page_content[:1000]
                    context_parts.append(f"--- High-Level Info: {filename} ---\n{content}")
            except Exception:
                continue
                
        return "\n\n".join(context_parts)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        try:
            collection = self.vectorstore._collection
            return {
                'collection_name': self.collection_name,
                'total_vectors': collection.count(),
                'persist_directory': str(self.persist_directory),
                'user_id': self.user_id or 'unscoped',
            }
        except Exception as e:
            return {'error': str(e)}

    def clear(self):
        """Clear all vectors from the store."""
        try:
            self.vectorstore.delete_collection()
            self.vectorstore = self._load_or_create()
            logger.info(f"Vector store collection '{self.collection_name}' cleared")
        except Exception as e:
            logger.error(f"Error clearing store: {e}")

    def get_all_documents(self) -> List[Document]:
        """Retrieve all documents from the collection."""
        try:
            results = self.vectorstore.get()
            docs = []
            
            ids = results.get('ids', [])
            contents = results.get('documents', [])
            metadatas = results.get('metadatas', [])
            
            if ids and contents and metadatas:
                for i in range(len(ids)):
                    docs.append(Document(
                        page_content=str(contents[i]),
                        metadata=dict(metadatas[i]) if metadatas[i] else {}
                    ))
            return docs
        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            return []

    @staticmethod
    def list_collections(persist_directory: str = "./chroma_db", user_id: Optional[str] = None) -> List[str]:
        """
        List all ChromaDB collections, optionally filtered by user_id prefix.
        Useful for debugging and the 'insight whoami' command.
        """
        try:
            chroma_host = os.getenv("CHROMA_HOST")
            chroma_port = os.getenv("CHROMA_PORT", "8000")

            import chromadb
            if chroma_host:
                client = chromadb.HttpClient(host=chroma_host, port=int(chroma_port))
            else:
                client = chromadb.PersistentClient(path=str(persist_directory))

            collections = client.list_collections()
            names = [c.name for c in collections]

            if user_id:
                names = [n for n in names if n.startswith(user_id[:20])]

            return names
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []


# ─── Convenience functions ──────────────────────────────────────

def create_vector_store(
    documents: List[Document],
    persist_directory: str = "./chroma_db",
    embedding_provider: str = "local",
    embedding_model: Optional[str] = None,
    chunking_strategy: str = "ast",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    user_id: Optional[str] = None,
    project_path: Optional[str] = None,
) -> VectorStoreManager:
    """
    Create a vector store from documents (convenience function).

    Args:
        documents: LangChain Documents to index
        persist_directory: Where to persist the store
        embedding_provider: "local" (free) or "openai" (paid)
        chunk_size: Chunk size for splitting
        chunk_overlap: Overlap between chunks
        user_id: User ID for scoped collection (from identity system)
        project_path: Project path for collection scoping

    Returns:
        VectorStoreManager instance
    """
    from insight.chunking import CodeChunker, ChunkingConfig

    # Chunk documents
    if chunking_strategy == "ast":
        from insight.chunking import ASTChunker
        chunker = ASTChunker()
        chunks = chunker.chunk_document_list(documents)
    else:
        chunker = CodeChunker(ChunkingConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        ))
        chunks = chunker.chunk_documents(documents)
    
    print(f"✂️  Created {len(chunks)} chunks from {len(documents)} documents using {chunking_strategy} strategy")

    # Create and index
    manager = VectorStoreManager(
        persist_directory=persist_directory,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        user_id=user_id,
        project_path=project_path,
    )
    manager.index_documents(chunks)

    return manager


def load_vector_store(
    persist_directory: str = "./chroma_db",
    embedding_provider: str = "local",
    embedding_model: Optional[str] = None,
    user_id: Optional[str] = None,
    project_path: Optional[str] = None,
    collection_name: Optional[str] = None,
) -> Optional[VectorStoreManager]:
    """Load an existing vector store."""
    chroma_host = os.getenv("CHROMA_HOST")
    
    # For remote ChromaDB, don't check local directory
    if not chroma_host and not Path(persist_directory).exists():
        logger.warning(f"Vector store not found at {persist_directory}")
        return None

    return VectorStoreManager(
        persist_directory=persist_directory,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        user_id=user_id,
        project_path=project_path,
        collection_name=collection_name,
    )
