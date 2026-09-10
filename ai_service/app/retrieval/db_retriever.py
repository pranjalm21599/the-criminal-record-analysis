"""
Fetches structured data from the backend (Member 1, port 8000) and the
analysis service (Member 4, port 8003). Same async-httpx pattern as
graph_retriever.py.
"""
import httpx

from app.config import settings


class DBRetriever:
    def __init__(self):
        self.backend_url = settings.BACKEND_API
        self.analysis_url = settings.ANALYSIS_API
        self.timeout = settings.REQUEST_TIMEOUT

    async def get_case_info(self, case_id: int) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.backend_url}/cases/{case_id}/summary")
            if resp.status_code != 200:
                return f"Case {case_id} data unavailable."

            data = resp.json()
            case = data.get("case", {})
            return "\n".join([
                f"Case: {case.get('title', 'Unknown')}",
                f"Status: {case.get('status', 'Unknown')}",
                f"FIRs: {data.get('total_firs', 0)}",
                f"Call Records: {data.get('total_call_records', 0)}",
                f"Transactions: {data.get('total_transactions', 0)}",
            ])
        except Exception:
            return f"Case {case_id} data unavailable."

    async def get_top_suspects(self) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.analysis_url}/analysis/risk/all")
            if resp.status_code != 200:
                return "Risk scores not available."

            suspects = resp.json().get("top_suspects", [])[:5]
            if not suspects:
                return "Risk scores not available."

            lines = ["Top 5 Suspects by Risk Score:"]
            for s in suspects:
                lines.append(
                    f"- {s['person']}: Score {s['risk_score']}/100 ({s['risk_level']} RISK)"
                )
            return "\n".join(lines)
        except Exception:
            return "Risk scores not available."

    async def get_anomalies(self) -> str:
        context_parts = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.analysis_url}/analysis/anomalies/transactions")
            if resp.status_code == 200:
                suspicious = resp.json().get("suspicious_transactions", [])[:3]
                if suspicious:
                    context_parts.append("Suspicious Transactions:")
                    for t in suspicious:
                        context_parts.append(
                            f"- ₹{t['amount']:,.0f} from {t['from_account']} to "
                            f"{t['to_account']} | Flags: {', '.join(t.get('flags', []))}"
                        )
        except Exception:
            pass

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.analysis_url}/analysis/anomalies/calls")
            if resp.status_code == 200:
                anomalies = resp.json().get("communication_anomalies", [])[:3]
                if anomalies:
                    context_parts.append("Communication Anomalies:")
                    for a in anomalies:
                        context_parts.append(f"- {a.get('description', '')}")
        except Exception:
            pass

        return "\n".join(context_parts) if context_parts else "No anomalies detected."

    async def get_communities(self) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.analysis_url}/analysis/communities")
            if resp.status_code != 200:
                return "Group detection data unavailable."

            communities = resp.json().get("communities", [])
            if not communities:
                return "Group detection data unavailable."

            lines = [f"Detected {len(communities)} criminal group(s):"]
            for c in communities[:5]:
                members = ", ".join(c["members"][:5])
                lines.append(f"- {c['label']} ({c['size']} members): {members}...")
            return "\n".join(lines)
        except Exception:
            return "Group detection data unavailable."
