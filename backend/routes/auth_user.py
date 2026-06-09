from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.security import OAuth2PasswordRequestForm
import models, schemas, auth
from database import get_db
from auth import get_current_user

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

@router.get("/api/user/me")
def get_user_profile(current_user: models.User = Depends(get_current_user)):
    """Mengambil data pengguna yang sedang login untuk mengecek status Telegram"""
    return {
        "username": current_user.username,
        "telegram_chat_id": current_user.telegram_chat_id
    }

@router.put("/api/user/telegram")
def update_telegram_id(data: schemas.TelegramUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Menyimpan ID Telegram yang baru diinput oleh pengguna"""
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    user.telegram_chat_id = data.telegram_chat_id
    db.commit()
    return {"pesan": "Notifikasi Telegram berhasil dihubungkan!"}

@router.get("/api/patch-db")
def patch_database(db: Session = Depends(get_db)):
    """Jalur rahasia untuk memperbarui tabel database di Railway secara otomatis"""
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN telegram_chat_id VARCHAR(50) DEFAULT NULL;"))
        db.commit()
        return {"pesan": "Sukses! Kolom telegram_chat_id berhasil ditambahkan ke database MySQL Anda."}
    except Exception as e:
        return {"pesan": f"Database sudah diperbarui atau terjadi kesalahan: {str(e)}"}