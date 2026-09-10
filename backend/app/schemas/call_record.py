from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CDRBase(BaseModel):
    caller_number: str
    receiver_number: str
    call_duration: int
    call_timestamp: datetime
    call_type: Optional[str] = "Voice"
    tower_location: Optional[str] = None
    imei_caller: Optional[str] = None
    imei_receiver: Optional[str] = None
    case_id: int

class CDRCreate(CDRBase):
    pass

class CDRRead(CDRBase):
    id: int
    class Config:
        from_attributes = True