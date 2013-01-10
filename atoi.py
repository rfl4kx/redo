
def atoi(v, default=0):
    try:
        return int(v)
    except ValueError:
        return default
