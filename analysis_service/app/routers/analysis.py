from fastapi import APIRouter, Query

from app.analyzers.centrality import calculate_centrality
from app.analyzers.community import detect_communities
from app.analyzers.anomaly import (
    detect_transaction_anomalies,
    detect_call_anomalies,
    detect_ml_anomalies
)
from app.analyzers.risk_scorer import (
    calculate_risk_scores,
    get_person_risk
)

router = APIRouter(
    prefix="/analysis",
    tags=["Network Analysis"]
)


@router.get("/centrality")
def centrality():
    return calculate_centrality()


@router.get("/communities")
def communities():
    return detect_communities()


@router.get("/anomalies/transactions")
def transaction_anomalies(
    threshold: float = Query(100000)
):
    return detect_transaction_anomalies(threshold)


@router.get("/anomalies/calls")
def call_anomalies():
    return detect_call_anomalies()


@router.get("/anomalies/ml")
def ml_anomalies():
    return detect_ml_anomalies()


@router.get("/risk/all")
def all_risk_scores():
    return calculate_risk_scores()


@router.get("/risk/{person_name}")
def person_risk(person_name: str):
    return get_person_risk(person_name)
