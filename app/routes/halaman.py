from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import get_user_by_email

router = APIRouter(tags=["Halaman Utama"])
templates = Jinja2Templates(directory="app/templates")


# Ambil user dari cookie
def get_current_user(request: Request, db: Session):
    email = request.cookies.get("user_email")
    if email:
        return get_user_by_email(db, email)
    return None


# ROOT (halaman awal)
@router.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    # kalau belum login → ke login
    if not user:
        return RedirectResponse(url="/login")

    # kalau sudah login → ke beranda
    return RedirectResponse(url="/beranda")


# BERANDA
@router.get("/beranda", response_class=HTMLResponse)
async def beranda(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        request=request,
        name="beranda.html",
        context={
            "user": user
        }
    )


# MATERI
@router.get("/materi", response_class=HTMLResponse)
async def materi(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        request=request,
        name="materi.html",
        context={
            "user": user
        }
    )

