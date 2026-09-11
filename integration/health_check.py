"""
Pings every service before a demo and reports what's up.

Run from the repo root:  python integration/health_check.py
"""
import sys

import requests

SERVICES = {
    "Backend (M1)": "http://localhost:8000/health",
    "NLP (M2)": "http://localhost:8001/health",
    "Graph (M3)": "http://localhost:8002/health",
    "Analysis (M4)": "http://localhost:8003/health",
    "Frontend (M5)": "http://localhost:5173",
    "AI Chat (M6)": "http://localhost:8004/health",
}


def check_all() -> bool:
    print("Checking all services...\n")
    all_ok = True

    for service, url in SERVICES.items():
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                detail = ""
                # Surface the dependency flags the services report, so a
                # service that is up but cut off from Neo4j doesn't read as
                # a clean pass.
                try:
                    body = resp.json()
                    if body.get("neo4j_connected") is False:
                        detail = "  (WARNING: not connected to Neo4j)"
                        all_ok = False
                except ValueError:
                    pass  # HTML from the frontend, not JSON
                print(f"[OK]   {service}: running at {url}{detail}")
            else:
                print(f"[WARN] {service}: responded with {resp.status_code}")
                all_ok = False
        except requests.ConnectionError:
            print(f"[DOWN] {service}: not reachable at {url}")
            all_ok = False
        except requests.Timeout:
            print(f"[DOWN] {service}: timed out at {url}")
            all_ok = False

    print("\n" + ("ALL SYSTEMS GO" if all_ok else "SOME SERVICES ARE DOWN"))
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if check_all() else 1)
