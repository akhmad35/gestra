from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json

from app.database import get_db
from app.routes.halaman import get_current_user
from app.services.kelas import get_kelas_by_id, get_all_kelas
from app.services.latihan import (
    create_latihan,
    get_latihan_by_kelas,
    get_latihan_by_id,
    update_latihan,
    delete_latihan,
    get_jawaban_by_latihan,
    grade_jawaban,
    get_stat_jawaban_kelas
)
from app.schemas.latihan import LatihanCreate, LatihanUpdate
from app.services.dataset import get_dataset_by_type, generate_random_questions

router = APIRouter(prefix="/guru", tags=["Guru"])
templates = Jinja2Templates(directory="app/templates")


# ===== DASHBOARD GURU =====
@router.get("/dashboard", response_class=HTMLResponse)
async def guru_dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard guru"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    # Ambil semua kelas yang dibuat guru
    from app.models.kelas import Kelas
    kelas_list = db.query(Kelas).filter(Kelas.guru_id == user.id).all()
    
    # Hitung statistik
    total_kelas = len(kelas_list)
    total_siswa = sum([len(k.enrollments) for k in kelas_list])
    
    # Ambil semua latihan
    from app.models.latihan import Latihan
    latihan_list = db.query(Latihan).filter(Latihan.guru_id == user.id).all()
    total_latihan = len(latihan_list)
    
    return templates.TemplateResponse(
        request=request,
        name="guru/dashboard.html",
        context={
            "user": user,
            "kelas_list": kelas_list,
            "total_kelas": total_kelas,
            "total_siswa": total_siswa,
            "total_latihan": total_latihan
        }
    )


# ===== MANAGE KELAS (GURU) =====
@router.get("/kelas/buat", response_class=HTMLResponse)
async def buat_kelas_page(request: Request, db: Session = Depends(get_db)):
    """Halaman buat kelas"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        request=request,
        name="guru/buat-kelas.html",
        context={"user": user}
    )


@router.post("/kelas/buat")
async def create_kelas_guru(
    request: Request,
    nama_kelas: str = Form(...),
    deskripsi: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Buat kelas baru (guru)"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    from app.services.kelas import create_kelas
    from app.schemas.kelas import KelasCreate
    
    kelas_data = KelasCreate(
        nama_kelas=nama_kelas,
        deskripsi=deskripsi,
        kode_kelas=""  # Will be generated
    )
    
    kelas = create_kelas(db, kelas_data, user.id)
    
    return RedirectResponse(
        url=f"/guru/kelas/{kelas.id}/detail",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/kelas/{kelas_id}/detail", response_class=HTMLResponse)
async def detail_kelas_guru(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Detail kelas (guru view)"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas or kelas.guru_id != user.id:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Kelas tidak ditemukan"}
        )
    
    # Ambil latihan di kelas ini
    latihan_list = get_latihan_by_kelas(db, kelas_id)
    
    # Ambil siswa di kelas
    siswa_list = kelas.enrollments
    
    return templates.TemplateResponse(
        request=request,
        name="guru/detail-kelas.html",
        context={
            "user": user,
            "kelas": kelas,
            "latihan_list": latihan_list,
            "siswa_list": siswa_list
        }
    )


@router.get("/kelas/{kelas_id}/edit", response_class=HTMLResponse)
async def edit_kelas_page(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Halaman edit kelas"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas or kelas.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    return templates.TemplateResponse(
        request=request,
        name="guru/edit-kelas.html",
        context={"user": user, "kelas": kelas}
    )


@router.post("/kelas/{kelas_id}/edit")
async def update_kelas_guru(
    request: Request,
    kelas_id: int,
    nama_kelas: str = Form(...),
    deskripsi: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update kelas"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas or kelas.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    kelas.nama_kelas = nama_kelas
    kelas.deskripsi = deskripsi
    db.add(kelas)
    db.commit()
    
    return RedirectResponse(
        url=f"/guru/kelas/{kelas_id}/detail",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/kelas/{kelas_id}/delete")
async def delete_kelas_guru(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Delete kelas"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas or kelas.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    db.delete(kelas)
    db.commit()
    
    return RedirectResponse(url="/guru/dashboard", status_code=status.HTTP_303_SEE_OTHER)


# ===== MANAGE LATIHAN (GURU) =====
@router.get("/latihan/buat/{kelas_id}", response_class=HTMLResponse)
async def buat_latihan_page(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Halaman buat latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas or kelas.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    dataset_huruf = get_dataset_by_type("huruf")
    dataset_kata = get_dataset_by_type("kata")
    
    return templates.TemplateResponse(
        request=request,
        name="guru/buat-latihan.html",
        context={
            "user": user, 
            "kelas": kelas,
            "dataset_huruf": dataset_huruf,
            "dataset_kata": dataset_kata
        }
    )


@router.post("/latihan/buat/{kelas_id}")
async def create_latihan_guru(
    request: Request,
    kelas_id: int,
    judul: str = Form(...),
    pertanyaan: str = Form(...),
    tipe_soal: str = Form(...),
    tingkat_kesulitan: str = Form(...),
    metode_pembuatan: str = Form("manual"),
    dataset_type: Optional[str] = Form(None),
    jumlah_soal: int = Form(5),
    durasi_menit: int = Form(0),
    waktu_mulai: Optional[str] = Form(None),
    waktu_selesai: Optional[str] = Form(None),
    status_latihan: str = Form("draft"),
    dataset_manual: Optional[str] = Form(None),
    izinkan_retry: Optional[str] = Form(None),
    max_attempt: int = Form(1),
    mode_timer: str = Form("total"),
    durasi_per_soal: int = Form(30),
    izinkan_lihat_hasil: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Buat latihan baru"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas or kelas.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    # Process waktu
    w_mulai = datetime.fromisoformat(waktu_mulai) if waktu_mulai else None
    w_selesai = datetime.fromisoformat(waktu_selesai) if waktu_selesai else None
    
    # Generate questions if random, or parse manual
    soal_tergenerate = None
    if metode_pembuatan == "random" and dataset_type:
        questions = generate_random_questions(dataset_type, jumlah_soal)
        soal_tergenerate = json.dumps(questions)
    elif metode_pembuatan == "manual" and dataset_manual:
        try:
            # Assuming dataset_manual comes as JSON array of selected items
            questions = json.loads(dataset_manual)
            soal_tergenerate = json.dumps(questions)
            jumlah_soal = len(questions)
        except:
            soal_tergenerate = "[]"
            
    is_retry = True if izinkan_retry in ["true", "on", "ya", "Ya"] else False
    is_lihat_hasil = True if izinkan_lihat_hasil in ["true", "on", "ya", "Ya", None] else False
    
    latihan_data = LatihanCreate(
        kelas_id=kelas_id,
        judul=judul,
        pertanyaan=pertanyaan,
        tipe_soal=tipe_soal,
        tingkat_kesulitan=tingkat_kesulitan,
        metode_pembuatan=metode_pembuatan,
        dataset_type=dataset_type,
        jumlah_soal=jumlah_soal,
        durasi_menit=durasi_menit,
        waktu_mulai=w_mulai,
        waktu_selesai=w_selesai,
        status=status_latihan,
        soal_tergenerate=soal_tergenerate,
        izinkan_retry=is_retry,
        max_attempt=max_attempt,
        mode_timer=mode_timer,
        durasi_per_soal=durasi_per_soal,
        izinkan_lihat_hasil=is_lihat_hasil
    )
    
    latihan = create_latihan(db, latihan_data, user.id)
    
    return RedirectResponse(
        url=f"/guru/latihan/{latihan.id}/edit",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/latihan/{latihan_id}/edit", response_class=HTMLResponse)
async def edit_latihan_page(
    request: Request,
    latihan_id: int,
    db: Session = Depends(get_db)
):
    """Halaman edit latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan or latihan.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    dataset_huruf = get_dataset_by_type("huruf")
    dataset_kata = get_dataset_by_type("kata")
    
    return templates.TemplateResponse(
        request=request,
        name="guru/edit-latihan.html",
        context={
            "user": user, 
            "latihan": latihan,
            "dataset_huruf": dataset_huruf,
            "dataset_kata": dataset_kata
        }
    )


@router.post("/latihan/{latihan_id}/update")
async def update_latihan_guru(
    request: Request,
    latihan_id: int,
    judul: str = Form(...),
    pertanyaan: str = Form(...),
    tipe_soal: str = Form(...),
    tingkat_kesulitan: str = Form(...),
    metode_pembuatan: str = Form("manual"),
    dataset_type: Optional[str] = Form(None),
    jumlah_soal: int = Form(5),
    durasi_menit: int = Form(0),
    waktu_mulai: Optional[str] = Form(None),
    waktu_selesai: Optional[str] = Form(None),
    status_latihan: str = Form("draft"),
    dataset_manual: Optional[str] = Form(None),
    izinkan_retry: Optional[str] = Form(None),
    max_attempt: int = Form(1),
    mode_timer: str = Form("total"),
    durasi_per_soal: int = Form(30),
    izinkan_lihat_hasil: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan or latihan.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    w_mulai = datetime.fromisoformat(waktu_mulai) if waktu_mulai else None
    w_selesai = datetime.fromisoformat(waktu_selesai) if waktu_selesai else None
    
    # Determine questions
    soal_tergenerate = latihan.soal_tergenerate
    
    # If settings changed, we might need to regenerate or re-parse
    if metode_pembuatan == "random" and dataset_type:
        # only regenerate if user changed the dataset or jumlah_soal
        if (latihan.dataset_type != dataset_type) or (latihan.jumlah_soal != jumlah_soal):
            questions = generate_random_questions(dataset_type, jumlah_soal)
            soal_tergenerate = json.dumps(questions)
    elif metode_pembuatan == "manual" and dataset_manual:
        try:
            questions = json.loads(dataset_manual)
            soal_tergenerate = json.dumps(questions)
            jumlah_soal = len(questions)
        except:
            pass
            
    is_retry = True if izinkan_retry in ["true", "on", "ya", "Ya"] else False
    is_lihat_hasil = True if izinkan_lihat_hasil in ["true", "on", "ya", "Ya", None] else False
    
    latihan_update = LatihanUpdate(
        judul=judul,
        pertanyaan=pertanyaan,
        tipe_soal=tipe_soal,
        tingkat_kesulitan=tingkat_kesulitan,
        metode_pembuatan=metode_pembuatan,
        dataset_type=dataset_type,
        jumlah_soal=jumlah_soal,
        durasi_menit=durasi_menit,
        waktu_mulai=w_mulai,
        waktu_selesai=w_selesai,
        status=status_latihan,
        soal_tergenerate=soal_tergenerate,
        izinkan_retry=is_retry,
        max_attempt=max_attempt,
        mode_timer=mode_timer,
        durasi_per_soal=durasi_per_soal,
        izinkan_lihat_hasil=is_lihat_hasil
    )
    
    update_latihan(db, latihan_id, latihan_update)
    
    return RedirectResponse(
        url=f"/guru/kelas/{latihan.kelas_id}/detail",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/latihan/{latihan_id}/delete")
async def delete_latihan_guru(
    request: Request,
    latihan_id: int,
    db: Session = Depends(get_db)
):
    """Delete latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan or latihan.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    kelas_id = latihan.kelas_id
    delete_latihan(db, latihan_id)
    
    return RedirectResponse(
        url=f"/guru/kelas/{kelas_id}/detail",
        status_code=status.HTTP_303_SEE_OTHER
    )


# ===== LIHAT JAWABAN SISWA (GURU) =====
@router.get("/latihan/{latihan_id}/jawaban", response_class=HTMLResponse)
async def lihat_jawaban_latihan(
    request: Request,
    latihan_id: int,
    db: Session = Depends(get_db)
):
    """Lihat semua jawaban untuk latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan or latihan.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    jawaban_list = get_jawaban_by_latihan(db, latihan_id)
    
    return templates.TemplateResponse(
        request=request,
        name="guru/jawaban-latihan.html",
        context={
            "user": user,
            "latihan": latihan,
            "jawaban_list": jawaban_list
        }
    )

@router.get("/kelas/{kelas_id}/nilai", response_class=HTMLResponse)
async def lihat_nilai_siswa(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Halaman nilai per siswa untuk kelas tertentu"""
    user = get_current_user(request, db)
    if not user or user.role != "guru":
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    if not kelas or kelas.guru_id != user.id:
        return RedirectResponse(url="/guru/dashboard")
    
    from app.models.latihan import Jawaban, Latihan
    jawaban_list = db.query(Jawaban).join(Latihan).filter(Latihan.kelas_id == kelas_id).all()
    
    total_siswa = len(kelas.enrollments)
    total_latihan = len(get_latihan_by_kelas(db, kelas_id))
    avg_score = sum([j.nilai for j in jawaban_list]) / len(jawaban_list) if jawaban_list else 0
    avg_score = round(avg_score, 1)
    
    return templates.TemplateResponse(
        request=request,
        name="guru/nilai-siswa.html",
        context={
            "user": user,
            "kelas": kelas,
            "jawaban_list": jawaban_list,
            "total_siswa": total_siswa,
            "total_latihan": total_latihan,
            "avg_score": avg_score
        }
    )
