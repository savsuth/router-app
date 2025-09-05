from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import networkx as nx

def draw_route(G: nx.Graph, pos: Dict[str, Tuple[float, float]], route: List[str], title: str = "Route"):
    plt.figure()
    nx.draw(G, pos, with_labels=True, node_size=700, font_size=10)
    edge_labels = {(u, v): f'{d["time"]:.1f}' for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    # Highlight route
    route_edges = list(zip(route, route[1:]))
    nx.draw_networkx_edges(G, pos, edgelist=route_edges, width=3)
    plt.title(title)
    plt.tight_layout()
    plt.show()
