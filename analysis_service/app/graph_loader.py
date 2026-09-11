"""
Pulls the knowledge graph out of Neo4j and turns it into a NetworkX graph.

Every analyzer in this service works off the NetworkX object rather than
issuing its own Cypher, so the graph is fetched once and reused. Results are
cached briefly because the dashboard hits several analysis endpoints at once
on page load and there's no point re-reading the whole graph five times.
"""
import logging
import os
import threading
import time
from typing import Dict, List, Optional, Tuple

import networkx as nx
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable

logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "criminal123")
CACHE_TTL = float(os.getenv("GRAPH_CACHE_TTL", "15"))

_FETCH_QUERY = """
MATCH (n)
OPTIONAL MATCH (n)-[r]->(m)
RETURN elementId(n)                AS source_id,
       head(labels(n))             AS source_label,
       coalesce(n.name, n.number, n.account_number, n.fir_number,
                n.case_number, n.plate_number, 'Unknown') AS source_name,
       n.role                      AS source_role,
       n.risk_score                AS source_risk,
       elementId(m)                AS target_id,
       head(labels(m))             AS target_label,
       coalesce(m.name, m.number, m.account_number, m.fir_number,
                m.case_number, m.plate_number, 'Unknown') AS target_name,
       m.role                      AS target_role,
       m.risk_score                AS target_risk,
       type(r)                     AS rel_type,
       properties(r)               AS rel_props
"""


class GraphLoader:
    def __init__(self) -> None:
        self._driver = None
        self._lock = threading.Lock()
        self._cache: Optional[nx.MultiDiGraph] = None
        self._cached_at = 0.0

    # ---------- connection ----------

    def _get_driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        return self._driver

    def is_connected(self) -> bool:
        try:
            self._get_driver().verify_connectivity()
            return True
        except Exception as exc:
            logger.warning("Neo4j not reachable at %s: %s", NEO4J_URI, exc)
            return False

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    # ---------- loading ----------

    def load(self, refresh: bool = False) -> nx.MultiDiGraph:
        """
        Return the graph as a NetworkX MultiDiGraph.

        Raises RuntimeError when Neo4j is unreachable — callers turn that into
        a 503 so the dashboard can say "graph service down" instead of quietly
        showing an empty, and therefore misleading, network.
        """
        with self._lock:
            fresh_enough = (
                self._cache is not None and (time.time() - self._cached_at) < CACHE_TTL
            )
            if fresh_enough and not refresh:
                return self._cache

            try:
                with self._get_driver().session() as session:
                    rows = [record.data() for record in session.run(_FETCH_QUERY)]
            except (ServiceUnavailable, Neo4jError, OSError) as exc:
                raise RuntimeError(f"Cannot reach Neo4j at {NEO4J_URI}: {exc}") from exc

            graph = nx.MultiDiGraph()
            for row in rows:
                src = row["source_id"]
                graph.add_node(
                    src,
                    label=row["source_label"] or "Unknown",
                    name=row["source_name"],
                    role=row["source_role"],
                    risk_score=row["source_risk"],
                )

                if row["target_id"] is None:
                    continue

                tgt = row["target_id"]
                graph.add_node(
                    tgt,
                    label=row["target_label"] or "Unknown",
                    name=row["target_name"],
                    role=row["target_role"],
                    risk_score=row["target_risk"],
                )
                graph.add_edge(src, tgt, type=row["rel_type"], **(row["rel_props"] or {}))

            self._cache = graph
            self._cached_at = time.time()
            return graph

    # ---------- helpers shared by the analyzers ----------

    @staticmethod
    def person_nodes(graph: nx.MultiDiGraph) -> List[str]:
        return [n for n, d in graph.nodes(data=True) if d.get("label") == "Person"]

    @staticmethod
    def person_projection(graph: nx.MultiDiGraph) -> Tuple[nx.Graph, Dict[str, str]]:
        """
        Collapse the multi-type graph into an undirected person-to-person graph.

        Two people are linked if they are directly related, or if they share any
        intermediate entity (a phone, an FIR, a bank account). That indirect link
        is the whole point — "these two never called each other but both used the
        same burner" is exactly the hidden connection investigators want.
        """
        undirected = graph.to_undirected(as_view=True)
        persons = GraphLoader.person_nodes(graph)
        person_set = set(persons)
        names = {n: graph.nodes[n].get("name", "Unknown") for n in persons}

        projected = nx.Graph()
        projected.add_nodes_from(persons)

        for person in persons:
            for neighbor in undirected.neighbors(person):
                if neighbor in person_set:
                    projected.add_edge(person, neighbor, weight=1.0, via="direct")
                    continue

                # Shared non-person entity: link every pair of people hanging off it.
                for other in undirected.neighbors(neighbor):
                    if other != person and other in person_set:
                        via = graph.nodes[neighbor].get("label", "Entity")
                        projected.add_edge(person, other, weight=1.0, via=via)

        return projected, names


graph_loader = GraphLoader()
