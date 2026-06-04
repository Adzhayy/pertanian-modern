import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Memuat variabel rahasia dari file .env
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://root:@127.0.0.1:3306/pertanian-modern" # <-- Ganti dengan nama db lokalmu
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