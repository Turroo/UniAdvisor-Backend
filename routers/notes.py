from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List
from firebase_admin import storage

from database.database import get_db
from models.note import Note
from models.course import Course
from models.note_ratings import NoteRating
from models.user import User
from models.report import Report
from schemas.note import NoteCreate, NoteWithRatingResponse
from schemas.rating import NoteRatingCreate, NoteRatingUpdate, NoteRatingResponse
from schemas.report import ReportCreate, ReportResponse
from auth.auth import get_current_user

router = APIRouter()

# 1. Ottenere gli appunti per un corso
@router.get("/{course_id}", response_model=list[NoteWithRatingResponse])
def get_notes(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    notes = db.query(Note).filter(Note.course_id == course_id).all()
    return notes

# 2. Caricare un nuovo appunto
@router.post("/", response_model=NoteWithRatingResponse)
def upload_note(
    note_data: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    # 🔍 DEBUG - Log ricevuti
    print("=" * 50)
    print("📤 UPLOAD NOTE REQUEST")
    print(f"📊 User ID: {current_user.id}")
    print(f"📊 User Email: {current_user.email}")
    print(f"📊 User Faculty ID: {current_user.faculty_id}")
    print(f"📊 Requested Course ID: {note_data.course_id}")
    print(f"📊 Description: {note_data.description}")
    print(f"📊 File ID: {note_data.file_id}")
    print("=" * 50)

    course = db.query(Course).filter(Course.id == note_data.course_id).first()
    if not course:
        print("❌ Course not found!")
        raise HTTPException(status_code=404, detail="Course not found.")
    
    print(f"📊 Course Faculty ID: {course.faculty_id}")
    print(f"📊 Faculty Match: {course.faculty_id == current_user.faculty_id}")
    print(f"📊 Faculty Types: user={type(current_user.faculty_id)}, course={type(course.faculty_id)}")

    if course.faculty_id != current_user.faculty_id:
        print("❌ Faculty mismatch - 403!")
        raise HTTPException(status_code=403, detail="You are not authorized to upload notes for this course.")

    print("✅ All checks passed, creating note...") # Debug

    new_note = Note(
        course_id=note_data.course_id,
        student_id=current_user.id,
        file_id=str(note_data.file_id),
        description=note_data.description
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    print("✅ Note created successfully!")
    print("=" * 50)
    print(f"📊 Created Note ID: {new_note.id}")
    print(f"📊 Created Note Description: {new_note.description}")
    print(f"📊 Created Note File ID: {new_note.file_id}")
    print("=" * 50)

    return new_note

# 3. Modificare un appunto
@router.put("/{note_id}")
def update_note(note_id: int, description: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id, Note.student_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found or unauthorized.")

    note.description = description
    db.commit()
    return {"message": "Note updated successfully."}

# 4. Eliminare un appunto
@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")

    if note.student_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this note.")

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
    
    return

# 5. Aggiungere una valutazione a una nota
@router.post("/ratings", response_model=NoteRatingResponse)
def add_rating(
    rating_data: NoteRatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.query(Note).filter(Note.id == rating_data.note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")

    if note.student_id == current_user.id:
        raise HTTPException(status_code=403, detail="You cannot rate your own note.")

    if current_user.faculty_id != note.course.faculty_id:
        raise HTTPException(status_code=403, detail="You can only rate notes from your faculty's courses.")

    existing_rating = db.query(NoteRating).filter(
        NoteRating.note_id == rating_data.note_id,
        NoteRating.student_id == current_user.id
    ).first()
    if existing_rating:
        raise HTTPException(status_code=400, detail="You have already rated this note.")

    new_rating = NoteRating(
        note_id=rating_data.note_id,
        student_id=current_user.id,
        rating=rating_data.rating,
        comment=rating_data.comment
    )

    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)

    return new_rating

# 6. Modificare una valutazione
@router.put("/ratings/{rating_id}", response_model=NoteRatingResponse)
def update_rating(
    rating_id: int,
    rating_data: NoteRatingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rating = db.query(NoteRating).filter(
        NoteRating.id == rating_id,
        NoteRating.student_id == current_user.id
    ).first()

    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found or unauthorized.")

    rating.rating = rating_data.rating
    rating.comment = rating_data.comment
    db.commit()
    db.refresh(rating)

    return rating

# 7. Eliminare una valutazione
@router.delete("/ratings/{rating_id}")
def delete_rating(
    rating_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rating = db.query(NoteRating).filter(
        NoteRating.id == rating_id,
        NoteRating.student_id == current_user.id
    ).first()

    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found or unauthorized.")

    db.delete(rating)
    db.commit()

    return {"message": "Rating deleted successfully."}

# 8. Ottenere la valutazione media degli appunti di un corso
@router.get("/{course_id}/average-rating")
def get_course_notes_average(course_id: int, db: Session = Depends(get_db)):
    avg_rating = (
        db.query(func.coalesce(func.avg(NoteRating.rating), 0))
        .join(Note, NoteRating.note_id == Note.id)
        .filter(Note.course_id == course_id)
        .scalar()
    )
    return {"course_id": course_id, "average_rating": round(avg_rating, 2)}

# 9. Ottenere la lista ordinata degli appunti di un corso
@router.get("/{course_id}/notes-sorted", response_model=list[NoteWithRatingResponse])
def get_sorted_notes(course_id: int, order: str = "desc", db: Session = Depends(get_db)):
    print(f"🔍 GET /notes/{course_id}/notes-sorted called with order={order}")
    
    notes_query = (
        db.query(Note, func.coalesce(func.avg(NoteRating.rating), -1).label("average_rating"))
        .outerjoin(NoteRating, Note.id == NoteRating.note_id)
        .filter(Note.course_id == course_id)
        .group_by(Note.id)
    )

    if order.lower() == "asc":
        notes_query = notes_query.order_by(func.coalesce(func.avg(NoteRating.rating), -1).asc(), Note.created_at.desc())
    else:
        notes_query = notes_query.order_by(func.coalesce(func.avg(NoteRating.rating), -1).desc(), Note.created_at.desc())

    notes_with_ratings = notes_query.all()
    print(f"📊 Query returned {len(notes_with_ratings)} notes")
    
    result = []
    for note, avg_rating in notes_with_ratings:
        print(f"   📝 Note ID={note.id}, avg_rating={avg_rating}, type={type(avg_rating).__name__}")
        
        # Check ratings count for this note
        ratings_count = db.query(NoteRating).filter(NoteRating.note_id == note.id).count()
        print(f"      ✅ This note has {ratings_count} ratings in DB")
        
        note_dict = note.__dict__
        note_dict['average_rating'] = round(avg_rating, 2) if avg_rating != -1 else None
        print(f"      ➡️ Final average_rating in response: {note_dict['average_rating']}")
        result.append(note_dict)

    print(f"🎉 Returning {len(result)} notes")
    return result

# 10. Ottenere gli appunti di un utente
@router.get("/usr/my-notes", response_model=list[NoteWithRatingResponse])
def get_my_notes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_notes = db.query(Note).filter(Note.student_id == current_user.id).all()
    if not user_notes:
        raise HTTPException(status_code=404, detail="You have not created any notes.")
    return user_notes

# 11. Ottenere le valutazioni di un utente
@router.get("/usr/my-reviews", response_model=list[NoteRatingResponse])
def get_my_reviews(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_reviews = db.query(NoteRating).filter(NoteRating.student_id == current_user.id).all()
    if not user_reviews:
        raise HTTPException(status_code=404, detail="You have not created any reviews.")
    return user_reviews

# 12. Ottenere tutte le recensioni di un singolo appunto
@router.get("/notes/{note_id}/reviews", response_model=list[NoteRatingResponse])
def get_note_reviews(note_id: int, db: Session = Depends(get_db)):
    reviews = db.query(NoteRating).filter(NoteRating.note_id == note_id).all()
    return reviews

# 13. Ottenere la media delle recensioni di un singolo appunto
@router.get("/notes/{note_id}/average-rating")
def get_note_average_rating(note_id: int, db: Session = Depends(get_db)):
    avg_rating = db.query(func.coalesce(func.avg(NoteRating.rating), 0)).filter(NoteRating.note_id == note_id).scalar()
    return {"note_id": note_id, "average_rating": round(avg_rating, 2)}

# 14. Ordinare le recensioni di un singolo appunto
@router.get("/notes/{note_id}/reviews-sorted", response_model=list[NoteRatingResponse])
def get_sorted_reviews(note_id: int, order: str = "desc", db: Session = Depends(get_db)):
    reviews_query = db.query(NoteRating).filter(NoteRating.note_id == note_id)
    if order.lower() == "asc":
        reviews_query = reviews_query.order_by(NoteRating.rating.asc())
    else:
        reviews_query = reviews_query.order_by(NoteRating.rating.desc())
    return reviews_query.all()

# 15. Creare un report
@router.post("/reports", response_model=ReportResponse)
def create_report(report: ReportCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if (report.id_review is None and report.id_note is None) or \
       (report.id_review is not None and report.id_note is not None):
        raise HTTPException(status_code=400, detail="You must provide either id_review or id_note, but not both.")

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
