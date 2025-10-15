from sqlalchemy import Column, Integer, String, ForeignKey, Date, func
from sqlalchemy.orm import relationship
from database.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating_clarity = Column(Integer, nullable=False)
    rating_feasibility = Column(Integer, nullable=False)
    rating_availability = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(Date, server_default=func.current_date())

    course = relationship("Course", back_populates="reviews")
    student = relationship("User", back_populates="reviews")
    reports = relationship("Report", back_populates="review", cascade="all, delete")