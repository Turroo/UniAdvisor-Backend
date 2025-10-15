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
        # verify_id_token si occupa di tutta la magia: controlla la firma,
        # la scadenza e che il token sia stato emesso dal tuo progetto Firebase.
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        # L'eccezione può essere per token scaduto, non valido, ecc.
        print(f"Firebase token verification failed: {e}") # Utile per il debug
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
    
    # 1. Prendi l'ID Token dall'header Authorization
    id_token = credentials.credentials
    
    # 2. Verifica il token con Firebase
    decoded_token = verify_firebase_token(id_token, credentials_exception)
    
    # 3. Estrai l'UID di Firebase dal token. La chiave è "user_id".
    firebase_uid = decoded_token.get("user_id")
    if firebase_uid is None:
        raise credentials_exception
        
    # 4. Cerca l'utente nel TUO database SQL usando il firebase_uid
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    # 5. Se non trovi l'utente nel tuo DB, significa che si è registrato
    #    su Firebase ma il processo di creazione del profilo nella tua API non è andato a buon fine.
    #    In un'app reale, potresti voler gestire questo caso (es. creando il profilo ora).
    #    Per ora, lo trattiamo come un errore di autorizzazione.
    if user is None:
        raise credentials_exception
    
    return user