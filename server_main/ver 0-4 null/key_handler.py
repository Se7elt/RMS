def validate_key(key):
    with open("keys.txt", "r") as f:
        keys = f.read().splitlines()
    if key in keys:
        keys.remove(key)
        with open("keys.txt", "w") as f:
            f.write("\n".join(keys) + "\n")
        return True
    return False
