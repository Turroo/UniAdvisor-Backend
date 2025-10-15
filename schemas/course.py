from pydantic import BaseModel
from typing import Optional

# Schema per la creazione di un corso
class CourseCreate(BaseModel):
    name: str
    faculty_id: int  # Ogni corso è associato a una facoltà
    teacher_id: int  # Il corso ha un professore assegnato

# Schema per la risposta di un corso
class CourseResponse(BaseModel):
    id: int
    name: str
    faculty_id: int  # Indica a quale facoltà appartiene il corso
    teacher_id: int  # Indica quale professore tiene il corso

    class Config:
        from_attributes = True  # Permette di convertire i modelli SQLAlchemy in Pydantic
