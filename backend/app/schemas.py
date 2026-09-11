from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CaseCreate(BaseModel):
    case_number: Optional[str] = None  # auto-generated when omitted
    title: str
    description: str = ""
    status: str = "open"


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: str
    title: str
    description: str = ""
    status: str


class CaseSummary(BaseModel):
    """Shape consumed by the dashboard's CaseDetail panel and the AI service."""

    case: CaseOut
    total_firs: int
    total_call_records: int
    total_transactions: int


class FIROut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fir_number: str
    case_id: Optional[int] = None
    police_station: str = ""
    offense_type: str = ""
    raw_text: str = ""


class UploadResult(BaseModel):
    message: str
    records_created: int = 0
    fir_id: Optional[int] = None
    entities_extracted: int = 0
    graph_nodes_created: int = 0
    warnings: List[str] = []
