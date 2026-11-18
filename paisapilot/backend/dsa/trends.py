def moving_average(values, k=3):
    window = values[-k:]
    return sum(window) / len(window) if window else 0.0

def is_unusual(current, history, factor=1.4):
    if not history:
        return False
    avg = moving_average(history)
    return avg > 0 and current > factor * avg