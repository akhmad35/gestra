from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.halaman import get_current_user
from app.services.kelas import get_kelas_by_siswa, get_kelas_by_id, check_siswa_di_kelas
from app.services.latihan import (
    get_latihan_by_kelas,
    get_latihan_by_id,
    submit_jawaban,
    get_jawaban_siswa,
    get_jawaban_by_siswa
)
from app.schemas.latihan import JawabanCreate

router = APIRouter(prefix="/murid", tags=["Murid"])
templates = Jinja2Templates(directory="app/templates")


# ===== DASHBOARD MURID =====
@router.get("/dashboard", response_class=HTMLResponse)
async def murid_dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard murid"""
    user = get_current_user(request, db)
    
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    # Ambil semua kelas yang diikuti murid
    kelas_list = get_kelas_by_siswa(db, user.id)
    
    return templates.TemplateResponse(
        request=request,
        name="murid/dashboard.html",
        context={
            "user": user,
            "kelas_list": kelas_list
        }
    )


# ===== KELAS MURID =====
@router.get("/kelas/{kelas_id}/latihan", response_class=HTMLResponse)
async def lihat_latihan_kelas(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Lihat semua latihan di kelas"""
    user = get_current_user(request, db)
    
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    # Check apakah siswa sudah bergabung di kelas
    sudah_bergabung = check_siswa_di_kelas(db, kelas_id, user.id)
    
    if not sudah_bergabung:
        return RedirectResponse(url="/kelas/daftar")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas:
        return RedirectResponse(url="/kelas/daftar")
    
    # Ambil latihan di kelas
    latihan_list = get_latihan_by_kelas(db, kelas_id)
    
    # Ambil jawaban siswa
    jawaban_siswa_list = get_jawaban_by_siswa(db, user.id, kelas_id)
    jawaban_dict = {j.latihan_id: j for j in jawaban_siswa_list}
    
    return templates.TemplateResponse(
        request=request,
        name="murid/latihan-kelas.html",
        context={
            "user": user,
            "kelas": kelas,
            "latihan_list": latihan_list,
            "jawaban_dict": jawaban_dict
        }
    )


# ===== KERJAKAN LATIHAN (MURID) =====
@router.get("/latihan/{latihan_id}/kerjakan", response_class=HTMLResponse)
async def kerjakan_latihan_page(
    request: Request,
    latihan_id: int,
    db: Session = Depends(get_db)
):
    """Halaman kerjakan latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan:
        return RedirectResponse(url="/murid/dashboard")
    
    # Check apakah siswa sudah bergabung di kelas
    sudah_bergabung = check_siswa_di_kelas(db, latihan.kelas_id, user.id)
    
    if not sudah_bergabung:
        return RedirectResponse(url="/kelas/daftar")
    
    # Ambil jawaban sebelumnya jika ada
    jawaban_sebelumnya = get_jawaban_siswa(db, latihan_id, user.id)
    
    kelas = get_kelas_by_id(db, latihan.kelas_id)
    
    return templates.TemplateResponse(
        request=request,
        name="murid/kerjakan-latihan.html",
        context={
            "user": user,
            "kelas": kelas,
            "latihan": latihan,
            "jawaban_sebelumnya": jawaban_sebelumnya
        }
    )


@router.post("/latihan/{latihan_id}/submit")
async def submit_latihan(
    request: Request,
    latihan_id: int,
    jawaban_text: str = Form(...),
    db: Session = Depends(get_db)
):
    """Submit jawaban latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan:
        return RedirectResponse(url="/murid/dashboard")
    
    # Check apakah siswa sudah bergabung di kelas
    sudah_bergabung = check_siswa_di_kelas(db, latihan.kelas_id, user.id)
    
    if not sudah_bergabung:
        return RedirectResponse(url="/kelas/daftar")
    
    # Submit jawaban
    jawaban_data = JawabanCreate(
        latihan_id=latihan_id,
        jawaban=jawaban_text
    )
    
    submit_jawaban(db, jawaban_data, user.id, latihan.kelas_id)
    
    return RedirectResponse(
        url=f"/murid/kelas/{latihan.kelas_id}/latihan",
        status_code=status.HTTP_303_SEE_OTHER
    )


# ===== LIHAT HASIL JAWABAN (MURID) =====
@router.get("/latihan/{latihan_id}/hasil", response_class=HTMLResponse)
async def lihat_hasil_jawaban(
    request: Request,
    latihan_id: int,
    db: Session = Depends(get_db)
):
    """Lihat hasil jawaban siswa"""
    user = get_current_user(request, db)
    
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan:
        return RedirectResponse(url="/murid/dashboard")
    
    # Ambil jawaban siswa
    jawaban = get_current_user(request, db) # Oops, this was wrong in the previous version too, but I'll use get_jawaban_siswa
    from app.services.latihan import get_jawaban_siswa
    jawaban = get_jawaban_siswa(db, latihan_id, user.id)
    
    if not jawaban:
        return RedirectResponse(
            url=f"/murid/kelas/{latihan.kelas_id}/latihan"
        )
    
    kelas = get_kelas_by_id(db, latihan.kelas_id)
    
    return templates.TemplateResponse(
        request=request,
        name="murid/hasil-jawaban.html",
        context={
            "user": user,
            "kelas": kelas,
            "latihan": latihan,
            "jawaban": jawaban
        }
    )
