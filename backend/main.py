from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal
import models
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from routes.lahan import proses_broadcast_otomatis



# Import rute yang sudah kita pecah
from routes import lahan, tanah, klinik, auth_user

# Membuat tabel-tabel di MySQL
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AgriDSS API",
    description="Backend Server Tersistematis untuk Sistem Pertanian Terpadu"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.on_event("startup")
def start_scheduler():
    scheduler = BackgroundScheduler()
    # Mengunci zona waktu
    tz = pytz.timezone('Asia/Jakarta')
    
    # Menyetel jadwal eksekusi: Setiap hari jam 06:00
    scheduler.add_job(proses_broadcast_otomatis, 'cron', hour=6, minute=0, timezone=tz)
    
    # Menyalakan mesin alarm
    scheduler.start()
    print("⏰ Mesin alarm otomatis berhasil dihidupkan!")

# Memasang (mendaftarkan) rute-rute yang ada di folder routes
app.include_router(auth_user.router)
app.include_router(lahan.router)
app.include_router(tanah.router)
app.include_router(klinik.router)