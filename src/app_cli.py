from graph_sim.build_graph import build_sample_graph
from graph_sim.shortest_path import dijkstra_route, astar_route, apply_rush_hour
from graph_sim.visualize import draw_route

if __name__ == "__main__":
    G, pos = build_sample_graph()
    src, dst = "A", "E"

    # Baseline (no traffic)
    path_d, cost_d = dijkstra_route(G, src, dst)
    print(f"Dijkstra: {path_d} | time={cost_d:.1f} min")
    draw_route(G, pos, path_d, title=f"Dijkstra {cost_d:.1f} min")

    # Rush hour (simulate traffic on certain roads)
    apply_rush_hour(G, [("B", "D"), ("C", "D")], factor=1.6)
    path_a, cost_a = astar_route(G, pos, src, dst)
    print(f"A*: {path_a} | time={cost_a:.1f} min (rush hour)")
    draw_route(G, pos, path_a, title=f"A* (rush hour) {cost_a:.1f} min")
