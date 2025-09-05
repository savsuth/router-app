from typing import Tuple, Dict
import networkx as nx

def build_sample_graph() -> Tuple[nx.Graph, Dict[str, Tuple[float, float]]]:

    G = nx.Graph()
    # Node positions (fake coordinates)
    pos = {
        "A": (0, 0),
        "B": (2, 1),
        "C": (2, -1),
        "D": (4, 0),
        "E": (6, 0),
    }
    G.add_nodes_from(pos.keys())

    # Edge times (minutes). Think of these as travel time.
    edges = [
        ("A", "B", 5),
        ("A", "C", 6),
        ("B", "C", 2),
        ("B", "D", 6),
        ("C", "D", 3),
        ("D", "E", 4),
        ("B", "E", 11)  # longer diagonal
    ]
    for u, v, t in edges:
        G.add_edge(u, v, time=float(t))
    return G, pos
