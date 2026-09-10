"""
Fetches relevant facts from the Knowledge Graph service (Member 3, port 8002).

Uses httpx.AsyncClient instead of `requests` so calls don't block FastAPI's
event loop — matters once more than one investigator is querying the chat
at the same time (e.g. during the live demo Q&A).
"""
import httpx

from app.config import settings


class GraphRetriever:
    def __init__(self):
        self.base_url = settings.GRAPH_API
        self.timeout = settings.REQUEST_TIMEOUT

    async def get_person_facts(self, person_name: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/graph/person/{person_name}/network",
                    params={"depth": 2},
                )
            if resp.status_code != 200:
                return ""

            data = resp.json()
            nodes = data.get("nodes", [])
            edges = data.get("edges", [])

            facts = [
                f"Facts about {person_name}:",
                f"- Connected to {data.get('total_nodes', 0)} entities",
                f"- Has {data.get('total_edges', 0)} relationships",
            ]

            type_counts: dict[str, int] = {}
            for node in nodes:
                ntype = node.get("type", "Unknown")
                if ntype != "Person":
                    type_counts[ntype] = type_counts.get(ntype, 0) + 1
            for ntype, count in type_counts.items():
                facts.append(f"- Connected to {count} {ntype}(s)")

            for edge in edges[:10]:
                facts.append(
                    f"- {edge.get('source')} --[{edge.get('type')}]--> {edge.get('target')}"
                )

            return "\n".join(facts)
        except Exception:
            return f"Could not retrieve graph data for {person_name}."

    async def find_path_between(self, person1: str, person2: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/graph/shortest-path",
                    params={"person1": person1, "person2": person2},
                )
            if resp.status_code != 200:
                return ""

            data = resp.json()
            if data.get("path_found"):
                path = " → ".join(data.get("path_nodes", []))
                degrees = data.get("degrees_of_separation", 0)
                return f"Connection: {path}\nDegrees of separation: {degrees}"
            return f"No direct connection found between {person1} and {person2}."
        except Exception:
            return "Could not check connection path."

    async def search_entities(self, query: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.base_url}/graph/search", params={"q": query})
            if resp.status_code != 200:
                return ""

            results = resp.json().get("results", [])
            if not results:
                return f"No entities found matching '{query}'."

            lines = [f"Found {len(results)} result(s) for '{query}':"]
            for r in results[:5]:
                lines.append(f"- [{r.get('type')}] {r.get('name')}")
            return "\n".join(lines)
        except Exception:
            return f"Search failed for '{query}'."
