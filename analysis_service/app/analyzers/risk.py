"""
Risk scoring — the 0-100 number the dashboard sorts its suspect table by.

Every component is explainable on purpose. An investigator has to be able to
ask "why is this person 75?" and get a real answer, so each score ships with
the factors that produced it rather than an opaque model output.

Weights (sum to 100):
    35  network position (centrality)
    25  criminal record (FIRs / charges in the graph)
    20  flagged financial activity
    20  suspicious communication patterns
"""
from typing import Dict, List

import networkx as nx

WEIGHT_NETWORK = 35
WEIGHT_RECORD = 25
WEIGHT_FINANCIAL = 20
WEIGHT_COMMUNICATION = 20


def _risk_level(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


def _normalize(value: float, maximum: float) -> float:
    if maximum <= 0:
        return 0.0
    return min(value / maximum, 1.0)


# Being named in an FIR as the complainant or a witness is not evidence of
# criminality. Without this, a victim who reported a large robbery outranks
# the accused, purely because they are well connected to the case.
_ROLE_MULTIPLIERS = {
    "victim": 0.15,
    "complainant": 0.15,
    "witness": 0.2,
}


def _role_multiplier(role: str | None) -> float:
    if not role:
        return 1.0
    return _ROLE_MULTIPLIERS.get(str(role).strip().lower(), 1.0)


def score_all(
    graph: nx.MultiDiGraph,
    projected: nx.Graph,
    names: Dict[str, str],
    centrality_rows: List[Dict],
    transaction_anomalies: List[Dict],
    call_anomalies: List[Dict],
) -> List[Dict]:
    if projected.number_of_nodes() == 0:
        return []

    centrality_by_name = {row["person"]: row for row in centrality_rows}

    # Count how many FIR/Case nodes each person is attached to in the graph.
    undirected = graph.to_undirected(as_view=True)
    charge_counts: Dict[str, int] = {}
    phones_by_person: Dict[str, set] = {}
    accounts_by_person: Dict[str, set] = {}

    for node in projected.nodes:
        name = names.get(node, "Unknown")
        charges, phones, accounts = 0, set(), set()
        for neighbor in undirected.neighbors(node):
            label = graph.nodes[neighbor].get("label")
            if label in ("FIR", "Case"):
                charges += 1
            elif label == "Phone":
                phones.add(graph.nodes[neighbor].get("name"))
            elif label == "BankAccount":
                accounts.add(graph.nodes[neighbor].get("name"))
        charge_counts[name] = charges
        phones_by_person[name] = phones
        accounts_by_person[name] = accounts

    max_charges = max(charge_counts.values(), default=0)

    # Map flagged activity back to people via their accounts and phone numbers.
    flagged_accounts: Dict[str, int] = {}
    for anomaly in transaction_anomalies:
        for account in (anomaly.get("from_account"), anomaly.get("to_account")):
            if account:
                flagged_accounts[account] = flagged_accounts.get(account, 0) + 1

    flagged_phones: Dict[str, int] = {}
    for anomaly in call_anomalies:
        for phone in (anomaly.get("caller"), anomaly.get("receiver")):
            if phone:
                flagged_phones[phone] = flagged_phones.get(phone, 0) + 1

    results = []
    for node in projected.nodes:
        name = names.get(node, "Unknown")
        centrality = centrality_by_name.get(name, {})
        factors: List[str] = []

        # --- network position ---
        degree_c = centrality.get("degree_centrality", 0.0)
        between_c = centrality.get("betweenness_centrality", 0.0)
        network_component = WEIGHT_NETWORK * min(degree_c * 0.6 + between_c * 0.4, 1.0)
        if degree_c > 0.5:
            factors.append(f"Highly connected (degree centrality {degree_c})")
        if between_c > 0.2:
            factors.append(f"Acts as a broker between groups (betweenness {between_c})")

        # --- criminal record ---
        charges = charge_counts.get(name, 0)
        record_component = WEIGHT_RECORD * _normalize(charges, max(max_charges, 1))
        if charges:
            factors.append(f"Linked to {charges} case/FIR record(s)")

        # --- financial ---
        financial_hits = sum(
            flagged_accounts.get(account, 0) for account in accounts_by_person.get(name, set()) if account
        )
        financial_component = WEIGHT_FINANCIAL * _normalize(financial_hits, 3)
        if financial_hits:
            factors.append(f"{financial_hits} flagged transaction(s) on linked accounts")

        # --- communication ---
        comm_hits = sum(
            flagged_phones.get(phone, 0) for phone in phones_by_person.get(name, set()) if phone
        )
        comm_component = WEIGHT_COMMUNICATION * _normalize(comm_hits, 3)
        if comm_hits:
            factors.append(f"{comm_hits} suspicious calling pattern(s)")

        # A shared phone is a strong signal on its own — two people on one
        # handset is either a burner or an alias.
        shared_phone = False
        for phone_node in undirected.neighbors(node):
            if graph.nodes[phone_node].get("label") == "Phone":
                phone_users = [
                    p for p in undirected.neighbors(phone_node)
                    if graph.nodes[p].get("label") == "Person"
                ]
                if len(phone_users) > 1:
                    shared_phone = True
        if shared_phone:
            factors.append("Shares a phone number with another suspect")

        total = network_component + record_component + financial_component + comm_component
        if shared_phone:
            total = min(total + 8, 100)

        role = graph.nodes[node].get("role")
        multiplier = _role_multiplier(role)
        if multiplier < 1.0:
            total *= multiplier
            factors.append(f"Recorded as {role} — not a suspect; score reduced accordingly")

        score = round(min(total, 100), 1)
        results.append({
            "person": name,
            "role": role or "suspect",
            "risk_score": score,
            "risk_level": _risk_level(score),
            "factors": factors or ["No aggravating factors identified"],
            "breakdown": {
                "network_position": round(network_component, 1),
                "criminal_record": round(record_component, 1),
                "financial_activity": round(financial_component, 1),
                "communication_patterns": round(comm_component, 1),
            },
            "direct_connections": centrality.get("direct_connections", projected.degree(node)),
        })

    results.sort(key=lambda r: r["risk_score"], reverse=True)
    return results
