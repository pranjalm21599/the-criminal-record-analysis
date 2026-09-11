"""
End-to-end pipeline smoke test.

Exercises the real investigator flow rather than poking each service in
isolation: create a case, upload the three evidence files, then confirm the
graph, the analysis and the AI assistant all see the result.

Run from the repo root:  python integration/data_pipeline.py
"""
import sys
from pathlib import Path

import requests

BACKEND = "http://localhost:8000"
NLP = "http://localhost:8001"
GRAPH = "http://localhost:8002"
ANALYSIS = "http://localhost:8003"
AI = "http://localhost:8004"

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"
TIMEOUT = 60

failures: list[str] = []


def step(number: int, title: str) -> None:
    print(f"\nStep {number}: {title}")


def fail(message: str) -> None:
    print(f"  FAILED: {message}")
    failures.append(message)


def run_pipeline() -> bool:
    print("Running end-to-end pipeline test")

    # --- 1. Case -------------------------------------------------------
    step(1, "Creating a case")
    case_id = None
    try:
        resp = requests.post(
            f"{BACKEND}/cases/",
            json={"title": "Andheri Jewellery Robbery", "status": "under_investigation"},
            timeout=TIMEOUT,
        )
        if resp.status_code in (200, 201):
            case_id = resp.json()["id"]
            print(f"  Case created: id={case_id} number={resp.json()['case_number']}")
        else:
            fail(f"backend returned {resp.status_code}: {resp.text[:200]}")
    except requests.RequestException as exc:
        fail(f"backend unreachable: {exc}")

    # --- 2. NLP --------------------------------------------------------
    step(2, "Checking NLP extraction directly")
    try:
        resp = requests.post(
            f"{NLP}/extract/text",
            json={"text": "Ravi Kumar (9876543210) was arrested in Mumbai for robbery.",
                  "document_type": "fir"},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            persons = data.get("named_entities", {}).get("persons", [])
            phones = data.get("pattern_entities", {}).get("phone", [])
            print(f"  Persons: {[p['text'] for p in persons]}  Phones: {phones}")
            if not phones:
                fail("NLP found no phone numbers — regex extraction is broken")
        else:
            fail(f"NLP returned {resp.status_code}")
    except requests.RequestException as exc:
        fail(f"NLP unreachable: {exc}")

    # --- 3. Upload (drives NLP -> graph automatically) ------------------
    step(3, "Uploading evidence files")
    uploads = [
        ("upload/fir", "sample_fir.txt", "text/plain"),
        # A second FIR from a different city that shares two people with the
        # first — without an overlapping case the graph is a single clique and
        # community detection has nothing to find.
        ("upload/fir", "sample_fir_delhi.txt", "text/plain"),
        ("upload/call-records", "sample_call_records.csv", "text/csv"),
        ("upload/transactions", "sample_transactions.csv", "text/csv"),
    ]
    for endpoint, filename, mime in uploads:
        path = SAMPLE_DIR / filename
        if not path.exists():
            fail(f"sample file missing: {path}")
            continue
        try:
            with path.open("rb") as handle:
                resp = requests.post(
                    f"{BACKEND}/{endpoint}",
                    files={"file": (filename, handle, mime)},
                    data={"case_id": case_id} if case_id else {},
                    timeout=TIMEOUT,
                )
            if resp.status_code == 200:
                body = resp.json()
                print(f"  {filename}: {body.get('message')}")
                if body.get("entities_extracted"):
                    print(f"    entities extracted: {body['entities_extracted']}")
                if body.get("graph_nodes_created"):
                    print(f"    graph writes: {body['graph_nodes_created']}")
                for warning in body.get("warnings", []):
                    print(f"    WARNING: {warning}")
                    failures.append(warning)
            else:
                fail(f"{filename} -> {resp.status_code}: {resp.text[:200]}")
        except requests.RequestException as exc:
            fail(f"{filename} upload failed: {exc}")

    # --- 4. Graph ------------------------------------------------------
    step(4, "Verifying the knowledge graph")
    try:
        resp = requests.get(f"{GRAPH}/graph/stats", timeout=TIMEOUT)
        if resp.status_code == 200:
            stats = resp.json()
            print(f"  Nodes: {stats['total_nodes']}  Relationships: {stats['total_relationships']}")
            for row in stats["node_counts"]:
                print(f"    {row['node_type']}: {row['count']}")
            if stats["total_nodes"] == 0:
                fail("graph is empty after ingestion")
        else:
            fail(f"graph stats returned {resp.status_code}")
    except requests.RequestException as exc:
        fail(f"graph service unreachable: {exc}")

    # --- 5. Analysis ---------------------------------------------------
    step(5, "Running full network analysis")
    try:
        resp = requests.post(f"{ANALYSIS}/analysis/run-full-analysis", timeout=TIMEOUT)
        if resp.status_code == 200:
            result = resp.json()
            summary = result["summary"]
            print(f"  Persons analysed: {result['graph_size']['persons']}")
            print(f"  Communities: {summary['communities_detected']}")
            print(f"  Transactions flagged: {summary['transactions_flagged']}")
            print(f"  Call patterns flagged: {summary['call_patterns_flagged']}")
            for suspect in result["top_suspects"][:3]:
                print(f"    {suspect['person']}: {suspect['risk_score']}/100 ({suspect['risk_level']})")
        else:
            fail(f"analysis returned {resp.status_code}: {resp.text[:200]}")
    except requests.RequestException as exc:
        fail(f"analysis service unreachable: {exc}")

    # --- 6. AI ---------------------------------------------------------
    step(6, "Asking the AI assistant")
    try:
        resp = requests.post(
            f"{AI}/chat/ask",
            json={"question": "Who are the top suspects in this network?", "case_id": case_id},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            answer = resp.json()["answer"]
            print(f"  {answer[:300]}")
            if "GEMINI_API_KEY is not set" in answer:
                print("  NOTE: set GEMINI_API_KEY in .env for real answers.")
        else:
            fail(f"AI service returned {resp.status_code}")
    except requests.RequestException as exc:
        fail(f"AI service unreachable: {exc}")

    # --- Result --------------------------------------------------------
    print("\n" + "=" * 60)
    if failures:
        print(f"PIPELINE COMPLETED WITH {len(failures)} PROBLEM(S):")
        for problem in failures:
            print(f"  - {problem}")
        return False
    print("PIPELINE PASSED — every stage produced data.")
    return True


if __name__ == "__main__":
    sys.exit(0 if run_pipeline() else 1)
