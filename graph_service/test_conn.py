import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# Same defaults as app/neo4j_driver.py, so this reports on the connection the
# service would actually make rather than printing "None" when there is no .env.
uri = os.getenv("NEO4J_URI") or "bolt://localhost:7687"
user = os.getenv("NEO4J_USER") or "neo4j"
password = os.getenv("NEO4J_PASSWORD") or "criminal123"

print(f"Testing connection to: {uri} ...")

try:
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        print("\n>>> SUCCESS: Successfully connected to your Neo4j Cloud Database! <<<")
except Exception as e:
    print("\n>>> FAILED to connect: <<<")
    print(e)