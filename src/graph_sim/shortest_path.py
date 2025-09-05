from typing import List, Tuple, Dict
import math
import networkx as nx

def dijkstra_route(G: nx.Graph, src: str, dst: str) -> Tuple[List[str], float]:
    path = nx.shortest_path(G, src, dst, weight="time")
    cost = sum(G[u][v]["time"] for u, v in zip(path, path[1:]))
    return path, cost

def _euclid(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0]-b[0], a[1]-b[1])

def astar_route(G: nx.Graph, pos: Dict[str, Tuple[float, float]], src: str, dst: str) -> Tuple[List[str], float]:
    """A* with Euclidean straight-line heuristic on node positions."""
    def h(n1, n2):
        return _euclid(pos[n1], pos[n2])
    path = nx.astar_path(G, src, dst, heuristic=lambda n: h(n, dst), weight="time")
    cost = sum(G[u][v]["time"] for u, v in zip(path, path[1:]))
    return path, cost

def apply_rush_hour(G: nx.Graph, affected_edges: List[Tuple[str, str]], factor: float = 1.5):
    """Multiply time on specific edges to simulate traffic."""
    for u, v in affected_edges:
        if G.has_edge(u, v):
            G[u][v]["time"] *= factor
