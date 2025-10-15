from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class NoteRatingCreate(BaseModel):
    note_id: int
    rating: int = Field(..., ge=1, le=5)  # Assicura che il rating sia tra 1 e 5
    comment: Optional[str] = None

class NoteRatingUpdate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class NoteRatingResponse(BaseModel):
    id: int
    note_id: int
    student_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
