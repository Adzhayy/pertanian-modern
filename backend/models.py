from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    telegram_chat_id = Column(String(50), nullable=True) # Untuk notif bot Telegram
    
    # Relasi: 1 User bisa punya banyak lahan aktif
    lahan = relationship("LahanAktif", back_populates="pemilik")

class MasterTanaman(Base):
    __tablename__ = "master_tanaman"
    
    id = Column(Integer, primary_key=True, index=True)
    nama_tanaman = Column(String(50), index=True) # Contoh: "Tomat", "Cabai"
    masa_panen_hari = Column(Integer)             # Berapa hari sampai panen
    ph_ideal_min = Column(Float)                  # Rentang pH (contoh: 6.0)
    ph_ideal_max = Column(Float)                  # Rentang pH (contoh: 7.0)

class LahanAktif(Base):
    __tablename__ = "lahan_aktif"
    
    id = Column(Integer, primary_key=True, index=True)
    nama_lahan = Column(String(100))               # Contoh: "Bedengan A"
    user_id = Column(Integer, ForeignKey("users.id"))
    tanaman_id = Column(Integer, ForeignKey("master_tanaman.id"))
    tanggal_tanam = Column(Date)
    status_selesai = Column(Boolean, default=False) # False = sedang ditanam, True = sudah panen
    
    # Relasi
    pemilik = relationship("User", back_populates="lahan")
    # Relasi ke tabel jadwal (akan dibuat nanti)
    jadwal = relationship("JadwalPerawatan", back_populates="lahan", cascade="all, delete-orphan")

class JadwalPerawatan(Base):
    __tablename__ = "jadwal_perawatan"
    
    id = Column(Integer, primary_key=True, index=True)
    lahan_id = Column(Integer, ForeignKey("lahan_aktif.id"))
    tanggal_tugas = Column(Date)
    jenis_tugas = Column(String(50))              # Contoh: "Siram", "Pupuk"
    status_selesai = Column(String(50), default="Menunggu") # Menunggu, Selesai, Ditunda Cuaca
    
    lahan = relationship("LahanAktif", back_populates="jadwal")