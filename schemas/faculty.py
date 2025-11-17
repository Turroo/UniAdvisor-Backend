from pydantic import BaseModel
from typing import Optional

# Schema for creating a faculty (admin only)
class FacultyCreate(BaseModel):
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    building_name: Optional[str] = None

# Schema for updating faculty location (admin only)
class FacultyLocationUpdate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    building_name: Optional[str] = None

# Schema for faculty response
class FacultyResponse(BaseModel):
    id: int
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    building_name: Optional[str] = None

    class Config:
        from_attributes = True