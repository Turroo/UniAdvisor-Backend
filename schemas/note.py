# file: schemas/note.py

from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

# Schema per la creazione di una nota.
# Non riceviamo più un file, ma l'URL di un file già caricato.
class NoteCreate(BaseModel):
    course_id: int
    description: Optional[str] = None
    file_id: HttpUrl # Pydantic valida che sia un URL valido

# Schema per la risposta
class NoteResponse(BaseModel):
    id: int
    course_id: int
    student_id: int
    description: Optional[str]
    file_id: str # In risposta mandiamo una stringa semplice
    created_at: datetime

    class Config:
        from_attributes = True