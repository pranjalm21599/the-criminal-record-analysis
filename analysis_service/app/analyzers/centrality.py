import networkx as nx
from app.utils.graph_converter import load_person_network


def calculate_centrality():
    graph = load_person_network()

    if graph.number_of_nodes() == 0:
        return {
            "total_persons": 0,
            "total_connections": 0,
            "results": []
        }

    degree = nx.degree_centrality(graph)
    betweenness = nx.betweenness_centrality(graph)
    closeness = nx.closeness_centrality(graph)
    pagerank = nx.pagerank(graph)

    results = []

    for person in graph.nodes():
        results.append({
            "person": person,
            "degree": round(degree.get(person, 0), 4),
            "betweenness": round(betweenness.get(person, 0), 4),
            "closeness": round(closeness.get(person, 0), 4),
            "pagerank": round(pagerank.get(person, 0), 4)
        })

    results.sort(
        key=lambda x: x["pagerank"],
        reverse=True
    )

    return {
        "total_persons": graph.number_of_nodes(),
        "total_connections": graph.number_of_edges(),
        "results": results
    }