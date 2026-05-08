import cv2
import numpy as np
import os
import tensorflow as tf
import string

# Menonaktifkan GPU untuk hemat RAM
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

LOADED_MODELS = {}

MODEL_PATHS = {
    "number": {
        "path": "models/CNN_Dataset_Huruf_Nomor.keras",
        "labels": ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    },
    "upper": {
        "path": "models/CNN_Dataset_Huruf_Besar_New.keras",
        "labels": list(string.ascii_uppercase)
    },
    "lower": {
        "path": "models/CNN_Dataset_Huruf_Kecil_New.keras",
        "labels": list(string.ascii_lowercase)
    }
}

def get_model(mode):
    if mode not in LOADED_MODELS:
        model_info = MODEL_PATHS.get(mode)
        if not model_info:
            raise ValueError(f"Mode {mode} tidak dikenali.")
        print(f"--- Memuat Model: {mode.upper()}")
        LOADED_MODELS[mode] = tf.keras.models.load_model(model_info["path"], compile=False)
    return LOADED_MODELS[mode]

def preprocess_canvas(canvas):
    # 1. Grayscale
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    
    # 2. Smoothing
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 3. Global Thresholding
    # Jika background putih (255) dan tulisan hitam (0), kita ambil nilai tengah
    _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY)
    
    # CEK APAKAH ADA TULISAN
    # Hitung jumlah piksel hitam (tulisan). 
    # Jika terlalu sedikit, berarti kanvas dianggap kosong.
    black_pixels = np.sum(thresh == 0)
    if black_pixels < 50:
        return None

    # 4. Resize & RGB Conversion
    # Melakukan resize ke 64x64 sebelum diconvert ke RGB agar lebih cepat
    resized_gray = cv2.resize(thresh, (64, 64))
    canvas_rgb = cv2.cvtColor(resized_gray, cv2.COLOR_GRAY2RGB)
    
    # 5. Final Preparation
    img_input = canvas_rgb.astype("float32") 
    img_input = np.expand_dims(img_input, axis=0)
    
    # Cek file ini untuk melihat apa yang dilihat AI
    cv2.imwrite("assets/debug/vsi_ai_final.png", thresh) 
    
    return img_input

def predict_from_canvas(canvas, mode):
    try:
        model = get_model(mode)
        labels = MODEL_PATHS[mode]["labels"]
        
        img_prepared = preprocess_canvas(canvas)
        
        # Jika kanvas kosong = ga diprediksi
        if img_prepared is None:
            return "Kosong", 0.0
        
        # Melakukan Prediksi
        preds = model.predict(img_prepared, verbose=0)[0]
        idx = int(np.argmax(preds))
        confidence = float(preds[idx])
        
        if confidence < 0.80: 
            return "Tidak Jelas", confidence

        result = labels[idx]
        return result, confidence
    except Exception as e:
        print(f"Error: {e}")
        return "Error", 0.0