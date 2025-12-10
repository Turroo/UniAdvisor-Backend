from pydantic import BaseModel
from datetime import time
from typing import Optional
# Importiamo lo schema del corso (che dovrebbe avere dentro l'aula)
from .course import Course 

class LessonBase(BaseModel):
    day_of_week: str
    start_time: time
    end_time: time
    course_id: int

class LessonCreate(LessonBase):
    pass # Non serve più classroom_id qui

class Lesson(LessonBase):
    id: int
    # Includiamo l'intero oggetto Corso nella risposta
    # così il frontend può fare: lesson.course.classroom.name
    course: Optional[Course] = None 

    class Config:
        orm_mode = True