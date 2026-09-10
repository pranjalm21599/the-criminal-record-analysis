from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class CaseBase(BaseModel):
    case_number: str
    title: str
    description: Optional[str] = None
    status: str = "Open"

class CaseCreate(CaseBase):
    pass

class CaseRead(CaseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CaseSummary(BaseModel):
    case_info: CaseRead
    fir_count: int
    person_count: int
    cdr_count: int
    transaction_count: int