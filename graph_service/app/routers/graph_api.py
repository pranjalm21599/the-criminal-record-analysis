"""
The /graph/* API surface.

This is the contract the rest of the system codes against: the React
dashboard (NetworkGraph, StatsCards), the AI service's GraphRetriever, and
the backend's ingestion pipeline all call these paths and depend on these
exact response keys. The older /network/* and /analytics/* routes in main.py
are kept for the standalone HTML dashboard.
"""
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.builders.case_builder import CaseBuilder
from app.builders.person_builder import PersonBuilder
from app.builders.phone_builder import PhoneBuilder
from app.neo4j_driver import db

router = APIRouter(prefix="/graph", tags=["Graph API"])

person_builder = PersonBuilder()
phone_builder = PhoneBuilder()
case_builder = CaseBuilder()

# Property to read a display name from, per node label.
_NAME_KEYS = [
    "name", "number", "account_number", "fir_number",
    "case_number", "plate_number", "title",
]


def _display_name(props: Dict) -> str:
    for key in _NAME_KEYS:
        if props.get(key):
            return str(props[key])
    return "Unknown"


class ExtractionPayload(BaseModel):
    """What the backend's ingestion pipeline posts after NLP runs."""

    fir_number: str = ""
    case_number: Optional[str] = None
    police_station: str = ""
    offense_type: str = ""
    persons: List[str] = []
    phones: List[str] = []
    vehicles: List[str] = []
    locations: List[str] = []
    organizations: List[str] = []
    bank_accounts: List[str] = []
    ipc_sections: List[str] = []
    # person name -> accused / victim / witness / associated, as inferred by NLP.
    roles: Dict[str, str] = {}
    # identifier -> owning person, resolved by text proximity in the backend.
    phone_owners: Dict[str, str] = {}
    account_owners: Dict[str, str] = {}


class TransactionPayload(BaseModel):
    from_account: str
    to_account: str
    amount: float = 0.0
    date: str = ""


@router.get("/stats")
def graph_stats():
    """Node and relationship counts by type — powers the dashboard stat cards."""
    node_query = """
    MATCH (n)
    RETURN head(labels(n)) AS node_type, count(*) AS count
    ORDER BY count DESC
    """
    rel_query = """
    MATCH ()-[r]->()
    RETURN type(r) AS relationship_type, count(*) AS count
    ORDER BY count DESC
    """
    try:
        node_counts = db.execute_query(node_query)
        rel_counts = db.execute_query(rel_query)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {exc}") from exc

    return {
        "node_counts": node_counts,
        "relationship_counts": rel_counts,
        "total_nodes": sum(row["count"] for row in node_counts),
        "total_relationships": sum(row["count"] for row in rel_counts),
    }


@router.get("/search")
def search_entities(q: str = Query(..., min_length=1)):
    """Case-insensitive substring search across every named entity."""
    query = """
    MATCH (n)
    WITH n, head(labels(n)) AS node_type,
         coalesce(n.name, n.number, n.account_number, n.fir_number,
                  n.case_number, n.plate_number, '') AS entity_name
    WHERE toLower(entity_name) CONTAINS toLower($q)
    RETURN node_type AS type, entity_name AS name, properties(n) AS properties
    LIMIT 25
    """
    try:
        results = db.execute_query(query, {"q": q})
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {exc}") from exc

    return {"query": q, "count": len(results), "results": results}


def _resolve_person_name(name: str) -> Optional[str]:
    """
    Turn whatever the investigator typed into an actual node name.

    Nobody searching a case file types "Imran Sheikh" with exact casing —
    they type "imran", or a surname. Matching only on the exact string sends
    the dashboard a 404 for a person who is right there in the graph.

    Tried in order of confidence: exact, case-insensitive exact, then
    substring. Among substring hits the shortest name wins, since "Ali"
    should resolve to "Ali" rather than "Mohammad Ali" when both exist.
    """
    exact = db.execute_query(
        "MATCH (p:Person {name: $name}) RETURN p.name AS name LIMIT 1", {"name": name}
    )
    if exact:
        return exact[0]["name"]

    fuzzy = db.execute_query(
        """
        MATCH (p:Person)
        WHERE toLower(p.name) = toLower($name)
           OR toLower(p.name) CONTAINS toLower($name)
        RETURN p.name AS name
        ORDER BY toLower(p.name) = toLower($name) DESC, size(p.name) ASC
        LIMIT 1
        """,
        {"name": name},
    )
    return fuzzy[0]["name"] if fuzzy else None


@router.get("/person/{name}/network")
def person_network(name: str, depth: int = Query(2, ge=1, le=4)):
    """
    The subgraph around one person, flattened into the {nodes, edges} shape
    Cytoscape expects on the frontend.
    """
    # depth is interpolated because Neo4j does not accept a parameter inside a
    # variable-length pattern; it is bounded to 1-4 by the Query validator above.
    # Nodes and edges are fetched as two flat queries rather than one nested
    # collect/unwind — same result, far easier to read and debug.
    node_query = f"""
    MATCH (p:Person {{name: $name}})
    OPTIONAL MATCH path = (p)-[*1..{depth}]-(other)
    WITH p, CASE WHEN path IS NULL THEN [p] ELSE nodes(path) END AS path_nodes
    UNWIND path_nodes AS n
    RETURN DISTINCT elementId(n) AS id, labels(n) AS labels, properties(n) AS props
    """
    edge_query = f"""
    MATCH path = (p:Person {{name: $name}})-[*1..{depth}]-(other)
    UNWIND relationships(path) AS r
    RETURN DISTINCT elementId(startNode(r)) AS source,
                    elementId(endNode(r))   AS target,
                    type(r)                 AS type
    """
    try:
        resolved = _resolve_person_name(name)
        if resolved is None:
            # Offer the closest names rather than a bare 404 — a typo or a
            # surname shouldn't leave the investigator with nothing to go on.
            suggestions = [
                row["name"]
                for row in db.execute_query(
                    "MATCH (p:Person) RETURN p.name AS name ORDER BY p.name LIMIT 8"
                )
            ]
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"No person matching '{name}' in the graph.",
                    "did_you_mean": suggestions,
                },
            )

        node_rows = db.execute_query(node_query, {"name": resolved})
        edge_rows = db.execute_query(edge_query, {"name": resolved})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {exc}") from exc

    name = resolved

    nodes = [
        {
            "id": n["id"],
            "name": _display_name(n["props"]),
            "label": (n["labels"] or ["Unknown"])[0],
            "properties": n["props"],
        }
        for n in node_rows
    ]
    edges = edge_rows

    return {
        "person": name,
        "depth": depth,
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }


@router.get("/shortest-path")
def shortest_path(person1: str, person2: str):
    """Degrees of separation between two people, with the chain in between."""
    query = """
    MATCH (a:Person {name: $person1}), (b:Person {name: $person2})
    MATCH path = shortestPath((a)-[*..15]-(b))
    RETURN [n IN nodes(path) | coalesce(n.name, n.number, n.account_number,
                                        n.fir_number, n.case_number, 'Unknown')] AS path_nodes,
           [r IN relationships(path) | type(r)] AS path_relationships,
           length(path) AS hops
    """
    try:
        # Same name resolution as /graph/person/{name}/network, so a path
        # search behaves consistently with an ego-network search.
        resolved1 = _resolve_person_name(person1)
        resolved2 = _resolve_person_name(person2)

        if resolved1 is None or resolved2 is None:
            missing = person1 if resolved1 is None else person2
            raise HTTPException(
                status_code=404, detail=f"No person matching '{missing}' in the graph."
            )

        results = db.execute_query(query, {"person1": resolved1, "person2": resolved2})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {exc}") from exc

    if not results:
        return {
            "path_found": False,
            "person1": resolved1,
            "person2": resolved2,
            "path_nodes": [],
            "degrees_of_separation": None,
        }

    row = results[0]
    return {
        "path_found": True,
        "person1": resolved1,
        "person2": resolved2,
        "path_nodes": row["path_nodes"],
        "path_relationships": row["path_relationships"],
        "degrees_of_separation": row["hops"],
    }


@router.get("/full")
def full_graph(limit: int = Query(500, ge=1, le=5000)):
    """The whole graph, same {nodes, edges} shape as /graph/person/{n}/network."""
    node_query = """
    MATCH (n)
    RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props
    LIMIT $limit
    """
    edge_query = """
    MATCH (a)-[r]->(b)
    RETURN elementId(a) AS source, elementId(b) AS target, type(r) AS type
    LIMIT $edge_limit
    """
    try:
        node_rows = db.execute_query(node_query, {"limit": limit})
        edge_rows = db.execute_query(edge_query, {"edge_limit": limit * 5})
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {exc}") from exc

    nodes = [
        {
            "id": n["id"],
            "name": _display_name(n["props"]),
            "label": (n["labels"] or ["Unknown"])[0],
            "properties": n["props"],
        }
        for n in node_rows
    ]
    node_ids = {n["id"] for n in nodes}
    # Drop edges pointing outside the limited node set, or the frontend
    # renders dangling references.
    edges = [
        e for e in edge_rows
        if e["source"] in node_ids and e["target"] in node_ids
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }


@router.post("/build/from-extraction")
def build_from_extraction(payload: ExtractionPayload):
    """
    Turn one document's NLP output into graph nodes and edges.

    This is step 4 of the pipeline: the backend calls it right after the NLP
    service returns, so a single FIR upload lands in the graph automatically.
    """
    created = 0
    try:
        if payload.fir_number:
            case_builder.create_fir_node({
                "fir_number": payload.fir_number,
                "police_station": payload.police_station,
                "offense_type": payload.offense_type,
                "ipc_sections": payload.ipc_sections,
                "case_number": payload.case_number,
            })
            created += 1

        # Relationship to the FIR depends on the person's role — charging the
        # complainant as an accused would poison every downstream analytic.
        role_to_edge = {
            "victim": "COMPLAINANT_IN",
            "witness": "WITNESS_IN",
        }

        for person in payload.persons:
            if not person.strip():
                continue
            role = payload.roles.get(person, "suspect")
            person_builder.create_or_update_person({"name": person, "role": role})
            created += 1

            if payload.fir_number:
                edge_type = role_to_edge.get(role, "ACCUSED_IN")
                db.execute_query(
                    f"""
                    MATCH (p:Person {{name: $name}})
                    MATCH (f:FIR {{fir_number: $fir}})
                    MERGE (p)-[:{edge_type}]->(f)
                    """,
                    {"name": person, "fir": payload.fir_number},
                )

        # Phones are attributed by text proximity (resolved upstream), not to
        # whoever was named first. A phone with no confident owner is still
        # created as a node — an unattributed number is evidence too — it just
        # gets no USES_PHONE edge.
        for phone in payload.phones:
            if not phone.strip():
                continue
            phone_builder.create_phone_node(phone, payload.phone_owners.get(phone))
            created += 1

        for label, values, key in [
            ("Vehicle", payload.vehicles, "plate_number"),
            ("Location", payload.locations, "name"),
            ("Organization", payload.organizations, "name"),
            ("BankAccount", payload.bank_accounts, "account_number"),
        ]:
            for value in values:
                if not str(value).strip():
                    continue
                db.execute_query(
                    f"MERGE (n:{label} {{{key}: $value}}) ON CREATE SET n.created_at = datetime()",
                    {"value": str(value)},
                )
                created += 1

                if payload.fir_number:
                    db.execute_query(
                        f"""
                        MATCH (n:{label} {{{key}: $value}})
                        MATCH (f:FIR {{fir_number: $fir}})
                        MERGE (n)-[:MENTIONED_IN]->(f)
                        """,
                        {"value": str(value), "fir": payload.fir_number},
                    )

                # Tie accounts to their holder so flagged transactions raise
                # the right person's risk score.
                if label == "BankAccount":
                    holder = payload.account_owners.get(str(value))
                    if holder:
                        db.execute_query(
                            """
                            MATCH (p:Person {name: $holder})
                            MATCH (a:BankAccount {account_number: $value})
                            MERGE (p)-[:OWNS_ACCOUNT]->(a)
                            """,
                            {"holder": holder, "value": str(value)},
                        )

        # Everyone named in the same FIR is a co-accused of everyone else.
        if payload.fir_number and len(payload.persons) > 1:
            db.execute_query(
                """
                MATCH (p1:Person)-[:ACCUSED_IN]->(f:FIR {fir_number: $fir})<-[:ACCUSED_IN]-(p2:Person)
                WHERE elementId(p1) < elementId(p2)
                MERGE (p1)-[r:CO_ACCUSED_WITH]->(p2)
                ON CREATE SET r.case = $fir
                """,
                {"fir": payload.fir_number},
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Graph write failed: {exc}") from exc

    return {
        "status": "success",
        "fir_number": payload.fir_number,
        "nodes_created": created,
        "persons": len(payload.persons),
        "phones": len(payload.phones),
    }


@router.post("/transaction")
def add_transaction(payload: TransactionPayload):
    """Create a money-flow edge between two bank accounts."""
    try:
        case_builder.create_financial_edge(
            payload.from_account, payload.to_account, payload.amount, payload.date
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Graph write failed: {exc}") from exc
    return {"status": "success", "from": payload.from_account, "to": payload.to_account}


@router.post("/person")
def add_person(name: str, role: str = "suspect"):
    try:
        person_id = person_builder.create_or_update_person({"name": name, "role": role})
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Graph write failed: {exc}") from exc
    return {"status": "success", "person_id": person_id, "name": name}
