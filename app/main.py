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

        # 1. Decode & Preprocess
        encoded_data = image_data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        canvas = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
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
        # Sesuai file predict.py kamu, parameternya: (canvas, mode, target=None)
        prediction, confidence = predict_from_canvas(final_canvas, mode, target=target)
        
        # Logika sinkronisasi is_correct
        target_clean = str(target).strip().lower()
        pred_clean = str(prediction).strip().lower()
        is_correct = (pred_clean == target_clean)

        return {
            "target": target,
            "prediction": prediction,
            "confidence": round(float(confidence * 100)),
            "correct": is_correct
        }
    except Exception as e:
        logger.error(f"Error pada /save: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})

# --- ENDPOINT VALIDASI KATA UTUH ---
@app.post("/predict-word")
async def final_word_validation(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        target = data.get("target")
        prediction = data.get("prediction")
        individual_scores = data.get("individual_scores", [])
        
        # Ambil ID pendukung (pastikan dikirim dari JS atau dari session)
        latihan_id = data.get("latihan_id", 1) # Default ke ID 1 jika testing
        siswa_id = data.get("siswa_id", 1)
        kelas_id = data.get("kelas_id", 1)

        # 1. Hitung Skor Akhir
        if individual_scores:
            final_score = sum(individual_scores) / len(individual_scores)
            is_correct = final_score >= 80 
        else:
            is_correct, score_raw = validate_word(prediction, target)
            final_score = score_raw * 100

        # 2. SIMPAN KE DATABASE (Tabel Jawaban)
        new_record = Jawaban(
            latihan_id=latihan_id,
            siswa_id=siswa_id,
            kelas_id=kelas_id,
            jawaban=prediction,
            benar=is_correct,
            nilai=round(final_score),
            attempts_count=1 # Bisa ditambah logikanya nanti
        )
        
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        
        logger.info(f"Nilai berhasil disimpan untuk Siswa {siswa_id}: {final_score}")

        return {
            "prediction": prediction,
            "score": round(final_score),
            "correct": is_correct,
            "target": target,
            "db_id": new_record.id # Mengembalikan ID database sebagai konfirmasi
        }
    except Exception as e:
        logger.error(f"Gagal simpan nilai: {e}")
        return JSONResponse(status_code=400, content={"error": "Gagal memproses data jawaban"})

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