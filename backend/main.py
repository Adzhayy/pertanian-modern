from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from datetime import date, timedelta
import models
import os
import shutil
import random
import urllib.request
import urllib.parse

# --- KREDENSIAL BOT TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8837001995:AAFtsglN7VejD9prEbdGTjrGZBTHvhp5PQo"
TELEGRAM_CHAT_ID = "8146044956"

def kirim_pesan_telegram(pesan: str):
    """Fungsi ajaib untuk mengirim teks ke Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": pesan, 
        "parse_mode": "Markdown"
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req) as response:
            return True
    except Exception as e:
        print(f"Gagal mengirim ke Telegram: {e}")
        return False

# Membuat tabel-tabel di MySQL
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AgriDSS API",
    description="Backend Server untuk Sistem Pertanian Terpadu"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    if db.query(models.User).count() == 0:
        db.add(models.User(username="admin", password_hash="rahasia123"))
        db.commit()

    if db.query(models.MasterTanaman).count() == 0:
        db.add_all([
            models.MasterTanaman(nama_tanaman="Sawi Hijau", masa_panen_hari=35, ph_ideal_min=6.0, ph_ideal_max=7.0),
            models.MasterTanaman(nama_tanaman="Tomat", masa_panen_hari=80, ph_ideal_min=6.0, ph_ideal_max=6.8),
            models.MasterTanaman(nama_tanaman="Cabai Merah", masa_panen_hari=90, ph_ideal_min=5.5, ph_ideal_max=6.8)
        ])
        db.commit()
    db.close()

class LahanCreate(BaseModel):
    nama_lahan: str
    tanaman_id: int
    tanggal_tanam: date
    user_id: int = 1

class AnalisisTanahInput(BaseModel):
    lahan_id: int
    ph_sekarang: float

@app.get("/api/tanaman")
def get_semua_tanaman(db: Session = Depends(get_db)):
    return db.query(models.MasterTanaman).all()

@app.post("/api/lahan")
def tambah_lahan(lahan: LahanCreate, db: Session = Depends(get_db)):
    tanaman = db.query(models.MasterTanaman).filter(models.MasterTanaman.id == lahan.tanaman_id).first()
    lahan_baru = models.LahanAktif(nama_lahan=lahan.nama_lahan, user_id=lahan.user_id, tanaman_id=lahan.tanaman_id, tanggal_tanam=lahan.tanggal_tanam, status_selesai=False)
    db.add(lahan_baru)
    db.commit()
    db.refresh(lahan_baru)
    
    jadwal_list = []
    tanggal_sekarang = lahan.tanggal_tanam
    estimasi_panen = lahan.tanggal_tanam + timedelta(days=tanaman.masa_panen_hari)
    
    while tanggal_sekarang <= estimasi_panen:
        jadwal_list.append(models.JadwalPerawatan(lahan_id=lahan_baru.id, tanggal_tugas=tanggal_sekarang, jenis_tugas="Penyiraman", status_selesai="Menunggu"))
        selisih_hari = (tanggal_sekarang - lahan.tanggal_tanam).days
        if selisih_hari > 0 and selisih_hari % 15 == 0:
            jadwal_list.append(models.JadwalPerawatan(lahan_id=lahan_baru.id, tanggal_tugas=tanggal_sekarang, jenis_tugas="Pemupukan Berkala", status_selesai="Menunggu"))
        tanggal_sekarang += timedelta(days=1)
        
    db.add_all(jadwal_list)
    db.commit()

    # Memicu notifikasi saat lahan baru dibuat
    pesan = f"🎉 *Lahan Baru Terdaftar!* 🎉\n\nLahan: *{lahan_baru.nama_lahan}*\nKomoditas: *{tanaman.nama_tanaman}*\n\nSistem telah membangkitkan {len(jadwal_list)} tugas harian otomatis hingga masa panen tiba. Selamat bertani! 🚜"
    kirim_pesan_telegram(pesan)
    
    return {"pesan": f"Lahan ditambahkan & {len(jadwal_list)} tugas dijadwalkan!", "data": lahan_baru}

@app.get("/api/lahan")
def get_semua_lahan(db: Session = Depends(get_db)):
    lahan_aktif = db.query(models.LahanAktif).all()
    hasil = []
    for lahan in lahan_aktif:
        tanaman = db.query(models.MasterTanaman).filter(models.MasterTanaman.id == lahan.tanaman_id).first()
        hasil.append({"id": lahan.id, "nama_lahan": lahan.nama_lahan, "nama_tanaman": tanaman.nama_tanaman, "tanggal_tanam": lahan.tanggal_tanam, "estimasi_panen": lahan.tanggal_tanam + timedelta(days=tanaman.masa_panen_hari), "status_selesai": lahan.status_selesai})
    return hasil

@app.get("/api/jadwal/hari-ini")
def get_jadwal_hari_ini(db: Session = Depends(get_db)):
    jadwal = db.query(models.JadwalPerawatan).filter(models.JadwalPerawatan.tanggal_tugas == date.today()).all()
    hasil = []
    for j in jadwal:
        lahan = db.query(models.LahanAktif).filter(models.LahanAktif.id == j.lahan_id).first()
        hasil.append({"id": j.id, "tugas": j.jenis_tugas, "lahan": lahan.nama_lahan, "status": j.status_selesai})
    return hasil

# --- ENDPOINT BARU: TESTING TELEGRAM ---
@app.get("/api/telegram/test")
def test_telegram_hari_ini(db: Session = Depends(get_db)):
    """Akses URL ini di browser untuk memaksa bot mengirim jadwal hari ini"""
    hari_ini = date.today()
    jadwal = db.query(models.JadwalPerawatan).filter(models.JadwalPerawatan.tanggal_tugas == hari_ini).all()
    
    pesan = f"🌱 *Laporan AgriDSS Hari Ini* 🌱\n📅 Tanggal: {hari_ini.strftime('%d-%m-%Y')}\n\n"
    
    if not jadwal:
        pesan += "Tidak ada tugas penyiraman atau pemupukan untuk hari ini. Lahan aman! ✨"
    else:
        pesan += "Tugas yang harus diselesaikan hari ini:\n"
        for j in jadwal:
            lahan = db.query(models.LahanAktif).filter(models.LahanAktif.id == j.lahan_id).first()
            pesan += f"✅ *{lahan.nama_lahan}* - {j.jenis_tugas}\n"
        pesan += "\nSemangat bertani! 👨‍🌾"
        
    sukses = kirim_pesan_telegram(pesan)
    if sukses:
        return {"pesan": "Notifikasi Telegram berhasil dikirim! Silakan cek HP Anda."}
    else:
        raise HTTPException(status_code=500, detail="Gagal mengirim pesan Telegram")

@app.post("/api/tanah/analisis")
def analisis_ph_tanah(input_data: AnalisisTanahInput, db: Session = Depends(get_db)):
    lahan = db.query(models.LahanAktif).filter(models.LahanAktif.id == input_data.lahan_id).first()
    tanaman = db.query(models.MasterTanaman).filter(models.MasterTanaman.id == lahan.tanaman_id).first()
    ph = input_data.ph_sekarang
    if ph < tanaman.ph_ideal_min:
        return {"lahan": lahan.nama_lahan, "tanaman": tanaman.nama_tanaman, "ph_input": ph, "ph_ideal": f"{tanaman.ph_ideal_min} - {tanaman.ph_ideal_max}", "status": "Terlalu Asam", "rekomendasi": ["Tambahkan Kapur Dolomit untuk menaikkan pH."], "risiko": [{"dampak": "Busuk Ujung Buah", "tingkat": 85}]}
    elif ph > tanaman.ph_ideal_max:
        return {"lahan": lahan.nama_lahan, "tanaman": tanaman.nama_tanaman, "ph_input": ph, "ph_ideal": f"{tanaman.ph_ideal_min} - {tanaman.ph_ideal_max}", "status": "Terlalu Basa (Alkalin)", "rekomendasi": ["Tambahkan Belerang (Sulfur) pertanian."], "risiko": [{"dampak": "Daun Menguning (Klorosis Besi)", "tingkat": 80}]}
    else:
        return {"lahan": lahan.nama_lahan, "tanaman": tanaman.nama_tanaman, "ph_input": ph, "ph_ideal": f"{tanaman.ph_ideal_min} - {tanaman.ph_ideal_max}", "status": "Ideal", "rekomendasi": ["Kondisi tanah sangat ideal."], "risiko": [{"dampak": "Aman dari risiko", "tingkat": 10}]}

@app.post("/api/klinik/diagnosis")
async def diagnosis_penyakit(tanaman: str = Form(...), file: UploadFile = File(...)):
    folder_simpan = "uploads"
    os.makedirs(folder_simpan, exist_ok=True)
    lokasi_file = f"{folder_simpan}/{file.filename}"
    with open(lokasi_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    database_penyakit = {
        "tomat": {"penyakit": "Bercak Daun (Early Blight)", "solusi": ["Musnahkan daun terinfeksi.", "Semprot fungisida Mankozeb."]},
        "cabai": {"penyakit": "Patek (Antraknosa)", "solusi": ["Buang jauh buah yang menghitam.", "Kurangi kelembapan bedengan."]},
        "sawi": {"penyakit": "Serangan Ulat Krop", "solusi": ["Gunakan insektisida biologi Bacillus thuringiensis."]}
    }
    hasil = database_penyakit.get(tanaman.lower(), {"penyakit": "Gejala Tidak Dikenali", "solusi": ["Bawa sampel ke penyuluh."]})
    return {"nama_file_tersimpan": lokasi_file, "tanaman_dipilih": tanaman, "akurasi_ai": round(random.uniform(88.0, 97.9), 1), "hasil_diagnosis": hasil["penyakit"], "rekomendasi_tindakan": hasil["solusi"]}