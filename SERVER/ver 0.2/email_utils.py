import imaplib
import email
import logging
import time
from config import get_config
from datetime import datetime
from email.header import decode_header
from device_handler import handle_key_email
from database_utils import register_device_in_db, create_metrics_table, insert_metrics_to_db
from system_info import send_system_info_via_email, send_metrics_via_email

logging.basicConfig(level=logging.INFO)

IMAP_SERVER = get_config("IMAP", "IMAP_SERVER")
IMAP_USER = get_config("IMAP", "IMAP_USER")
IMAP_PASSWORD = get_config("IMAP", "IMAP_PASSWORD")


def fetch_and_process_emails(connection, retry_delay=5):
    """Функция для повторного подключения при ошибках."""
    while True:
        try:
            with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
                mail.login(IMAP_USER, IMAP_PASSWORD)
                mail.select("inbox")
                status, messages = mail.search(None, 'ALL')
                email_ids = messages[0].split()

                # Получение и обработка писем
                for email_id in email_ids:
                    process_email(mail, email_id, connection)
                    mail.store(email_id, '+FLAGS', '\\Deleted')

                mail.expunge()
                logging.info("Все письма обработаны.")
                time.sleep(5)  # Интервал перед следующей проверкой
        except Exception as e:
            logging.error(f"Ошибка при обработке почты: {e}")
            logging.info(f"Переподключение через {retry_delay} секунд...")
            time.sleep(retry_delay)


def process_email(mail, email_id, connection):
    try:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = decode_subject(msg)
                from_ = msg.get("From")
                body = get_email_body(msg)

                # Определение типа устройства
                device_type = None
                if subject.startswith("Client"):
                    device_type = "client"
                elif subject.startswith("Proxy"):
                    device_type = "proxy"
                elif subject.startswith("Server"):
                    device_type = "server"

                # Логика обработки писем
                if "Key Verification" in subject:
                    handle_key_email(from_, msg)
                elif "Device Information" in subject:
                    ip_address = subject.split(" - ")[1]
                    process_device_information_email(connection, ip_address, body, device_type)
                elif "Metrics" in subject:
                    ip_address = subject.split(" - ")[1]
                    process_metrics_email(connection, ip_address, body)

    except Exception as e:
        logging.error(f"Ошибка при обработке письма {email_id}: {e}")

def process_system_info_email(body):
    # Декодируем и сохраняем информацию о системе
    print("Received system info email:", body)

def process_metrics_email(body):
    # Декодируем и сохраняем метрики
    print("Received metrics email:", body)

def decode_subject(msg):
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else "utf-8")
    return subject

def get_email_body(msg):
    """Извлечение тела email-сообщения."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            # Если это текстовая часть
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
                if body:
                    return body.decode("utf-8", errors="replace")
    else:
        body = msg.get_payload(decode=True)
        if body:
            return body.decode("utf-8", errors="replace")
    return body  # Возвращает пустую строку, если ничего не найдено

def process_device_information_email(connection, ip_address, email_body, device_type):
    try:
        device_info = {"type": device_type}  # Добавляем тип устройства
        for line in email_body.splitlines():
            if line.startswith("IP Address: "):
                device_info["ip_address"] = line.split(":")[1].strip()
            elif line.startswith("    CPU: "):
                device_info["cpu_info"] = line.split(":")[1].strip()
            elif line.startswith("    RAM: "):
                device_info["ram_info"] = line.split(":")[1].strip()
            elif line.startswith("    Disk: "):
                device_info["disk_space"] = line.split(":")[1].strip()
            elif line.startswith("    OS: "):
                device_info["os_info"] = line.split(":")[1].strip()
            elif line.startswith("    GPU: "):
                device_info["gpu_info"] = line.split(":")[1].strip()

        # Отладочный вывод информации об устройстве
        print(f"Извлеченная информация об устройстве: {device_info}")

        required_fields = ["ip_address", "cpu_info", "ram_info", "disk_space", "os_info", "gpu_info", "type"]
        if all(field in device_info for field in required_fields):
            register_device_in_db(connection, device_info)
            create_metrics_table(connection, ip_address)
        else:
            print("Не все обязательные поля присутствуют в устройстве.")
            print(f"Отсутствующие поля: {[field for field in required_fields if field not in device_info]}")

    except Exception as e:
        print(f"Ошибка при обработке письма с информацией об устройстве: {e}")

def process_metrics_email(connection, ip_address, email_body):
    try:
        # Разделение письма на отдельные блоки метрик по времени
        metric_blocks = email_body.split('-------------------------------------')

        for block in metric_blocks:
            # Пропускаем пустые блоки
            if not block.strip():
                continue

            # Извлечение метрик из каждого блока
            metrics = {}
            for line in block.splitlines():
                line = line.strip()  # Убираем пробелы в начале и конце строки
                if line.startswith("Время: "):
                    # Парсим и конвертируем время в формат timestamp
                    time_str = line.split(": ", 1)[1].strip()  # Извлекаем строку времени без добавления года
                    metrics["timestamp"] = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                elif line.startswith("CPU Load: "):
                    metrics["cpu_load_proc"] = float(line.split(":")[1].strip().replace('%', ''))
                elif line.startswith("RAM Usage: "):
                    metrics["ram_usage_proc"] = float(line.split(":")[1].strip().replace('%', ''))
                elif line.startswith("Network Sent: "):
                    metrics["network_sent_bytes"] = int(line.split(":")[1].strip().replace(" bytes", ""))
                elif line.startswith("Network Received: "):
                    metrics["network_recv_bytes"] = int(line.split(":")[1].strip().replace(" bytes", ""))
                elif line.startswith("Температуры:"):
                    # Пропускаем строку заголовка
                    continue
                elif "Composite:   " in line:
                    # Преобразуем температуру в вещественное число (например, отрезая '+')
                    metrics["temperatures_C"] = float(line.split(":")[1].strip().replace("°C", "").replace("+", ""))

            # Убедимся, что метрики корректно извлечены и добавляем в БД
            if metrics:
                insert_metrics_to_db(connection, ip_address, metrics)

    except Exception as e:
        print(f"Ошибка при обработке письма с метриками: {e}")


