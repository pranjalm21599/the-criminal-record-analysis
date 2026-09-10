from app.neo4j_driver import db
from typing import List, Dict

class NetworkAnalytics:
    def get_degree_centrality(self, limit: int = 15) -> List[Dict]:
        query = """
        MATCH (p:Person)
        OPTIONAL MATCH (p)-[r]-(connected)
        WITH p, count(r) AS total_connections, collect(distinct type(r)) AS relationship_types
        RETURN p.name AS suspect, 
               p.role AS assigned_role, 
               total_connections, 
               relationship_types
        ORDER BY total_connections DESC
        LIMIT $limit
        """
        return db.execute_query(query, {"limit": limit})

    def trace_money_trail(self, start_account: str = "CH-SWISS-909") -> List[Dict]:
        query = """
        MATCH path = (source:BankAccount {account_number: $start_account})-[:TRANSFERRED_TO*1..4]->(dest:BankAccount)
        WITH nodes(path) AS accounts, relationships(path) AS transfers
        RETURN [a in accounts | {account: a.account_number, bank: a.bank_name, country: a.country, city: a.city}] AS account_chain,
               [t in transfers | {amount: t.amount, date: t.date, memo: t.memo}] AS transfer_chain
        """
        return db.execute_query(query, {"start_account": start_account})

    def detect_kingpin_candidates(self) -> List[Dict]:
        query = """
        MATCH (k:Person)
        WHERE EXISTS { (k)-[:COMMANDS]->(:Person) }
           OR EXISTS { (k)-[:OWNS_ACCOUNT]->(:BankAccount)-[:TRANSFERRED_TO]->() }
        OPTIONAL MATCH (k)-[:COMMANDS]->(subordinate:Person)
        OPTIONAL MATCH (k)-[:OWNS_ACCOUNT]->(acc:BankAccount)-[tx:TRANSFERRED_TO]->(recipientAcc:BankAccount)<-[:OWNS_ACCOUNT]-(recipientPerson:Person)
        RETURN k.name AS candidate_name,
               k.role AS role,
               k.risk_score AS risk_score,
               collect(DISTINCT subordinate.name) AS direct_subordinates,
               collect(DISTINCT recipientPerson.name) AS direct_payees
        """
        return db.execute_query(query)

    def detect_critical_bridge(self) -> List[Dict]:
        """
        Identifies bottleneck / broker nodes that bridge low-level field mules
        to high-level leadership and bank accounts.
        """
        query = """
        MATCH (p:Person)
        MATCH (p)-[]-(n1), (p)-[]-(n2)
        WHERE elementId(n1) < elementId(n2) 
          AND NOT (n1)-[]-(n2)
        WITH p, count(DISTINCT [n1, n2]) AS broker_score
        RETURN p.name AS person, 
               p.role AS role, 
               broker_score
        ORDER BY broker_score DESC
        LIMIT 3
        """
        return db.execute_query(query)