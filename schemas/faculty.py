from pydantic import BaseModel

# Schema per la creazione di una facoltà
class FacultyCreate(BaseModel):
    name: str

# Schema per la risposta della facoltà
class FacultyResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
