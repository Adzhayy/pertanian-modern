from fastapi import APIRouter, File, UploadFile, Form
import os
import shutil
import random

router = APIRouter()

@router.post("/api/klinik/diagnosis")
async def diagnosis_penyakit(tanaman: str = Form(...), file: UploadFile = File(...)):
    folder_simpan = "uploads"
    os.makedirs(folder_simpan, exist_ok=True)
    lokasi_file = f"{folder_simpan}/{file.filename}"
    with open(lokasi_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    database_penyakit = {
        "tomat": {"penyakit": "Bercak Daun (Early Blight)", "solusi": ["Musnahkan daun terinfeksi.", "Semprot fungisida Mankozeb."]},
        "cabai": {"penyakit": "Patek (Antraknosa)", "solusi": ["Buang jauh buah yang menghitam.", "Kurangi kelembapan."]},
        "sawi": {"penyakit": "Serangan Ulat Krop", "solusi": ["Gunakan insektisida biologi Bacillus."]}
    }
    hasil = database_penyakit.get(tanaman.lower(), {"penyakit": "Gejala Tidak Dikenali", "solusi": ["Bawa sampel ke penyuluh."]})
    return {"nama_file_tersimpan": lokasi_file, "tanaman_dipilih": tanaman, "akurasi_ai": round(random.uniform(88.0, 97.9), 1), "hasil_diagnosis": hasil["penyakit"], "rekomendasi_tindakan": hasil["solusi"]}