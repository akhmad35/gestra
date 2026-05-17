from fastapi import APIRouter, Request, Depends, Form, status, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.routes.halaman import get_current_user
from app.services.auth import get_password_hash, get_user_by_email

router = APIRouter(tags=["Profil"])
templates = Jinja2Templates(directory="app/templates")

def ensure_foto_profil_column(db: Session):
    """Safely alters SQLite database schema to add the column if missing"""
    try:
        from sqlalchemy import text
        db.execute(text("ALTER TABLE users ADD COLUMN foto_profil VARCHAR(255) DEFAULT '/static/assets/images/mascot.png'"))
        db.commit()
    except Exception:
        pass

@router.get("/profil", response_class=HTMLResponse)
@router.get("/profile", response_class=HTMLResponse)
async def profil(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
        
    ensure_foto_profil_column(db)
    
    # Ambil riwayat latihan dan kuis riil untuk menampilkan statistik dynamic
    from app.services.latihan import get_all_jawaban_by_siswa
    from app.models.quiz import QuizSession
    
    riwayat_list = get_all_jawaban_by_siswa(db, user.id)
    quiz_sessions = db.query(QuizSession).filter(QuizSession.siswa_id == user.id).all()
    
    total_latihan = len(riwayat_list)
    total_kuis = len(quiz_sessions)
    total_aktivitas = total_latihan + total_kuis
    
    # Hitung rata-rata
    sum_nilai = sum([r.nilai for r in riwayat_list]) + sum([q.skor_akhir for q in quiz_sessions])
    rata_rata = round(sum_nilai / total_aktivitas, 1) if total_aktivitas > 0 else 0
    
    # Hitung hari pengerjaan unik (streak)
    unique_dates = set()
    for r in riwayat_list:
        if r.dikumpulkan_pada:
            unique_dates.add(r.dikumpulkan_pada.date())
    for q in quiz_sessions:
        if q.waktu_mulai:
            unique_dates.add(q.waktu_mulai.date())
    streak = len(unique_dates)

    stats = {
        "total_latihan": total_latihan,
        "total_kuis": total_kuis,
        "total_aktivitas": total_aktivitas,
        "rata_rata": rata_rata,
        "streak": streak
    }
    
    return templates.TemplateResponse(
        request, 
        "profil.html", 
        {
            "user": user,
            "stats": stats
        }
    )

@router.get("/edit-profile", response_class=HTMLResponse)
async def edit_profil_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
        
    ensure_foto_profil_column(db)
    return templates.TemplateResponse(request, "edit-profil.html", {"user": user})

@router.post("/edit-profile")
async def update_profil(
    request: Request, 
    nama: str = Form(...),
    email: str = Form(...),
    password: str = Form(None),
    foto_profil: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
        
    ensure_foto_profil_column(db)
    
    # Check if email is already taken by another user
    if email != user.email:
        existing_user = get_user_by_email(db, email)
        if existing_user:
            return templates.TemplateResponse(
                request, 
                "edit-profil.html", 
                {"user": user, "error": "Email sudah digunakan oleh akun lain"}
            )
        user.email = email
    
    user.nama = nama
    
    if password and password.strip():
        user.password = get_password_hash(password)
        
    # Handle foto_profil file upload
    if foto_profil and foto_profil.filename:
        import os
        import shutil
        from datetime import datetime
        
        # Ensure static upload path exists
        upload_dir = os.path.join("app", "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Validate extensions
        ext = os.path.splitext(foto_profil.filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            filename = f"avatar_{user.id}_{int(datetime.utcnow().timestamp())}{ext}"
            file_path = os.path.join(upload_dir, filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(foto_profil.file, buffer)
                
            # Update user model attribute with accessible relative URL path
            user.foto_profil = f"/static/uploads/{filename}"
        
    db.commit()
    db.refresh(user)
    
    # Update cookie if email changed
    response = RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_email", value=user.email, path="/")
    return response

@router.post("/profil")
async def update_profil_simple(
    request: Request, 
    nama: str = Form(...),
    db: Session = Depends(get_db)
):
    """Old simple update kept for compatibility"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
        
    ensure_foto_profil_column(db)
    
    user.nama = nama
    db.commit()
    
    return RedirectResponse(url="/profil", status_code=status.HTTP_303_SEE_OTHER)
