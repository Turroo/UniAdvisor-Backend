from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base

class NoteRating(Base):
    __tablename__ = "note_ratings"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)  # Nota valutata
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # Studente che vota
    rating = Column(Integer, nullable=False)  # Voto da 1 a 5
    comment = Column(String, nullable=True)  # Commento opzionale
    created_at = Column(DateTime, default=datetime.utcnow)  # Data della valutazione

    # Relazioni
    note = relationship("Note", back_populates="ratings")
    student = relationship("User", back_populates="ratings")
