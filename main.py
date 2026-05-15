import base64
import numpy as np
import cv2
import uvicorn
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.modules.level_huruf.predict import predict_from_canvas
from app.modules.level_kata.validator import validate_word

app = FastAPI(title="GESTRA Multi-Level API")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/css", StaticFiles(directory=os.path.join(BASE_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(BASE_DIR, "js")), name="js")
app.mount("/assets", StaticFiles(directory=os.path.join(BASE_DIR, "assets")), name="assets")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "pages"))

# Route Website

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="beranda.html"
    )

@app.get("/{page_name}.html", response_class=HTMLResponse)
async def render_page(request: Request, page_name: str):
    return templates.TemplateResponse(
        request=request, 
        name=f"{page_name}.html"
    )

# [LEVEL HURUF] Update Endpoint /save
@app.post("/save")
async def save_canvas(request: Request):
    data = await request.json()
    mode, target, image_data = data.get("mode"), data.get("target"), data.get("image")

    # 1. Decode Image
    encoded_data = image_data.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    canvas = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    canvas = cv2.resize(canvas, (1200, 900), interpolation=cv2.INTER_LANCZOS4)

    # 2. Preprocessing
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Inisialisasi default
    prediction = "Kosong"
    confidence = 0.0

    if contours:
        valid_boxes = [cv2.boundingRect(c) for c in contours if cv2.boundingRect(c)[2] * cv2.boundingRect(c)[3] > 50]
        
        if valid_boxes:
            # Hitung Bounding Box Gabungan
            min_x = min([box[0] for box in valid_boxes])
            min_y = min([box[1] for box in valid_boxes])
            max_x = max([box[0] + box[2] for box in valid_boxes])
            max_y = max([box[1] + box[3] for box in valid_boxes])
            
            letter_crop = cv2.bitwise_not(thresh[min_y:max_y, min_x:max_x])
            canvas_1200 = np.ones((900, 1200, 3), dtype=np.uint8) * 255
            letter_res = cv2.cvtColor(letter_crop, cv2.COLOR_GRAY2BGR)
            
            nh, nw = letter_res.shape[:2]
            y_off, x_off = max(0, (900 - nh) // 2), max(0, (1200 - nw) // 2)
            h_limit, w_limit = min(nh, 900 - y_off), min(nw, 1200 - x_off)
            
            canvas_1200[y_off:y_off+h_limit, x_off:x_off+w_limit] = letter_res[:h_limit, :w_limit]
            
            # SIMPAN DEBUG
            cv2.imwrite(os.path.join(BASE_DIR, "assets", "debug", "hasil_input_gambar.png"), canvas_1200)
            
            # PREDIKSI (Cukup panggil sekali di sini)
            prediction, confidence = predict_from_canvas(canvas_1200, mode)

    # Ambil prediksi asli dari model
    prediction, confidence = predict_from_canvas(canvas_1200, mode)
    
    # Debug huruf level kata
    print(f"Target: {target}")
    print(f"AI Guess: {prediction}")
    print(f"Confidence: {confidence * 100:.2f}%")

    target_clean = str(target).strip().lower()
    pred_clean = str(prediction).strip().lower()

    original_guess = prediction 

    if pred_clean != target_clean and pred_clean not in ["kosong", "error", "tidak jelas"]:
        prediction = "Tidak Jelas"
    
    is_correct = (pred_clean == target_clean)

    return {
        "target": target,
        "prediction": prediction,
        "original_guess": original_guess,
        "confidence": round(float(confidence * 100)),
        "correct": is_correct
    }

# [LEVEL KATA] Update Endpoint /predict-word
@app.post("/predict-word")
async def final_word_validation(request: Request):
    data = await request.json()
    target = data.get("target")
    prediction = data.get("prediction")
    individual_scores = data.get("individual_scores", []) # Ambil array skor

    if individual_scores:
        # Hitung rata-rata: (Total Nilai Huruf) / Jumlah Huruf
        final_score = sum(individual_scores) / len(individual_scores)
        is_correct = final_score >= 80 
    else:
        is_correct, score_raw = validate_word(prediction, target)
        final_score = score_raw * 100

    return {
        "prediction": prediction,
        "score": round(final_score),
        "correct": is_correct,
        "target": target,
        "total_letters": len(prediction)
    }
    
if __name__ == "__main__":
    print("GESTRA System Berjalan di http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)