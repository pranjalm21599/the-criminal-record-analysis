from app.neo4j_driver import db

def seed_database():
    print("Clearing and populating rich syndicate data...")
    
    # Clear existing test nodes to ensure a fresh demo slate
    clear_query = "MATCH (n) DETACH DELETE n"
    db.execute_query(clear_query)

    cypher_script = """
    // 1. Create Persons & Roles
    MERGE (k:Person {id: "P001", name: "Vikram Sethi", role: "Kingpin", risk_score: 98})
    MERGE (l1:Person {id: "P002", name: "Sameer Khan", role: "Lieutenant / Handler", risk_score: 85})
    MERGE (l2:Person {id: "P003", name: "Anita Roy", role: "Accountant / Hawala Broker", risk_score: 75})
    MERGE (f1:Person {id: "P004", name: "Ravi Kumar", role: "Courier / Mule", risk_score: 55})
    MERGE (f2:Person {id: "P005", name: "Vikas Sharma", role: "Courier / Mule", risk_score: 60})
    MERGE (f3:Person {id: "P006", name: "Amit Verma", role: "Logistics", risk_score: 50})
    MERGE (f4:Person {id: "P007", name: "Pooja Das", role: "Associate", risk_score: 40})

    // 2. Associates / Hierarchy
    MERGE (k)-[:COMMANDS]->(l1)
    MERGE (k)-[:COMMANDS]->(l2)
    MERGE (l1)-[:COORDINATES]->(f1)
    MERGE (l1)-[:COORDINATES]->(f2)
    MERGE (l1)-[:COORDINATES]->(f3)
    MERGE (f1)-[:ASSOCIATED_WITH {context: "Frequent meetings in Andheri"}]->(f2)
    MERGE (f2)-[:ASSOCIATED_WITH {context: "Childhood associates"}]->(f3)

    // 3. Phones and Usages
    MERGE (ph_k:Phone {number: "+91-99999-00001", type: "Encrypted Satellite"})
    MERGE (ph_l1:Phone {number: "+91-98888-11111", type: "Smart Phone"})
    MERGE (ph_l2:Phone {number: "+91-97777-22222", type: "Smart Phone"})
    MERGE (ph_f1:Phone {number: "+91-96666-33333", type: "Burner"})
    MERGE (ph_f2:Phone {number: "+91-95555-44444", type: "Burner"})
    MERGE (ph_shared:Phone {number: "+91-90000-88888", type: "Shared Burner (Safehouse)"})

    MERGE (k)-[:USES_PHONE]->(ph_k)
    MERGE (l1)-[:USES_PHONE]->(ph_l1)
    MERGE (l2)-[:USES_PHONE]->(ph_l2)
    MERGE (f1)-[:USES_PHONE]->(ph_f1)
    MERGE (f2)-[:USES_PHONE]->(ph_f2)
    
    // Shared burner phone - creates an entity resolution red flag
    MERGE (f1)-[:USES_PHONE]->(ph_shared)
    MERGE (f2)-[:USES_PHONE]->(ph_shared)

    // 4. Call Detail Records (CDRs)
    MERGE (ph_k)-[:CALLED {call_count: 14, total_duration: 1800}]->(ph_l1)
    MERGE (ph_k)-[:CALLED {call_count: 8, total_duration: 920}]->(ph_l2)
    MERGE (ph_l1)-[:CALLED {call_count: 42, total_duration: 5400}]->(ph_f1)
    MERGE (ph_l1)-[:CALLED {call_count: 38, total_duration: 4900}]->(ph_f2)
    MERGE (ph_l1)-[:CALLED {call_count: 21, total_duration: 2100}]->(ph_f3)
    MERGE (ph_f1)-[:CALLED {call_count: 15, total_duration: 800}]->(ph_f2)

    // 5. Bank Accounts & Hawala Money Trail
    MERGE (b_k:BankAccount {account_number: "CH-SWISS-909", bank_name: "Offshore Vault", country: "Switzerland"})
    MERGE (b_l2:BankAccount {account_number: "HDFC-404011", bank_name: "HDFC Bank", city: "Mumbai"})
    MERGE (b_mule1:BankAccount {account_number: "SBI-881920", bank_name: "State Bank of India", city: "Delhi"})
    MERGE (b_mule2:BankAccount {account_number: "ICICI-110293", bank_name: "ICICI Bank", city: "Lucknow"})

    MERGE (k)-[:OWNS_ACCOUNT]->(b_k)
    MERGE (l2)-[:OWNS_ACCOUNT]->(b_l2)
    MERGE (f1)-[:OWNS_ACCOUNT]->(b_mule1)
    MERGE (f2)-[:OWNS_ACCOUNT]->(b_mule2)

    MERGE (b_k)-[:TRANSFERRED_TO {amount: 2500000.0, date: "2026-03-01", memo: "Consulting"}]->(b_l2)
    MERGE (b_l2)-[:TRANSFERRED_TO {amount: 450000.0, date: "2026-03-03", memo: "Cash split"}]->(b_mule1)
    MERGE (b_l2)-[:TRANSFERRED_TO {amount: 420000.0, date: "2026-03-03", memo: "Cash split"}]->(b_mule2)

    // 6. FIRs & Legal Cases
    MERGE (c1:Case {case_number: "CR-2026-440", title: "Cross-State Gold Smuggling Ring", status: "Active"})
    MERGE (fir1:FIR {fir_number: "FIR-2026-089", police_station: "Marine Drive", offense_type: "Smuggling & Money Laundering"})
    MERGE (fir2:FIR {fir_number: "FIR-2026-104", police_station: "Andheri West", offense_type: "Illegal Possession & Arms"})

    MERGE (fir1)-[:RELATED_TO]->(c1)
    MERGE (fir2)-[:RELATED_TO]->(c1)

    MERGE (f1)-[:CHARGED_IN]->(fir1)
    MERGE (f2)-[:CHARGED_IN]->(fir1)
    MERGE (l1)-[:CHARGED_IN]->(fir1)
    MERGE (f1)-[:CO_ACCUSED_WITH {case: "FIR-2026-089"}]->(f2)
    MERGE (f2)-[:CO_ACCUSED_WITH {case: "FIR-2026-089"}]->(l1)

    MERGE (f3)-[:CHARGED_IN]->(fir2)
    MERGE (f1)-[:CHARGED_IN]->(fir2)
    MERGE (f3)-[:CO_ACCUSED_WITH {case: "FIR-2026-104"}]->(f1)
    """

    db.execute_query(cypher_script)
    print("\n>>> SUCCESS: Crime syndicate dataset successfully injected into Neo4j! <<<")

if __name__ == "__main__":
    seed_database()