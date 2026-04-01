"""
Conversational Chain for INsight.

Supports multi-turn conversations about a codebase with
conversation memory that maintains context across questions.

KEY FIXES:
- Memory overwrite bug removed (was creating new memory every call)
- Conversations now persist to Supabase when available
- Session history survives CLI restarts
"""

from typing import Optional, List, Dict, Any, Tuple, Generator
import uuid
import os
import re
import json
import hashlib
import logging

try:
    from langchain.chains import ConversationalRetrievalChain
    from langchain.memory import ConversationBufferWindowMemory
except ImportError:
    from langchain_classic.chains import ConversationalRetrievalChain
    from langchain_classic.memory import ConversationBufferWindowMemory

from langchain_core.documents import Document
from insight.chains.qa_chain import create_qa_chain, get_llm
from insight.chains.agent_logic import InsightAgent
from insight.utils.fs_scanner import FilesystemScanner

logger = logging.getLogger(__name__)

# In-memory session storage
_sessions: Dict[str, ConversationalRetrievalChain] = {}
_memories: Dict[str, ConversationBufferWindowMemory] = {}


def _get_user_machine_id() -> Optional[str]:
    """Get the current user's machine_id for Supabase persistence."""
    try:
        from insight.identity import _generate_machine_fingerprint
        return _generate_machine_fingerprint()
    except Exception:
        return None


def _persist_conversation(session_id: str, question: str, answer: str, sources: List[str]):
    """Save a conversation exchange to Supabase (best-effort, non-blocking)."""
    try:
        machine_id = _get_user_machine_id()
        if not machine_id:
            return

        from insight.database.manager import db_manager
        db_manager.save_conversation(
            machine_id=machine_id,
            session_id=session_id,
            question=question,
            answer=answer,
            sources=sources,
        )
    except Exception as e:
        logger.debug(f"Conversation persistence failed (non-critical): {e}")


def create_conversational_chain(
    vectorstore_manager,
    session_id: Optional[str] = None,
    llm_provider: str = "ollama",
    llm_model: Optional[str] = None,
    temperature: float = 0.0,
    k: int = 12,
    memory_window: int = 10,
    streaming: bool = False
) -> tuple:
    """Create or retrieve a conversational chain with memory."""
    # Create new session if none provided
    if not session_id:
        hex_id = uuid.uuid4().hex
        short_id = "".join([hex_id[i] for i in range(min(12, len(hex_id)))])
        session_id = f"session_{short_id}"

    # ─── MEMORY: Reuse existing or create new ───────────────────
    # BUG FIX: Previously, a new memory was always created on line 66-71,
    # completely discarding the cached memory from _memories[session_id].
    # Now we properly reuse the existing memory for multi-turn conversations.
    if session_id in _memories:
        memory = _memories[session_id]
    else:
        memory = ConversationBufferWindowMemory(
            k=memory_window,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        _memories[session_id] = memory

    llm = get_llm(provider=llm_provider, model=llm_model, temperature=temperature, streaming=streaming)
    retriever = vectorstore_manager.as_retriever(k=k)

    # NOTE: We do NOT create a new memory here. We reuse the one from above.
    # This is the critical bug fix — the old code had:
    #   memory = ConversationBufferWindowMemory(...)  # <-- overwrote cached memory
    # which broke multi-turn conversations.

    from insight.chains.qa_chain import SYSTEM_SYSTEM_PROMPT, ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, HUMAN_PROMPT_TEMPLATE
    
    # Custom prompts for the chain
    system_message_prompt = SystemMessagePromptTemplate.from_template(SYSTEM_SYSTEM_PROMPT)
    human_message_prompt = HumanMessagePromptTemplate.from_template(HUMAN_PROMPT_TEMPLATE)
    chat_prompt = ChatPromptTemplate.from_messages([
        system_message_prompt,
        human_message_prompt
    ])

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        verbose=False,
        combine_docs_chain_kwargs={"prompt": chat_prompt}
    )

    _sessions[session_id] = chain
    # Memory is already in _memories[session_id], no need to re-assign

    return session_id, chain


def _get_chat_context(vectorstore_manager, question: str, chat_history: List, llm) -> Tuple[List[Document], str]:
    """Shared logic for preparing enriched context for chat."""
    from insight.chains.agent_logic import InsightAgent
    from insight.utils.fs_scanner import FilesystemScanner
    
    # 1. FIND TRUE ROOT
    master_root = os.getcwd()
    temp_path = master_root
    for i in range(5): 
        if os.path.exists(os.path.join(temp_path, ".git")):
            master_root = temp_path
            break
        parent = os.path.dirname(temp_path)
        if parent == temp_path: break
        temp_path = parent

    enriched_context = []
    
    # 2. AGENTIC RESEARCH (Only for specific entity/code queries to avoid hangs)
    specific_keywords = ["function", "class", "file", "method", "code", "logic", "how to", "where is", "implementation", "refactor"]
    is_specific = any(k in question.lower() for k in specific_keywords) or re.search(r'[A-Za-z0-9_\-\.]+\.[A-Za-z]+', question)
    
    global_intents = ["whole project", "project flow", "system flow", "architecture", "structure", "overview", "full project", "everything"]
    is_global = any(kw in question.lower() for kw in global_intents)
    
    if is_specific and not is_global:
        agent = InsightAgent(vectorstore_manager, llm)
        agent_result = agent.run(question, chat_history)
        enriched_context = agent_result["context"]
    else:
        # Standard fast RAG
        enriched_context = vectorstore_manager.search(question, k=6)

    # 3. PATH DISCOVERY
    local_path_match = re.search(r'(?:explain|describe|tell me about|what is|about|in|show)\s+(?:the\s+|me\s+the\s+)?([a-zA-Z0-9][a-zA-Z0-9_\-\.]*(?:/[a-zA-Z0-9_\-\.]+)*)(?:\s+folder|\s+directory|\s+module)?', question.lower())
    if local_path_match:
        try:
            target_name = str(local_path_match.group(1)).strip('/')
            paths_to_check = [os.path.join(master_root, target_name), os.path.join(os.getcwd(), target_name)]
            for p in paths_to_check:
                if os.path.exists(p) and os.path.isdir(p):
                    enriched_context.append(Document(page_content=FilesystemScanner.scan_directory(p), metadata={"source": f"Local Discovery: {target_name}"}))
                    break
        except Exception: pass

    # 4. GLOBAL PROJECT DISCOVERY
    if is_global or (not enriched_context and len(question) > 10):
        project_map = FilesystemScanner.scan_directory(master_root, max_depth=3)
        enriched_context.append(Document(page_content=f"--- GLOBAL PROJECT ARCHITECTURE ---\n{project_map}", metadata={"source": "Project Root Scan"}))

    # 5. DIAGRAM MANDATE
    if any(k in question.lower() for k in ["flow", "diagram", "architecture", "visualize"]):
        question += "\n\n[HARD RULE]: Wrap your diagram in a fenced code block: ```text ... ```"

    return enriched_context, question


def chat(
    vectorstore_manager,
    question: str,
    session_id: Optional[str] = None,
    llm_provider: str = "ollama",
    llm_model: Optional[str] = None,
) -> Dict:
    session_id, chain = create_conversational_chain(vectorstore_manager, session_id=session_id, llm_provider=llm_provider, llm_model=llm_model)
    chat_history = _memories[session_id].load_memory_variables({}).get("chat_history", []) if session_id in _memories else []
    
    enriched_context, final_question = _get_chat_context(vectorstore_manager, question, chat_history, chain.combine_docs_chain.llm_chain.llm)
    
    result = chain.combine_docs_chain.invoke({"input_documents": enriched_context, "question": final_question, "chat_history": chat_history})
    answer = result.get("output_text", "Could not generate answer.")

    sources = sorted(list(set([doc.metadata.get('source', 'unknown') for doc in enriched_context])))[:5]

    if session_id in _memories:
         _memories[session_id].save_context({"question": question}, {"answer": answer})

    # Persist to Supabase (non-blocking)
    _persist_conversation(session_id, question, answer, sources)

    return {
        "session_id": str(session_id),
        "answer": str(answer),
        "sources": sources,
    }


def stream_chat(
    vectorstore_manager,
    question: str,
    session_id: Optional[str] = None,
    llm_provider: str = "ollama",
    llm_model: Optional[str] = None,
):
    yield {"status": "Starting engine..."}
    try:
        session_id, chain = create_conversational_chain(vectorstore_manager, session_id=session_id, llm_provider=llm_provider, llm_model=llm_model, streaming=True)
    except Exception as e:
        yield {"error": f"Initialization failed: {str(e)}", "final": True}
        return

    yield {"status": "Retrieving context..."}
    chat_history = _memories[session_id].load_memory_variables({}).get("chat_history", []) if session_id in _memories else []
    
    yield {"status": "Researching codebase..."}
    enriched_context, final_question = _get_chat_context(vectorstore_manager, question, chat_history, chain.combine_docs_chain.llm_chain.llm)

    yield {"status": "Synthesizing answer..."}
    sources = list(set([doc.metadata.get("source", "unknown") for doc in enriched_context]))
    yield {"session_id": str(session_id), "sources": [s for i, s in enumerate(sources) if i < 5]}

    # Truncate context for safety (Groq has tighter TPM limits than OpenAI/Claude)
    max_context_chars = 12000 if llm_provider == "groq" else 20000
    context_str = "\n\n".join([doc.page_content for doc in enriched_context])
    if len(context_str) > max_context_chars:
        context_str = context_str[:max_context_chars] + "\n\n[TRUNCATED FOR CONTEXT LIMITS]"

    from insight.chains.qa_chain import SYSTEM_SYSTEM_PROMPT, HUMAN_PROMPT_TEMPLATE, ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    prompt_messages = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SYSTEM_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(HUMAN_PROMPT_TEMPLATE)
    ]).format_messages(context=context_str, question=final_question, chat_history=chat_history)
    
    full_answer = ""
    try:
        for chunk in chain.combine_docs_chain.llm_chain.llm.stream(prompt_messages):
            token = ""
            if hasattr(chunk, 'content'):
                token = str(chunk.content)
            else:
                token = str(chunk)
                
            if token:
                full_answer += token
                yield {"token": token}

        if session_id in _memories:
             _memories[session_id].save_context({"question": question}, {"answer": full_answer})

        # Persist to Supabase (non-blocking)
        _persist_conversation(session_id, question, full_answer, sources[:5])

        yield {"final": True, "answer": full_answer}
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg: err_msg = "Rate Limit Reached. Please retry in a few minutes."
        yield {"error": err_msg, "final": True}
        return


def clear_session(session_id: str) -> bool:
    """Clear a conversation session."""
    if session_id in _sessions:
        _sessions.pop(session_id, None)
        _memories.pop(session_id, None)
        return True
    return False


def list_sessions() -> list:
    """List all active session IDs."""
    return list(_sessions.keys())
