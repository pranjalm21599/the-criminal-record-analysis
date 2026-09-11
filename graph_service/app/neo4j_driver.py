import os

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.time import Date, DateTime, Duration, Time

load_dotenv()


def _jsonable(value):
    """
    Convert Neo4j temporal values into ISO strings.

    Left alone, FastAPI serialises a Neo4j DateTime by reflecting over its
    private fields, so a created_at comes back as a nested blob of
    _DateTime__date / _Time__ticks objects instead of a timestamp. Anything
    consuming these properties — the dashboard, the AI service — gets that
    noise, so it is normalised once here rather than in every route.
    """
    if isinstance(value, (DateTime, Date, Time)):
        return value.iso_format()
    if isinstance(value, Duration):
        return str(value)
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value

# Defaults match docker-compose so the service starts even with no .env file.
NEO4J_URI = os.getenv("NEO4J_URI") or "bolt://localhost:7687"
NEO4J_USER = os.getenv("NEO4J_USER") or "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or "criminal123"


class Neo4jDriver:
    """
    Thin wrapper around the Neo4j driver.

    The connection is created lazily on first query rather than at import
    time — otherwise the whole FastAPI app fails to import when Neo4j isn't
    up yet, which is exactly what happens when Docker starts the services in
    parallel.
    """

    _instance = None

    def __init__(self):
        self._driver = None

    @classmethod
    def get_instance(cls) -> "Neo4jDriver":
        if cls._instance is None:
            cls._instance = Neo4jDriver()
        return cls._instance

    @property
    def driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
        return self._driver

    def execute_query(self, query: str, params: dict = None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [_jsonable(record.data()) for record in result]

    def verify(self) -> bool:
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None


# Global reusable instance
db = Neo4jDriver.get_instance()
