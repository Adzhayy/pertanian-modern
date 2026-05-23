import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Memuat variabel rahasia dari file .env
load_dotenv()

# Mengambil URL dari .env, jika tidak ada, gunakan nilai default kosong
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/db_agridss")

# Membuat 'mesin' penghubung ke MySQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Membuat sesi database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk membuat model/tabel
Base = declarative_base()