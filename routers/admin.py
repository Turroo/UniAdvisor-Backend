from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from firebase_admin import auth as firebase_auth, storage

from database.database import get_db
from models.user import User
from models.faculty import Faculty
from models.course import Course
from models.teacher import Teacher
from models.note import Note
from models.review import Review
from models.report import Report
from models.note_ratings import NoteRating
from auth.auth import get_current_user
from schemas.admin import (
    UserResponse, UserDeleteResponse,
    NoteResponse, NoteDeleteResponse,
    ReviewResponse, ReviewDeleteResponse,
    FacultyResponse, FacultyCreate,
    CourseResponse, CourseCreate,
    TeacherResponse, NoteRatingResponse, NoteRatingDeleteResponse, TeacherCreate,
)
from schemas.report import ReportResponse

router = APIRouter()

# 1. Gestione utenti
@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_detail(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user

@router.delete("/users/{user_id}", response_model=UserDeleteResponse)
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot delete themselves")
    
    try:
        firebase_auth.delete_user(user.firebase_uid)
    except firebase_auth.UserNotFoundError:
        print(f"Warning: User with UID {user.firebase_uid} not found in Firebase, but deleting from local DB.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting user from Firebase: {e}")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@router.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can view all users")
    return db.query(User).all()

# 2. Gestione note e recensioni
@router.get("/notes", response_model=List[NoteResponse])
def get_notes(db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    return db.query(Note).all()

@router.delete("/notes/{note_id}", response_model=NoteDeleteResponse)
def delete_note(note_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    try:
        bucket = storage.bucket()
        if note.file_id and f"/b/{bucket.name}/o/" in note.file_id:
            file_path = note.file_id.split(f"/b/{bucket.name}/o/")[1].split("?")[0]
            blob = bucket.blob(file_path.replace('%2F', '/'))
            if blob.exists():
                blob.delete()
    except Exception as e:
        print(f"Failed to delete file from Firebase Storage: {e}")

    db.delete(note)
    db.commit()
    return {"message": "Note deleted successfully"}

@router.get("/reviews", response_model=List[ReviewResponse])
def get_reviews(db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    return db.query(Review).all()

@router.delete("/reviews/{review_id}", response_model=ReviewDeleteResponse)
def delete_review(review_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    db.delete(review)
    db.commit()
    return {"message": "Review deleted successfully"}

# 3. Gestione facoltà e corsi
@router.get("/faculties", response_model=List[FacultyResponse])
def get_faculties(db: Session = Depends(get_db)):
    return db.query(Faculty).all()

@router.post("/faculties", response_model=FacultyResponse)
def add_faculty(faculty: FacultyCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    new_faculty = Faculty(name=faculty.name)
    db.add(new_faculty)
    db.commit()
    db.refresh(new_faculty)
    return new_faculty

@router.delete("/faculties/{faculty_id}")
def delete_faculty(faculty_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
    
    db.delete(faculty)
    db.commit()
    return {"message": "Faculty deleted successfully"}

# 4. Gestione insegnanti
@router.get("/teachers", response_model=List[TeacherResponse])
def get_all_teachers(db: Session = Depends(get_db)):
    return db.query(Teacher).all()

@router.post("/teachers", response_model=TeacherResponse)
def add_teacher(teacher: TeacherCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    
    new_teacher = Teacher(name=teacher.name)
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    return new_teacher

@router.delete("/teachers/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

    db.delete(teacher)
    db.commit()
    return {"message": "Teacher deleted successfully"}

# 5. Gestione Corsi
@router.get("/courses", response_model=List[CourseResponse])
def get_courses(db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    return db.query(Course).all()

@router.post("/courses", response_model=CourseResponse)
def add_course(course: CourseCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    
    new_course = Course(
        name=course.name,
        faculty_id=course.faculty_id,
        teacher_id=course.teacher_id
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

@router.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}

# 6. Gestione Altro
@router.get("/note-ratings", response_model=List[NoteRatingResponse])
def get_note_ratings(db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    return db.query(NoteRating).all()

@router.delete("/note-ratings/{rating_id}", response_model=NoteRatingDeleteResponse)
def delete_note_rating(rating_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if not admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    rating = db.query(NoteRating).filter(NoteRating.id == rating_id).first()
    if not rating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note rating not found")

    db.delete(rating)
    db.commit()
    return {"message": "Note rating deleted successfully"}

@router.get("/reports", response_model=List[ReportResponse])
def get_all_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can view reports.")
    return db.query(Report).all()

@router.delete("/reports/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete reports.")
    
    report = db.query(Report).filter(Report.id_report == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    db.delete(report)
    db.commit()
    return {"message": "Report deleted successfully."}