# file: main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import users, faculty, course, notes, admin # Assicurati di importare tutti i router

load_dotenv()

app = FastAPI(
    title="UniAdvisor API",
    description="L'API backend per il progetto UniAdvisor",
    version="1.0.0"
)

# --- Configurazione CORS ---
# Permette al tuo frontend (es. React in locale su porta 3000) di comunicare
# con la tua API backend senza problemi di sicurezza del browser.
# Per la produzione, potresti voler restringere gli origins.
origins = [
    "http://localhost",
    "http://localhost:3000",
    # Aggiungi qui l'URL del tuo frontend deployato se ne hai uno
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permette tutti i metodi (GET, POST, etc.)
    allow_headers=["*"], # Permette tutti gli header
)


# --- Inclusione dei Router ---
# Ogni router rappresenta un "microservizio" logico della tua applicazione.
app.include_router(users.router, prefix="/users", tags=["Users & Profiles"])
app.include_router(faculty.router, prefix="/faculties", tags=["Faculties"])
app.include_router(course.router, prefix="/courses", tags=["Courses"])
app.include_router(notes.router, prefix="/notes", tags=["Notes"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


# --- Endpoint Radice ---
@app.get("/", tags=["Root"])
def read_root():
    """Endpoint di benvenuto per verificare che l'API sia online."""
    return {"message": "Benvenuto sull'API di UniAdvisor!"}

# Permetti tutte le origini in sviluppo
origins = [
    "http://localhost",
    "http://localhost:3000",
    "*"  # Permetti TUTTO (ok per sviluppo, specifica in produzione)
]