import cv2
import numpy as np

def segment_letters(canvas):
    """Segmentasi kata menjadi daftar gambar huruf individu."""
    orig_h, orig_w = canvas.shape[:2]
    
    # Grayscale & Thresholding
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Cari kontur huruf
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    initial_boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w * h < 300: continue # Filter noise kecil
        initial_boxes.append([x, y, w, h])

    if not initial_boxes: return []

    # Urutkan box dari kiri ke kanan
    initial_boxes.sort(key=lambda b: b[0])

    # Gabungkan box 
    merged_boxes = []
    curr = initial_boxes[0]
    for next_box in initial_boxes[1:]:
        # Cek overlap pada sumbu X
        x_overlap = max(0, min(curr[0] + curr[2], next_box[0] + next_box[2]) - max(curr[0], next_box[0]))
        
        # Jika overlap lebih dari 30% lebar box terkecil, gabungkan
        if x_overlap > min(curr[2], next_box[2]) * 0.3:
            new_x = min(curr[0], next_box[0])
            new_y = min(curr[1], next_box[1])
            new_w = max(curr[0] + curr[2], next_box[0] + next_box[2]) - new_x
            new_h = max(curr[1] + curr[3], next_box[1] + next_box[3]) - new_y
            curr = [new_x, new_y, new_w, new_h]
        else:
            merged_boxes.append(curr)
            curr = next_box
    merged_boxes.append(curr)

    letters = []
    for x, y, w, h in merged_boxes:
        crop = thresh[y:y+h, x:x+w]
        
        # Buat canvas putih persegi agar proporsi huruf terjaga (Padding)
        size = max(h, w) + 30
        letter_canvas = np.zeros((size, size), dtype=np.uint8)
        y_off = (size - h) // 2
        x_off = (size - w) // 2
        letter_canvas[y_off:y_off+h, x_off:x_off+w] = crop
        
        # Invert balik (BG Putih, Tulisan Hitam) sesuai dataset
        letter_canvas = 255 - letter_canvas
        letters.append(letter_canvas)

    return letters