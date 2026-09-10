import networkx as nx
from app.utils.graph_converter import load_person_network


def detect_communities():
    graph = load_person_network()

    if graph.number_of_nodes() == 0:
        return {
            "total_communities": 0,
            "communities": []
        }

    undirected_graph = graph.to_undirected()

    communities = nx.community.greedy_modularity_communities(
        undirected_graph
    )

    results = []

    for index, community in enumerate(communities, start=1):
        results.append({
            "community_id": index,
            "members": sorted(list(community)),
            "size": len(community)
        })

    results.sort(
        key=lambda x: x["size"],
        reverse=True
    )

    return {
        "total_communities": len(results),
        "communities": results
    }