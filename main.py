import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ===== DATABASE SETUP =====
SQLALCHEMY_DATABASE_URL = "sqlite:///./supervisi.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ===== MODELS =====
class Guru(Base):
    __tablename__ = "guru"
    id = Column(Integer, primary_key=True, index=True)
    nip = Column(String, default="")
    nama_guru = Column(String, index=True)
    sekolah = Column(String)
    jenjang = Column(String)
    mata_pelajaran = Column(String)
    kelas_semester = Column(String)


class Supervisi(Base):
    __tablename__ = "supervisi"
    guru_id = Column(Integer, primary_key=True, index=True)
    administrasi_data = Column(Text, default="{}")
    administrasi_skor = Column(Float, default=0)
    administrasi_persen = Column(Float, default=0)
    administrasi_predikat = Column(String, default="-")
    atp_data = Column(Text, default="{}")
    atp_skor = Column(Float, default=0)
    atp_persen = Column(Float, default=0)
    atp_predikat = Column(String, default="-")
    modul_ajar_data = Column(Text, default="{}")
    modul_ajar_skor = Column(Float, default=0)
    modul_ajar_persen = Column(Float, default=0)
    modul_ajar_predikat = Column(String, default="-")
    observasi_data = Column(Text, default="{}")
    observasi_skor = Column(Float, default=0)
    observasi_persen = Column(Float, default=0)
    observasi_predikat = Column(String, default="-")
    refleksi = Column(Text, default="")
    umpan_balik = Column(Text, default="")
    tindak_lanjut = Column(Text, default="")


Base.metadata.create_all(bind=engine)


# ===== SCHEMAS =====
class GuruCreate(BaseModel):
    nama_guru: str
    sekolah: str
    jenjang: str
    mata_pelajaran: str
    kelas_semester: str
    nip: str = ""


class SupervisiSubmit(BaseModel):
    guru_id: int
    kategori: str
    data_jawaban: dict


class RefleksiSubmit(BaseModel):
    guru_id: int
    refleksi: str


# ===== APP SETUP =====
app = FastAPI(title="Aplikasi Supervisi Guru")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===== HELPERS =====
def get_predikat(persen: float) -> str:
    if persen >= 91:
        return "Sangat Baik"
    if persen >= 81:
        return "Baik"
    if persen >= 71:
        return "Cukup"
    return "Kurang"


MAX_SKOR = {
    "administrasi": 34,
    "atp": 24,
    "modul_ajar": 48,
    "observasi": 76,
}


def generate_feedback(observasi_persen: float, refleksi: str) -> tuple:
    refleksi_lower = refleksi.lower()

    # 1. Narasi Umpan Balik Motivasi
    if observasi_persen >= 91:
        ub = (
            f"Luar biasa! Praktik pembelajaran yang Anda tampilkan sangat inspiratif dengan pencapaian skor {observasi_persen}%. "
            "Keterlibatan aktif siswa dan penguasaan kelas yang Anda tunjukkan mencerminkan dedikasi serta profesionalisme yang tinggi. "
            "Teruslah menjadi teladan, berinovasi dalam media pembelajaran, dan bagikan praktik baik ini kepada rekan-rekan guru lainnya."
        )
    elif observasi_persen >= 81:
        ub = (
            f"Sangat baik! Pembelajaran di kelas berjalan dengan lancar dan kondusif (skor {observasi_persen}%). "
            "Anda telah berhasil menciptakan suasana belajar yang menyenangkan. Mari tingkatkan kembali sedikit variasi pada "
            "pemanfaatan media interaktif dan metode pembelajaran berbasis aktivitas agar siswa semakin bersemangat dan berdaya."
        )
    elif observasi_persen >= 71:
        ub = (
            f"Performa yang cukup baik dan berpotensi (skor {observasi_persen}%). Anda telah berusaha maksimal dalam menyampaikan materi. "
            "Setiap proses mengajar adalah ruang untuk bertumbuh. Fokuslah pada penguatan keterlibatan siswa dan penggunaan strategi "
            "pembelajaran yang lebih kontekstual agar suasana kelas menjadi jauh lebih hidup dan bermakna."
        )
    else:
        ub = (
            f"Terima kasih atas dedikasi dan kerja keras Anda di kelas (skor {observasi_persen}%). Mengajar adalah seni yang terus berkembang, "
            "dan setiap tantangan adalah kesempatan emas untuk belajar. Jangan berkecil hati; fokuslah pada penguasaan manajemen kelas, "
            "penyusunan langkah pembelajaran yang lebih terstruktur, serta pelibatan siswa secara aktif. Anda pasti bisa mencapai hasil yang jauh lebih baik!"
        )

    # Tambahan berdasarkan Refleksi Guru
    if "sulit" in refleksi_lower or "kesulitan" in refleksi_lower or "kendala" in refleksi_lower:
        ub += (
            "\n\nKeberanian Anda dalam mengenali kendala saat bernalar dan berrefleksi adalah langkah awal seorang pendidik yang hebat. "
            "Kami siap mendukung dan mendampingi Anda melalui diskusi serta kolaborasi agar kendala tersebut dapat teratasi dengan baik."
        )
    elif "semangat" in refleksi_lower or "antusias" in refleksi_lower or "senang" in refleksi_lower:
        ub += (
            "\n\nRefleksi Anda menunjukkan energi positif dan antusiasme yang luar biasa. "
            "Pertahankan optimisme ini, karena semangat Anda adalah kunci utama keberhasilan belajar para siswa!"
        )

    # 2. Narasi Tindak Lanjut Konstruktif & Penuh Motivasi
    if observasi_persen >= 81:
        tindak = (
            "1. Lakukan refleksi mandiri secara konsisten di setiap akhir pekan.\n"
            "2. Bagikan praktik baik (best practice) hasil pembelajaran Anda dalam kegiatan Komunitas Belajar (Kombel) atau KKG/MGMP sekolah.\n"
            "3. Cobalah eksplorasi strategi pembelajaran digital berbasis AI/interaktif untuk memperkaya pengalaman belajar siswa."
        )
    elif observasi_persen >= 71:
        tindak = (
            "1. Diskusikan rancangan modul ajar dan pemilihan media pembelajaran bersama rekan sejawat atau guru pamong.\n"
            "2. Ikuti pelatihan singkat / webinar terkait strategi manajemen kelas dan diferensiasi pembelajaran.\n"
            "3. Lakukan observasi peer-teaching (mengamati rekan guru senior mengajar) untuk mendapatkan inspirasi baru."
        )
    else:
        tindak = (
            "1. Jadwalkan sesi pendampingan khusus (coaching/mentoring) dengan Kepala Sekolah atau Pengawas dalam kurun waktu 2 minggu ke depan.\n"
            "2. Susun ulang rencana pembelajaran (Modul Ajar) yang fokus pada metode pembelajaran aktif dan mudah dipahami siswa.\n"
            "3. Lakukan observasi ulang kelas dengan suasana yang lebih rileks dan penuh persiapan."
        )

    return ub, tindak


def generate_kesimpulan_narasi(sup: Supervisi, guru: Guru) -> str:
    if not sup:
        return "Belum ada data supervisi yang diisi."

    admin_p = sup.administrasi_persen or 0
    atp_p = sup.atp_persen or 0
    modul_p = sup.modul_ajar_persen or 0
    obs_p = sup.observasi_persen or 0

    # Evaluasi Ringkas Pra Observasi
    pra_notes = []
    if admin_p >= 81:
        pra_notes.append(f"administrasi amat lengkap ({admin_p}%)")
    else:
        pra_notes.append(f"administrasi perlu penguatan ({admin_p}%)")

    if atp_p >= 81:
        pra_notes.append(f"alur tujuan pembelajaran (ATP) tersusun runtut ({atp_p}%)")
    else:
        pra_notes.append(f"ATP perlu diselaraskan ({atp_p}%)")

    if modul_p >= 81:
        pra_notes.append(f"modul ajar dirancang sangat baik ({modul_p}%)")
    else:
        pra_notes.append(f"modul ajar memerlukan penyempurnaan ({modul_p}%)")

    narasi_pra = "Pada tahap Pra Observasi, " + ", ".join(pra_notes) + "."

    # Evaluasi Observasi
    if obs_p >= 91:
        narasi_obs = f" Pelaksanaan pembelajaran di kelas sangat memukau ({obs_p}%) dan menjadi inspirasi."
    elif obs_p >= 81:
        narasi_obs = f" Pelaksanaan pembelajaran di kelas berjalan efektif dan kondusif ({obs_p}%)."
    elif obs_p >= 71:
        narasi_obs = f" Pelaksanaan pembelajaran di kelas cukup baik ({obs_p}%) dengan peluang besar untuk ditingkatkan."
    else:
        narasi_obs = f" Pelaksanaan pembelajaran di kelas membutuhkan perhatian dan pendampingan bersama ({obs_p}%)."

    # Motivasi Penutup Kesimpulan
    narasi_penutup = f" Berdasarkan potensi yang dimiliki Guru {guru.nama_guru}, diharapkan tindak lanjut yang disepakati dapat dilaksanakan dengan penuh semangat demi kemajuan belajar peserta didik."

    return f"Bapak/Ibu {guru.nama_guru} ({guru.mata_pelajaran}): {narasi_pra}{narasi_obs}{narasi_penutup}"

# ===== ROUTES =====
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/guru")
def create_guru(guru: GuruCreate, db: Session = Depends(get_db)):
    db_guru = Guru(
        nip=guru.nip,
        nama_guru=guru.nama_guru,
        sekolah=guru.sekolah,
        jenjang=guru.jenjang,
        mata_pelajaran=guru.mata_pelajaran,
        kelas_semester=guru.kelas_semester,
    )
    db.add(db_guru)
    db.commit()
    db.refresh(db_guru)
    return {"id": db_guru.id, "message": "Guru berhasil disimpan"}


@app.get("/api/guru/{guru_id}")
def get_guru(guru_id: int, db: Session = Depends(get_db)):
    guru = db.query(Guru).filter(Guru.id == guru_id).first()
    if not guru:
        raise HTTPException(status_code=404, detail="Guru tidak ditemukan")
    sup = db.query(Supervisi).filter(Supervisi.guru_id == guru_id).first()
    return {
        "guru": {
            "id": guru.id,
            "nip": guru.nip,
            "nama_guru": guru.nama_guru,
            "sekolah": guru.sekolah,
            "jenjang": guru.jenjang,
            "mata_pelajaran": guru.mata_pelajaran,
            "kelas_semester": guru.kelas_semester,
        },
        "supervisi": {
            "administrasi_predikat": sup.administrasi_predikat if sup else "-",
            "administrasi_persen": sup.administrasi_persen if sup else 0,
            "atp_predikat": sup.atp_predikat if sup else "-",
            "atp_persen": sup.atp_persen if sup else 0,
            "modul_ajar_predikat": sup.modul_ajar_predikat if sup else "-",
            "modul_ajar_persen": sup.modul_ajar_persen if sup else 0,
            "observasi_predikat": sup.observasi_predikat if sup else "-",
            "observasi_persen": sup.observasi_persen if sup else 0,
        },
    }


@app.delete("/api/guru/{guru_id}")
def delete_guru(guru_id: int, db: Session = Depends(get_db)):
    db.query(Supervisi).filter(Supervisi.guru_id == guru_id).delete()
    db.query(Guru).filter(Guru.id == guru_id).delete()
    db.commit()
    return {"message": "Guru dihapus"}


@app.post("/api/supervisi")
def submit_supervisi(data: SupervisiSubmit, db: Session = Depends(get_db)):
    guru = db.query(Guru).filter(Guru.id == data.guru_id).first()
    if not guru:
        raise HTTPException(status_code=404, detail="Guru tidak ditemukan")

    sup = db.query(Supervisi).filter(Supervisi.guru_id == data.guru_id).first()
    if not sup:
        sup = Supervisi(guru_id=data.guru_id)
        db.add(sup)

    max_skor = MAX_SKOR.get(data.kategori, 34)
    total = sum(data.data_jawaban.values())
    persen = round((total / max_skor) * 100, 2) if max_skor > 0 else 0
    predikat = get_predikat(persen)

    if data.kategori == "administrasi":
        sup.administrasi_data = json.dumps(data.data_jawaban)
        sup.administrasi_skor = total
        sup.administrasi_persen = persen
        sup.administrasi_predikat = predikat
    elif data.kategori == "atp":
        sup.atp_data = json.dumps(data.data_jawaban)
        sup.atp_skor = total
        sup.atp_persen = persen
        sup.atp_predikat = predikat
    elif data.kategori == "modul_ajar":
        sup.modul_ajar_data = json.dumps(data.data_jawaban)
        sup.modul_ajar_skor = total
        sup.modul_ajar_persen = persen
        sup.modul_ajar_predikat = predikat
    elif data.kategori == "observasi":
        sup.observasi_data = json.dumps(data.data_jawaban)
        sup.observasi_skor = total
        sup.observasi_persen = persen
        sup.observasi_predikat = predikat

    db.commit()
    return {
        "message": "Tersimpan",
        "skor": total,
        "persen": persen,
        "predikat": predikat,
    }


@app.post("/api/refleksi")
def submit_refleksi(data: RefleksiSubmit, db: Session = Depends(get_db)):
    sup = db.query(Supervisi).filter(Supervisi.guru_id == data.guru_id).first()
    if not sup:
        sup = Supervisi(guru_id=data.guru_id)
        db.add(sup)
    sup.refleksi = data.refleksi
    ub, tl = generate_feedback(sup.observasi_persen, data.refleksi)
    sup.umpan_balik = ub
    sup.tindak_lanjut = tl
    db.commit()
    return {"umpan_balik": ub, "tindak_lanjut": tl}


@app.get("/api/supervisi/{guru_id}")
def get_supervisi(guru_id: int, db: Session = Depends(get_db)):
    sup = db.query(Supervisi).filter(Supervisi.guru_id == guru_id).first()
    if not sup:
        raise HTTPException(status_code=404, detail="Data supervisi tidak ditemukan")
    return {
        "guru_id": sup.guru_id,
        "administrasi_skor": sup.administrasi_skor,
        "administrasi_persen": sup.administrasi_persen,
        "administrasi_predikat": sup.administrasi_predikat,
        "atp_skor": sup.atp_skor,
        "atp_persen": sup.atp_persen,
        "atp_predikat": sup.atp_predikat,
        "modul_ajar_skor": sup.modul_ajar_skor,
        "modul_ajar_persen": sup.modul_ajar_persen,
        "modul_ajar_predikat": sup.modul_ajar_predikat,
        "observasi_skor": sup.observasi_skor,
        "observasi_persen": sup.observasi_persen,
        "observasi_predikat": sup.observasi_predikat,
        "refleksi": sup.refleksi,
        "umpan_balik": sup.umpan_balik,
        "tindak_lanjut": sup.tindak_lanjut,
    }


@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    gurus = db.query(Guru).all()
    guru_list = []
    selesai_count = 0
    total_persen = 0
    count_persen = 0

    for g in gurus:
        sup = db.query(Supervisi).filter(Supervisi.guru_id == g.id).first()
        administrasi_persen = getattr(sup, 'administrasi_persen', 0) if sup else 0
        atp_persen = getattr(sup, 'atp_persen', 0) if sup else 0
        modul_persen = getattr(sup, 'modul_ajar_persen', 0) if sup else 0
        observasi_persen = getattr(sup, 'observasi_persen', 0) if sup else 0

        is_selesai = (
            administrasi_persen > 0 and
            atp_persen > 0 and
            modul_persen > 0 and
            observasi_persen > 0
        )
        if is_selesai:
            selesai_count += 1

        if observasi_persen > 0:
            total_persen += observasi_persen
            count_persen += 1

        guru_list.append({
            "id": g.id,
            "nama_guru": g.nama_guru,
            "nip": getattr(g, 'nip', ''),
            "kelas_semester": g.kelas_semester,
            "mata_pelajaran": g.mata_pelajaran,
            "administrasi_persen": administrasi_persen,
            "atp_persen": atp_persen,
            "modul_ajar_persen": modul_persen,
            "observasi_persen": observasi_persen,
            "status": "Selesai" if is_selesai else "Belum Selesai",
        })

    avg_all = round(total_persen / count_persen, 2) if count_persen > 0 else 0

    return {
        "total_guru": len(guru_list),
        "total_supervisi": selesai_count,
        "rata_rata_observasi": avg_all,
        "guru_list": guru_list,
    }


@app.get("/api/kesimpulan-rekap")
def get_kesimpulan_rekap(db: Session = Depends(get_db)):
    gurus = db.query(Guru).all()
    rekap_list = []
    
    for g in gurus:
        sup = db.query(Supervisi).filter(Supervisi.guru_id == g.id).first()
        narasi_kesimpulan = generate_kesimpulan_narasi(sup, g) if sup else "Belum ada data supervisi."
        
        rekap_list.append({
            "id": g.id,
            "nama_guru": g.nama_guru,
            "nip": getattr(g, 'nip', '-'),
            "kelas_semester": g.kelas_semester,
            
            "administrasi_skor": getattr(sup, 'administrasi_skor', 0) if sup else 0,
            "administrasi_persen": getattr(sup, 'administrasi_persen', 0) if sup else 0,
            "administrasi_predikat": getattr(sup, 'administrasi_predikat', '-') if sup else '-',
            
            "atp_skor": getattr(sup, 'atp_skor', 0) if sup else 0,
            "atp_persen": getattr(sup, 'atp_persen', 0) if sup else 0,
            "atp_predikat": getattr(sup, 'atp_predikat', '-') if sup else '-',
            
            "modul_ajar_skor": getattr(sup, 'modul_ajar_skor', 0) if sup else 0,
            "modul_ajar_persen": getattr(sup, 'modul_ajar_persen', 0) if sup else 0,
            "modul_ajar_predikat": getattr(sup, 'modul_ajar_predikat', '-') if sup else '-',
            
            "observasi_skor": getattr(sup, 'observasi_skor', 0) if sup else 0,
            "observasi_persen": getattr(sup, 'observasi_persen', 0) if sup else 0,
            "observasi_predikat": getattr(sup, 'observasi_predikat', '-') if sup else '-',
            
            "refleksi": getattr(sup, 'refleksi', '') if sup else '',
            "umpan_balik": getattr(sup, 'umpan_balik', '') if sup else '',
            "tindak_lanjut": getattr(sup, 'tindak_lanjut', '') if sup else '',
            "kesimpulan_narasi": narasi_kesimpulan
        })
        
    return rekap_list


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)