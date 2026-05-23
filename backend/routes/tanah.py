from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models, schemas
from database import get_db

router = APIRouter()

@router.post("/api/tanah/analisis")
def analisis_ph_tanah(input_data: schemas.AnalisisTanahInput, db: Session = Depends(get_db)):
    lahan = db.query(models.LahanAktif).filter(models.LahanAktif.id == input_data.lahan_id).first()
    tanaman = db.query(models.MasterTanaman).filter(models.MasterTanaman.id == lahan.tanaman_id).first()
    ph = input_data.ph_sekarang
    if ph < tanaman.ph_ideal_min:
        return {"lahan": lahan.nama_lahan, "tanaman": tanaman.nama_tanaman, "ph_input": ph, "ph_ideal": f"{tanaman.ph_ideal_min}-{tanaman.ph_ideal_max}", "status": "Terlalu Asam", "rekomendasi": ["Tambahkan Kapur Dolomit."], "risiko": [{"dampak": "Busuk Ujung Buah", "tingkat": 85}]}
    elif ph > tanaman.ph_ideal_max:
        return {"lahan": lahan.nama_lahan, "tanaman": tanaman.nama_tanaman, "ph_input": ph, "ph_ideal": f"{tanaman.ph_ideal_min}-{tanaman.ph_ideal_max}", "status": "Terlalu Basa", "rekomendasi": ["Tambahkan Belerang (Sulfur)."], "risiko": [{"dampak": "Klorosis Besi", "tingkat": 80}]}
    else:
        return {"lahan": lahan.nama_lahan, "tanaman": tanaman.nama_tanaman, "ph_input": ph, "ph_ideal": f"{tanaman.ph_ideal_min}-{tanaman.ph_ideal_max}", "status": "Ideal", "rekomendasi": ["Kondisi tanah sangat ideal."], "risiko": [{"dampak": "Aman", "tingkat": 10}]}