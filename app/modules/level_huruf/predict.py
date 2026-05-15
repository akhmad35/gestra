import os
import numpy as np
import cv2
import tensorflow as tf
import string

# Konfigurasi Environment
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

LOADED_MODELS = {}

# Path models
MODEL_PATHS = {
    "number": {
        "path": "models/CNN_Dataset_Huruf_Nomor.keras",
        "labels": list(string.digits)
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

# Fungsi untuk mendapatkan models
def get_model(mode):
    if mode not in LOADED_MODELS:
        model_info = MODEL_PATHS.get(mode)
        if not model_info:
            raise ValueError(f"Mode {mode} tidak dikenali.")
        print(f"--- Memuat Model: {mode.upper()}")
        LOADED_MODELS[mode] = tf.keras.models.load_model(model_info["path"], compile=False)
    return LOADED_MODELS[mode]

# Fungsi untuk melakukan preprocess pada canvas
def preprocess_canvas(canvas):
    # Grayscale dan Smoothing
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Global Thresholding
    # Jika background putih (255) dan tulisan hitam (0), kita ambil nilai tengah
    _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY)
    
    # Pengecekan apakah ada tulisan dalam canvas atau tidak
    # Hitung jumlah piksel hitam (tulisan). Jika terlalu sedikit, berarti kanvas dianggap kosong
    black_pixels = np.sum(thresh == 0)
    if black_pixels < 50:
        return None

    # Resize & RGB Conversion
    # Melakukan resize ke 64x64 sebelum diconvert ke RGB agar lebih cepat
    resized_gray = cv2.resize(thresh, (64, 64))
    canvas_rgb = cv2.cvtColor(resized_gray, cv2.COLOR_GRAY2RGB)
    
    # Final Preparation
    img_input = canvas_rgb.astype("float32") 
    img_input = np.expand_dims(img_input, axis=0)

    cv2.imwrite("assets/debug/vsi_ai_final.png", thresh) 
    return img_input

# Fungsi untuk prediksi tulisan dari canvas
def predict_from_canvas(canvas, mode):
    try:
        model = get_model(mode)
        labels = MODEL_PATHS[mode]["labels"]
        
        img_prepared = preprocess_canvas(canvas)
        
        # Jika canvas kosong, maka tidak terjadi prediksi dan akan mengembalikan nilai "Kosong"
        if img_prepared is None:
            return "Kosong", 0.0
        
        # Melakukan Prediksi
        preds = model.predict(img_prepared, verbose=0)[0]
        idx = int(np.argmax(preds))
        confidence = float(preds[idx])
        
        # Jika confidencenya kurang dari 80%, maka tulisan dianggap tidak jelas
        if confidence < 0.80: 
            return "Tidak Jelas", confidence

        result = labels[idx]
        return result, confidence
    except Exception as e:
        print(f"Error: {e}")
        return "Error", 0.0