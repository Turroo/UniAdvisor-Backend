from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base

class Report(Base):
    __tablename__ = "reports"

    id_report = Column(Integer, primary_key=True, index=True)
    id_review = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=True)
    id_note = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=True)
    id_user = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String, nullable=False)
    datetime = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reports")
    review = relationship("Review", back_populates="reports")
    note = relationship("Note", back_populates="reports")
