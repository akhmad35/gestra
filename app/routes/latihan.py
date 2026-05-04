from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.routes.halaman import get_current_user

router = APIRouter(tags=["Latihan"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/latihan", response_class=HTMLResponse)
async def latihan(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "latihan.html", {"user": user})

@router.get("/latihan-kata", response_class=HTMLResponse)
async def latihan_kata(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "latihan-kata.html", {"user": user})

@router.get("/canvas-latihan", response_class=HTMLResponse)
async def canvas_latihan(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "canvas-latihan.html", {"user": user})
