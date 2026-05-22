from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# KONFIGURASI DATABASE
# Ganti 'root' dan 'password_kamu' sesuai dengan pengaturan phpMyAdmin di komputermu.
# Jika kamu menggunakan XAMPP/LAMPP bawaan, biasanya password-nya kosong (hanya 'root:@localhost').
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:Adzha123-@localhost:3306/db_agridss"

# Membuat 'mesin' penghubung ke MySQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Membuat sesi database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk membuat model/tabel nantinya
Base = declarative_base()