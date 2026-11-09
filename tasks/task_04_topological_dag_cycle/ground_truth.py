"""Ground Truth Reference Implementation for Task 04: Deterministic Dependency Graph."""

import heapq
from typing import List, Dict, Set


class CycleDetectedError(Exception):
    def __init__(self, cycle_path: List[str]):
        super().__init__(f"Cycle detected: {' -> '.join(cycle_path)}")
        self.cycle_path = cycle_path


class DependencyGraph:
    def __init__(self):
        # adj[u] = list of packages that depend on u (edges: depends_on -> package)
        self._adj: Dict[str, Set[str]] = {}
        # in_degree[package] = number of unsatisfied dependencies
        self._in_degree: Dict[str, int] = {}
        self._all_nodes: Set[str] = set()

    def add_package(self, package: str) -> None:
        self._all_nodes.add(package)
        if package not in self._adj:
            self._adj[package] = set()
        if package not in self._in_degree:
            self._in_degree[package] = 0

    def add_dependency(self, package: str, depends_on: str) -> None:
        self.add_package(package)
        self.add_package(depends_on)
        if package not in self._adj[depends_on]:
            self._adj[depends_on].add(package)
            self._in_degree[package] += 1

    def resolve(self) -> List[str]:
        # Kahn's algorithm with min-heap for deterministic tie-breaking
        in_deg = dict(self._in_degree)
        ready_heap = [node for node in self._all_nodes if in_deg[node] == 0]
        heapq.heapify(ready_heap)

        resolved_order = []

        while ready_heap:
            current = heapq.heappop(ready_heap)
            resolved_order.append(current)

            for neighbor in sorted(self._adj[current]):
                in_deg[neighbor] -= 1
                if in_deg[neighbor] == 0:
                    heapq.heappush(ready_heap, neighbor)

        if len(resolved_order) == len(self._all_nodes):
            return resolved_order

        # Cycle detected! Extract minimal cycle path iteratively
        unresolved = {node for node, deg in in_deg.items() if deg > 0}
        cycle_path = self._extract_minimal_cycle(unresolved)
        raise CycleDetectedError(cycle_path)

    def _extract_minimal_cycle(self, candidate_nodes: Set[str]) -> List[str]:
        # Reverse map to find who depends on who: prereqs of node
        # We trace depends_on -> package or package -> depends_on
        # In dependency terms: package depends on prereq
        prereqs: Dict[str, List[str]] = {node: [] for node in candidate_nodes}
        for u in candidate_nodes:
            for v in self._adj[u]:
                if v in candidate_nodes:
                    prereqs[v].append(u)

        start_node = next(iter(candidate_nodes))
        visited_index = {}
        path = []

        curr = start_node
        while curr not in visited_index:
            visited_index[curr] = len(path)
            path.append(curr)
            # Pick next node in cycle from prerequisites
            next_nodes = prereqs.get(curr, [])
            if not next_nodes:
                # Fallback to outgoing
                next_nodes = [v for v in self._adj[curr] if v in candidate_nodes]
            curr = next_nodes[0]

        # Extract loop: from visited_index[curr] to end + [curr]
        cycle_start = visited_index[curr]
        cycle = path[cycle_start:] + [curr]
        return cycle
