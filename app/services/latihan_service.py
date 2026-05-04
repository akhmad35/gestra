import random


LETTER_SEQUENCE = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
WORD_BANK = [
    {"kata": "BOLA", "gambar": "⚽"},
    {"kata": "IKAN", "gambar": "🐟"},
    {"kata": "AYAM", "gambar": "🐔"},
    {"kata": "BUKU", "gambar": "📘"},
]


def get_next_letter(current_letter: str | None = None) -> str:
    if not current_letter or current_letter.upper() not in LETTER_SEQUENCE:
        return LETTER_SEQUENCE[0]

    idx = LETTER_SEQUENCE.index(current_letter.upper())
    return LETTER_SEQUENCE[(idx + 1) % len(LETTER_SEQUENCE)]


def evaluate_letter_input(user_input: str, expected_letter: str) -> dict:
    cleaned_input = (user_input or "").strip().upper()
    expected = (expected_letter or "").strip().upper()
    is_correct = cleaned_input == expected
    score = 100 if is_correct else 40
    return {"benar": is_correct, "skor": score, "expected": expected}


def get_random_word_task() -> dict:
    return random.choice(WORD_BANK)


def evaluate_word_input(user_input: str, expected_word: str) -> dict:
    cleaned_input = (user_input or "").strip().upper()
    expected = (expected_word or "").strip().upper()
    is_correct = cleaned_input == expected
    score = 100 if is_correct else 50
    return {"benar": is_correct, "skor": score, "expected": expected}
