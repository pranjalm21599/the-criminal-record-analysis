from app.neo4j_driver import db
from typing import Dict

class CaseBuilder:
    def create_case_node(self, case_data: Dict):
        """
        Creates or updates a Case node.
        """
        query = """
        MERGE (c:Case {case_number: $case_number})
        ON CREATE SET 
            c.title = $title,
            c.status = $status,
            c.description = $description,
            c.created_at = datetime()
        ON MATCH SET c.status = $status
        RETURN c.case_number as case_number
        """
        return db.execute_query(query, {
            "case_number": case_data.get('case_number'),
            "title": case_data.get('title', ''),
            "status": case_data.get('status', 'open'),
            "description": case_data.get('description', '')
        })

    def create_fir_node(self, fir_data: Dict):
        """
        Creates or updates an FIR node and links it to a Case if case_number is provided.
        """
        query = """
        MERGE (f:FIR {fir_number: $fir_number})
        ON CREATE SET
            f.police_station = $police_station,
            f.date_filed = $date_filed,
            f.offense_type = $offense_type,
            f.ipc_sections = $ipc_sections,
            f.created_at = datetime()
        RETURN f.fir_number as fir_number
        """
        res = db.execute_query(query, {
            "fir_number": fir_data.get('fir_number', ''),
            "police_station": fir_data.get('police_station', ''),
            "date_filed": fir_data.get('date_filed', ''),
            "offense_type": fir_data.get('offense_type', ''),
            "ipc_sections": fir_data.get('ipc_sections', [])
        })

        if fir_data.get('case_number'):
            link_query = """
            MATCH (f:FIR {fir_number: $fir_number})
            MATCH (c:Case {case_number: $case_number})
            MERGE (f)-[:RELATED_TO]->(c)
            """
            db.execute_query(link_query, {
                "fir_number": fir_data.get('fir_number'),
                "case_number": fir_data.get('case_number')
            })
        return res

    def create_financial_edge(self, from_account: str, to_account: str, 
                               amount: float, date: str):
        """
        Creates BankAccount nodes and a TRANSFERRED_TO transaction edge between them.
        """
        query = """
        MERGE (a1:BankAccount {account_number: $from_account})
        MERGE (a2:BankAccount {account_number: $to_account})
        CREATE (a1)-[r:TRANSFERRED_TO {amount: $amount, date: $date}]->(a2)
        RETURN a1.account_number as from_acc, a2.account_number as to_acc, r.amount as amount
        """
        return db.execute_query(query, {
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "date": date
        })