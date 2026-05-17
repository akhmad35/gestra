import random

DATASET_HURUF = [
    {"id": f"huruf_{chr(i)}", "label": chr(i), "image": f"https://placehold.co/80x80?text={chr(i)}"}
    for i in range(65, 91)
]

DATASET_KATA = [
    {"id": "kata_buku", "label": "Buku", "image": "https://placehold.co/80x80?text=Buku"},
    {"id": "kata_meja", "label": "Meja", "image": "https://placehold.co/80x80?text=Meja"},
    {"id": "kata_kursi", "label": "Kursi", "image": "https://placehold.co/80x80?text=Kursi"},
    {"id": "kata_kaca", "label": "Kaca", "image": "https://placehold.co/80x80?text=Kaca"},
    {"id": "kata_pintu", "label": "Pintu", "image": "https://placehold.co/80x80?text=Pintu"},
    {"id": "kata_jendela", "label": "Jendela", "image": "https://placehold.co/80x80?text=Jendela"},
    {"id": "kata_sepatu", "label": "Sepatu", "image": "https://placehold.co/80x80?text=Sepatu"},
    {"id": "kata_baju", "label": "Baju", "image": "https://placehold.co/80x80?text=Baju"},
    {"id": "kata_topi", "label": "Topi", "image": "https://placehold.co/80x80?text=Topi"},
    {"id": "kata_tas", "label": "Tas", "image": "https://placehold.co/80x80?text=Tas"}
]

def get_dataset_by_type(dataset_type: str):
    if dataset_type == "huruf":
        return DATASET_HURUF
    elif dataset_type == "kata":
        return DATASET_KATA
    return []

def generate_random_questions(dataset_type: str, jumlah: int):
    dataset = get_dataset_by_type(dataset_type)
    if not dataset:
        return []
    
    # Ensure we don't ask for more than we have, or sample with replacement if needed
    if jumlah > len(dataset):
        # Sample with replacement if requesting more than available
        return random.choices(dataset, k=jumlah)
    else:
        return random.sample(dataset, k=jumlah)
