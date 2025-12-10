# file: main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import users, faculty, course, notes, admin, location, lessons

load_dotenv()

app = FastAPI(
    title="UniAdvisor API",
    description="L'API backend per il progetto UniAdvisor con supporto per mappe e navigazione campus",
    version="2.0.0"
)

# --- Configurazione CORS ---
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://10.0.2.2:8000",  # Android emulator
    # Aggiungi qui l'URL del tuo frontend deployato se ne hai uno
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permetti tutto in sviluppo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Inclusione dei Router ---
app.include_router(users.router, prefix="/users", tags=["Users & Profiles"])
app.include_router(faculty.router, prefix="/faculties", tags=["Faculties"])
app.include_router(course.router, prefix="/courses", tags=["Courses"])
app.include_router(notes.router, prefix="/notes", tags=["Notes"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(location.router, prefix="/location", tags=["Location & Maps"])
app.include_router(lessons.router, prefix="/lessons", tags=["Lessons"])

# --- Endpoint Radice ---
@app.get("/", tags=["Root"])
def read_root():
    """Endpoint di benvenuto per verificare che l'API sia online."""
    return {
        "message": "Benvenuto sull'API di UniAdvisor!",
        "version": "2.0.0",
        "features": [
            "User Authentication",
            "Course Management",
            "Notes Sharing",
            "Reviews & Ratings",
            "Campus Maps & Navigation",
            "Lessons"
        ]
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": "2.0.0"}