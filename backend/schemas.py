from pydantic import BaseModel
from datetime import date

class LahanCreate(BaseModel):
    nama_lahan: str
    tanaman_id: int
    tanggal_tanam: date
    user_id: int = 1

class AnalisisTanahInput(BaseModel):
    lahan_id: int
    ph_sekarang: float