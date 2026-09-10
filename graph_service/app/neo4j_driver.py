import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

class Neo4jDriver:
    _instance = None

    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Neo4jDriver()
        return cls._instance

    def execute_query(self, query: str, params: dict = None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    def close(self):
        self.driver.close()

# Global reusable instance
db = Neo4jDriver.get_instance()