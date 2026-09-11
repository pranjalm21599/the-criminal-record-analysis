"""
The ingestion pipeline: FIR text -> NLP entities -> knowledge graph.

Every downstream call is best-effort. If the NLP or graph service is down,
the upload itself still succeeds and the response carries a warning — a
partially-populated system is far better during a live demo than a 500 on
the very first action.
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

NLP_API = os.getenv("NLP_API", "http://localhost:8001")
GRAPH_API = os.getenv("GRAPH_API", "http://localhost:8002")
TIMEOUT = float(os.getenv("PIPELINE_TIMEOUT", "20"))


def extract_entities(text: str, fir_id: int) -> tuple[dict, list[str]]:
    """Ask the NLP service (M2) to pull entities out of raw FIR text."""
    warnings: list[str] = []
    try:
        resp = requests.post(
            f"{NLP_API}/extract/fir/{fir_id}",
            json={"text": text, "document_id": fir_id, "document_type": "fir"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json(), warnings
    except requests.RequestException as exc:
        logger.warning("NLP service unavailable: %s", exc)
        warnings.append(f"NLP service unreachable at {NLP_API} — entities not extracted.")
        return {}, warnings


def push_to_graph(extraction: dict, fir_record: dict) -> tuple[int, list[str]]:
    """Hand the extracted entities to the graph service (M3)."""
    warnings: list[str] = []
    if not extraction:
        return 0, warnings

    payload = {
        "fir_number": fir_record.get("fir_number", ""),
        "case_number": fir_record.get("case_number"),
        "police_station": fir_record.get("police_station", ""),
        "offense_type": fir_record.get("offense_type", ""),
        "persons": extraction.get("persons", []),
        "phones": extraction.get("phones", []),
        "vehicles": extraction.get("vehicles", []),
        "locations": extraction.get("locations", []),
        "organizations": extraction.get("organizations", []),
        "bank_accounts": extraction.get("bank_accounts", []),
        "ipc_sections": extraction.get("ipc_sections", []),
        "roles": extraction.get("roles", {}),
        "phone_owners": extraction.get("phone_owners", {}),
        "account_owners": extraction.get("account_owners", {}),
    }

    try:
        resp = requests.post(
            f"{GRAPH_API}/graph/build/from-extraction", json=payload, timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json().get("nodes_created", 0), warnings
    except requests.RequestException as exc:
        logger.warning("Graph service unavailable: %s", exc)
        warnings.append(f"Graph service unreachable at {GRAPH_API} — graph not updated.")
        return 0, warnings


def push_calls_to_graph(rows: list[dict]) -> tuple[int, list[str]]:
    """Create Phone-[:CALLED]->Phone edges from parsed CDR rows."""
    warnings: list[str] = []
    created = 0
    try:
        for row in rows:
            resp = requests.post(
                f"{GRAPH_API}/calls",
                json={
                    "caller": str(row["caller"]),
                    "receiver": str(row["receiver"]),
                    "call_count": 1,
                    "total_duration": int(row.get("duration") or 0),
                },
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            created += 1
    except requests.RequestException as exc:
        logger.warning("Graph service unavailable during CDR load: %s", exc)
        warnings.append(f"Graph service unreachable at {GRAPH_API} — {created} of {len(rows)} calls linked.")
    return created, warnings


def push_transactions_to_graph(rows: list[dict]) -> tuple[int, list[str]]:
    """Create BankAccount-[:TRANSFERRED_TO]->BankAccount edges."""
    warnings: list[str] = []
    created = 0
    try:
        for row in rows:
            resp = requests.post(
                f"{GRAPH_API}/graph/transaction",
                json={
                    "from_account": str(row["from_account"]),
                    "to_account": str(row["to_account"]),
                    "amount": float(row.get("amount") or 0),
                    "date": str(row.get("date") or ""),
                },
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            created += 1
    except requests.RequestException as exc:
        logger.warning("Graph service unavailable during transaction load: %s", exc)
        warnings.append(
            f"Graph service unreachable at {GRAPH_API} — {created} of {len(rows)} transactions linked."
        )
    return created, warnings
