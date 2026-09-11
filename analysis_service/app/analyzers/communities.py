"""
Community detection — partitions the network into likely criminal groups.

Uses greedy modularity maximisation from NetworkX (no external python-louvain
dependency needed), falling back to connected components on tiny graphs where
modularity is undefined.
"""
import logging
from typing import Dict, List

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

logger = logging.getLogger(__name__)


def detect_communities(projected: nx.Graph, names: Dict[str, str]) -> List[Dict]:
    if projected.number_of_nodes() == 0:
        return []

    groups: List[set]
    if projected.number_of_edges() == 0:
        # Nobody is linked yet — every person is their own group.
        groups = [{n} for n in projected.nodes]
    else:
        try:
            groups = [set(c) for c in greedy_modularity_communities(projected)]
        except Exception as exc:
            logger.info("Modularity clustering failed, using components: %s", exc)
            groups = [set(c) for c in nx.connected_components(projected)]

    groups.sort(key=len, reverse=True)

    communities = []
    for index, members in enumerate(groups, start=1):
        subgraph = projected.subgraph(members)
        density = nx.density(subgraph) if len(members) > 1 else 0.0

        # The most connected member inside the group is the likely ringleader.
        ringleader = None
        if members:
            ringleader = names.get(
                max(members, key=lambda n: subgraph.degree(n)), "Unknown"
            )

        communities.append({
            "label": f"Group-{index}",
            "size": len(members),
            "members": sorted(names.get(m, "Unknown") for m in members),
            "cohesion": round(density, 3),
            "likely_ringleader": ringleader,
        })

    return communities


def modularity_score(projected: nx.Graph, communities: List[Dict], names: Dict[str, str]) -> float:
    """How cleanly the network splits. Above ~0.3 means real group structure."""
    if projected.number_of_edges() == 0 or not communities:
        return 0.0

    name_to_node: Dict[str, str] = {}
    for node, name in names.items():
        name_to_node.setdefault(name, node)

    partition = []
    for community in communities:
        nodes = {name_to_node[n] for n in community["members"] if n in name_to_node}
        if nodes:
            partition.append(nodes)

    try:
        return round(nx.algorithms.community.modularity(projected, partition), 3)
    except Exception:
        return 0.0
