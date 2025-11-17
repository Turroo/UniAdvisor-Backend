from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import relationship
from database.database import Base

class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    
    # Location fields for campus map
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(Text, nullable=True)
    building_name = Column(String, nullable=True)

    # Relationships
    students = relationship("User", back_populates="faculty", cascade="save-update")
    courses = relationship("Course", back_populates="faculty", cascade="all, delete-orphan")