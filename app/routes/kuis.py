from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import random
import string
from datetime import datetime

from app.database import get_db
from app.routes.halaman import get_current_user
from app.models.quiz import QuizSession, QuizDetail
from app.models.user import User
from app.routes.latihan import decode_base64_image
from app.modules.system_validator import (
    run_pipeline_validation,
    evaluate_model_output,
    get_failsafe_response
)
from app.modules.level_huruf.predict import predict_from_canvas

router = APIRouter(prefix="/murid", tags=["Kuis"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/quiz-random/start")
async def start_random_quiz(request: Request, db: Session = Depends(get_db), timer: bool = False):
    """Mulai sesi kuis random 10 soal"""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    # Buat sesi baru
    session = QuizSession(
        siswa_id=user.id,
        mode="timer" if timer else "random",
        total_soal=10,
        status="ongoing",
        waktu_mulai=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return RedirectResponse(url=f"/murid/quiz/kerjakan/{session.id}")

@router.get("/quiz/kerjakan/{session_id}", response_class=HTMLResponse)
async def kerjakan_quiz(request: Request, session_id: int, db: Session = Depends(get_db)):
    """Halaman kuis yang menggunakan canvas existing"""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    session = db.query(QuizSession).filter(QuizSession.id == session_id, QuizSession.siswa_id == user.id).first()
    if not session:
        return RedirectResponse(url="/murid/dashboard")
    
    if session.status == "finished":
        return RedirectResponse(url=f"/murid/quiz/hasil/{session.id}")
    
    # Tentukan nomor soal sekarang
    current_question_no = len(session.details) + 1
    
    if current_question_no > session.total_soal:
        session.status = "finished"
        session.waktu_selesai = datetime.utcnow()
        session.durasi_detik = (session.waktu_selesai - session.waktu_mulai).total_seconds()
        db.commit()
        return RedirectResponse(url=f"/murid/quiz/hasil/{session.id}")
    
    # Generate target acak untuk soal ini jika belum ada (biasanya belum ada karena flow-nya sequential)
    mode_choices = ["upper", "lower", "number"]
    selected_mode = random.choice(mode_choices)
    
    if selected_mode == "upper":
        target = random.choice(string.ascii_uppercase)
    elif selected_mode == "lower":
        target = random.choice(string.ascii_lowercase)
    else:
        target = str(random.randint(0, 9))
    
    # Gunakan template canvas-latihan-huruf.html tapi dengan konteks kuis
    return templates.TemplateResponse(
        request=request,
        name="canvas-latihan-huruf.html",
        context={
            "user": user,
            "is_quiz": True,
            "is_timer": session.mode == "timer",
            "session": session,
            "current_question_no": current_question_no,
            "target": target,
            "mode": selected_mode
        }
    )

@router.post("/quiz/submit/{session_id}")
async def submit_quiz_answer(
    request: Request, 
    session_id: int, 
    db: Session = Depends(get_db)
):
    """API untuk submit jawaban per soal dalam kuis"""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    
    session = db.query(QuizSession).filter(QuizSession.id == session_id, QuizSession.siswa_id == user.id).first()
    if not session or session.status == "finished":
        return JSONResponse(status_code=400, content={"detail": "Invalid session"})
    
    try:
        data = await request.json()
        image_data = data.get("image")
        target = data.get("target")
        mode = data.get("mode")
        is_timeout = data.get("timeout", False)
        question_no = data.get("question_no")
        
        # Gunakan nomor soal dari client jika ada, jika tidak fallback ke hitung manual
        current_no = question_no if question_no else (len(session.details) + 1)
        
        # Jika user sedang mencoba lagi soal yang sama (detail sudah ada), kita update saja
        existing_detail = db.query(QuizDetail).filter(
            QuizDetail.session_id == session.id,
            QuizDetail.nomor_soal == current_no
        ).first()

        prediction = "None"
        confidence = 0.0
        is_correct = False
        status_msg = "unknown"
        message_msg = ""
        
        if not is_timeout and image_data:
            # 1. Run Pipeline Validation (checks base64, decoding, and domain match)
            validation_res = run_pipeline_validation(image_data, mode, target)
            if not validation_res.get("valid", True):
                prediction = "unknown"
                confidence = 0.0
                is_correct = False
                status_msg = validation_res.get("status")
                message_msg = validation_res.get("message")
            else:
                canvas = validation_res["canvas"]
                prediction, confidence = predict_from_canvas(canvas, mode)
                
                # Check output completeness
                if prediction is None or confidence is None:
                    prediction = "unknown"
                    confidence = 0.0
                    is_correct = False
                    status_msg = "Terjadi mismatch antara frontend - backend - model"
                    message_msg = "Coba ulangi ya 😊 sistem sedang menyesuaikan input"
                else:
                    eval_res = evaluate_model_output(prediction, confidence, mode, target=target)
                    is_correct = eval_res["correct"]
                    status_msg = eval_res["status"]
                    message_msg = eval_res["message"]
        else:
            prediction = "Timeout"
            confidence = 0.0
            is_correct = False
            status_msg = "Tidak Yakin, coba ulang"
            message_msg = "Coba lagi ya 😊"
        
        if existing_detail:
            # Update detail yang sudah ada (jika murid coba lagi di soal yang sama)
            existing_detail.prediction = prediction
            existing_detail.confidence = float(confidence * 100)
            # Jika sebelumnya sudah benar, jangan biarkan jadi salah lagi (opsional)
            # Tapi biasanya murid hanya coba lagi kalau salah.
            if not existing_detail.is_correct:
                existing_detail.is_correct = is_correct
            detail = existing_detail
        else:
            # Simpan detail soal baru
            detail = QuizDetail(
                session_id=session.id,
                nomor_soal=current_no,
                target_char=target,
                prediction=prediction,
                confidence=float(confidence * 100),
                is_correct=is_correct,
                waktu_jawab=datetime.utcnow()
            )
            db.add(detail)
        
        # Update session counters (Benar/Salah)
        # Hitung ulang dari semua detail untuk akurasi data
        db.commit()
        db.refresh(session)
        
        session.benar_count = len([d for d in session.details if d.is_correct])
        session.salah_count = len([d for d in session.details if not d.is_correct])
        session.skor_akhir = session.benar_count * 10
            
        db.commit()
        db.refresh(session)
        db.refresh(session) # Pastikan data terbaru di-fetch
        
        # Check if kuis selesai
        total_dikerjakan = len(session.details)
        finished = total_dikerjakan >= session.total_soal
        
        if finished:
            session.status = "finished"
            session.waktu_selesai = datetime.utcnow()
            session.durasi_detik = (session.waktu_selesai - session.waktu_mulai).total_seconds()
            db.commit()
            
        return {
            "correct": is_correct,
            "prediction": prediction,
            "confidence": round(float(confidence) * 100, 2),
            "finished": finished,
            "total_dikerjakan": total_dikerjakan,
            "next_url": f"/murid/quiz/kerjakan/{session.id}" if not finished else f"/murid/quiz/hasil/{session.id}",
            "status": status_msg,
            "message": message_msg
        }
        
    except Exception as e:
        print(f"Error in submit_quiz_answer: {e}")
        return JSONResponse(status_code=200, content=get_failsafe_response(message=f"Terjadi kesalahan sistem: {str(e)}"))

@router.get("/quiz/hasil/{session_id}", response_class=HTMLResponse)
async def quiz_hasil(request: Request, session_id: int, db: Session = Depends(get_db)):
    """Halaman hasil akhir kuis"""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    session = db.query(QuizSession).filter(QuizSession.id == session_id, QuizSession.siswa_id == user.id).first()
    if not session:
        return RedirectResponse(url="/murid/dashboard")
    
    # Hitung akurasi rata-rata
    avg_accuracy = sum([d.confidence for d in session.details]) / len(session.details) if session.details else 0
    
    return templates.TemplateResponse(
        request=request,
        name="murid/quiz-hasil.html",
        context={
            "user": user,
            "session": session,
            "avg_accuracy": round(avg_accuracy, 1)
        }
    )

@router.get("/quiz/detail/{session_id}", response_class=HTMLResponse)
async def quiz_detail(request: Request, session_id: int, db: Session = Depends(get_db)):
    """Halaman detail riwayat kuis"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
    if not session:
        return RedirectResponse(url="/murid/riwayat-nilai")
    
    return templates.TemplateResponse(
        request=request,
        name="murid/quiz-detail.html",
        context={
            "user": user,
            "session": session
        }
    )
