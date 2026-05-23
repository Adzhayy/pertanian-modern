from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
import models, schemas
from database import get_db
from utils import kirim_pesan_telegram

router = APIRouter()

@router.get("/api/tanaman")
def get_semua_tanaman(db: Session = Depends(get_db)):
    return db.query(models.MasterTanaman).all()

@router.post("/api/lahan")
def tambah_lahan(lahan: schemas.LahanCreate, db: Session = Depends(get_db)):
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
        if (tanggal_sekarang - lahan.tanggal_tanam).days > 0 and (tanggal_sekarang - lahan.tanggal_tanam).days % 15 == 0:
            jadwal_list.append(models.JadwalPerawatan(lahan_id=lahan_baru.id, tanggal_tugas=tanggal_sekarang, jenis_tugas="Pemupukan Berkala", status_selesai="Menunggu"))
        tanggal_sekarang += timedelta(days=1)
        
    db.add_all(jadwal_list)
    db.commit()

    kirim_pesan_telegram(f"🎉 *Lahan Baru Terdaftar!*\n\nLahan: *{lahan_baru.nama_lahan}*\nKomoditas: *{tanaman.nama_tanaman}*\n\nSistem menjadwalkan {len(jadwal_list)} tugas harian.")
    return {"pesan": "Berhasil!", "data": lahan_baru}

@router.get("/api/lahan")
def get_semua_lahan(db: Session = Depends(get_db)):
    lahan_aktif = db.query(models.LahanAktif).all()
    return [{"id": l.id, "nama_lahan": l.nama_lahan, "nama_tanaman": db.query(models.MasterTanaman).filter(models.MasterTanaman.id == l.tanaman_id).first().nama_tanaman, "tanggal_tanam": l.tanggal_tanam, "estimasi_panen": l.tanggal_tanam + timedelta(days=db.query(models.MasterTanaman).filter(models.MasterTanaman.id == l.tanaman_id).first().masa_panen_hari), "status_selesai": l.status_selesai} for l in lahan_aktif]

@router.get("/api/jadwal/hari-ini")
def get_jadwal_hari_ini(db: Session = Depends(get_db)):
    jadwal = db.query(models.JadwalPerawatan).filter(models.JadwalPerawatan.tanggal_tugas == date.today()).all()
    return [{"id": j.id, "tugas": j.jenis_tugas, "lahan": db.query(models.LahanAktif).filter(models.LahanAktif.id == j.lahan_id).first().nama_lahan, "status": j.status_selesai} for j in jadwal]

@router.get("/api/telegram/test")
def test_telegram_hari_ini(db: Session = Depends(get_db)):
    hari_ini = date.today()
    jadwal = db.query(models.JadwalPerawatan).filter(models.JadwalPerawatan.tanggal_tugas == hari_ini).all()
    pesan = f"🌱 *Laporan AgriDSS Hari Ini* 🌱\n📅 {hari_ini.strftime('%d-%m-%Y')}\n\n"
    if not jadwal:
        pesan += "Lahan aman! ✨"
    else:
        for j in jadwal:
            pesan += f"✅ *{db.query(models.LahanAktif).filter(models.LahanAktif.id == j.lahan_id).first().nama_lahan}* - {j.jenis_tugas}\n"
    sukses = kirim_pesan_telegram(pesan)
    if sukses: return {"pesan": "Notifikasi dikirim!"}
    raise HTTPException(status_code=500, detail="Gagal kirim")