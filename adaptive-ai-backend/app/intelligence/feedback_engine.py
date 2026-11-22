def rating_score(rating: int) -> float:
    if not 1 <= rating <= 5:
        raise ValueError("rating must be from 1 to 5")
    return (rating - 1) / 4


def bounded_update(current: float, rating: int, learning_rate: float = 0.08) -> float:
    if not 0.0 <= current <= 1.0:
        raise ValueError("current score must be between 0 and 1")
    if not 0.0 < learning_rate <= 0.25:
        raise ValueError("learning_rate must be greater than 0 and at most 0.25")
    target = rating_score(rating)
    return round(max(0.0, min(1.0, current + learning_rate * (target - current))), 4)
