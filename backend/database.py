import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Coba ambil kunci URL dari server awan (Railway) TERLEBIH DAHULU
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Jika di awan kosong (berarti sedang dijalankan di laptop), baru pakai lokal
if not DATABASE_URL:
    load_dotenv() # Muat file .env lokal
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "mysql+pymysql://root:@127.0.0.1:3306/pertanian-modern" # Default lokal
    )

# Membuat 'mesin' penghubung ke MySQL
engine = create_engine(DATABASE_URL)

# Membuat sesi database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk membuat model/tabel
Base = declarative_base()

# --- FUNGSI INJEKSI SESI DATABASE ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()