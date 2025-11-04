# auth/auth.py

import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
import json

from database.database import get_db
from models.user import User

# --- INIZIALIZZAZIONE FIREBASE ADMIN ---
# ✅ Usa variabile d'ambiente invece del file
firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS")

if firebase_creds_json:
    # Se la variabile d'ambiente esiste, usala (per Render/produzione)
    try:
        creds_dict = json.loads(firebase_creds_json)
        creds = credentials.Certificate(creds_dict)
        print("✅ Firebase initialized from environment variable")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid FIREBASE_CREDENTIALS JSON: {e}")
else:
    # Altrimenti usa il file locale (per sviluppo locale)
    creds_path = os.path.join(os.path.dirname(__file__), '..', 'firebase-credentials.json')
    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            "Firebase credentials not found. "
            "Set FIREBASE_CREDENTIALS environment variable or provide firebase-credentials.json file."
        )
    creds = credentials.Certificate(creds_path)
    print("✅ Firebase initialized from local file")

firebase_admin.initialize_app(creds)
# -----------------------------------------

auth_scheme = HTTPBearer()

def verify_firebase_token(id_token: str, credentials_exception):
    """
    Verifica l'ID Token di Firebase.
    Se valido, restituisce il payload decodificato.
    Altrimenti, solleva un'eccezione.
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Firebase token verification failed: {e}")
        raise credentials_exception


def get_current_user(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """
    Dependency per FastAPI: prende il token Bearer, lo verifica con Firebase
    e restituisce l'utente corrispondente dal database SQL.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    id_token = credentials.credentials
    decoded_token = verify_firebase_token(id_token, credentials_exception)
    firebase_uid = decoded_token.get("user_id")
    
    if firebase_uid is None:
        raise credentials_exception
        
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if user is None:
        raise credentials_exception
    
    return user