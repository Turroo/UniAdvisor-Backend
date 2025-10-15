from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.faculty import Faculty
from models.user import User
from schemas.faculty import FacultyCreate, FacultyResponse
from auth.auth import get_current_user  # Per autenticazione admin

router = APIRouter()

# ✅ **Ottenere tutte le facoltà disponibili**
@router.get("/", response_model=list[FacultyResponse])
def get_faculties(db: Session = Depends(get_db)):
    faculties = db.query(Faculty).all()
    return faculties


# ✅ **Aggiungere una nuova facoltà (solo admin)**
@router.post("/", response_model=FacultyResponse)
def create_faculty(
    faculty: FacultyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Solo admin
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    new_faculty = Faculty(name=faculty.name)
    db.add(new_faculty)
    db.commit()
    db.refresh(new_faculty)
    return new_faculty


# ✅ **Iscrivere l'utente autenticato a una facoltà**
@router.post("/enroll/{faculty_id}")
def enroll_in_faculty(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Ora usiamo l'utente autenticato
):
    # Controlliamo se l'utente è già iscritto a una facoltà
    if current_user.faculty_id is not None:
        raise HTTPException(status_code=400, detail="User is already enrolled in a faculty")

    # Verifica se la facoltà esiste
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")

    # Assegna la facoltà all'utente
    current_user.faculty_id = faculty_id
    db.commit()
    db.refresh(current_user)

    return {"message": f"User successfully enrolled in faculty {faculty.name}"}


# ✅ **Ottenere la facoltà dell'utente autenticato**
@router.get("/my-faculty", response_model=FacultyResponse)
def get_my_faculty(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Ora usiamo l'utente autenticato
):
    # Controlliamo se l'utente è iscritto a una facoltà
    if current_user.faculty_id is None:
        raise HTTPException(status_code=404, detail="User is not enrolled in any faculty")

    # Ottieni la facoltà associata all'utente
    faculty = db.query(Faculty).filter(Faculty.id == current_user.faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")

    return faculty

# ✅ **Cambiare facoltà per l'utente autenticato**
@router.put("/change-faculty/{faculty_id}")
def change_faculty(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Ora usiamo l'utente autenticato
):
    # Verifica se la nuova facoltà esiste
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="New faculty not found")

    # Se l'utente è già iscritto alla stessa facoltà, non fare nulla
    if current_user.faculty_id == faculty_id:
        raise HTTPException(status_code=400, detail="User is already enrolled in this faculty")

    # Aggiorna la facoltà dell'utente
    current_user.faculty_id = faculty_id
    db.commit()
    db.refresh(current_user)

    return {"message": f"User successfully changed faculty to {faculty.name}"}
