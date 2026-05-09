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
from app.modules.level_kata.predict import predict_word
from app.modules.level_kata.segmenter import segment_letters
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

# [LEVEL HURUF] Endpoint untuk latihan per-huruf
@app.post("/save")
async def save_canvas(request: Request):
    data = await request.json()
    mode = data.get("mode")
    target = data.get("target")
    image_data = data.get("image")

    # Decode image dari Base64
    encoded_data = image_data.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    canvas = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    prediction, confidence = predict_from_canvas(canvas, mode)
    is_correct = str(prediction).strip().lower() == str(target).strip().lower()

    return {
        "target": target,
        "prediction": prediction,
        "confidence": round(float(confidence) * 100, 2),
        "correct": is_correct
    }

# [LEVEL KATA] Endpoint untuk latihan per-kata
@app.post("/predict-word")
async def predict_word_api(request: Request):
    try:
        data = await request.json()
        target, image_data = data.get("target"), data.get("image")

        # 1. Decode & Resize Main Canvas
        encoded_data = image_data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        canvas = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        canvas = cv2.resize(canvas, (1200, 900), interpolation=cv2.INTER_LANCZOS4)

        # 2. Segmentasi
        letters = segment_letters(canvas)
        if not letters:
            return {"prediction": "Kosong", "score": 0, "correct": False}

        processed_letters = []
        debug_dir = os.path.join(BASE_DIR, "assets", "debug")

        for i, letter_img in enumerate(letters):
            # A. Buat Kanvas Putih 1200x900 (3 Channel)
            canvas_1200 = np.ones((900, 1200, 3), dtype=np.uint8) * 255
            
            # B. FIX: Paksa potongan huruf jadi RGB
            if len(letter_img.shape) == 2:
                letter_img = cv2.cvtColor(letter_img, cv2.COLOR_GRAY2RGB)
            
            # BAGIAN PERBESAR (SCALING PROPORSIAL)
            h_orig, w_orig = letter_img.shape[:2]
            
            # Kita set target tinggi huruf sekitar 75% dari tinggi kanvas (900px)
            # Jadi target_h = 675px agar ada padding atas-bawah yang pas
            target_h = 675 
            scale = target_h / h_orig
            
            # Cek juga lebarnya, jangan sampai setelah di-scale malah melebihi 1200px
            if (w_orig * scale) > 1000:
                scale = 1000 / w_orig
                
            new_w = int(w_orig * scale)
            new_h = int(h_orig * scale)

            # Resize dengan kualitas tinggi (LANCZOS4) agar garis tetap smooth
            letter_resized = cv2.resize(letter_img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
            #-----------------------------------------

            # C. Hitung Offset Tengah yang baru
            y_off = (900 - new_h) // 2
            x_off = (1200 - new_w) // 2
            
            # D. Tempel ke tengah kanvas 1200x900
            canvas_1200[y_off:y_off+new_h, x_off:x_off+new_w] = letter_resized
            processed_letters.append(canvas_1200)

            # E. Simpan Debug
            cv2.imwrite(os.path.join(debug_dir, f"seg_{i}.png"), canvas_1200)

        # 3. Prediksi & Validasi
        predicted_result = predict_word(processed_letters)
        is_correct, score = validate_word(predicted_result, target)

        return {
            "prediction": predicted_result,
            "score": round(score, 2),
            "correct": is_correct,
            "debug_images": [f"/assets/debug/seg_{i}.png" for i in range(len(letters))]
        }
    except Exception as e:
        print(f"🚨 Error: {e}")
        return {"error": str(e), "correct": False}
    
if __name__ == "__main__":
    print("GESTRA System Berjalan di http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)