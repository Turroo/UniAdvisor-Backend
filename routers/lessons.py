from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database.database import get_db
import models.lesson as models
import schemas.lesson as schemas

router = APIRouter(
    prefix="/lessons",
    tags=["lessons"]
)

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