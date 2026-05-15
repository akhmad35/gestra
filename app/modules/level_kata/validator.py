try:
    from Levenshtein import ratio
except ImportError:
    from difflib import SequenceMatcher

    def ratio(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()


def validate_word(predicted, target):
    predicted = predicted.lower().strip()
    target = target.lower().strip()

    score = ratio(predicted, target)
    is_correct = score >= 0.8

    return is_correct, score
