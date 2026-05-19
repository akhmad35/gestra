from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.routes.halaman import get_current_user
import base64
import cv2
import numpy as np
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["Latihan"])
templates = Jinja2Templates(directory="app/templates")

# Import prediction modules
from app.modules.level_huruf.predict import predict_from_canvas
# from app.modules.level_kata.segmenter import segment_letters
# from app.modules.level_kata.predict import predict_word
from app.modules.level_kata.validator import validate_word
from app.services.latihan import submit_jawaban_otomatis

# ===== Request Models =====
class PredictLetterRequest(BaseModel):
    mode: str  # "upper", "lower", "number"
    target: str
    image: str  # base64
    latihan_id: Optional[int] = None
    kelas_id: Optional[int] = None

class PredictWordRequest(BaseModel):
    target: str
    image: str  # base64
    latihan_id: Optional[int] = None
    kelas_id: Optional[int] = None

# ===== Helper function to decode base64 image =====
def decode_base64_image(image_data: str):
    """Decode base64 image string to cv2 image"""
    try:
        # Remove data URL prefix if present
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Error decoding image: {e}")
        return None

# ===== Routes =====
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

@router.get("/canvas-latihan-huruf", response_class=HTMLResponse)
async def canvas_latihan_huruf(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    timer = request.query_params.get("timer") == "true"
    level = request.query_params.get("level", "medium")
    if level not in {"easy", "medium", "hard"}:
        level = "medium"
    return templates.TemplateResponse(request, "canvas-latihan-huruf.html", {"user": user, "is_timer": timer, "level": level})

@router.get("/canvas-latihan")
async def legacy_canvas_latihan_redirect(request: Request, db: Session = Depends(get_db)):
    """
    Backward-compat route untuk tautan lama.
    Redirect ke halaman canvas huruf sambil mempertahankan query params.
    """
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    query = str(request.url.query)
    target_url = f"/canvas-latihan-huruf?{query}" if query else "/canvas-latihan-huruf"
    return RedirectResponse(url=target_url, status_code=307)

@router.get("/canvas-latihan.html")
async def legacy_canvas_latihan_html_redirect(request: Request, db: Session = Depends(get_db)):
    """
    Backward-compat route untuk nama file lama.
    Redirect ke route FastAPI yang benar.
    """
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    query = str(request.url.query)
    target_url = f"/canvas-latihan-huruf?{query}" if query else "/canvas-latihan-huruf"
    return RedirectResponse(url=target_url, status_code=307)

@router.get("/canvas-latihan-kata", response_class=HTMLResponse)
async def canvas_latihan_kata(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    timer = request.query_params.get("timer") == "true"
    level = request.query_params.get("level", "medium")
    if level not in {"easy", "medium", "hard"}:
        level = "medium"
    return templates.TemplateResponse(request, "canvas-latihan-kata.html", {"user": user, "is_timer": timer, "level": level})

@router.get("/canvas-latihan-kata.html")
async def legacy_canvas_latihan_kata_html_redirect(request: Request, db: Session = Depends(get_db)):
    """
    Backward-compat route untuk nama file lama level kata.
    """
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    query = str(request.url.query)
    target_url = f"/canvas-latihan-kata?{query}" if query else "/canvas-latihan-kata"
    return RedirectResponse(url=target_url, status_code=307)