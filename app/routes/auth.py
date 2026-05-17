from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth import get_user_by_email, create_user, verify_password, update_user_role
from app.schemas.user import UserCreate

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    # Kalau sudah login, langsung ke beranda
    user_email = request.cookies.get("user_email")
    if user_email:
        user = get_user_by_email(db, user_email)
        if user:
            return RedirectResponse(url="/beranda")
    return templates.TemplateResponse(request, "login.html")

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(request, "login.html", {"error": "Email atau password salah"})
    
    response = RedirectResponse(url="/guru/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_email", value=user.email, path="/")
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    # Kalau sudah login, langsung ke beranda
    user_email = request.cookies.get("user_email")
    if user_email:
        user = get_user_by_email(db, user_email)
        if user:
            return RedirectResponse(url="/beranda")
    return templates.TemplateResponse(request, "daftar.html")

@router.post("/register")
async def register(
    request: Request, 
    nama: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    existing_user = get_user_by_email(db, email)
    if existing_user:
        return templates.TemplateResponse(request, "daftar.html", {"error": "Email sudah terdaftar"})
    
    user_in = UserCreate(nama=nama, email=email, password=password)
    user = create_user(db, user_in)
    
    response = RedirectResponse(url="/pilih-peran", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_email", value=user.email, path="/")
    return response

@router.get("/pilih-peran", response_class=HTMLResponse)
async def pilih_peran_page(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email:
        return RedirectResponse(url="/login")
    user = get_user_by_email(db, user_email)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "pilih-peran.html")

@router.post("/pilih-peran")
async def set_peran(request: Request, role: str = Form(...), db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email:
        return RedirectResponse(url="/login")
    
    user = get_user_by_email(db, user_email)
    if user:
        update_user_role(db, user.id, role)
        
    return RedirectResponse(url="/guru/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("user_email")
    return response
