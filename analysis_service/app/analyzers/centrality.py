"""
Centrality: who matters structurally in this network?

Four measures, because each answers a different investigative question:
  degree      - who is busiest / most connected
  betweenness - who sits on the paths between others (couriers, brokers)
  closeness    - who can reach the whole network fastest
  eigenvector - who is connected to other important people (command layer)
"""
import logging
from typing import Dict, List

import networkx as nx

logger = logging.getLogger(__name__)


def _safe_eigenvector(graph: nx.Graph) -> Dict[str, float]:
    """
    Eigenvector centrality fails to converge on disconnected or degenerate
    graphs, which is common early on when only a couple of FIRs are loaded.
    Fall back to PageRank, which is well-defined in those cases.
    """
    try:
        return nx.eigenvector_centrality(graph, max_iter=500, tol=1e-06)
    except (nx.PowerIterationFailedConvergence, nx.NetworkXException) as exc:
        logger.info("Eigenvector centrality fell back to PageRank: %s", exc)
        try:
            return nx.pagerank(graph)
        except Exception:
            return {n: 0.0 for n in graph.nodes}


def compute_centrality(projected: nx.Graph, names: Dict[str, str], limit: int = 20) -> List[Dict]:
    if projected.number_of_nodes() == 0:
        return []

    degree = nx.degree_centrality(projected)
    betweenness = nx.betweenness_centrality(projected) if projected.number_of_nodes() > 2 else {}
    closeness = nx.closeness_centrality(projected)
    eigenvector = _safe_eigenvector(projected)

    results = []
    for node in projected.nodes:
        results.append({
            "person": names.get(node, "Unknown"),
            "degree_centrality": round(degree.get(node, 0.0), 4),
            "betweenness_centrality": round(betweenness.get(node, 0.0), 4),
            "closeness_centrality": round(closeness.get(node, 0.0), 4),
            "eigenvector_centrality": round(eigenvector.get(node, 0.0), 4),
            "direct_connections": projected.degree(node),
        })

    results.sort(key=lambda r: r["degree_centrality"], reverse=True)
    return results[:limit]


def key_players(centrality_rows: List[Dict]) -> Dict:
    """Name the single most notable person under each measure."""
    if not centrality_rows:
        return {}

    def top(metric: str) -> Dict:
        best = max(centrality_rows, key=lambda r: r[metric])
        return {"person": best["person"], "score": best[metric]}

    return {
        "most_connected": top("degree_centrality"),
        "key_broker": top("betweenness_centrality"),
        "fastest_reach": top("closeness_centrality"),
        "most_influential": top("eigenvector_centrality"),
    }
