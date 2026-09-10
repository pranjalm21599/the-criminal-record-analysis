import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

print(f"Testing connection to: {uri} ...")

try:
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        print("\n>>> SUCCESS: Successfully connected to your Neo4j Cloud Database! <<<")
except Exception as e:
    print("\n>>> FAILED to connect: <<<")
    print(e)