import os
import time
from email_utils import send_email_response, get_email_response
from metrics import get_server_ip

FLAG_FILE = "key_status.txt"

def save_key_status(status):
    with open(FLAG_FILE, 'w') as f:
        f.write("true" if status else "false")

def load_key_status():
    if not os.path.exists(FLAG_FILE):
        return False
    with open(FLAG_FILE, 'r') as f:
        return f.read().strip() == "true"

def send_key_to_server(main_server_email):
    if load_key_status():
        print("Ключ уже подтвержден ранее.")
        return True

    key = input("Введите ключ, выданный главным сервером: ")
    send_email_response(main_server_email, f"Client Key Verification - {get_server_ip()}", key)

    print("Ожидание подтверждения ключа от главного сервера...")
    while True:
        response = get_email_response("Key answer")
        if response:
            if "approved" in response.lower():
                print("Ключ подтвержден. Начало работы.")
                save_key_status(True)
                return True
            elif "unapproved" in response.lower():
                print("Ключ не подтвержден:", response)
                save_key_status(False)
                return False
        time.sleep(5)
