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


def _random_huruf_target():
    selected_mode = random.choice(["upper", "lower"])
    target_char = random.choice(string.ascii_uppercase if selected_mode == "upper" else string.ascii_lowercase)
    return selected_mode, target_char


def _random_kata_target():
    kata_bank = [
        "buku", "kucing", "rumah", "pelangi", "senyum", "apel", "bunga", "bola", "jari", "pohon"
    ]
    return random.choice(kata_bank)


@router.get("/quiz-huruf/start")
async def start_quiz_huruf(request: Request, db: Session = Depends(get_db), timer: bool = False, level: str = None):
    """Mulai quiz huruf, dengan mode speed atau random sesuai query parameter."""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")

    # Validation: if timer is True but level is not chosen or invalid, redirect to pilih-level
    if timer and level not in {"easy", "medium", "hard"}:
        return RedirectResponse(url="/murid/pilih-level?type=huruf")

    # Initialize a new QuizSession
    session_mode = f"speed_huruf_{level}" if timer else "random_huruf"
    session = QuizSession(
        siswa_id=user.id,
        mode=session_mode,
        total_soal=10,
        status="ongoing",
        waktu_mulai=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return RedirectResponse(
        url=f"/murid/quiz/kerjakan/{session.id}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/quiz-kata/start")
async def start_quiz_kata(request: Request, db: Session = Depends(get_db), timer: bool = False, level: str = None):
    """Mulai quiz kata, dengan mode speed atau random sesuai query parameter."""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")

    # Validation: if timer is True but level is not chosen or invalid, redirect to pilih-level
    if timer and level not in {"easy", "medium", "hard"}:
        return RedirectResponse(url="/murid/pilih-level?type=kata")

    # Initialize a new QuizSession
    session_mode = f"speed_kata_{level}" if timer else "random_kata"
    session = QuizSession(
        siswa_id=user.id,
        mode=session_mode,
        total_soal=10,
        status="ongoing",
        waktu_mulai=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return RedirectResponse(
        url=f"/murid/quiz/kerjakan/{session.id}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/quiz-gabungan/start")
async def start_quiz_gabungan(request: Request, db: Session = Depends(get_db), timer: bool = False, level: str = None):
    """Mulai quiz gabungan: mix antara latihan huruf dan latihan kata."""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")

    # Validation: if timer is True but level is not chosen or invalid, redirect to pilih-level
    if timer and level not in {"easy", "medium", "hard"}:
        return RedirectResponse(url="/murid/pilih-level?type=gabungan")

    # Initialize a new QuizSession
    session_mode = f"speed_gabungan_{level}" if timer else "random_gabungan"
    session = QuizSession(
        siswa_id=user.id,
        mode=session_mode,
        total_soal=10,
        status="ongoing",
        waktu_mulai=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return RedirectResponse(
        url=f"/murid/quiz/kerjakan/{session.id}",
        status_code=status.HTTP_303_SEE_OTHER
    )


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
    
    # Parse mode details
    mode_str = session.mode
    is_timer = mode_str.startswith("speed") or "timer" in mode_str
    
    level = "medium"
    if "easy" in mode_str:
        level = "easy"
    elif "hard" in mode_str:
        level = "hard"
        
    # Tentukan jenis quiz (huruf, kata, gabungan)
    if "kata" in mode_str:
        quiz_type = "kata"
    elif "gabungan" in mode_str:
        quiz_type = "huruf" if current_question_no % 2 != 0 else "kata"
    else:
        quiz_type = "huruf"
        
    # Generate target acak
    if quiz_type == "kata":
        target = _random_kata_target()
        selected_mode = "lower"
        template_name = "canvas-latihan-kata.html"
    else:
        mode_choices = ["upper", "lower", "number"]
        selected_mode = random.choice(mode_choices)
        if selected_mode == "upper":
            target = random.choice(string.ascii_uppercase)
        elif selected_mode == "lower":
            target = random.choice(string.ascii_lowercase)
        else:
            target = str(random.randint(0, 9))
        template_name = "canvas-latihan-huruf.html"
    
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "user": user,
            "is_quiz": True,
            "is_timer": is_timer,
            "session": session,
            "current_question_no": current_question_no,
            "target": target,
            "mode": selected_mode,
            "level": level
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
        is_word = data.get("is_word", False)
        
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
        
        if is_word:
            prediction = data.get("prediction", "None")
            confidence = float(data.get("confidence", 0.0)) / 100.0
            is_correct = data.get("is_correct", False)
            status_msg = "Selesai"
            message_msg = "Hebat!"
        elif not is_timeout and image_data:
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
        
        db.commit()
        db.refresh(session)
        
        session.benar_count = len([d for d in session.details if d.is_correct])
        session.salah_count = len([d for d in session.details if not d.is_correct])
        session.skor_akhir = session.benar_count * 10
            
        db.commit()
        db.refresh(session)
        
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
    
    mode_str = session.mode
    is_timer = mode_str.startswith("speed") or "timer" in mode_str
    
    # Parse jenis kuis
    if "huruf" in mode_str:
        jenis_kuis = "Huruf"
    elif "kata" in mode_str:
        jenis_kuis = "Kata"
    elif "gabungan" in mode_str:
        jenis_kuis = "Gabungan"
    else:
        jenis_kuis = "Umum"

    # Parse level
    level = "Bebas"
    if "easy" in mode_str:
        level = "Mudah"
    elif "medium" in mode_str:
        level = "Sedang"
    elif "hard" in mode_str:
        level = "Sulit"
        
    duration_formatted = f"{int(session.durasi_detik // 60)}m {int(session.durasi_detik % 60)}s" if session.durasi_detik else "0s"
    persentase = round((session.benar_count / session.total_soal) * 100) if session.total_soal else 0
    
    # Dynamic retry url
    retry_level = "medium"
    if "easy" in mode_str:
        retry_level = "easy"
    elif "hard" in mode_str:
        retry_level = "hard"
        
    if "speed_huruf" in mode_str:
        retry_url = f"/murid/quiz-huruf/start?timer=true&level={retry_level}"
    elif "speed_kata" in mode_str:
        retry_url = f"/murid/quiz-kata/start?timer=true&level={retry_level}"
    elif "speed_gabungan" in mode_str:
        retry_url = f"/murid/quiz-gabungan/start?timer=true&level={retry_level}"
    elif "random_huruf" in mode_str:
        retry_url = "/murid/quiz-huruf/start"
    elif "random_kata" in mode_str:
        retry_url = "/murid/quiz-kata/start"
    elif "random_gabungan" in mode_str:
        retry_url = "/murid/quiz-gabungan/start"
    else:
        retry_url = "/murid/pilih-quiz"
        
    return templates.TemplateResponse(
        request=request,
        name="murid/quiz-hasil.html",
        context={
            "user": user,
            "session": session,
            "avg_accuracy": round(avg_accuracy, 1),
            "jenis_kuis": jenis_kuis,
            "level": level,
            "is_timer": is_timer,
            "duration_formatted": duration_formatted,
            "persentase": persentase,
            "retry_url": retry_url
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
