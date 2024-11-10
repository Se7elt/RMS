import random
import string
def generate_key():
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    with open("keys.txt", "a") as f:
        f.write(key + "\n")
    return key
generate_key()