from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get("/")
def list_cases(db: Session = Depends(get_db)):
    cases = db.query(models.Case).order_by(models.Case.id.desc()).all()
    return {"cases": [schemas.CaseOut.model_validate(c).model_dump() for c in cases]}


@router.post("/", status_code=201)
def create_case(payload: schemas.CaseCreate, db: Session = Depends(get_db)):
    case_number = payload.case_number or (
        f"CASE-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    )
    if db.query(models.Case).filter_by(case_number=case_number).first():
        raise HTTPException(status_code=409, detail=f"Case {case_number} already exists.")

    case = models.Case(
        case_number=case_number,
        title=payload.title,
        description=payload.description,
        status=payload.status,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return schemas.CaseOut.model_validate(case).model_dump()


@router.get("/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.get(models.Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    return schemas.CaseOut.model_validate(case).model_dump()


@router.get("/{case_id}/summary")
def get_case_summary(case_id: int, db: Session = Depends(get_db)):
    case = db.get(models.Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    return {
        "case": schemas.CaseOut.model_validate(case).model_dump(),
        "total_firs": db.query(models.FIR).filter_by(case_id=case_id).count(),
        "total_call_records": db.query(models.CallRecord).filter_by(case_id=case_id).count(),
        "total_transactions": db.query(models.Transaction).filter_by(case_id=case_id).count(),
    }


@router.delete("/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    case = db.get(models.Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    db.delete(case)
    db.commit()
    return {"message": f"Case {case_id} deleted."}
