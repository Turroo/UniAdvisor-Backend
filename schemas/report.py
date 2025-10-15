from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReportCreate(BaseModel):
    id_review: Optional[int] = None
    id_note: Optional[int] = None
    reason: str

class ReportResponse(BaseModel):
    id_report: int
    id_review : Optional[int]
    id_note: Optional[int]
    id_user: int
    datetime: datetime
    reason: str

    class Config:
        orm_mode = True
