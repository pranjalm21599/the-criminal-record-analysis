from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from ..models.case import Case
from ..models.fir import FIR
from ..models.call_record import CallRecord
from ..models.transaction import Transaction
from ..schemas.case import CaseCreate, CaseRead, CaseSummary

router = APIRouter(prefix="/cases", tags=["Case Management"])

@router.post("/", response_model=CaseRead)
def create_case(case: CaseCreate, db: Session = Depends(get_db)):
    db_case = Case(**case.model_dump())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

@router.get("/", response_model=List[CaseRead])
def get_all_cases(db: Session = Depends(get_db)):
    return db.query(Case).all()

@router.get("/{case_id}/summary", response_model=CaseSummary)
def get_case_summary(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return {
        "case_info": case,
        "fir_count": db.query(FIR).filter(FIR.case_id == case_id).count(),
        "person_count": 0, # Add logic based on associated FIRs/Records
        "cdr_count": db.query(CallRecord).filter(CallRecord.case_id == case_id).count(),
        "transaction_count": db.query(Transaction).filter(Transaction.case_id == case_id).count()
    }