from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.database import get_db
from app.routes.halaman import get_current_user
from app.services.kelas import get_kelas_by_siswa, get_kelas_by_id, check_siswa_di_kelas, keluar_kelas
from app.services.latihan import (
    get_latihan_by_kelas,
    get_latihan_by_id,
    submit_jawaban,
    get_jawaban_siswa,
    get_jawaban_by_siswa,
    get_all_jawaban_by_siswa
)
from app.schemas.latihan import JawabanCreate

router = APIRouter(prefix="/murid", tags=["Murid"])
templates = Jinja2Templates(directory="app/templates")


# ===== DASHBOARD MURID =====
@router.get("/dashboard", response_class=HTMLResponse)
async def murid_dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard murid"""
    user = get_current_user(request, db)
    
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    # Ambil semua kelas yang diikuti murid
    kelas_list = get_kelas_by_siswa(db, user.id)
    kelas_ids = [k.id for k in kelas_list]
    
    # Ambil latihan yang tersedia (bukan draft) untuk kelas-kelas tersebut
    from app.models.latihan import Latihan
    latihan_tersedia = []
    if kelas_ids:
        latihan_tersedia = db.query(Latihan).filter(Latihan.kelas_id.in_(kelas_ids), Latihan.status != "draft").all()
        
    # Evaluate status of latihan
    now = datetime.now()
    latihan_data = []
    for lat in latihan_tersedia:
        st = "aktif"
        if lat.status == "selesai":
            st = "selesai"
        else:
            if lat.waktu_mulai and now < lat.waktu_mulai:
                st = "belum_dimulai"
            elif lat.waktu_selesai and now > lat.waktu_selesai:
                st = "berakhir"
                
        # Check if student already submitted
        from app.services.latihan import get_jawaban_siswa
        sudah_dikerjakan = get_jawaban_siswa(db, lat.id, user.id) is not None
        
        latihan_data.append({
            "latihan": lat,
            "status_waktu": st,
            "sudah_dikerjakan": sudah_dikerjakan,
            "nama_kelas": next((k.nama_kelas for k in kelas_list if k.id == lat.kelas_id), "Unknown")
        })
    
    # Generate data tambahan untuk kelas (Progress, Tugas Baru)
    import random
    kelas_list_data = []
    for k in kelas_list:
        progress_val = random.randint(10, 90)
        tugas_baru_val = sum(1 for l in latihan_data if l["latihan"].kelas_id == k.id and l["status_waktu"] == "aktif" and not l["sudah_dikerjakan"])
        kelas_list_data.append({
            "kelas": k,
            "progress": progress_val,
            "tugas_baru": tugas_baru_val
        })
    
    return templates.TemplateResponse(
        request=request,
        name="murid/dashboard.html",
        context={
            "user": user,
            "kelas_list": kelas_list,
            "kelas_list_data": kelas_list_data,
            "latihan_data": latihan_data
        }
    )


# ===== KELAS MURID =====
@router.get("/kelas/{kelas_id}/latihan", response_class=HTMLResponse)
async def lihat_latihan_kelas(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Lihat semua latihan di kelas"""
    user = get_current_user(request, db)
    
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    # Check apakah siswa sudah bergabung di kelas
    sudah_bergabung = check_siswa_di_kelas(db, kelas_id, user.id)
    
    if not sudah_bergabung:
        return RedirectResponse(url="/kelas/daftar")
    
    kelas = get_kelas_by_id(db, kelas_id)
    
    if not kelas:
        return RedirectResponse(url="/kelas/daftar")
    
    # Ambil latihan di kelas
    latihan_list = get_latihan_by_kelas(db, kelas_id)
    
    # Ambil jawaban siswa
    jawaban_siswa_list = get_jawaban_by_siswa(db, user.id, kelas_id)
    jawaban_dict = {j.latihan_id: j for j in jawaban_siswa_list}
    
    return templates.TemplateResponse(
        request=request,
        name="murid/latihan-kelas.html",
        context={
            "user": user,
            "kelas": kelas,
            "latihan_list": latihan_list,
            "jawaban_dict": jawaban_dict
        }
    )


@router.post("/kelas/{kelas_id}/keluar")
async def keluar_kelas_endpoint(
    request: Request,
    kelas_id: int,
    db: Session = Depends(get_db)
):
    """Siswa keluar dari kelas"""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    success = keluar_kelas(db, kelas_id, user.id)
    if success:
        return RedirectResponse(url="/murid/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url=f"/murid/kelas/{kelas_id}/latihan", status_code=status.HTTP_303_SEE_OTHER)


# ===== KERJAKAN LATIHAN (MURID) =====
@router.get("/latihan/{latihan_id}/kerjakan", response_class=HTMLResponse)
async def kerjakan_latihan_page(
    request: Request,
    latihan_id: int,
    db: Session = Depends(get_db)
):
    """Halaman kerjakan latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan:
        return RedirectResponse(url="/murid/dashboard")
    
    # Check apakah siswa sudah bergabung di kelas
    sudah_bergabung = check_siswa_di_kelas(db, latihan.kelas_id, user.id)
    
    if not sudah_bergabung:
        return RedirectResponse(url="/kelas/daftar")
    
    # Ambil jawaban sebelumnya jika ada
    jawaban_sebelumnya = get_jawaban_siswa(db, latihan_id, user.id)
    
    if jawaban_sebelumnya:
        if not latihan.izinkan_retry:
            return RedirectResponse(url=f"/murid/latihan/{latihan_id}/hasil")
        if latihan.max_attempt != -1 and jawaban_sebelumnya.attempts_count >= latihan.max_attempt:
            return RedirectResponse(url=f"/murid/latihan/{latihan_id}/hasil")
            
    kelas = get_kelas_by_id(db, latihan.kelas_id)
    
    # Parse soal tergenerate
    soal_list = []
    if latihan.soal_tergenerate:
        try:
            soal_list = json.loads(latihan.soal_tergenerate)
        except:
            pass

    target = request.query_params.get("target")
    index = request.query_params.get("index")

    if (not target or not index) and len(soal_list) > 0:
        import urllib.parse
        first_word = soal_list[0].get("label", "")
        return RedirectResponse(
            url=f"/murid/latihan/{latihan_id}/kerjakan?target={urllib.parse.quote(first_word)}&index=0",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="murid/kerjakan-latihan.html",
        context={
            "user": user,
            "kelas": kelas,
            "latihan": latihan,
            "jawaban_sebelumnya": jawaban_sebelumnya,
            "soal_list": json.dumps(soal_list)
        }
    )


@router.post("/latihan/{latihan_id}/submit")
async def submit_latihan(
    request: Request,
    latihan_id: int,
    jawaban_text: str = Form(...),
    db: Session = Depends(get_db)
):
    """Submit jawaban latihan"""
    user = get_current_user(request, db)
    
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan:
        return RedirectResponse(url="/murid/dashboard")
    
    # Check apakah siswa sudah bergabung di kelas
    sudah_bergabung = check_siswa_di_kelas(db, latihan.kelas_id, user.id)
    
    if not sudah_bergabung:
        return RedirectResponse(url="/kelas/daftar")
    
    # Parse JSON jawaban dan hitung nilai
    overall_score = 0
    overall_correct = False
    try:
        ans_list = json.loads(jawaban_text)
        if isinstance(ans_list, list) and len(ans_list) > 0:
            total_nilai = sum(item.get("nilai", 0) for item in ans_list)
            overall_score = int(total_nilai / len(ans_list))
            overall_correct = overall_score >= 70
    except Exception as e:
        print(f"Error parsing JSON in submit_latihan: {e}")

    # Ambil model Jawaban untuk update atau insert
    from app.models.latihan import Jawaban
    existing = db.query(Jawaban).filter(
        (Jawaban.latihan_id == latihan_id) &
        (Jawaban.siswa_id == user.id)
    ).first()
    
    if existing:
        existing.jawaban = jawaban_text
        existing.nilai = overall_score
        existing.benar = overall_correct
        existing.attempts_count += 1
        existing.dikoreksi_pada = datetime.utcnow()
        existing.dikumpulkan_pada = datetime.utcnow()
        db.add(existing)
    else:
        db_jawaban = Jawaban(
            latihan_id=latihan_id,
            siswa_id=user.id,
            kelas_id=latihan.kelas_id,
            jawaban=jawaban_text,
            nilai=overall_score,
            benar=overall_correct,
            attempts_count=1,
            dikoreksi_pada=datetime.utcnow()
        )
        db.add(db_jawaban)
    db.commit()
    
    return RedirectResponse(
        url=f"/murid/latihan/{latihan_id}/hasil",
        status_code=status.HTTP_303_SEE_OTHER
    )


# ===== LIHAT HASIL JAWABAN (MURID) =====
@router.get("/latihan/{latihan_id}/hasil", response_class=HTMLResponse)
async def lihat_hasil_jawaban(
    request: Request,
    latihan_id: int,
    db: Session = Depends(get_db)
):
    """Lihat hasil jawaban siswa"""
    user = get_current_user(request, db)
    
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    latihan = get_latihan_by_id(db, latihan_id)
    
    if not latihan:
        return RedirectResponse(url="/murid/dashboard")
    
    # Ambil jawaban siswa
    jawaban = get_current_user(request, db) # Oops, this was wrong in the previous version too, but I'll use get_jawaban_siswa
    from app.services.latihan import get_jawaban_siswa
    jawaban = get_jawaban_siswa(db, latihan_id, user.id)
    
    if not jawaban:
        return RedirectResponse(
            url=f"/murid/kelas/{latihan.kelas_id}/latihan"
        )
    
    kelas = get_kelas_by_id(db, latihan.kelas_id)
    
    # Parse detail jawaban jika berformat JSON list
    detail_jawaban = []
    total_soal = 0
    total_benar = 0
    total_salah = 0
    is_json = False
    
    if jawaban and jawaban.jawaban:
        try:
            parsed = json.loads(jawaban.jawaban)
            if isinstance(parsed, list):
                detail_jawaban = parsed
                total_soal = len(detail_jawaban)
                total_benar = sum(1 for item in detail_jawaban if item.get("benar", False))
                total_salah = total_soal - total_benar
                is_json = True
        except Exception as e:
            print(f"Fallback parsing old format in lihat_hasil_jawaban: {e}")
    
    return templates.TemplateResponse(
        request=request,
        name="murid/hasil-jawaban.html",
        context={
            "user": user,
            "kelas": kelas,
            "latihan": latihan,
            "jawaban": jawaban,
            "detail_jawaban": detail_jawaban,
            "total_soal": total_soal,
            "total_benar": total_benar,
            "total_salah": total_salah,
            "is_json": is_json
        }
    )


# ===== RIWAYAT NILAI (MURID) =====
@router.get("/riwayat-nilai", response_class=HTMLResponse)
async def riwayat_nilai(request: Request, db: Session = Depends(get_db)):
    """Halaman riwayat nilai murid"""
    user = get_current_user(request, db)
    
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    # Ambil semua jawaban/nilai latihan kelas
    riwayat_list = get_all_jawaban_by_siswa(db, user.id)
    
    # Ambil semua sesi kuis random/timer
    from app.models.quiz import QuizSession
    quiz_sessions = db.query(QuizSession).filter(QuizSession.siswa_id == user.id).order_by(QuizSession.waktu_mulai.desc()).all()
    
    total_kuis = len(riwayat_list) + len(quiz_sessions)
    total_lulus = len([r for r in riwayat_list if r.nilai >= 70]) + len([q for q in quiz_sessions if q.skor_akhir >= 70])
    
    sum_nilai = sum([r.nilai for r in riwayat_list]) + sum([q.skor_akhir for q in quiz_sessions])
    rata_rata = sum_nilai / total_kuis if total_kuis > 0 else 0
    
    stats = {
        "total_kuis": total_kuis,
        "total_lulus": total_lulus,
        "rata_rata": round(rata_rata, 1)
    }
    
    return templates.TemplateResponse(
        request=request,
        name="murid/riwayat-nilai.html",
        context={
            "user": user,
            "riwayat_list": riwayat_list,
            "quiz_sessions": quiz_sessions,
            "stats": stats
        }
    )

# ===== QUIZ BARU (AI, TIMER, INTERAKTIF) =====
@router.get("/quiz-random")
async def quiz_random(request: Request, db: Session = Depends(get_db)):
    """Quiz Random (Redirect ke canvas-latihan-huruf dengan target acak)"""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    
    import random
    import string
    
    # Pilih target acak (bisa huruf atau angka)
    mode_choices = ["upper", "lower", "number"]
    selected_mode = random.choice(mode_choices)
    
    if selected_mode == "upper":
        target = random.choice(string.ascii_uppercase)
    elif selected_mode == "lower":
        target = random.choice(string.ascii_lowercase)
    else:
        target = str(random.randint(0, 9))
        
    # Redirect ke canvas yang ada
    return RedirectResponse(
        url=f"/canvas-latihan-huruf?target={target}&mode={selected_mode}&random=true",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/quiz-timer")
async def quiz_timer(request: Request, db: Session = Depends(get_db)):
    """Quiz Timer (Redirect ke canvas-latihan-huruf dengan timer=true)"""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
        
    import random
    import string
    
    # Pilih target acak (bisa huruf atau angka)
    mode_choices = ["upper", "lower", "number"]
    selected_mode = random.choice(mode_choices)
    
    if selected_mode == "upper":
        target = random.choice(string.ascii_uppercase)
    elif selected_mode == "lower":
        target = random.choice(string.ascii_lowercase)
    else:
        target = str(random.randint(0, 9))
        
    # Redirect ke canvas dengan parameter timer=true
    return RedirectResponse(
        url=f"/canvas-latihan-huruf?target={target}&mode={selected_mode}&timer=true",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/quiz-interaktif", response_class=HTMLResponse)
async def quiz_interaktif(request: Request, db: Session = Depends(get_db)):
    """Halaman Quiz Interaktif"""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="murid/quiz-interaktif.html", context={"user": user})

# ===== ACHIEVEMENT & PROGRESS =====
@router.get("/achievement", response_class=HTMLResponse)
async def achievement_page(request: Request, db: Session = Depends(get_db)):
    """Halaman Achievement"""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="murid/achievement.html", context={"user": user})

@router.get("/progress", response_class=HTMLResponse)
async def progress_page(request: Request, db: Session = Depends(get_db)):
    """Halaman Progress"""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="murid/progress.html", context={"user": user})

@router.get("/aktivitas", response_class=HTMLResponse)
async def aktivitas_menu(request: Request, db: Session = Depends(get_db)):
    """Menu pilihan aktivitas murid (Speed Quiz, Quiz Random, Gabung Kelas)"""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="murid/menu-aktivitas.html", context={"user": user})


@router.get("/pilih-quiz", response_class=HTMLResponse)
async def pilih_quiz(request: Request, db: Session = Depends(get_db)):
    """Halaman pemilihan jenis quiz setelah memilih mode speed atau random."""
    user = get_current_user(request, db)
    if not user or user.role != "murid":
        return RedirectResponse(url="/login")

    mode = request.query_params.get("mode", "random")
    if mode not in {"speed", "random"}:
        mode = "random"

    return templates.TemplateResponse(
        request=request,
        name="murid/pilih-quiz.html",
        context={"user": user, "mode": mode}
    )
