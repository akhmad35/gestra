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
from app.modules.level_kata.segmenter import segment_letters
from app.modules.level_kata.predict import predict_word
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
    return templates.TemplateResponse(request, "canvas-latihan-huruf.html", {"user": user})

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
    return templates.TemplateResponse(request, "canvas-latihan-kata.html", {"user": user})

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

# ===== Prediction Endpoints =====
@router.post("/save")
async def predict_letter(request_data: PredictLetterRequest, request: Request, db: Session = Depends(get_db)):
    """
    Predict single letter/number from canvas drawing
    Expected payload: { mode: "upper"|"lower"|"number", target: string, image: base64 }
    Returns: { correct: bool, prediction: string, confidence: float }
    """
    try:
        # Decode image
        canvas = decode_base64_image(request_data.image)
        if canvas is None:
            return JSONResponse(
                {"correct": False, "prediction": "Error", "confidence": 0.0},
                status_code=400
            )
        
        # Predict
        prediction, confidence = predict_from_canvas(canvas, request_data.mode)
        
        # Check if correct
        correct = (prediction.lower() == request_data.target.lower()) and confidence >= 0.80
        
        # Save if user is logged in and providing IDs
        user = get_current_user(request, db)
        if user and user.role == "murid" and request_data.latihan_id and request_data.kelas_id:
            score = int(confidence * 100)
            submit_jawaban_otomatis(
                db, 
                request_data.latihan_id, 
                user.id, 
                request_data.kelas_id, 
                prediction, 
                score, 
                correct
            )
        
        return {
            "correct": correct,
            "prediction": prediction,
            "confidence": round(float(confidence) * 100, 2)
        }
    except Exception as e:
        print(f"Error in predict_letter: {e}")
        return JSONResponse(
            {"correct": False, "prediction": "Error", "confidence": 0.0},
            status_code=500
        )

@router.post("/predict-word")
async def predict_word_endpoint(request_data: PredictWordRequest, request: Request, db: Session = Depends(get_db)):
    """
    Predict word from canvas drawing
    Expected payload: { target: string, image: base64 }
    Returns: { correct: bool, prediction: string, score: float, total_letters: int, debug_images: list }
    """
    try:
        # Decode image
        canvas = decode_base64_image(request_data.image)
        if canvas is None:
            return JSONResponse(
                {"correct": False, "prediction": "", "score": 0.0, "total_letters": 0, "debug_images": []},
                status_code=400
            )
        
        # Segment letters
        letter_images = segment_letters(canvas)
        
        if not letter_images:
            return JSONResponse(
                {"correct": False, "prediction": "", "score": 0.0, "total_letters": 0, "debug_images": []},
                status_code=200
            )
        
        # Predict word
        predicted_word = predict_word(letter_images)
        
        # Validate
        is_correct, similarity_score = validate_word(predicted_word, request_data.target)
        
        # Save if user is logged in and providing IDs
        user = get_current_user(request, db)
        if user and user.role == "murid" and request_data.latihan_id and request_data.kelas_id:
            score = int(similarity_score)
            submit_jawaban_otomatis(
                db, 
                request_data.latihan_id, 
                user.id, 
                request_data.kelas_id, 
                predicted_word, 
                score, 
                is_correct
            )
            
        return {
            "correct": is_correct,
            "prediction": predicted_word,
            "score": round(float(similarity_score), 3),
            "total_letters": len(letter_images),
            "debug_images": []
        }
    except Exception as e:
        print(f"Error in predict_word: {e}")
        return JSONResponse(
            {"correct": False, "prediction": "", "score": 0.0, "total_letters": 0, "debug_images": []},
            status_code=500
        )
