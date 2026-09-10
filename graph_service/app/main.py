from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.builders.person_builder import PersonBuilder
from app.builders.phone_builder import PhoneBuilder
from app.builders.case_builder import CaseBuilder
from app.resolvers.entity_resolver import EntityResolver

app = FastAPI(
    title="Criminal Network Analysis Graph API",
    description="Backend graph engine powered by Neo4j for crime network detection",
    version="1.0.0"
)

person_builder = PersonBuilder()
phone_builder = PhoneBuilder()
case_builder = CaseBuilder()
resolver = EntityResolver()

# --- Request Schemas ---
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

# --- Routes ---
@app.get("/")
def root():
    return {"status": "online", "system": "Criminal Network Graph API"}

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

@app.get("/analytics/shared-phones")
def detect_shared_phones():
    shared = resolver.detect_shared_identifiers()
    return {"shared_identifiers": shared}

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