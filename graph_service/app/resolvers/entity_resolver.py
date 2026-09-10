from app.neo4j_driver import db
from typing import Dict, List

class EntityResolver:
    def link_co_accused(self, fir_number: str, person_names: List[str]):
        """
        Links multiple persons to an FIR and creates CO_ACCUSED 
        relationships between all suspects on that same case.
        """
        query = """
        MATCH (f:FIR {fir_number: $fir_number})
        UNWIND $names AS name
        MERGE (p:Person {name: name})
        MERGE (p)-[:CHARGED_IN]->(f)
        """
        db.execute_query(query, {"fir_number": fir_number, "names": person_names})

        cross_link_query = """
        MATCH (p1:Person)-[:CHARGED_IN]->(f:FIR {fir_number: $fir_number})<-[:CHARGED_IN]-(p2:Person)
        WHERE elementId(p1) < elementId(p2)
        MERGE (p1)-[r:CO_ACCUSED_WITH {case: $fir_number}]->(p2)
        RETURN p1.name as suspect1, p2.name as suspect2
        """
        return db.execute_query(cross_link_query, {"fir_number": fir_number})

    def detect_shared_identifiers(self):
        """
        Detects distinct people who are linked to the exact same phone number.
        """
        query = """
        MATCH (p1:Person)-[:USES_PHONE]->(ph:Phone)<-[:USES_PHONE]-(p2:Person)
        WHERE elementId(p1) < elementId(p2)
        RETURN p1.name AS person_1, p2.name AS person_2, ph.number AS shared_phone
        """
        return db.execute_query(query)

    def get_person_network(self, person_name: str, depth: int = 2):
        """
        Traverses outwards up to 'depth' hops to extract the full 
        subgraph for visual analysis on the frontend.
        """
        query = f"""
        MATCH path = (p:Person {{name: $name}})-[*1..{depth}]-(target)
        RETURN [n in nodes(path) | {{id: elementId(n), labels: labels(n), props: properties(n)}}] AS nodes,
               [r in relationships(path) | {{type: type(r), from: elementId(startNode(r)), to: elementId(endNode(r)), props: properties(r)}}] AS relationships
        LIMIT 100
        """
        return db.execute_query(query, {"name": person_name})

    def find_connection_path(self, start_name: str, end_name: str):
        """
        Finds the shortest link between any two people through 
        phones, cases, associates, or accounts.
        """
        query = """
        MATCH (p1:Person {name: $start_name}), (p2:Person {name: $end_name})
        MATCH path = shortestPath((p1)-[*]-(p2))
        RETURN [n in nodes(path) | coalesce(n.name, n.number, n.fir_number, n.account_number)] AS chain,
               [r in relationships(path) | type(r)] AS link_types
        """
        return db.execute_query(query, {"start_name": start_name, "end_name": end_name})