from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_id = Column(String, nullable=False)  # ID di GridFS
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relazioni
    course = relationship("Course", back_populates="notes")
    student = relationship("User", back_populates="notes")
    ratings = relationship("NoteRating", back_populates="note", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="note", cascade="all, delete")