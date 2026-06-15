from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
import models, schemas
from database import get_db, SessionLocal
from utils import kirim_pesan_telegram
from auth import get_current_user

router = APIRouter()

@router.get("/api/tanaman")
def get_semua_tanaman(db: Session = Depends(get_db)):
    return db.query(models.MasterTanaman).all()

@router.post("/api/lahan")
def tambah_lahan(lahan: schemas.LahanCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    tanaman = db.query(models.MasterTanaman).filter(models.MasterTanaman.id == lahan.tanaman_id).first()
    if not tanaman:
        raise HTTPException(status_code=404, detail="ID Tanaman tidak ditemukan di database")
    lahan_baru = models.LahanAktif(nama_lahan=lahan.nama_lahan, user_id=current_user.id, tanaman_id=lahan.tanaman_id, tanggal_tanam=lahan.tanggal_tanam, status_selesai=False)
    db.add(lahan_baru)
    db.commit()
    db.refresh(lahan_baru)
    
    jadwal_list = []
    tanggal_sekarang = lahan.tanggal_tanam
    estimasi_panen = lahan.tanggal_tanam + timedelta(days=tanaman.masa_panen_hari)
    
    while tanggal_sekarang <= estimasi_panen:
        jadwal_list.append(models.JadwalPerawatan(lahan_id=lahan_baru.id, tanggal_tugas=tanggal_sekarang, jenis_tugas="Penyiraman", status_selesai="Menunggu"))
        if (tanggal_sekarang - lahan.tanggal_tanam).days > 0 and (tanggal_sekarang - lahan.tanggal_tanam).days % 15 == 0:
            jadwal_list.append(models.JadwalPerawatan(lahan_id=lahan_baru.id, tanggal_tugas=tanggal_sekarang, jenis_tugas="Pemupukan Berkala", status_selesai="Menunggu"))
        tanggal_sekarang += timedelta(days=1)
        
    db.add_all(jadwal_list)
    db.commit()

    kirim_pesan_telegram(f"🎉 *Lahan Baru Terdaftar!*\n\nLahan: *{lahan_baru.nama_lahan}*\nKomoditas: *{tanaman.nama_tanaman}*\n\nSistem menjadwalkan {len(jadwal_list)} tugas harian.",current_user.telegram_chat_id)
    return {"pesan": "Berhasil!", "data": lahan_baru}

@router.get("/api/lahan")
def get_semua_lahan(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    lahan_aktif = db.query(models.LahanAktif).filter(models.LahanAktif.user_id == current_user.id).all()
    return [{"id": l.id, "nama_lahan": l.nama_lahan, "nama_tanaman": db.query(models.MasterTanaman).filter(models.MasterTanaman.id == l.tanaman_id).first().nama_tanaman, "tanggal_tanam": l.tanggal_tanam, "estimasi_panen": l.tanggal_tanam + timedelta(days=db.query(models.MasterTanaman).filter(models.MasterTanaman.id == l.tanaman_id).first().masa_panen_hari), "status_selesai": l.status_selesai} for l in lahan_aktif]

# --- FITUR BARU: HAPUS LAHAN ---
@router.delete("/api/lahan/{lahan_id}")
def hapus_lahan(lahan_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 1. Cari data lahan di database
    lahan = db.query(models.LahanAktif).filter(models.LahanAktif.id == lahan_id).first()
    
    if not lahan:
        raise HTTPException(status_code=404, detail="Lahan tidak ditemukan")
        
    # 2. Keamanan: Pastikan yang menghapus adalah pemilik asli lahan tersebut
    if lahan.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Anda tidak berhak menghapus lahan ini!")

    # 3. Hapus semua jadwal perawatan yang berkaitan dengan lahan ini dulu (agar tidak jadi sampah data)
    db.query(models.JadwalPerawatan).filter(models.JadwalPerawatan.lahan_id == lahan_id).delete()
    
    # 4. Hapus lahan utamanya
    db.delete(lahan)
    db.commit()
    
    # Opsional: Kirim notif ke Telegram kalau ada yang dihapus
    kirim_pesan_telegram(f"🗑️ *Lahan Dihapus*\nLahan *{lahan.nama_lahan}* beserta seluruh jadwalnya telah dihapus oleh pengguna.",current_user.telegram_chat_id)
    
    return {"pesan": "Lahan berhasil dihapus selamanya!"}

# --- 1. MESIN BROADCAST INTI (Berjalan di latar belakang) ---
def proses_broadcast_otomatis():
    # Buka koneksi database sendiri tanpa bantuan API
    db = SessionLocal()
    try:
        hari_ini = date.today()
        jadwal_hari_ini = db.query(models.JadwalPerawatan).filter(
            models.JadwalPerawatan.tanggal_tugas == hari_ini,
            models.JadwalPerawatan.status_selesai == "Menunggu"
        ).all()

        if not jadwal_hari_ini:
            return "Aman! Tidak ada tugas yang menunggu hari ini."

        tugas_per_user = {}
        for jadwal in jadwal_hari_ini:
            lahan = db.query(models.LahanAktif).filter(models.LahanAktif.id == jadwal.lahan_id).first()
            if not lahan: continue
            
            user = db.query(models.User).filter(models.User.id == lahan.user_id).first()
            if not user or not user.telegram_chat_id: continue 
            
            if user.id not in tugas_per_user:
                tugas_per_user[user.id] = {"chat_id": user.telegram_chat_id, "tugas": []}
            tugas_per_user[user.id]["tugas"].append(f"🌱 *{lahan.nama_lahan}* - {jadwal.jenis_tugas}")

        jumlah_terkirim = 0
        for user_id, data in tugas_per_user.items():
            pesan = f"🌅 *Selamat Pagi, Petani!* 🌅\n📅 {hari_ini.strftime('%d-%m-%Y')}\n\nBerikut adalah tugas perawatan lahan Anda hari ini yang menunggu diselesaikan:\n\n"
            for t in data["tugas"]:
                pesan += f"• {t}\n"
            pesan += "\nSemangat bertani hari ini! Jangan lupa 'Tandai Selesai' di Dashboard ya! 🚜"
            
            sukses = kirim_pesan_telegram(pesan, data["chat_id"])
            if sukses: jumlah_terkirim += 1

        return f"Berhasil mengirim pengingat pagi ke {jumlah_terkirim} petani!"
    finally:
        # Selalu tutup database setelah selesai agar peladen tidak berat
        db.close()

# --- 2. JALUR API UNTUK TOMBOL MANUAL DI DASHBOARD ---
@router.get("/api/telegram/broadcast")
def broadcast_pengingat_harian():
    # Tombol manual akan memanggil mesin inti di atas
    hasil = proses_broadcast_otomatis()
    return {"pesan": hasil}

@router.get("/api/jadwal/hari-ini")
def get_jadwal_hari_ini(db: Session = Depends(get_db)):
    jadwal = db.query(models.JadwalPerawatan).filter(models.JadwalPerawatan.tanggal_tugas == date.today()).all()
    return [{"id": j.id, "tugas": j.jenis_tugas, "lahan": db.query(models.LahanAktif).filter(models.LahanAktif.id == j.lahan_id).first().nama_lahan, "status": j.status_selesai} for j in jadwal]

@router.put("/api/jadwal/{jadwal_id}/selesai")
def selesaikan_tugas(jadwal_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    jadwal = db.query(models.JadwalPerawatan).filter(models.JadwalPerawatan.id == jadwal_id).first()
    if not jadwal:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")

    lahan = db.query(models.LahanAktif).filter(models.LahanAktif.id == jadwal.lahan_id).first()
    if lahan.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke jadwal ini")

    jadwal.status_selesai = "Selesai"
    db.commit()

    kirim_pesan_telegram(
        f"✅ *Tugas Selesai!*\n\n"
        f"Lahan: *{lahan.nama_lahan}*\n"
        f"Tugas: *{jadwal.jenis_tugas}* telah selesai dikerjakan. Kerja bagus! 👨‍🌾",
        current_user.telegram_chat_id
    )
    
    return {"pesan": "Tugas berhasil ditandai selesai!"}