from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional
from fastapi import HTTPException  # ✅ Importa HTTPException

# Valori consentiti per i rating
VALID_RATINGS = {1, 2, 3, 4, 5}

class ReviewCreate(BaseModel):
    rating_clarity: float
    rating_feasibility: float
    rating_availability: float
    comment: Optional[str] = None

    @field_validator("rating_clarity", "rating_feasibility", "rating_availability", mode="before")
    def validate_ratings(cls, value):
        if value not in VALID_RATINGS:
            raise HTTPException(
                status_code=400,
                detail="Puoi inserire solo i voti: 1, 2, 3, 4, 5."
            )
        return value

class ReviewResponse(BaseModel):
    id: int
    course_id: int
    created_at: date
    rating_clarity: float
    rating_feasibility: float
    rating_availability: float
    comment: Optional[str] = None

    @field_validator('created_at', mode='before')
    def convert_datetime_to_date(cls, value):
        if isinstance(value, datetime):
            return value.date()  # Estrae solo la parte data
        return value

    class Config:
        from_attributes = True
