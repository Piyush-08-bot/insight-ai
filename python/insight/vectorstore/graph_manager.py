"""
Code Graph Management for INSIGHT V2.

Uses NetworkX to build a directed dependency graph of the codebase,
allowing for relationship-aware retrieval (following call chains).
"""

import networkx as nx
from typing import List, Dict, Any, Set, Optional
from pathlib import Path
import json

class GraphManager:
    """
    Manages a directed graph of code relationships.
    Nodes: Files/Functions
    Edges: CALLS, IMPORTS, DEFINES
    """

    def __init__(self, persist_path: Optional[str] = None):
        self.graph = nx.DiGraph()
        self.persist_path = Path(persist_path) if persist_path else None
        if self.persist_path and self.persist_path.exists():
            self.load()

    def add_file_node(self, file_path: str, metadata: Dict[str, Any]):
        """Add a file to the graph and its internal components."""
        self.graph.add_node(file_path, type='file', language=metadata.get('language'))
        
        # Add functions as sub-nodes
        functions = metadata.get('functions', [])
        if isinstance(functions, str): # Handle serialized string from Chroma
            functions = [f.strip() for f in functions.split(',') if f.strip() != 'none']
            
        for func_data in functions:
            func_name = func_data['name'] if isinstance(func_data, dict) else func_data
            func_node = f"{file_path}::{func_name}"
            self.graph.add_node(func_node, type='function', name=func_name, file=file_path)
            self.graph.add_edge(file_path, func_node, rel='defines')

        # Add calls as edges
        calls = metadata.get('calls', [])
        if isinstance(calls, str):
            calls = [c.strip() for c in calls.split(',') if c.strip() != 'none']
            
        for call in calls:
            # We don't know WHERE the call goes yet, just that this file calls it
            # We'll resolve these edges later
            self.graph.add_node(call, type='unresolved_call')
            self.graph.add_edge(file_path, call, rel='calls')

    def resolve_edges(self):
        """
        Attempt to resolve 'unresolved_call' nodes by matching them 
        to 'function' nodes in other files.
        """
        unresolved = [n for n, d in self.graph.nodes(data=True) if d.get('type') == 'unresolved_call']
        functions = {d.get('name'): n for n, d in self.graph.nodes(data=True) if d.get('type') == 'function'}
        
        for call_name in unresolved:
            if call_name in functions:
                target_node = functions[call_name]
                # Redirect edges from the unresolved name to the actual function node
                for source in list(self.graph.predecessors(call_name)):
                    self.graph.add_edge(source, target_node, rel='calls')
                self.graph.remove_node(call_name)

    def get_related_files(self, file_path: str, depth: int = 1) -> Set[str]:
        """Get files related to the given file via call chain."""
        if file_path not in self.graph:
            return set()
            
        related = set()
        # Use ego_graph to find neighbors within depth
        ego = nx.ego_graph(self.graph, file_path, radius=depth, undirected=True)
        for node, data in ego.nodes(data=True):
            if data.get('type') == 'file':
                related.add(node)
            elif data.get('type') == 'function':
                related.add(data.get('file'))
                
        if file_path in related:
            related.remove(file_path)
        return related

    def save(self):
        """Persist graph to JSON."""
        if not self.persist_path:
            return
        data = nx.node_link_data(self.graph)
        with open(self.persist_path, 'w') as f:
            json.dump(data, f)

    def load(self):
        """Load graph from JSON."""
        if not self.persist_path or not self.persist_path.exists():
            return
        with open(self.persist_path, 'r') as f:
            data = json.load(f)
            self.graph = nx.node_link_graph(data)
