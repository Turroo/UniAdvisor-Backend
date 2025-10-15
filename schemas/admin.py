from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date,datetime

# 📌 Utente
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    birth_date: date
    city: str
    faculty_id: Optional[int] = None

class UserDeleteResponse(BaseModel):
    message: str

# 📌 Nota
class NoteResponse(BaseModel):
    id: int
    course_id: int
    student_id: int
    file_id: str
    description: Optional[str] = None

class NoteDeleteResponse(BaseModel):
    message: str

# 📌 Recensione
class ReviewResponse(BaseModel):
    id: int
    course_id: int
    student_id: int
    rating_clarity: int
    rating_feasibility: int
    rating_availability: int
    comment: Optional[str] = None
    created_at: date

class ReviewDeleteResponse(BaseModel):
    message: str

# 📌 Valutazione Note
class NoteRatingResponse(BaseModel):
    id: int
    note_id: int
    student_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime

class NoteRatingDeleteResponse(BaseModel):
    message: str


# 📌 Facoltà e corsi
class FacultyResponse(BaseModel):
    id: int
    name: str

class FacultyCreate(BaseModel):
    name: str

class CourseResponse(BaseModel):
    id: int
    name: str
    faculty_id: int

class CourseCreate(BaseModel):
    name: str
    faculty_id: int
    teacher_id: Optional[int] = None

# 📌 Insegnante
class TeacherResponse(BaseModel):
    id: int
    name: str

class CourseResponse(BaseModel):
    id: int
    name: str
    faculty_id: int
    teacher_id: Optional[int] = None  # Aggiunto il teacher_id opzionale


class TeacherCreate(BaseModel):
    name: str

class Config:
    from_attributes = True

