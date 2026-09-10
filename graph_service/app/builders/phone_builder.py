from app.neo4j_driver import db
from typing import List, Dict

class PhoneBuilder:
    def create_phone_node(self, phone_number: str, owner_name: str = None) -> bool:
        """
        MERGE phone node and link to its owner if owner_name is provided.
        """
        query = """
        MERGE (ph:Phone {number: $number})
        ON CREATE SET ph.created_at = datetime()
        RETURN ph.number
        """
        db.execute_query(query, {"number": phone_number})

        if owner_name:
            link_query = """
            MATCH (p:Person {name: $person_name})
            MATCH (ph:Phone {number: $number})
            MERGE (p)-[r:USES_PHONE]->(ph)
            ON CREATE SET r.created_at = datetime()
            """
            db.execute_query(link_query, {
                "person_name": owner_name,
                "number": phone_number
            })
        return True

    def create_call_relationship(self, caller: str, receiver: str, 
                                  call_count: int = 1, total_duration: int = 0):
        """
        Creates or updates: (Phone)-[:CALLED]->(Phone)
        Accumulates call count and duration if record already exists.
        """
        query = """
        MERGE (p1:Phone {number: $caller})
        MERGE (p2:Phone {number: $receiver})
        MERGE (p1)-[r:CALLED]->(p2)
        ON CREATE SET r.call_count = $call_count, 
                      r.total_duration = $total_duration,
                      r.created_at = datetime()
        ON MATCH SET r.call_count = r.call_count + $call_count,
                     r.total_duration = r.total_duration + $total_duration
        RETURN p1.number, p2.number, r.call_count as count
        """
        return db.execute_query(query, {
            "caller": caller,
            "receiver": receiver,
            "call_count": call_count,
            "total_duration": total_duration
        })