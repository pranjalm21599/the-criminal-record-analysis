from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

from app.builders.person_builder import PersonBuilder
from app.builders.phone_builder import PhoneBuilder
from app.builders.case_builder import CaseBuilder
from app.neo4j_driver import db
from app.resolvers.entity_resolver import EntityResolver
from app.resolvers.network_analytics import NetworkAnalytics
from app.routers import graph_api

app = FastAPI(
    title="Criminal Network Analysis Graph API",
    description="Backend graph engine powered by Neo4j for crime network detection",
    version="1.0.0"
)

# Enable CORS for hackathon cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

person_builder = PersonBuilder()
phone_builder = PhoneBuilder()
case_builder = CaseBuilder()
resolver = EntityResolver()
analytics = NetworkAnalytics()

# The /graph/* contract used by the frontend, the AI service and the
# ingestion pipeline. Registered before the legacy routes below.
app.include_router(graph_api.router)


@app.get("/health")
def health():
    """Reports Neo4j reachability, not just process liveness."""
    try:
        db.execute_query("RETURN 1 AS ok")
        neo4j_connected = True
    except Exception:
        neo4j_connected = False

    return {
        "status": "ok",
        "service": "Knowledge Graph",
        "neo4j_connected": neo4j_connected,
    }

# --- Schemas ---
class PersonCreate(BaseModel):
    name: str
    role: Optional[str] = "suspect"
    aliases: Optional[List[str]] = []
    phone_numbers: Optional[List[str]] = []

class CallRecordCreate(BaseModel):
    caller: str
    receiver: str
    call_count: Optional[int] = 1
    total_duration: Optional[int] = 0

class FIRCreate(BaseModel):
    fir_number: str
    police_station: str
    offense_type: str
    case_number: Optional[str] = None
    ipc_sections: Optional[List[str]] = []

class CoAccusedRequest(BaseModel):
    fir_number: str
    suspect_names: List[str]

# --- Visual Dashboard Route ---
@app.get("/dashboard", response_class=HTMLResponse)
def view_dashboard():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

# --- Ingestion & Resolution Routes ---
@app.get("/")
def root():
    return {"status": "online", "dashboard_url": "/dashboard", "docs_url": "/docs"}

@app.post("/persons")
def add_person(payload: PersonCreate):
    person_id = person_builder.create_or_update_person(payload.model_dump())
    return {"status": "success", "person_id": person_id, "name": payload.name}

@app.post("/calls")
def log_call(payload: CallRecordCreate):
    res = phone_builder.create_call_relationship(
        payload.caller, payload.receiver, payload.call_count, payload.total_duration
    )
    return {"status": "success", "record": res}

@app.post("/firs")
def register_fir(payload: FIRCreate):
    res = case_builder.create_fir_node(payload.model_dump())
    return {"status": "success", "fir": res}

@app.post("/resolve/co-accused")
def link_suspects_in_case(payload: CoAccusedRequest):
    links = resolver.link_co_accused(payload.fir_number, payload.suspect_names)
    return {"status": "success", "links_created": links}

@app.get("/network/full-graph")
def get_full_graph():
    return resolver.get_full_graph_data()

@app.get("/network/person/{name}")
def get_network(name: str, depth: int = 2):
    graph_data = resolver.get_person_network(name, depth)
    return {"person": name, "depth": depth, "subgraph": graph_data}

@app.get("/network/shortest-path")
def find_path(start: str, end: str):
    path = resolver.find_connection_path(start, end)
    if not path:
        raise HTTPException(status_code=404, detail="No connection path found")
    return {"path": path[0]}

# --- Centrality & Intelligence Routes ---
@app.get("/analytics/shared-phones")
def detect_shared_phones():
    return {"shared_identifiers": resolver.detect_shared_identifiers()}

@app.get("/analytics/centrality")
def get_centrality(limit: int = 15):
    return {"centrality": analytics.get_degree_centrality(limit=limit)}

@app.get("/analytics/money-trail/{account_number}")
def trace_money(account_number: str):
    trail = analytics.trace_money_trail(account_number)
    return {"source_account": account_number, "trails": trail}

@app.get("/analytics/kingpins")
def identify_kingpins():
    candidates = analytics.detect_kingpin_candidates()
    return {"kingpin_candidates": candidates}

@app.get("/analytics/bridge-nodes")
def identify_bridge_nodes():
    bridges = analytics.detect_critical_bridge()
    return {"bridge_nodes": bridges}

@app.get("/analytics/dossier")
def get_dossier():
    return analytics.generate_intelligence_brief()

@app.get("/analytics/cells")
def get_syndicate_cells():
    return {"cells": analytics.detect_syndicate_cells()}

@app.get("/analytics/simulate-arrest/{suspect_name}")
def simulate_arrest(suspect_name: str):
    return analytics.simulate_target_arrest(suspect_name)
