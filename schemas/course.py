from pydantic import BaseModel
from typing import Optional

# Schema for creating a course
class CourseCreate(BaseModel):
    name: str
    faculty_id: int
    teacher_id: Optional[int] = None
    room_number: Optional[str] = None
    building_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    floor: Optional[int] = None

# Schema for updating course location (admin only)
class CourseLocationUpdate(BaseModel):
    room_number: Optional[str] = None
    building_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    floor: Optional[int] = None

# Schema for course response
class CourseResponse(BaseModel):
    id: int
    name: str
    faculty_id: int
    teacher_id: Optional[int] = None
    room_number: Optional[str] = None
    building_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    floor: Optional[int] = None

    class Config:
        from_attributes = True