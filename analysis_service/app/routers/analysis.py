"""
Analysis API (Member 4).

Endpoint names and response keys here are fixed by two consumers — the React
dashboard (RiskTable, CommunityPanel, StatsCards) and the AI service's
DBRetriever. Changing a key means changing both, so keep them stable.
"""
import logging
import os
from typing import Dict, List

import requests
from fastapi import APIRouter, HTTPException, Query

from app.analyzers import anomalies as anomaly_analyzer
from app.analyzers import centrality as centrality_analyzer
from app.analyzers import communities as community_analyzer
from app.analyzers import risk as risk_analyzer
from app.graph_loader import GraphLoader, graph_loader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])

BACKEND_API = os.getenv("BACKEND_API", "http://localhost:8000")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "15"))


def _load_graph(refresh: bool = False):
    try:
        graph = graph_loader.load(refresh=refresh)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    projected, names = GraphLoader.person_projection(graph)
    return graph, projected, names


def _fetch(path: str, key: str) -> List[Dict]:
    """Pull records from the backend. Returns [] when it's unreachable."""
    try:
        resp = requests.get(f"{BACKEND_API}{path}", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get(key, [])
    except requests.RequestException as exc:
        logger.warning("Backend unreachable for %s: %s", path, exc)
        return []


@router.get("/centrality")
def get_centrality(limit: int = Query(20, ge=1, le=200)):
    _, projected, names = _load_graph()
    rows = centrality_analyzer.compute_centrality(projected, names, limit=limit)
    return {
        "total_persons": projected.number_of_nodes(),
        "centrality": rows,
        "key_players": centrality_analyzer.key_players(rows),
    }


@router.get("/communities")
def get_communities():
    _, projected, names = _load_graph()
    detected = community_analyzer.detect_communities(projected, names)
    return {
        "total_communities": len(detected),
        "modularity": community_analyzer.modularity_score(projected, detected, names),
        "communities": detected,
    }


@router.get("/anomalies/transactions")
def get_transaction_anomalies():
    transactions = _fetch("/records/transactions", "transactions")
    flagged = anomaly_analyzer.detect_transaction_anomalies(transactions)
    return {
        "total_transactions": len(transactions),
        "total_flagged": len(flagged),
        "suspicious_transactions": flagged,
    }


@router.get("/anomalies/calls")
def get_call_anomalies():
    calls = _fetch("/records/calls", "call_records")
    flagged = anomaly_analyzer.detect_call_anomalies(calls)
    return {
        "total_call_records": len(calls),
        "total_flagged": len(flagged),
        "communication_anomalies": flagged,
    }


@router.get("/risk/all")
def get_all_risk_scores(limit: int = Query(50, ge=1, le=500)):
    graph, projected, names = _load_graph()

    centrality_rows = centrality_analyzer.compute_centrality(projected, names, limit=1000)
    txn_anomalies = anomaly_analyzer.detect_transaction_anomalies(
        _fetch("/records/transactions", "transactions")
    )
    call_anomalies = anomaly_analyzer.detect_call_anomalies(_fetch("/records/calls", "call_records"))

    scores = risk_analyzer.score_all(
        graph, projected, names, centrality_rows, txn_anomalies, call_anomalies
    )

    levels = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for entry in scores:
        levels[entry["risk_level"]] += 1

    return {
        "total_scored": len(scores),
        "critical_risk": levels["CRITICAL"],
        "high_risk": levels["HIGH"],
        "medium_risk": levels["MEDIUM"],
        "low_risk": levels["LOW"],
        "top_suspects": scores[:limit],
    }


@router.get("/risk/{person_name}")
def get_person_risk(person_name: str):
    graph, projected, names = _load_graph()
    centrality_rows = centrality_analyzer.compute_centrality(projected, names, limit=1000)
    txn_anomalies = anomaly_analyzer.detect_transaction_anomalies(
        _fetch("/records/transactions", "transactions")
    )
    call_anomalies = anomaly_analyzer.detect_call_anomalies(_fetch("/records/calls", "call_records"))

    scores = risk_analyzer.score_all(
        graph, projected, names, centrality_rows, txn_anomalies, call_anomalies
    )
    for entry in scores:
        if entry["person"].lower() == person_name.lower():
            return entry

    raise HTTPException(status_code=404, detail=f"No person named '{person_name}' in the graph.")


@router.post("/run-full-analysis")
def run_full_analysis():
    """
    Everything at once, with a fresh graph read. This is what the dashboard's
    'Run Full Analysis' button calls before the demo.
    """
    graph, projected, names = _load_graph(refresh=True)

    centrality_rows = centrality_analyzer.compute_centrality(projected, names, limit=1000)
    detected_communities = community_analyzer.detect_communities(projected, names)
    txn_anomalies = anomaly_analyzer.detect_transaction_anomalies(
        _fetch("/records/transactions", "transactions")
    )
    call_anomalies = anomaly_analyzer.detect_call_anomalies(_fetch("/records/calls", "call_records"))
    scores = risk_analyzer.score_all(
        graph, projected, names, centrality_rows, txn_anomalies, call_anomalies
    )

    return {
        "status": "complete",
        "graph_size": {
            "total_nodes": graph.number_of_nodes(),
            "total_edges": graph.number_of_edges(),
            "persons": projected.number_of_nodes(),
        },
        "key_players": centrality_analyzer.key_players(centrality_rows),
        "centrality": centrality_rows[:20],
        "communities": detected_communities,
        "suspicious_transactions": txn_anomalies[:20],
        "communication_anomalies": call_anomalies[:20],
        "top_suspects": scores[:20],
        "summary": {
            "communities_detected": len(detected_communities),
            "transactions_flagged": len(txn_anomalies),
            "call_patterns_flagged": len(call_anomalies),
            "critical_risk_persons": sum(1 for s in scores if s["risk_level"] == "CRITICAL"),
        },
    }
