# file: routers/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from firebase_admin import auth as firebase_auth

# Importazioni dal tuo progetto
from database.database import get_db
from models.user import User
from schemas.user import UserProfileCreate, UserProfileUpdate, UserResponse
from auth.auth import get_current_user, verify_firebase_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
auth_scheme = HTTPBearer()


@router.post("/profile", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_profile(
    profile_data: UserProfileCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    """
    Crea il profilo utente nel DB SQL dopo la registrazione su Firebase.
    Questo endpoint è il ponte tra i due sistemi.
    """
    id_token = credentials.credentials
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token")

    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")

    if not firebase_uid or not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token is missing UID or email")

    existing_user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User profile already exists")

    new_user = User(
        firebase_uid=firebase_uid,
        email=email,
        hashed_password="managed_by_firebase",  # Placeholder
        first_name=profile_data.first_name,
        last_name=profile_data.last_name,
        birth_date=profile_data.birth_date,
        city=profile_data.city,
        is_admin=db.query(User).count() == 0,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        firebase_uid=new_user.firebase_uid,
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        birth_date=new_user.birth_date,
        city=new_user.city,
        is_admin=new_user.is_admin,
        faculty_id=new_user.faculty_id,
        faculty_name=new_user.faculty.name if new_user.faculty else None
    )


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Restituisce il profilo dell'utente attualmente loggato.
    """
    print("=" * 50)
    print("📡 GET /users/me endpoint called")
    print(f"👤 User ID: {current_user.id}")
    print(f"👤 User Email: {current_user.email}")
    print(f"🏫 Faculty ID: {current_user.faculty_id}")
    
    # ✅ Costruisci manualmente la risposta con faculty_name
    if current_user.faculty:
        print(f"✅ Faculty found: {current_user.faculty.name}")
        faculty_name = current_user.faculty.name
    else:
        print("⚠️ No faculty assigned to this user")
        faculty_name = None
    
    user_response = UserResponse(
        id=current_user.id,
        firebase_uid=current_user.firebase_uid,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        birth_date=current_user.birth_date,
        city=current_user.city,
        is_admin=current_user.is_admin,
        faculty_id=current_user.faculty_id,
        faculty_name=faculty_name  # ✅ Popola faculty_name
    )
    
    print(f"📤 Sending response with faculty_name: {faculty_name}")
    print("=" * 50)
    
    return user_response


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    profile_update: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permette all'utente autenticato di aggiornare il proprio profilo.
    """
    # exclude_unset=True aggiorna solo i campi forniti nella richiesta
    update_data = profile_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        firebase_uid=current_user.firebase_uid,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        birth_date=current_user.birth_date,
        city=current_user.city,
        is_admin=current_user.is_admin,
        faculty_id=current_user.faculty_id,
        faculty_name=current_user.faculty.name if current_user.faculty else None
    )


@router.delete("/me")
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina l'account di un utente sia da Firebase Authentication
    sia dal database SQL (tramite cascade).
    """
    firebase_uid = current_user.firebase_uid

    try:
        # 1. Elimina l'utente da Firebase Authentication
        firebase_auth.delete_user(firebase_uid)
        
        # 2. Se l'eliminazione da Firebase ha successo, l'utente viene eliminato
        #    dal nostro database SQL grazie a 'ON DELETE CASCADE'
        #    impostato sulla tabella 'profiles' (se l'hai creata in quel modo).
        #    Se non hai una tabella profiles separata, ma l'UID è in 'users',
        #    la cancellazione del record scatenerà le altre cascade.
        db.delete(current_user)
        db.commit()

        return {"message": "User account deleted successfully from all systems."}

    except firebase_auth.UserNotFoundError:
        # L'utente non esiste più su Firebase, ma esiste ancora nel nostro DB.
        # È un caso di dati non allineati. Procediamo a pulire il nostro DB.
        db.delete(current_user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in Firebase, but was cleaned up from local DB."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the user: {e}"
        )