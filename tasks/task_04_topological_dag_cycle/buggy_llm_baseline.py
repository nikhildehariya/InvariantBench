"""Buggy LLM Baseline Implementation for Task 04.

Representative of typical frontier LLM outputs:
1. Uses recursive DFS which crashes with RecursionError on deep chains.
2. Uses standard FIFO queue rather than priority heap, violating deterministic
   alphabetical tie-breaking.
3. Fails to reconstruct the minimal cycle path when cycles occur.
"""

from typing import List, Dict, Set


class CycleDetectedError(Exception):
    def __init__(self, cycle_path: List[str]):
        super().__init__(f"Cycle detected: {' -> '.join(cycle_path)}")
        self.cycle_path = cycle_path


class DependencyGraph:
    def __init__(self):
        self._adj: Dict[str, List[str]] = {}
        self._all_nodes: Set[str] = set()

    def add_package(self, package: str) -> None:
        self._all_nodes.add(package)
        if package not in self._adj:
            self._adj[package] = []

    def add_dependency(self, package: str, depends_on: str) -> None:
        self.add_package(package)
        self.add_package(depends_on)
        self._adj[depends_on].append(package)

    def resolve(self) -> List[str]:
        # LLM TRAP 1: Recursive DFS (hits RecursionError on deep graphs)
        visited = set()
        visiting = set()
        order = []

        def dfs(node: str):
            visiting.add(node)
            for neighbor in self._adj.get(node, []):
                if neighbor in visiting:
                    # LLM TRAP 2: Raises dummy empty or incomplete cycle path
                    raise CycleDetectedError([])
                if neighbor not in visited:
                    dfs(neighbor)
            visiting.remove(node)
            visited.add(node)
            order.append(node)

        # LLM TRAP 3: Iterates over set unordered, producing non-deterministic sort
        for node in list(self._all_nodes):
            if node not in visited:
                dfs(node)

        return list(reversed(order))
