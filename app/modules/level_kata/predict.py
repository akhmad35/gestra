import os
import numpy as np
import cv2
import tensorflow as tf
import string

# Konfigurasi Environment (Hemat RAM & Bersih)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# Path model relatif terhadap root proyek
MODEL_PATH = "models/CNN_Dataset_Huruf_Kecil_New.keras"
model = tf.keras.models.load_model(MODEL_PATH, compile=False)
labels = list(string.ascii_lowercase)

def preprocess(img):
    """Pra-pemrosesan gambar huruf individu sesuai input model (64x64x3)."""
    # Resize
    img = cv2.resize(img, (64, 64), interpolation=cv2.INTER_AREA)
    img = img.astype("float32")
    
    # Konversi ke RGB karena model Sequential mengharapkan 3 channel
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    
    # Tambahkan dimensi batch (1, 64, 64, 3)
    return np.expand_dims(img, axis=0)

def predict_word(letters):
    """Prediksi rangkaian gambar huruf menjadi satu string kata."""
    predicted_word = ""
    
    for i, letter_img in enumerate(letters):
        # Simpan debug untuk cek hasil segmentasi jika diperlukan
        # cv2.imwrite(f"assets/debug/letter_{i}.png", letter_img)
        
        x = preprocess(letter_img)
        preds = model.predict(x, verbose=0)[0]
        idx = int(np.argmax(preds))
        
        predicted_word += labels[idx]
        
    return predicted_word