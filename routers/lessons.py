from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import math
from datetime import date

from database.database import get_db
import models.lesson as models
import schemas.lesson as schemas
from pydantic import BaseModel
router = APIRouter(
)

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000 
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class CheckInRequest(BaseModel):
    latitude: float
    longitude: float

@router.post("/", response_model=schemas.Lesson)
def create_lesson(lesson: schemas.LessonCreate, db: Session = Depends(get_db)):
    db_lesson = models.Lesson(**lesson.dict())
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson

@router.get("/course/{course_id}", response_model=List[schemas.Lesson])
def get_lessons_by_course(course_id: int, db: Session = Depends(get_db)):
    # SQLAlchemy caricherà automaticamente il corso associato se definito nello schema
    return db.query(models.Lesson).filter(models.Lesson.course_id == course_id).all()

@router.post("/{lesson_id}/check-in")
def check_in_lesson(lesson_id: int, location: CheckInRequest, db: Session = Depends(get_db)):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # 1. Verifica Distanza
    course = lesson.course
    if not course.latitude or not course.longitude:
        raise HTTPException(status_code=400, detail="Course location not set")

    dist = calculate_distance(location.latitude, location.longitude, course.latitude, course.longitude)
    if dist > 150: 
        raise HTTPException(status_code=400, detail=f"Too far ({int(dist)}m). Get closer!")

    # 2. LOGICA LAZY RESET
    today = date.today()
    
    # Se l'ultimo check-in non è di oggi (o è nullo), resettiamo a 1 (nuovo giorno)
    if lesson.last_checkin_date != today:
        lesson.checkins = 1
        lesson.last_checkin_date = today
    else:
        # Se è lo stesso giorno, incrementiamo
        lesson.checkins += 1

    db.commit()
    db.refresh(lesson)

    return {"message": "Check-in successful", "new_occupancy": lesson.checkins}