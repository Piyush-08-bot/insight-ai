"""
LangGraph Agent Logic for INSIGHT V2.

Implements a multi-step 'Researcher' agent that can perform 
iterative retrieval, reasoning, and self-correction.
"""

from typing import Annotated, List, Dict, Any, TypedDict, Union
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.documents import Document
import os
import re
import json
from insight.utils.fs_scanner import FilesystemScanner

class AgentState(TypedDict):
    """The state of the agentic research loop."""
    question: str
    chat_history: List[BaseMessage]
    context: List[Document]
    answer: str
    steps: int
    should_continue: bool

class InsightAgent:
    """
    State-based agent that resolves complex codebase questions 
    by following function calls and re-querying when necessary.
    """

    def __init__(self, vectorstore_manager, llm):
        self.vectorstore = vectorstore_manager
        self.llm = llm
        self.max_steps = 3
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentState)
        
        # Define nodes
        builder.add_node("research", self.research_node)
        builder.add_node("analyze", self.analyze_node)
        builder.add_node("synthesize", self.synthesize_node)
        
        # Define edges
        builder.set_entry_point("research")
        builder.add_edge("research", "analyze")
        
        builder.add_conditional_edges(
            "analyze",
            self.decide_to_continue,
            {
                "continue": "research",
                "finish": "synthesize"
            }
        )
        
        builder.add_edge("synthesize", END)
        
        return builder.compile()

    def _gather_deep_context(self, query: str, k: int = 5) -> List[Document]:
        """Multi-stage context gathering."""
        # 1. Semantic Search
        docs = self.vectorstore.search(query, k=k)
        
        # 2. Filesystem Awareness
        # Matches files (with extensions) AND folders (ending in / or no extension but existing)
        # Regex: find absolute or relative paths
        paths = re.findall(r'(\.?[/a-zA-Z0-9_\-\.]+)', query)
        for p in paths:
            if not p or p in ('.', '..', '/'):
                continue
            
            # Check relative to CWD
            full_p = os.path.abspath(os.path.join(os.getcwd(), p))
            if os.path.exists(full_p):
                if os.path.isfile(full_p):
                    try:
                        with open(full_p, 'r') as f:
                            raw_content = f.read()
                            full_content = str(raw_content)
                            page_content = "".join([str(full_content)[j] for j in range(min(5000, len(str(full_content))))])
                            docs.append(Document(
                                page_content=f"--- FILE CONTENTS: {p} ---\n{page_content}", 
                                metadata={"source": str(p), "type": "filesystem"}
                            ))
                    except:
                        pass
                elif os.path.isdir(full_p):
                    # For directories, provide a scan
                    fs_info = FilesystemScanner.scan_directory(full_p)
                    docs.append(Document(
                        page_content=f"--- FOLDER: {p} ---\n{fs_info}",
                        metadata={"source": p, "type": "filesystem_scan"}
                    ))
        
        # 3. Graph Walk
        graph_docs = self.vectorstore.search_with_graph(query, k=k)
        
        # Combine and deduplicate
        all_docs = docs + graph_docs
        seen_contents = set()
        unique_docs = []
        for d in all_docs:
            if d.page_content not in seen_contents:
                unique_docs.append(d)
                seen_contents.add(d.page_content)
        
        return unique_docs

    def research_node(self, state: AgentState):
        """Node for performing graph-aware retrieval."""
        # On first step, do traditional move
        if not state["context"]:
            new_docs = self._gather_deep_context(state["question"])
        else:
            # If we're expanding, use the 'next_query' identified in analyze_node
            next_query = state.get("next_query", state["question"])
            new_docs = self.vectorstore.search(next_query, k=3)
        
        existing_context: list = list(state.get("context", []))
        current_steps: int = int(str(state.get("steps", 0)))
        return {
            "context": existing_context + list(new_docs),
            "steps": current_steps + 1
        }

    def analyze_node(self, state: AgentState):
        """Node for critiquing context and identifying missing symbols."""
        context_summary = ""
        for i, d in enumerate(state["context"]):
            src = d.metadata.get('source', 'unknown')
            snippet = "".join([d.page_content[j] for j in range(min(200, len(d.page_content)))])
            context_summary += f"[{i}] {src}: {snippet}...\n"

        prompt = f"""You are the internal 'Critic' for INSIGHT. 
Review the progress on answering this question: "{state['question']}"

CURRENT CONTEXT:
{context_summary}

GOAL:
Provide a precise, technical deep-dive. 

REASONING RULES:
1. If the user asks for a specific FUNCTION (e.g. 'CodeChunker function') and you have the CLASS context but not the individual function's implementation, you MUST ask for the function definition.
2. If you see code that calls a method not in context, your next query MUST be that method's definition.
3. If you have enough info, set status to 'COMPLETE'.

Output ONLY a JSON block:
{{
  "status": "CONTINUE" | "COMPLETE",
  "next_query": "specific search query",
  "reasoning": "Quick rationale"
}}
"""

        try:
            res = self.llm.invoke(prompt)
            # Find JSON in response
            match = re.search(r'\{.*\}', res.content, re.DOTALL)
            if not match:
                return {"should_continue": False}
            
            data = json.loads(match.group(0))
            should_continue = data.get("status") == "CONTINUE" and state["steps"] < self.max_steps
            
            return {
                "should_continue": should_continue,
                "next_query": data.get("next_query")
            }
        except Exception:
            return {"should_continue": False}

    def synthesize_node(self, state: AgentState):
        """Final output generation node."""
        return {"answer": "Synthesis complete. Context enriched."}

    def decide_to_continue(self, state: AgentState):
        if state["should_continue"]:
            return "continue"
        return "finish"

    def run(self, question: str, chat_history: List = None):
        """Run the agentic loop."""
        initial_state = {
            "question": question,
            "chat_history": chat_history or [],
            "context": [],
            "answer": "",
            "steps": 0,
            "should_continue": True
        }
        return self.graph.invoke(initial_state)
