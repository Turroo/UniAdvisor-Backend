from pydantic import BaseModel
from datetime import time,date
from typing import Optional

# --- DEFINIZIONE "LITE" DEL CORSO (Per evitare circular imports) ---
# Qui mappiamo esattamente i campi che hai nel tuo database (models/course.py)
class CourseLocationInfo(BaseModel):
    id: int
    name: str
    room_number: Optional[str] = None
    building_name: Optional[str] = None
    floor: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    teacher_name: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True # Fix per Pydantic V2
# -------------------------------------------------------------------

class LessonBase(BaseModel):
    day_of_week: str
    start_time: time
    end_time: time
    course_id: int

class LessonCreate(LessonBase):
    pass

class Lesson(LessonBase):
    id: int
    # Qui includiamo l'oggetto CourseLocationInfo definito sopra
    course: Optional[CourseLocationInfo] = None 
    checkins: int = 0
    last_checkin_date: Optional[date] = None

    class Config:
        from_attributes = True # Fix per Pydantic V2