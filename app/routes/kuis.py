from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.routes.halaman import get_current_user

router = APIRouter(tags=["Kuis"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/kuis", response_class=HTMLResponse)
async def kuis(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "kuis.html", {"user": user})

@router.post("/kuis")
async def mulai_kuis_guru(
    request: Request, 
    kode_kuis: str = Form(...), 
    password_kuis: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    # Dummy validation for teacher's quiz
    if kode_kuis == "12345" and password_kuis == "guru123":
        # In a real app, redirect to the actual quiz URL with the session
        return templates.TemplateResponse(request, "kuis.html", {"user": user, "success": "Berhasil masuk ke kuis!"})
    else:
        return templates.TemplateResponse(request, "kuis.html", {"user": user, "error": "Kode atau password kuis salah"})
