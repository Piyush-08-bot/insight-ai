"""
QA Chain for INsight.

Creates a RetrievalQA chain using Ollama (free, default)
or OpenAI (paid, optional) for question answering over code.
"""

from typing import Optional
import os
from dotenv import load_dotenv

try:
    from langchain.chains import RetrievalQA
    from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
except ImportError:
    from langchain_classic.chains import RetrievalQA
    from langchain_classic.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from langchain_core.language_models import BaseChatModel

load_dotenv()

SYSTEM_SYSTEM_PROMPT = """You are INSIGHT — a real-time streaming code intelligence assistant.
Your job is to produce responses in a **progressive, phased manner** suitable for terminal streaming.

---------------------------------------------------------------------
🛡️ ANTI-HALLUCINATION MANDATE (STRICT)
---------------------------------------------------------------------
1. ONLY base your answer on the [Retrieved Context].
2. If the user asks for a file, function, or class that is NOT present in the provided context, you MUST state that it was not found.
3. NEVER invent code, logic, or project components (e.g., do not invent auth.py or ValidateInboundRequest if they are not in context).
4. If you cannot find the exact match, suggest the most similar existing entities from the context instead of hallucinating.

---------------------------------------------------------------------
⚡ OUTPUT STYLE (MANDATORY)
---------------------------------------------------------------------
You MUST divide your answer into clearly separated phases. 
Each phase should be short, meaningful, and independently useful.

---------------------------------------------------------------------
🧠 PHASE STRUCTURE
---------------------------------------------------------------------
Follow this EXACT structure:

[PHASE 0] STATUS
→ One-line progress message (like system thinking)
Example: "Analyzing CodeChunker function..."

[PHASE 1] OVERVIEW
→ 2–3 lines max: What the entity does high-level.
→ IF ENTITY NOT FOUND: State "Entity '<name>' not found in codebase context."

[PHASE 2] SIGNATURE
→ Show function/class definition. Mention parameters briefly.

[PHASE 3] LOGIC (STEP-BY-STEP)
→ Break implementation into numbered steps. Each step should be small/streamable.

[PHASE 4] KEY INSIGHTS
→ Important observations only. No repetition.

---------------------------------------------------------------------
🎯 STRICT RULES
---------------------------------------------------------------------
- If user asked for a FUNCTION: ONLY explain that function. Do NOT explain entire file or class.
- Do NOT output everything at once. Keep sections concise.
- No diagrams unless explicitly asked.
- Tone: Direct, architect-level, precise.
"""

HUMAN_PROMPT_TEMPLATE = """[Retrieved Context]
{context}

[Conversation State]
{chat_history}

[The User's Inquiry]
{question}

---
💡 INSTRUCTION: 
Produce the response following the [PHASE STRUCTURE] defined in the system prompt. 
Ensure Phase 0 and 1 are extremely fast to output.
Focus STRICTLY on the requested code entity.

Response:"""


def get_llm(provider: str = "ollama", model: Optional[str] = None, temperature: float = 0.0, streaming: bool = False) -> BaseChatModel:
    """
    Get an LLM instance.

    Args:
        provider: "ollama" (free, default) or "openai" (paid)
        model: Model name. Defaults: ollama→"qwen2.5-coder", openai→"gpt-4-turbo-preview"
        temperature: Creativity level (0-1)
        streaming: Whether to enable streaming output
    """
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model_name=model or "gpt-4o-mini",
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            streaming=streaming,
            max_retries=0  # FAIL FAST to avoid hangs
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model_name=model or "claude-3-5-sonnet-latest",
            temperature=temperature,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            streaming=streaming,
            max_retries=0
        )
    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model or "gemini-1.5-flash",
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            streaming=streaming,
            max_retries=0
        )
    elif provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model_name=model or "llama-3.1-8b-instant",  # Updated to latest stable instantly-available model
            temperature=temperature,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            streaming=streaming,
            max_retries=0
        )
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model or "qwen2.5-coder:latest",
            temperature=temperature,
            streaming=streaming
        )


def create_qa_chain(
    vectorstore_manager,
    llm_provider: str = "ollama",
    llm_model: Optional[str] = None,
    temperature: float = 0.2,
    k: int = 8,
    prompt_template: Optional[str] = None
) -> RetrievalQA:
    """
    Create a RetrievalQA chain.

    Args:
        vectorstore_manager: VectorStoreManager instance
        llm_provider: "ollama" (free) or "openai" (paid)
        llm_model: Model name override
        temperature: LLM temperature
        k: Number of documents to retrieve
        prompt_template: Custom prompt template (ignored if ChatPrompt is used)

    Returns:
        RetrievalQA chain instance
    """
    llm = get_llm(provider=llm_provider, model=llm_model, temperature=temperature)

    retriever = vectorstore_manager.as_retriever(k=k)

    # Use ChatPromptTemplate for better steering
    system_message_prompt = SystemMessagePromptTemplate.from_template(SYSTEM_SYSTEM_PROMPT)
    human_message_prompt = HumanMessagePromptTemplate.from_template(HUMAN_PROMPT_TEMPLATE)
    
    chat_prompt = ChatPromptTemplate.from_messages([
        system_message_prompt,
        human_message_prompt
    ])

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        verbose=False,
        chain_type_kwargs={"prompt": chat_prompt}
    )

    return qa_chain
