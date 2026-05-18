import base64
import numpy as np
import cv2
import logging
import string
from typing import Dict, Any, Tuple, Optional

# Setup Logging
logger = logging.getLogger("gestra.validator")

# Define domain mappings
DOMAINS = {
    "upper": set(string.ascii_uppercase),
    "lower": set(string.ascii_lowercase),
    "number": set(string.digits),
}


def validate_base64_image(image_data: str) -> Tuple[bool, Optional[bytes], str]:
    """
    Validasi 1: Apakah base64 image valid?
    """
    if not image_data:
        return False, None, "Base64 image kosong atau tidak ditemukan."

    try:
        # Check and strip prefix
        if "," in image_data:
            header, image_data = image_data.split(",", 1)

        # Check padding
        padding_needed = len(image_data) % 4
        if padding_needed:
            image_data += "=" * (4 - padding_needed)

        decoded_bytes = base64.b64decode(image_data)
        if len(decoded_bytes) == 0:
            return (
                False,
                None,
                "Base64 image berhasil didecode tetapi menghasilkan 0 byte.",
            )

        return True, decoded_bytes, "Base64 image valid."
    except Exception as e:
        logger.error(f"[Validator] Base64 validation failed: {e}")
        return False, None, f"Base64 image tidak valid atau rusak: {str(e)}"


def decode_and_validate_canvas(
    decoded_bytes: bytes,
) -> Tuple[bool, Optional[np.ndarray], str]:
    """
    Validasi 2: Apakah decoding base64 berhasil menjadi gambar OpenCV?
    """
    try:
        nparr = np.frombuffer(decoded_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False, None, "Gambar gagal di-decode oleh OpenCV (hasil None)."

        # Check image dimensions
        h, w = img.shape[:2]
        if h == 0 or w == 0:
            return False, None, f"Dimensi gambar tidak valid: {w}x{h}."

        return True, img, f"Gambar berhasil di-decode. Dimensi: {w}x{h}."
    except Exception as e:
        logger.error(f"[Validator] Image decoding failed: {e}")
        return False, None, f"Gagal membaca format gambar: {str(e)}"


def validate_domain_match(target: str, mode: str) -> Tuple[bool, str]:
    """
    Validasi 3: Apakah label target sesuai dengan domain model yang dipilih?
    """
    if not target:
        return True, "Target kosong (opsional)."

    mode_clean = str(mode).strip().lower()
    target_char = str(target).strip()

    # We only validate the first character for letter-level domain check
    if len(target_char) > 0:
        char_to_check = target_char[0]
    else:
        return False, "Target tidak berisi karakter valid."

    if mode_clean not in DOMAINS:
        return (
            False,
            f"Mode '{mode}' tidak dikenal. Domain yang tersedia: {list(DOMAINS.keys())}.",
        )

    valid_set = DOMAINS[mode_clean]

    if char_to_check in valid_set:
        return True, f"Karakter '{char_to_check}' sesuai dengan domain '{mode_clean}'."
    else:
        return (
            False,
            f"Model tidak cocok dengan input. Karakter '{char_to_check}' tidak berada dalam domain '{mode_clean}'.",
        )


def evaluate_model_output(
    prediction: str, confidence: float, mode: str, target: Optional[str] = None
) -> Dict[str, Any]:

    target_char = str(target).strip() if target else ""
    pred_clean = str(prediction).strip()

    # 1. domain check tetap
    domain_match, domain_msg = validate_domain_match(target_char, mode)
    if not domain_match:
        return {
            "status": "Coba lagi!",
            "message": "Coba lagi ya 😊",
            "correct": False,
            "explanation": domain_msg,
        }

    # 2. kosong / tidak jelas
    if pred_clean == "Kosong" or confidence == 0.0:
        return {
            "status": "Coba lagi!",
            "message": "Coba lagi ya 😊",
            "correct": False,
            "explanation": "Canvas kosong atau tidak jelas",
        }

    # 3. ✨ LOGIKA UTAMA: HARUS MATCH TARGET
    is_match = pred_clean.lower() == target_char.lower()

    if is_match:
        return {
            "status": "Benar",
            "message": "Bagus 👍",
            "correct": True,
            "explanation": "Huruf sesuai target",
        }

    # 4. kalau tidak match = langsung salah
    return {
        "status": "Coba lagi!",
        "message": "Coba lagi ya 😊",
        "correct": False,
        "explanation": f"Prediksi '{pred_clean}' tidak sama dengan target '{target_char}'",
    }


def get_failsafe_response(message: Optional[str] = None) -> Dict[str, Any]:
    """
    Format Failsafe Response yang aman (Section 5)
    """
    fallback_msg = (
        message if message else "Coba ulangi ya 😊 sistem sedang menyesuaikan input"
    )
    return {
        "prediction": "unknown",
        "confidence": 0.0,
        "status": "system_error",
        "message": fallback_msg,
        "correct": False,
        "target": "",
    }


def run_pipeline_validation(image_data: str, mode: str, target: str) -> Dict[str, Any]:
    """
    Melakukan full pipeline checks (Debugging Mode - Section 4) secara berurutan.
    """
    logger.info(
        f"[Validator] Menjalankan validasi pipeline untuk target='{target}', mode='{mode}'"
    )

    # 1. Apakah base64 image valid?
    base64_ok, decoded_bytes, base64_msg = validate_base64_image(image_data)
    if not base64_ok:
        logger.warning(f"[Validator] Validasi 1 gagal: {base64_msg}")
        return {
            "valid": False,
            "step_failed": 1,
            "status": "Terjadi mismatch antara frontend - backend - model",
            "message": "Coba ulangi ya 😊 sistem sedang menyesuaikan input",
            "detail": base64_msg,
        }

    # 2. Apakah decoding base64 berhasil?
    decode_ok, canvas, decode_msg = decode_and_validate_canvas(decoded_bytes)
    if not decode_ok:
        logger.warning(f"[Validator] Validasi 2 gagal: {decode_msg}")
        return {
            "valid": False,
            "step_failed": 2,
            "status": "Terjadi mismatch antara frontend - backend - model",
            "message": "Coba ulangi ya 😊 sistem sedang menyesuaikan input",
            "detail": decode_msg,
        }

    # 3. Apakah domain cocok dengan input?
    domain_ok, domain_msg = validate_domain_match(target, mode)
    if not domain_ok:
        logger.warning(f"[Validator] Validasi 3 gagal: {domain_msg}")
        return {
            "valid": False,
            "step_failed": 3,
            "status": "Model tidak cocok dengan input",
            "message": "Coba lagi ya 😊",
            "detail": domain_msg,
        }

    logger.info("[Validator] Seluruh pre-checks pipeline valid.")
    return {"valid": True, "canvas": canvas, "detail": "Pipeline input valid."}
