"""
Upload endpoints. Each one persists the evidence, then drives the rest of
the pipeline (NLP -> graph) so a single drag-and-drop populates the whole
system — which is exactly what the demo walks through.
"""
import os
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.services import file_parser, pipeline

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _save_raw(filename: str, content: bytes) -> str:
    """Keep the original file on disk so evidence is never lost to a parse bug."""
    safe_name = Path(filename).name  # strip any path components from the client
    destination = UPLOAD_DIR / safe_name
    destination.write_bytes(content)
    return str(destination)


_PLATE_RE = re.compile(r"[A-Z]{2}[-\s]?\d{1,2}[-\s]?[A-Z]{1,2}[-\s]?\d{4}", re.IGNORECASE)
_DIGITS_RE = re.compile(r"\d")

# Words that show up inside spaCy PERSON spans on FIR text but never name a
# person — "Vehicle MH01AB1234" and "Maruti Swift" both get tagged PERSON by
# the small English model, and an un-filtered pipeline then ranks a car as a
# suspect on the dashboard.
_NON_PERSON_TOKENS = {
    "vehicle", "car", "motorcycle", "bike", "scooter", "truck", "van",
    "maruti", "swift", "honda", "hyundai", "toyota", "tata", "mahindra",
    "police", "station", "ipc", "section", "fir", "report", "bank",
    "account", "phone", "mobile", "rs", "inr", "pan", "aadhaar",
}


def _is_person_name(
    candidate: str, identifier_veto: set[str], entity_veto: set[str]
) -> bool:
    """
    Filter spaCy's PERSON hits down to things that plausibly name a person.

    The small English model was not trained on Indian police reports, so it
    happily tags vehicles, place names and firms as people. Everything
    downstream — the graph, community detection, the risk table — inherits
    that error, so it gets cleaned up here at the aggregation point.

    Two kinds of veto, deliberately applied differently:
      identifier_veto (plates, phones, accounts) matches as a substring,
        because they turn up inside a larger span like "Vehicle MH01AB1234";
      entity_veto (locations, organisations) must match the whole string,
        since spaCy often labels the same text GPE in one sentence and
        PERSON in another. Substring matching there would wrongly delete a
        real person whose name contains a place name.
    """
    text = candidate.strip()
    if len(text) < 3:
        return False

    # Registration plates and anything carrying digits.
    if _DIGITS_RE.search(text) or _PLATE_RE.search(text):
        return False

    lowered = text.lower()
    if any(token in _NON_PERSON_TOKENS for token in re.split(r"\W+", lowered) if token):
        return False

    if lowered in {other.strip().lower() for other in entity_veto if other}:
        return False

    if any(other and other.lower() in lowered for other in identifier_veto):
        return False

    return True


# Police officers are named in every FIR and are never suspects. Left in, the
# investigating officer turns up in the risk table — which is exactly the kind
# of error that destroys trust in the tool.
_OFFICER_RE = re.compile(
    r"(?:Investigating Officer|Inspector|Sub-?Inspector|Officer|I\.?O\.?|"
    r"ASI|SI|Constable|SHO)\s*:?\s*([A-Z][A-Za-z.]*(?:\s+[A-Z][A-Za-z.]*)*)",
)

# "resident of X", "Police Station: X" — contexts that introduce a place.
_LOCATIVE_LEAD = (
    r"(?:resident of|residing at|situated at|located (?:at|in)|near|"
    r"Police Station|District|in|at|from|of)"
)


_RANK_PREFIX_RE = re.compile(
    r"^(?:Inspector|Sub-?Inspector|ASI|SI|SHO|Constable|Officer|Shri|Smt|Mr|Ms|Mrs|Dr)\.?\s+",
    re.IGNORECASE,
)


def _officer_names(text: str) -> set[str]:
    """
    Officer names, with and without their rank.

    "Investigating Officer: Inspector S. Chauhan" captures the rank too, but
    spaCy reports the person as "S. Chauhan" — so both spellings go into the
    veto set or the exact-match check misses.
    """
    names: set[str] = set()
    for match in _OFFICER_RE.finditer(text):
        raw = match.group(1).strip()
        if not raw:
            continue
        names.add(raw)
        stripped = _RANK_PREFIX_RE.sub("", raw).strip()
        if stripped:
            names.add(stripped)
    return names


def _looks_like_a_place(name: str, text: str) -> bool:
    """
    True when every mention of `name` sits behind a locative cue.

    spaCy's small model tags "Karol Bagh" as a PERSON and, in the same
    document, the actual person "Rakesh Gupta" as a LOCATION — so a
    cross-reference between its own labels cannot fix this. What is reliable
    is the surrounding grammar: a name that is only ever written as "resident
    of X" or "Police Station: X" is a place, whereas a real suspect also
    appears as a bare subject ("Mohammad Ali coordinated...").
    """
    occurrences = len(re.findall(re.escape(name), text))
    if occurrences == 0:
        return False

    locative = len(
        re.findall(rf"{_LOCATIVE_LEAD}\s*:?\s+{re.escape(name)}", text, re.IGNORECASE)
    )
    return locative >= occurrences


def _attribute_to_nearest_person(
    text: str, identifiers: list[str], person_names: list[str], max_distance: int = 200
) -> dict[str, str]:
    """
    Map each identifier (phone, bank account) to the person named closest to
    it in the document.

    FIR narratives introduce identifiers right next to their owner — "Ravi
    Kumar, whose mobile number 9876543210..." — so character proximity is a
    good first-pass ownership signal. The alternative the graph builder used
    before was attributing every phone to whichever person happened to be
    named first, which in a typical FIR is the complainant: the victim ended
    up owning every suspect's burner.

    Identifiers with no person within max_distance are left unattributed
    rather than guessed at.
    """
    if not identifiers or not person_names:
        return {}

    # All mention positions for each person, so a later reference still counts.
    person_positions: list[tuple[int, str]] = []
    for person in person_names:
        start = text.find(person)
        while start != -1:
            person_positions.append((start + len(person) // 2, person))
            start = text.find(person, start + 1)

    if not person_positions:
        return {}

    owners: dict[str, str] = {}
    for identifier in identifiers:
        position = text.find(identifier)
        if position == -1:
            continue
        centre = position + len(identifier) // 2

        nearest_person, nearest_distance = None, None
        for person_centre, person in person_positions:
            distance = abs(person_centre - centre)
            if nearest_distance is None or distance < nearest_distance:
                nearest_person, nearest_distance = person, distance

        if nearest_person and nearest_distance is not None and nearest_distance <= max_distance:
            owners[identifier] = nearest_person

    return owners


def _resolve_case(db: Session, case_id: Optional[int]) -> Optional[int]:
    if case_id is None:
        return None
    if not db.get(models.Case, case_id):
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    return case_id


@router.post("/fir")
async def upload_fir(
    file: UploadFile = File(...),
    case_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    case_id = _resolve_case(db, case_id)
    saved_path = _save_raw(file.filename, content)

    try:
        text = file_parser.extract_text(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not text:
        raise HTTPException(status_code=400, detail="No readable text found in the document.")

    # Persist first with a placeholder number, then refine it from what NLP finds.
    fir = models.FIR(
        fir_number=f"PENDING-{file.filename}",
        case_id=case_id,
        raw_text=text,
        source_file=saved_path,
    )
    db.add(fir)
    db.commit()
    db.refresh(fir)

    extraction, warnings = pipeline.extract_entities(text, fir.id)

    header = extraction.get("header") or {}
    fir.fir_number = header.get("fir_number") or f"FIR-{fir.id}"
    fir.police_station = header.get("police_station") or ""
    crimes = extraction.get("crimes_mentioned") or []
    fir.offense_type = crimes[0] if crimes else ""

    def _values(key: str) -> list[str]:
        """Normalise one entity list — spaCy returns {"text": ...}, regex returns str."""
        out = []
        for value in extraction.get(key, []) or []:
            text_value = value.get("text") if isinstance(value, dict) else value
            if text_value and str(text_value).strip():
                out.append(str(text_value).strip())
        return out

    # A 12-digit account number starting with 91 also satisfies the phone
    # pattern (country code + 10 digits), so the same string arrives as both a
    # phone and an account. When that happens the account reading wins — it
    # came from a longer, more specific match — otherwise the graph grows a
    # phantom Phone node and the account's owner appears to "use" it.
    account_values_raw = set(_values("bank_accounts"))
    phone_values_raw = [p for p in _values("phones") if p not in account_values_raw]

    def _entity_values(key: str) -> list[str]:
        return phone_values_raw if key == "phones" else _values(key)

    # Regex-derived identifiers are reliable; use them to veto bad PERSON hits.
    identifier_veto = set(_values("vehicles")) | set(phone_values_raw) | account_values_raw
    # Anything spaCy also called a place or a firm, plus the officers who
    # filed the report and names that only ever appear in a locative context.
    entity_veto = (
        set(_values("locations"))
        | set(_values("organizations"))
        | _officer_names(text)
        | {p for p in _values("persons") if _looks_like_a_place(p, text)}
    )

    entity_rows = []
    for entity_type, key in [
        ("person", "persons"),
        ("phone", "phones"),
        ("vehicle", "vehicles"),
        ("location", "locations"),
        ("organization", "organizations"),
        ("bank_account", "bank_accounts"),
    ]:
        for text_value in _entity_values(key):
            if entity_type == "person" and not _is_person_name(
                text_value, identifier_veto, entity_veto
            ):
                continue
            entity_rows.append(
                models.ExtractedEntity(fir_id=fir.id, entity_type=entity_type, value=text_value)
            )

    # Roles the NLP service inferred from surrounding text (accused / victim /
    # witness). Carried into the graph so risk scoring doesn't rank the
    # complainant above the accused. "accused" wins when a name has several.
    roles: dict[str, str] = {}
    for relationship in extraction.get("relationships", []) or []:
        person_name = str(relationship.get("person", "")).strip()
        role = str(relationship.get("role", "")).strip()
        if not person_name or not role:
            continue
        if roles.get(person_name) != "accused":
            roles[person_name] = role

    # The FIR states who complained, in so many words. That is a stronger
    # signal than the NLP service's keyword-proximity guess, so it wins:
    # a complainant scored as an accused is a serious error to show an
    # investigator.
    for match in re.finditer(
        r"(?:complaint (?:by|from)|complainant(?:,)?|reported by)\s*:?\s*"
        r"([A-Z][A-Za-z.]*(?:\s+[A-Z][A-Za-z.]*)*)",
        text,
    ):
        complainant = match.group(1).strip()
        if complainant:
            roles[complainant] = "victim"

    db.add_all(entity_rows)
    db.commit()

    case = db.get(models.Case, case_id) if case_id else None

    person_values = [e.value for e in entity_rows if e.entity_type == "person"]
    phone_values = [e.value for e in entity_rows if e.entity_type == "phone"]
    account_values = [e.value for e in entity_rows if e.entity_type == "bank_account"]

    nodes_created, graph_warnings = pipeline.push_to_graph(
        {
            **extraction,
            "persons": person_values,
            "phones": phone_values,
            "vehicles": [e.value for e in entity_rows if e.entity_type == "vehicle"],
            "locations": [e.value for e in entity_rows if e.entity_type == "location"],
            "organizations": [e.value for e in entity_rows if e.entity_type == "organization"],
            "bank_accounts": account_values,
            "roles": roles,
            "phone_owners": _attribute_to_nearest_person(text, phone_values, person_values),
            "account_owners": _attribute_to_nearest_person(text, account_values, person_values),
        },
        {
            "fir_number": fir.fir_number,
            "case_number": case.case_number if case else None,
            "police_station": fir.police_station,
            "offense_type": fir.offense_type,
        },
    )

    return {
        "message": f"FIR {fir.fir_number} processed successfully.",
        "fir_id": fir.id,
        "records_created": 1,
        "entities_extracted": len(entity_rows),
        "graph_nodes_created": nodes_created,
        "warnings": warnings + graph_warnings,
    }


@router.post("/call-records")
async def upload_call_records(
    file: UploadFile = File(...),
    case_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    case_id = _resolve_case(db, case_id)
    _save_raw(file.filename, content)

    rows = file_parser.parse_call_records(content)
    if not rows:
        raise HTTPException(
            status_code=400,
            detail="No usable rows. Expected CSV columns like caller, receiver, duration, timestamp.",
        )

    db.add_all([
        models.CallRecord(
            case_id=case_id,
            caller=r["caller"],
            receiver=r["receiver"],
            duration=r["duration"],
            call_time=r["call_time"],
            tower_location=r["tower_location"],
        )
        for r in rows
    ])
    db.commit()

    linked, warnings = pipeline.push_calls_to_graph(rows)

    return {
        "message": f"{len(rows)} call records ingested.",
        "records_created": len(rows),
        "graph_nodes_created": linked,
        "warnings": warnings,
    }


@router.post("/transactions")
async def upload_transactions(
    file: UploadFile = File(...),
    case_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    case_id = _resolve_case(db, case_id)
    _save_raw(file.filename, content)

    rows = file_parser.parse_transactions(content)
    if not rows:
        raise HTTPException(
            status_code=400,
            detail="No usable rows. Expected CSV columns like from_account, to_account, amount, date.",
        )

    db.add_all([
        models.Transaction(
            case_id=case_id,
            from_account=r["from_account"],
            to_account=r["to_account"],
            amount=r["amount"],
            txn_date=r["date"],
            memo=r["memo"],
        )
        for r in rows
    ])
    db.commit()

    linked, warnings = pipeline.push_transactions_to_graph(rows)

    return {
        "message": f"{len(rows)} transactions ingested.",
        "records_created": len(rows),
        "graph_nodes_created": linked,
        "warnings": warnings,
    }
