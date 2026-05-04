from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.halaman import get_current_user
from app.services.auth import get_user_by_email
from app.services.kelas import (
    get_all_kelas, 
    get_kelas_by_id,
    get_kelas_by_siswa,
    siswa_bergabung_kelas,
    check_siswa_di_kelas,
    get_siswa_di_kelas
)

router = APIRouter(prefix="/kelas", tags=["Kelas"])
templates = Jinja2Templates(directory="app/templates")


# ===== DAFTAR KELAS =====
@router.get("/daftar", response_class=HTMLResponse)
async def daftar_kelas_page(request: Request, db: Session = Depends(get_db)):
    """Halaman daftar kelas"""
    user = get_current_user(request, db)
    
    if not user:
        return RedirectResponse(url="/login")
    
    # Ambil semua kelas
    semua_kelas = get_all_kelas(db)
    
    # Ambil kelas yang sudah diikuti siswa
    kelas_diikuti = get_kelas_by_siswa(db, user.id)
    kelas_diikuti_ids = [k.id for k in kelas_diikuti]
    
    return templates.TemplateResponse(
        request=request,
        name="daftar-kelas.html",
        context={
            "user": user,
            "semua_kelas": semua_kelas,
            "kelas_diikuti_ids": kelas_diikuti_ids
        }
    )


# ===== DETAIL KELAS =====
@router.get("/{kelas_id}/detail", response_class=HTMLResponse)
async def detail_kelas_page(
    request: Request, 
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Halaman detail kelas"""
    user = get_current_user(request, db)
    
    if not user:
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": "Kelas tidak ditemukan"}
        )
    
    # Cek apakah siswa sudah bergabung
    sudah_bergabung = check_siswa_di_kelas(db, kelas_id, user.id)
    
    # Ambil guru
    guru = None
    if kelas.guru_id:
        from app.models.user import User
        guru = db.query(User).filter(User.id == kelas.guru_id).first()
    
    # Ambil jumlah siswa di kelas
    siswa_list = get_siswa_di_kelas(db, kelas_id)
    
    return templates.TemplateResponse(
        request=request,
        name="detail-kelas.html",
        context={
            "user": user,
            "kelas": kelas,
            "sudah_bergabung": sudah_bergabung,
            "guru": guru,
            "jumlah_siswa": len(siswa_list)
        }
    )


# ===== BERGABUNG KE KELAS =====
@router.post("/{kelas_id}/bergabung")
async def bergabung_kelas(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Bergabung ke kelas"""
    user = get_current_user(request, db)
    
    if not user:
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas:
        return RedirectResponse(url="/kelas/daftar")
    
    # Siswa bergabung
    enrollment = siswa_bergabung_kelas(db, kelas_id, user.id)
    
    if enrollment:
        return RedirectResponse(
            url=f"/kelas/{kelas_id}/detail",
            status_code=status.HTTP_303_SEE_OTHER
        )
    else:
        # Sudah bergabung sebelumnya
        return RedirectResponse(
            url=f"/kelas/{kelas_id}/detail",
            status_code=status.HTTP_303_SEE_OTHER
        )


# ===== BERGABUNG DENGAN KODE KELAS =====
@router.post("/bergabung-kode", response_class=HTMLResponse)
async def bergabung_dengan_kode(
    request: Request,
    kode_kelas: str = Form(...),
    db: Session = Depends(get_db)
):
    """Bergabung ke kelas menggunakan kode kelas"""
    from app.services.kelas import get_kelas_by_kode
    
    user = get_current_user(request, db)
    
    if not user:
        return RedirectResponse(url="/login")
    
    kelas = get_kelas_by_kode(db, kode_kelas.upper())
    
    if not kelas:
        return templates.TemplateResponse(
            request=request,
            name="daftar-kelas.html",
            context={
                "user": user,
                "error": "Kode kelas tidak ditemukan"
            }
        )
    
    # Cek apakah sudah bergabung
    if check_siswa_di_kelas(db, kelas.id, user.id):
        return RedirectResponse(
            url=f"/kelas/{kelas.id}/detail",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    # Bergabung
    siswa_bergabung_kelas(db, kelas.id, user.id)
    
    return RedirectResponse(
        url=f"/kelas/{kelas.id}/detail",
        status_code=status.HTTP_303_SEE_OTHER
    )
