from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    city = Column(String, nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True) 

    faculty = relationship("Faculty", back_populates="students")
    notes = relationship("Note", back_populates="student", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="student", cascade="all, delete-orphan")  # Relazione con le recensioni scritte
    ratings = relationship("NoteRating", back_populates="student", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user")