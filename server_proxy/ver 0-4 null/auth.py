import os
from ipaddress import ip_address

from email_utils import send_email_response, get_email_response
from metrics import get_device_info, get_server_ip
import time

FLAG_FILE = "key_status.txt"


# Функция для сохранения статуса ключа
def save_key_status(status):
    with open(FLAG_FILE, 'w') as f:
        f.write("true" if status else "false")


# Функция для чтения статуса ключа
def load_key_status():
    if not os.path.exists(FLAG_FILE):
        return False  # Если файл не существует, возвращаем False
    with open(FLAG_FILE, 'r') as f:
        return f.read().strip() == "true"


# Функция для отправки ключа на сервер и проверки подтверждения
def send_key_to_server(main_server_email):
    # Проверяем, был ли ключ уже подтвержден
    if load_key_status():
        print("Ключ уже подтвержден ранее. Доступ к отправке метрик.")
        return True

    # Запрашиваем ввод ключа, если он не был подтвержден
    key = input("Введите ключ, выданный сервером: ")
    subject = f"Proxy Key Verification - {get_server_ip()}"
    send_email_response(main_server_email, subject, key)

    # Ожидание ответа от сервера
    print("Ожидание подтверждения ключа от сервера...")
    while True:
        response = get_email_response("Key answer")
        if response:
            if "approved" in response.lower():
                print("Ключ подтвержден. Отправка характеристик устройства.")
                save_key_status(True)  # Сохраняем подтверждение

                # Отправка характеристик устройства
                device_info = get_device_info()
                device_ip = get_server_ip()
                send_email_response(main_server_email, f"Proxy Device Information - {device_ip}", device_info)

                print("Информация об устройстве отправлена на сервер.")
                return True
            elif "unapproved" in response.lower():
                print("Ключ не подтвержден:", response)
                save_key_status(False)  # Сохраняем отказ
                return False
        time.sleep(5)