from app.neo4j_driver import db
import networkx as nx


def load_person_network():
    query = """
    MATCH (p:Person)
    OPTIONAL MATCH (p)-[r]-(connected:Person)
    RETURN
        p.name AS person,
        connected.name AS connected_person,
        type(r) AS relationship
    """

    records = db.execute_query(query)

    graph = nx.DiGraph()

    for record in records:
        person = record["person"]
        connected = record["connected_person"]

        # Add every Person, including isolated persons
        if person:
            graph.add_node(person)

        if connected:
            graph.add_node(connected)

            graph.add_edge(
                person,
                connected,
                relationship=record["relationship"]
            )

    return graph