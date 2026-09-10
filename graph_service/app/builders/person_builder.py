from app.neo4j_driver import db
from typing import Dict
import uuid

class PersonBuilder:
    def create_or_update_person(self, person_data: Dict) -> str:
        """
        MERGE finds the person or creates them if they don't exist.
        Returns the person's unique ID.
        """
        person_id = person_data.get('id') or str(uuid.uuid4())

        query = """
        MERGE (p:Person {name: $name})
        ON CREATE SET 
            p.id = $id,
            p.aliases = $aliases,
            p.role = $role,
            p.phone_numbers = $phones,
            p.created_at = datetime()
        ON MATCH SET
            p.aliases = $aliases,
            p.role = CASE WHEN $role <> 'unknown' THEN $role ELSE p.role END,
            p.updated_at = datetime()
        RETURN p.id as id, p.name as name
        """

        db.execute_query(query, {
            "id": person_id,
            "name": person_data.get('name', '').strip(),
            "aliases": person_data.get('aliases', []),
            "role": person_data.get('role', 'unknown'),
            "phones": person_data.get('phone_numbers', [])
        })

        return person_id

    def link_persons_as_associates(self, person1: str, person2: str, context: str = ""):
        """
        Creates relationship: (Person1)-[:ASSOCIATED_WITH]->(Person2)
        """
        query = """
        MATCH (p1:Person {name: $person1})
        MATCH (p2:Person {name: $person2})
        MERGE (p1)-[r:ASSOCIATED_WITH]->(p2)
        ON CREATE SET r.context = $context, r.created_at = datetime()
        RETURN p1.name, p2.name
        """
        return db.execute_query(query, {
            "person1": person1,
            "person2": person2,
            "context": context
        })