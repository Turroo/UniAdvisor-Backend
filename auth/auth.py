# auth/auth.py

import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database.database import get_db
from models.user import User
import os

# --- INIZIALIZZAZIONE FIREBASE ADMIN ---
# Cerca il file delle credenziali. Assicurati che sia presente nel tuo progetto.
# Per il deploy su un PaaS, dovrai gestire questo file come una variabile d'ambiente.
creds_path = os.path.join(os.path.dirname(__file__), '..', 'firebase-credentials.json')
if not os.path.exists(creds_path):
    raise FileNotFoundError("Firebase credentials file not found. Make sure 'firebase-credentials.json' is in the root of your backend directory.")

creds = credentials.Certificate(creds_path)
firebase_admin.initialize_app(creds)
# -----------------------------------------

auth_scheme = HTTPBearer()

# Le funzioni hash_password e create_access_token non sono più necessarie.

def verify_firebase_token(id_token: str, credentials_exception):
    """
    Verifica l'ID Token di Firebase.
    Se valido, restituisce il payload decodificato.
    Altrimenti, solleva un'eccezione.
    """
    try:
        print(f"🔍 Verifying token with Firebase Admin SDK...")
        decoded_token = auth.verify_id_token(id_token)
        print(f"✅ Token verified, UID: {decoded_token.get('user_id')}")
        return decoded_token
    except Exception as e:
        print(f"❌ Firebase token verification error: {type(e).__name__}: {e}")
        raise credentials_exception


def get_current_user(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """
    Dependency per FastAPI: prende il token Bearer, lo verifica con Firebase
    e restituisce l'utente corrispondente dal database SQL.
    """
    print("=" * 80)
    print("🔐 GET_CURRENT_USER CALLED")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Prendi l'ID Token dall'header Authorization
    id_token = credentials.credentials
    print(f"📊 Token received (first 50 chars): {id_token[:50]}..." if id_token else "❌ NO TOKEN!")
    
    # 2. Verifica il token con Firebase
    try:
        decoded_token = verify_firebase_token(id_token, credentials_exception)
        print(f"✅ Token verified successfully")
    except Exception as e:
        print(f"❌ Token verification failed: {e}")
        raise credentials_exception
    
    # 3. Estrai l'UID di Firebase dal token. La chiave è "user_id".
    firebase_uid = decoded_token.get("user_id")
    print(f"📊 Firebase UID from token: {firebase_uid}")
    
    if firebase_uid is None:
        print("❌ Firebase UID is None!")
        raise credentials_exception
        
    # 4. Cerca l'utente nel TUO database SQL usando il firebase_uid
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if user is None:
        print(f"❌ User not found in database for UID: {firebase_uid}")
        raise credentials_exception
    
    print(f"✅ User found: ID={user.id}, Email={user.email}, Faculty={user.faculty_id}")
    print("=" * 80)
    
    return user