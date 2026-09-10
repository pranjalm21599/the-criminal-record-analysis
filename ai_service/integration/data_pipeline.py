"""
End-to-end pipeline smoke test:
Upload FIR -> NLP extracts entities -> Graph builds -> Analysis runs -> AI answers

Run this: python integration/data_pipeline.py
"""
import requests

BASE_BACKEND = "http://localhost:8000"
BASE_NLP = "http://localhost:8001"
BASE_GRAPH = "http://localhost:8002"
BASE_ANALYSIS = "http://localhost:8003"
BASE_AI = "http://localhost:8004"

SAMPLE_FIR_TEXT = """
FIRST INFORMATION REPORT
FIR No: 001/2024 | Date: 15-03-2024
Police Station: Andheri West, Mumbai

Accused: Ravi Kumar (Ph: 9876543210), Mohammad Ali (Vehicle: MH01AB1234)
Victim: Suresh Sharma (Ph: 9000011111)
Crime: Robbery, IPC Section 394, 34

On 14/03/2024, accused persons Ravi Kumar and Mohammad Ali robbed victim
Suresh Sharma of Rs. 2,50,000 cash near Station Road, Andheri.
"""


def run_pipeline():
    print("Running end-to-end data pipeline test\n")

    print("Step 1: Creating case...")
    case_resp = requests.post(f"{BASE_BACKEND}/cases/", json={
        "case_number": "CASE-TEST-001",
        "title": "Test Drug Network Case",
        "status": "under_investigation",
    })
    case_id = case_resp.json().get("id", 1) if case_resp.status_code in (200, 201, 422) else 1
    print(f"  Case ID: {case_id} (status {case_resp.status_code})")

    print("\nStep 2: Running NLP extraction...")
    nlp_resp = requests.post(f"{BASE_NLP}/extract/text", json={
        "text": SAMPLE_FIR_TEXT,
        "document_type": "fir",
    })
    if nlp_resp.status_code != 200:
        print(f"  FAILED: NLP extraction returned {nlp_resp.status_code}")
        return
    entities = nlp_resp.json()
    print(f"  Persons found: {len(entities.get('named_entities', {}).get('persons', []))}")
    print(f"  Phones found: {len(entities.get('pattern_entities', {}).get('phone', []))}")

    print("\nStep 3: Building knowledge graph...")
    graph_resp = requests.post(
        f"{BASE_GRAPH}/graph/build/from-extraction",
        json=entities.get("named_entities", {}),
    )
    print(f"  Graph service responded {graph_resp.status_code}")

    print("\nStep 4: Running network analysis...")
    analysis_resp = requests.post(f"{BASE_ANALYSIS}/analysis/run-full-analysis")
    print(f"  Analysis service responded {analysis_resp.status_code}")

    print("\nStep 5: Asking the AI assistant...")
    ai_resp = requests.post(f"{BASE_AI}/chat/ask", json={
        "question": "Who are the top suspects in the network?",
        "case_id": case_id,
    })
    if ai_resp.status_code == 200:
        answer = ai_resp.json()
        print(f"  AI answer: {answer['answer'][:200]}...")
    else:
        print(f"  FAILED: AI service returned {ai_resp.status_code}")

    print("\nPipeline test complete.")


if __name__ == "__main__":
    run_pipeline()
