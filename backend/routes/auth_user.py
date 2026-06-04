from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import models, schemas, auth
from database import get_db

router = APIRouter()

@router.post("/api/register")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    cek_user = db.query(models.User).filter(models.User.username == user.username).first()
    if cek_user:
        raise HTTPException(status_code=400, detail="Username sudah terdaftar")
    
    hashed_pw = auth.get_password_hash(user.password)
    user_baru = models.User(username=user.username, password_hash=hashed_pw)
    db.add(user_baru)
    db.commit()
    return {"pesan": "Registrasi berhasil, silakan login."}

@router.post("/api/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Username atau password salah")
    
    # Berikan token JWT (KTP Digital)
    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}