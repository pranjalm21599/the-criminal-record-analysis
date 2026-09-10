from app.neo4j_driver import db
from app.analyzers.centrality import calculate_centrality


def calculate_risk_scores():
    centrality_data = calculate_centrality()

    query = """
    MATCH (p:Person)
    OPTIONAL MATCH (p)-[:ASSOCIATED_WITH]-(connected:Person)
    WITH p, count(connected) AS connections
    RETURN
        p.name AS person,
        connections
    """

    records = db.execute_query(query)

    connection_map = {
        record["person"]: record["connections"]
        for record in records
    }

    results = []

    for item in centrality_data["results"]:
        person = item["person"]

        degree_score = item["degree"] * 25
        betweenness_score = item["betweenness"] * 30
        pagerank_score = item["pagerank"] * 30
        connection_score = min(
            connection_map.get(person, 0) * 5,
            15
        )

        risk_score = (
            degree_score
            + betweenness_score
            + pagerank_score
            + connection_score
        )

        risk_score = min(round(risk_score, 2), 100)

        if risk_score >= 70:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        results.append({
            "person": person,
            "risk_score": risk_score,
            "risk_level": risk_level
        })

    results.sort(
        key=lambda x: x["risk_score"],
        reverse=True
    )

    return {
        "total_persons": len(results),
        "results": results
    }


def get_person_risk(person_name):
    data = calculate_risk_scores()

    for person in data["results"]:
        if person["person"].lower() == person_name.lower():
            return person

    return {
        "person": person_name,
        "risk_score": 0,
        "risk_level": "UNKNOWN"
    }