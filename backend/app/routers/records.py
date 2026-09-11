"""
Read-only access to the structured evidence tables.

The analysis service (M4) pulls call records and transactions from here to
run its anomaly models, so these stay plain JSON lists with stable keys.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/records", tags=["Records"])


@router.get("/calls")
def list_call_records(
    case_id: Optional[int] = None,
    limit: int = Query(5000, le=50000),
    db: Session = Depends(get_db),
):
    query = db.query(models.CallRecord)
    if case_id is not None:
        query = query.filter_by(case_id=case_id)

    rows = query.limit(limit).all()
    return {
        "count": len(rows),
        "call_records": [
            {
                "id": r.id,
                "caller": r.caller,
                "receiver": r.receiver,
                "duration": r.duration,
                "call_time": r.call_time,
                "tower_location": r.tower_location,
            }
            for r in rows
        ],
    }


@router.get("/transactions")
def list_transactions(
    case_id: Optional[int] = None,
    limit: int = Query(5000, le=50000),
    db: Session = Depends(get_db),
):
    query = db.query(models.Transaction)
    if case_id is not None:
        query = query.filter_by(case_id=case_id)

    rows = query.limit(limit).all()
    return {
        "count": len(rows),
        "transactions": [
            {
                "id": r.id,
                "from_account": r.from_account,
                "to_account": r.to_account,
                "amount": r.amount,
                "date": r.txn_date,
                "memo": r.memo,
            }
            for r in rows
        ],
    }


@router.get("/firs")
def list_firs(
    case_id: Optional[int] = None,
    limit: int = Query(1000, le=10000),
    db: Session = Depends(get_db),
):
    query = db.query(models.FIR)
    if case_id is not None:
        query = query.filter_by(case_id=case_id)

    rows = query.limit(limit).all()
    return {
        "count": len(rows),
        "firs": [
            {
                "id": r.id,
                "fir_number": r.fir_number,
                "case_id": r.case_id,
                "police_station": r.police_station,
                "offense_type": r.offense_type,
                "date_filed": r.date_filed,
            }
            for r in rows
        ],
    }


@router.get("/entities")
def list_entities(
    entity_type: Optional[str] = None,
    fir_id: Optional[int] = None,
    limit: int = Query(2000, le=20000),
    db: Session = Depends(get_db),
):
    query = db.query(models.ExtractedEntity)
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    if fir_id is not None:
        query = query.filter_by(fir_id=fir_id)

    rows = query.limit(limit).all()
    return {
        "count": len(rows),
        "entities": [
            {"id": r.id, "fir_id": r.fir_id, "type": r.entity_type, "value": r.value}
            for r in rows
        ],
    }
