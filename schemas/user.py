# file: schemas/user.py

from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

# Schema per l'aggiornamento del profilo (solo campi modificabili)
class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    city: Optional[str] = None

# Schema per la creazione del profilo
class UserProfileCreate(BaseModel):
    first_name: str
    last_name: str
    birth_date: date
    city: str

# Schema di risposta standard
class UserResponse(BaseModel):
    id: int
    firebase_uid: str
    email: EmailStr
    first_name: str
    last_name: str
    birth_date: date
    city: str
    is_admin: bool
    faculty_id: Optional[int] = None
    faculty_name: Optional[str] = None # Nome della facoltà associata

    class Config:
        from_attributes = True