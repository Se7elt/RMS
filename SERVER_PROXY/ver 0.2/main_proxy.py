import time
import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread
from auth import send_key_to_server, load_key_status
from metrics import collect_metrics, get_server_ip
from email_utils import send_email_response
from command_handler import await_server_command
from config_utils import initialize_config, check_flag_and_data, prompt_for_data

# Инициализация конфигурации
config = initialize_config()

# Проверка и запрос данных, если необходимо
if not check_flag_and_data(config):
    prompt_for_data(config)

SMTP_SERVER = config["EMAIL"]["SMTP_SERVER"]
SMTP_PORT = config["EMAIL"]["SMTP_PORT"]
SMTP_USER = config["EMAIL"]["SMTP_USER"]
SMTP_PASSWORD = config["EMAIL"]["SMTP_PASSWORD"]
IMAP_SERVER = config["EMAIL"]["IMAP_SERVER"]
IMAP_USER = config["EMAIL"]["IMAP_USER"]
IMAP_PASSWORD = config["EMAIL"]["IMAP_PASSWORD"]
main_server_email = config["MAIN_SERVER"]["MAIN_SERVER_EMAIL"]

def forward_to_main_server(subject, body, client_ip):
    """Пересылка сообщения от клиента на главный сервер с добавлением IP в тему."""
    msg = MIMEMultipart()
    msg["From"] = IMAP_USER
    msg["To"] = main_server_email
    msg["Subject"] = f"{subject} - {client_ip}"
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(IMAP_USER, IMAP_PASSWORD)
            server.sendmail(IMAP_USER, main_server_email, msg.as_string())
        print(f"Сообщение '{subject}' от {client_ip} переслано на главный сервер.")
    except Exception as e:
        print(f"Ошибка при пересылке на главный сервер: {e}")
        print("Попытка переподключения...")
        time.sleep(5)
        forward_to_main_server(subject, body, client_ip)  # Повторная попытка


def forward_response_to_client(client_ip, subject, body):
    """Пересылка ответа от главного сервера клиенту по его IP."""
    client_email = f"{client_ip}@example.com"

    msg = MIMEMultipart()
    msg["From"] = IMAP_USER
    msg["To"] = client_email
    msg["Subject"] = f"Ответ от сервера: {subject} - {client_ip}"
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(IMAP_USER, IMAP_PASSWORD)
            server.sendmail(IMAP_USER, client_email, msg.as_string())
        print(f"Ответ с темой '{subject}' переслан клиенту с IP {client_ip}.")
    except Exception as e:
        print(f"Ошибка при пересылке ответа клиенту: {e}")
        print("Попытка переподключения...")
        time.sleep(5)
        forward_response_to_client(client_ip, subject, body)  # Повторная попытка


def process_incoming_emails():
    """Циклическая обработка входящих писем с проверкой состояния подключения к IMAP серверу."""
    while True:
        try:
            with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
                mail.login(IMAP_USER, IMAP_PASSWORD)
                mail.select("inbox")

                # Выполняем поиск и обработку новых писем
                status, messages = mail.search(None, "ALL")
                email_ids = messages[0].split()

                for email_id in email_ids:
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])

                            # Извлечение темы письма
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding if encoding else "utf-8")

                            # Извлечение тела письма
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                            else:
                                body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

                            client_ip = subject.split("-")[-1].strip()

                            if "Client Key Verification" in subject or "Client Device Information" in subject or "Metrics" in subject:
                                forward_to_main_server(subject, body, client_ip)
                            elif "Ответ от сервера" in subject:
                                forward_response_to_client(client_ip, subject, body)

                            mail.store(email_id, '+FLAGS', '\\Deleted')
                mail.expunge()

        except imaplib.IMAP4.error as e:
            print(f"IMAP error: {e}")
            print("Попытка переподключения...")
            time.sleep(5)
        except Exception as e:
            print(f"Ошибка при обработке входящих писем: {e}")
            time.sleep(5)


def send_metrics_periodically():
    """Функция для сбора и отправки метрик каждые 10 секунд с проверкой состояния SMTP подключения."""
    device_ip = get_server_ip()
    retry_count = 0
    while retry_count < 5:  # Ограничиваем количество попыток
        metrics = collect_metrics(duration=10)
        metrics_text = ""
        for metric in metrics:
            timestamp = metric['timestamp'][:19].replace("T", " ")
            metrics_text += (
                f"-------------------------------------\n"
                f"Время: {timestamp}\n"
                f"CPU Load: {metric['cpu_load']}%\n"
                f"RAM Usage: {metric['ram_usage']}%\n"
                f"Network Sent: {metric['network_sent']} bytes\n"
                f"Network Received: {metric['network_received']} bytes\n"
                f"Температуры:\n{metric['temperatures']}\n"
                "-------------------------------------\n\n"
            )

        try:
            send_email_response(main_server_email, f"Metrics - {device_ip}", metrics_text)
            print("Метрики успешно отправлены.")
            retry_count = 0  # Сбросить счетчик попыток после успешной отправки
        except Exception as e:
            print(f"Ошибка при отправке метрик: {e}")
            retry_count += 1
            print(f"Попытка {retry_count} из 5.")
            time.sleep(5)

        time.sleep(10)

    if retry_count >= 5:
        print("Превышено количество попыток отправки метрик.")


def listen_for_commands():
    """Ожидание команд от сервера в отдельном потоке с проверкой состояния подключения."""
    server_ip = get_server_ip()
    await_server_command(server_ip)


if __name__ == "__main__":
    if not load_key_status():
        if not send_key_to_server(main_server_email):
            print("Доступ к отправке метрик не получен. Завершение работы.")
            exit(1)

    metrics_thread = Thread(target=send_metrics_periodically)
    commands_thread = Thread(target=listen_for_commands)
    email_thread = Thread(target=process_incoming_emails)

    metrics_thread.start()
    commands_thread.start()
    email_thread.start()

    metrics_thread.join()
    commands_thread.join()
    email_thread.join()
