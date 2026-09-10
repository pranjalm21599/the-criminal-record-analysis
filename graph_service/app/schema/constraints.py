from app.neo4j_driver import db

def create_constraints():
    """
    Create uniqueness constraints and indexes.
    These ensure MERGE queries run quickly without duplicates.
    """
    constraints = [
        # Uniqueness constraints
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (ph:Phone) REQUIRE ph.number IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (v:Vehicle) REQUIRE v.plate_number IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (b:BankAccount) REQUIRE b.account_number IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Case) REQUIRE c.case_number IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (f:FIR) REQUIRE f.fir_number IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE",

        # Search indexes
        "CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.name)",
        "CREATE INDEX IF NOT EXISTS FOR (ph:Phone) ON (ph.number)",
    ]

    for query in constraints:
        try:
            db.execute_query(query)
            print(f"Created: {query[:50]}...")
        except Exception as e:
            print(f"Skipped / Failed: {e}")

if __name__ == "__main__":
    create_constraints()
    print("\nSchema setup complete!")