from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database.database import get_db
from models.course import Course
from models.review import Review
from models.user import User
from models.teacher import Teacher
from models.report import Report
from schemas.course import CourseCreate, CourseResponse
from schemas.review import ReviewCreate, ReviewResponse
from schemas.report import ReportCreate, ReportResponse
from auth.auth import get_current_user  # Per autenticazione admin
from fastapi.encoders import jsonable_encoder
from typing import List  # ✅ Per specificare il tipo di lista nel response_model
router = APIRouter()

def reset_sequence(db: Session, table_name: str, column_name: str):
    """ Reset the sequence to the max ID in the table. """
    db.execute(text(f"""
        SELECT setval(pg_get_serial_sequence('{table_name}', '{column_name}'), 
                      COALESCE((SELECT MAX({column_name}) FROM {table_name}) + 1 , 1), false)
    """))
    db.commit()


# 📌 Ottenere tutti i corsi
@router.get("/", response_model=list[CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    return courses

# 📌 Ottenere i corsi appartenenti a una specifica facoltà
@router.get("/faculty/{faculty_id}", response_model=list[CourseResponse])
def get_courses_by_faculty(faculty_id: int, db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.faculty_id == faculty_id).all()
    if not courses:
        raise HTTPException(status_code=404, detail="No courses found for this faculty")
    return courses

# 📌 Ottenere il professore di un corso
@router.get("/{course_id}/teacher", response_model=dict)
def get_course_teacher(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    teacher = db.query(Teacher).filter(Teacher.id == course.teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {"teacher_id": teacher.id, "name": teacher.name}

# 📌 Aggiungere una recensione con controllo del valore minimo
@router.post("/{course_id}/reviews", response_model=ReviewResponse)
def add_review(course_id: int, review: ReviewCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    student_id = current_user.id  # Ottieni l'ID dello studente loggato

    # Controllo che i voti siano almeno 1
    if any(r < 1 for r in [review.rating_clarity, review.rating_feasibility, review.rating_availability]):
        raise HTTPException(status_code=400, detail="Ratings must be at least 1.")

    # Verifica che l'utente esista nella tabella users
    user = db.query(User).filter(User.id == student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Controlla se il corso esiste
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    
    # Controlla se l'utente ha già lasciato una recensione per questo corso
    existing_review = db.query(Review).filter(Review.course_id == course_id, Review.student_id == student_id).first()

    if existing_review:
        # Se una recensione esiste già, permetti di modificarla
        existing_review.rating_clarity = review.rating_clarity
        existing_review.rating_feasibility = review.rating_feasibility
        existing_review.rating_availability = review.rating_availability
        existing_review.comment = review.comment
        
        db.commit()
        db.refresh(existing_review)
        
        return existing_review
    else:
        # Se non esiste, crea una nuova recensione
        new_review = Review(
            course_id=course_id,
            student_id=student_id,
            rating_clarity=review.rating_clarity,
            rating_feasibility=review.rating_feasibility,
            rating_availability=review.rating_availability,
            comment=review.comment
        )

        db.add(new_review)
        db.commit()
        db.refresh(new_review)

        return new_review

# 📌 Ottenere tutte le recensioni di un corso
@router.get("/{course_id}/reviews", response_model=list[ReviewResponse])
def get_course_reviews(course_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.course_id == course_id).all()
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this course.")
    return reviews

@router.get("/my-reviews", response_model=list[ReviewResponse])
def get_student_reviews(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    reviews = db.query(Review).filter(Review.student_id == current_user.id).all()
    
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this student.")
    
    return reviews


# 📌 Modificare una recensione
@router.put("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(review_id: int, updated_review: ReviewCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    review = db.query(Review).filter(Review.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")
    
    if review.student_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only edit your own reviews.")

    review.rating_clarity = updated_review.rating_clarity
    review.rating_feasibility = updated_review.rating_feasibility
    review.rating_availability = updated_review.rating_availability
    review.comment = updated_review.comment

    db.commit()
    db.refresh(review)

    return review

# 📌 Eliminare una recensione
@router.delete("/reviews/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    review = db.query(Review).filter(Review.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")
    
    if review.student_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only delete your own reviews.")

    db.delete(review)
    db.commit()

    reset_sequence(db, "reviews", "id")

    return {"message": "Review deleted successfully"}

# 📌 Funzione per arrotondare al primo intero o mezzo superiore
def round_up_half(value: float) -> float:
    return round(value * 2) / 2

# 📌 Ottenere la media dei voti di un corso con arrotondamento
@router.get("/{course_id}/ratings")
def get_course_ratings(course_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.course_id == course_id).all()
    
    if not reviews:
        raise HTTPException(status_code=404, detail="No ratings found for this course.")

    avg_clarity = round_up_half(sum(r.rating_clarity for r in reviews) / len(reviews))
    avg_feasibility = round_up_half(sum(r.rating_feasibility for r in reviews) / len(reviews))
    avg_availability = round_up_half(sum(r.rating_availability for r in reviews) / len(reviews))

    return {
        "course_id": course_id,
        "average_clarity": avg_clarity,
        "average_feasibility": avg_feasibility,
        "average_availability": avg_availability
    }

@router.post("/reports", response_model=ReportResponse)
def create_report(report: ReportCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not report.id_review and not report.id_note:
        raise HTTPException(status_code=400, detail="A report must be linked to either a review or a note.")
    
    new_report = Report(
        id_review=report.id_review,
        id_note=report.id_note,
        id_user=current_user.id,
        reason=report.reason
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

@router.get("/reports", response_model=List[ReportResponse])
def get_all_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can view reports.")

    return db.query(Report).all()

@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can delete reports.")
    
    report = db.query(Report).filter(Report.id_report == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    db.delete(report)
    db.commit()
    return {"message": "Report deleted successfully."}

@router.get("/{course_id}/details", response_model=CourseResponse)
def get_course_detail(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course