"""
Turns uploaded files into text / rows.

PDF support is optional: if pypdf isn't installed the service still runs and
reports a clear message instead of crashing on import.
"""
import csv
import io
from typing import List

try:
    from pypdf import PdfReader

    _HAS_PDF = True
except ImportError:  # pragma: no cover - depends on optional install
    _HAS_PDF = False


def extract_text(filename: str, content: bytes) -> str:
    """Best-effort text extraction from a PDF or plain-text upload."""
    name = filename.lower()

    if name.endswith(".pdf"):
        if not _HAS_PDF:
            raise ValueError("PDF support requires the 'pypdf' package. Upload a .txt file instead.")
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    # .txt, .md, and anything else we can decode
    return content.decode("utf-8", errors="replace").strip()


def _pick(row: dict, *candidates: str) -> str:
    """
    Read a value from a CSV row by trying several likely column names.

    Real CDR/bank exports never agree on headers ("caller" vs "a_party" vs
    "from"), so accept the common spellings rather than forcing one format.
    """
    normalized = {(k or "").strip().lower().replace(" ", "_"): (v or "") for k, v in row.items()}
    for candidate in candidates:
        value = normalized.get(candidate, "").strip()
        if value:
            return value
    return ""


def parse_call_records(content: bytes) -> List[dict]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8", errors="replace")))
    rows = []
    for row in reader:
        caller = _pick(row, "caller", "from", "a_party", "calling_number", "source")
        receiver = _pick(row, "receiver", "to", "b_party", "called_number", "destination")
        if not caller or not receiver:
            continue

        duration_raw = _pick(row, "duration", "duration_sec", "call_duration", "seconds")
        try:
            duration = int(float(duration_raw)) if duration_raw else 0
        except ValueError:
            duration = 0

        rows.append({
            "caller": caller,
            "receiver": receiver,
            "duration": duration,
            "call_time": _pick(row, "timestamp", "call_time", "datetime", "date", "time"),
            "tower_location": _pick(row, "tower_location", "tower", "cell_site", "location"),
        })
    return rows


def parse_transactions(content: bytes) -> List[dict]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8", errors="replace")))
    rows = []
    for row in reader:
        from_account = _pick(row, "from_account", "from", "sender", "debit_account", "source_account")
        to_account = _pick(row, "to_account", "to", "receiver", "credit_account", "destination_account")
        if not from_account or not to_account:
            continue

        amount_raw = _pick(row, "amount", "value", "txn_amount", "transaction_amount")
        try:
            amount = float(amount_raw.replace(",", "").replace("₹", "")) if amount_raw else 0.0
        except ValueError:
            amount = 0.0

        rows.append({
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "date": _pick(row, "date", "txn_date", "timestamp", "transaction_date"),
            "memo": _pick(row, "memo", "description", "narration", "remarks"),
        })
    return rows
