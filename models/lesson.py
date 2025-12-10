from sqlalchemy import Column, Integer, String, Time, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base 

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(String) # Es: "Monday"
    start_time = Column(Time)    # Es: 13:00
    end_time = Column(Time)      # Es: 16:00

    # Colleghiamo la lezione SOLO al Corso
    course_id = Column(Integer, ForeignKey("courses.id"))

    # Relazione per recuperare il corso (e tramite lui, l'aula)
    course = relationship("Course", back_populates="lessons")