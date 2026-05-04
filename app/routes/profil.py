from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.routes.halaman import get_current_user
from app.services.auth import get_password_hash, get_user_by_email

router = APIRouter(tags=["Profil"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/profil", response_class=HTMLResponse)
@router.get("/profile", response_class=HTMLResponse)
async def profil(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "profil.html", {"user": user})

@router.get("/edit-profile", response_class=HTMLResponse)
async def edit_profil_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "edit-profil.html", {"user": user})

@router.post("/edit-profile")
async def update_profil(
    request: Request, 
    nama: str = Form(...),
    email: str = Form(...),
    password: str = Form(None),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
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
    
    user.nama = nama
    db.commit()
    
    return RedirectResponse(url="/profil", status_code=status.HTTP_303_SEE_OTHER)
