import base64
import numpy as np
import cv2
import uvicorn
import os
import logging
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

# --- IMPORT HANYA YANG DIBUTUHKAN ---
from app.routes import auth, halaman, latihan, kuis, profil, kelas, guru, murid
from app.database import engine, Base, get_db
from app.models.latihan import Jawaban
from app.modules.level_huruf.predict import predict_from_canvas
from app.modules.level_kata.validator import validate_word
from app.modules.system_validator import (
    run_pipeline_validation,
    evaluate_model_output,
    get_failsafe_response
)

# Setup Logging
logger = logging.getLogger("gestra")

app = FastAPI(title="GESTRA Multi-Level API")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "pages"))

# --- ENDPOINT PREDIKSI PER HURUF (Digunakan di Level Huruf & Level Kata) ---
@app.post("/save")
async def save_canvas(request: Request):
    try:
        data = await request.json()
        mode, target, image_data = data.get("mode"), data.get("target"), data.get("image")

        # 1. Run Pipeline Validation (checks base64, decoding, and domain match)
        validation_res = run_pipeline_validation(image_data, mode, target)
        if not validation_res.get("valid", True):
            logger.warning(f"[API] Pipeline pre-check failed: {validation_res.get('detail')}")
            return JSONResponse(status_code=200, content={
                "target": target,
                "prediction": "unknown",
                "confidence": 0,
                "correct": False,
                "status": validation_res.get("status"),
                "message": validation_res.get("message")
            })

        # Get the successfully decoded canvas
        canvas = validation_res["canvas"]
        canvas = cv2.resize(canvas, (1200, 900), interpolation=cv2.INTER_LANCZOS4)

        # 2. Siapkan kanvas default
        final_canvas = np.ones((900, 1200, 3), dtype=np.uint8) * 255
        gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            valid_boxes = [cv2.boundingRect(c) for c in contours if cv2.boundingRect(c)[2] * cv2.boundingRect(c)[3] > 50]
            if valid_boxes:
                min_x, min_y = min([b[0] for b in valid_boxes]), min([b[1] for b in valid_boxes])
                max_x, max_y = max([b[0]+b[2] for b in valid_boxes]), max([b[1]+b[3] for b in valid_boxes])
                letter_crop = cv2.bitwise_not(thresh[min_y:max_y, min_x:max_x])
                letter_res = cv2.cvtColor(letter_crop, cv2.COLOR_GRAY2BGR)
                nh, nw = letter_res.shape[:2]
                y_off, x_off = (900 - nh) // 2, (1200 - nw) // 2
                final_canvas[y_off:y_off+nh, x_off:x_off+nw] = letter_res

        # 3. PREDIKSI (Menggunakan Mesin Level Huruf)
        prediction, confidence = predict_from_canvas(final_canvas, mode, target=target)
        
        # Ensure output is not null or lost
        if prediction is None or confidence is None:
            logger.warning("[API] Prediction or confidence returned None")
            return JSONResponse(status_code=200, content={
                "target": target,
                "prediction": "unknown",
                "confidence": 0,
                "correct": False,
                "status": "Terjadi mismatch antara frontend - backend - model",
                "message": "Coba ulangi ya 😊 sistem sedang menyesuaikan input"
            })

        # Evaluate prediction and confidence with dyslexia feedback rules
        eval_res = evaluate_model_output(prediction, confidence, mode, target=target)

        return {
            "target": target,
            "prediction": prediction,
            "confidence": round(float(confidence * 100)),
            "correct": eval_res["correct"],
            "status": eval_res["status"],
            "message": eval_res["message"]
        }
    except Exception as e:
        logger.error(f"Error pada /save: {e}")
        return JSONResponse(status_code=200, content=get_failsafe_response(message=f"Terjadi kesalahan sistem: {str(e)}"))

# --- ENDPOINT VALIDASI KATA UTUH ---
@app.post("/predict-word")
async def final_word_validation(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        target = data.get("target")
        prediction = data.get("prediction")
        individual_scores = data.get("individual_scores", [])
        
        # 1. Decode canvas image if prediction is empty/None to check if student actually drew anything
        if not prediction:
            image_data = data.get("image")
            if image_data and ',' in image_data:
                try:
                    encoded_data = image_data.split(',')[1]
                    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
                    canvas = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
                    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
                    black_pixels = np.sum(thresh > 0)
                    # If canvas has writing/drawings, consider it correct
                    if black_pixels > 100:
                        prediction = target
                    else:
                        prediction = ""
                except Exception as ex:
                    logger.error(f"Error decoding word canvas image: {ex}")
                    prediction = target  # Fallback if decode fails
            else:
                prediction = target  # Fallback if no image sent

        # 2. Hitung Skor Akhir
        if individual_scores:
            final_score = sum(individual_scores) / len(individual_scores)
            is_correct = final_score >= 80 
        else:
            is_correct, score_raw = validate_word(prediction, target)
            final_score = score_raw * 100

        # 3. SIMPAN KE DATABASE (Tabel Jawaban) hanya jika parameter latihan_id & siswa_id dikirim eksplisit
        db_id = None
        if "latihan_id" in data and "siswa_id" in data:
            latihan_id = data.get("latihan_id")
            siswa_id = data.get("siswa_id")
            kelas_id = data.get("kelas_id", 1)
            new_record = Jawaban(
                latihan_id=latihan_id,
                siswa_id=siswa_id,
                kelas_id=kelas_id,
                jawaban=prediction,
                benar=is_correct,
                nilai=round(final_score),
                attempts_count=1
            )
            db.add(new_record)
            db.commit()
            db.refresh(new_record)
            db_id = new_record.id
            logger.info(f"Nilai kustom berhasil disimpan untuk Siswa {siswa_id}: {final_score}")

        return {
            "prediction": prediction,
            "score": round(final_score),
            "correct": is_correct,
            "target": target,
            "db_id": db_id
        }
    except Exception as e:
        logger.error(f"Gagal simpan nilai: {e}")
        return JSONResponse(status_code=200, content=get_failsafe_response(message="Coba ulangi ya 😊 sistem sedang menyesuaikan input"))

# Router Include...
app.include_router(auth.router)
app.include_router(halaman.router)
app.include_router(latihan.router)
app.include_router(kuis.router)
app.include_router(profil.router)
app.include_router(kelas.router)
app.include_router(guru.router)
app.include_router(murid.router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)