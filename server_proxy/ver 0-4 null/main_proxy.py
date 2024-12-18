import time
import threading
import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

# Словарь для отслеживания почты клиентов
client_requests = {}
smtp_connection = None
imap_connection = None


def main():
    # Инициализируем конфигурацию и проверяем флаг данных почты
    config = initialize_config()
    if not check_flag_and_data(config):
        prompt_for_data(config)

    # Проверка статуса ключа перед продолжением работы
    if not load_key_status():
        main_server_email = config["MAIN_SERVER"]["MAIN_SERVER_EMAIL"]
        print("Требуется ввод ключа верификации.")

        # Запрос и проверка ключа через send_key_to_server
        if not send_key_to_server(main_server_email):
            print("Ключ не подтвержден. Программа завершает работу.")
            return  # Выход из программы, если ключ не подтвержден

    # Основная логика программы
    print("Запуск основной логики программы...")

def connect_smtp():
    """Устанавливает соединение с SMTP-сервером и проверяет его стабильность."""
    global smtp_connection
    try:
        smtp_connection = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp_connection.starttls()
        smtp_connection.login(SMTP_USER, SMTP_PASSWORD)
        print("Соединение с SMTP-сервером успешно установлено.")
    except Exception as e:
        print(f"Ошибка подключения к SMTP-серверу: {e}")
        smtp_connection = None

def connect_imap():
    """Устанавливает соединение с IMAP-сервером и проверяет его стабильность."""
    global imap_connection
    try:
        imap_connection = imaplib.IMAP4_SSL(IMAP_SERVER)
        imap_connection.login(IMAP_USER, IMAP_PASSWORD)
        print("Соединение с IMAP-сервером успешно установлено.")
    except Exception as e:
        print(f"Ошибка подключения к IMAP-серверу: {e}")
        imap_connection = None

def check_smtp_connection():
    """Проверяет, стабильно ли соединение с SMTP. При необходимости переподключается."""
    global smtp_connection
    try:
        status = smtp_connection.noop()[0]
        if status != 250:  # 250 означает успешный отклик
            print("SMTP-соединение нестабильно, переподключение...")
            connect_smtp()
    except:
        print("SMTP-соединение потеряно, переподключение...")
        connect_smtp()

def check_imap_connection():
    """Проверяет, стабильно ли соединение с IMAP. При необходимости переподключается."""
    global imap_connection
    try:
        imap_connection.noop()
    except:
        print("IMAP-соединение потеряно, переподключение...")
        connect_imap()

def forward_to_main_server(subject, body, client_email):
    """Пересылка сообщения от клиента на главный сервер."""
    check_smtp_connection()  # Проверяем соединение перед отправкой
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = main_server_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        smtp_connection.sendmail(SMTP_USER, main_server_email, msg.as_string())
        print(f"Сообщение '{subject}' от клиента {client_email} переслано на главный сервер.")
    except Exception as e:
        print(f"Ошибка при пересылке на главный сервер: {e}")
        time.sleep(5)  # Пауза перед повторной попыткой
        forward_to_main_server(subject, body, client_email)  # Повторный вызов в случае ошибки

def forward_response_to_client(subject, body):
    """Пересылка ответа от главного сервера клиенту, почту которого сохранили в client_requests."""
    client_email = client_requests.get(subject)

    if client_email:
        check_smtp_connection()
        msg = MIMEMultipart()
        msg["From"] = IMAP_USER
        msg["To"] = client_email
        msg["Subject"] = f"Key answer: {subject}"
        msg.attach(MIMEText(body, "plain"))

        try:
            smtp_connection.sendmail(SMTP_USER, client_email, msg.as_string())
            print(f"Ответ '{subject}' переслан клиенту {client_email}.")
        except Exception as e:
            print(f"Ошибка при пересылке ответа клиенту: {e}")
            time.sleep(5)
            forward_response_to_client(subject, body)

        del client_requests[subject]
    else:
        print(f"Клиент для ответа '{subject}' не найден.")

def process_incoming_emails():
    """Циклическая обработка входящих писем с проверкой состояния подключения к IMAP серверу."""
    while True:
        check_imap_connection()  # Проверка соединения перед началом цикла обработки
        try:
            imap_connection.select("inbox")
            status, messages = imap_connection.search(None, "ALL")
            email_ids = messages[0].split()

            for email_id in email_ids:
                status, msg_data = imap_connection.fetch(email_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])

                        # Декодируем тему письма
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")

                        from_email = msg.get("From")

                        # Декодируем тело письма
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                        else:
                            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

                        # Проверка темы письма и пересылка только необходимых сообщений
                        if subject.startswith("Client Device Information - ") or subject.startswith("Metrics - "):
                            print(f"Пересылка сообщения '{subject}' от клиента {from_email} на главный сервер.")
                            forward_to_main_server(subject, body, from_email)
                        else:
                            print(f"Сообщение '{subject}' от {from_email} не требует пересылки.")

                        # Помечаем письмо как удалённое после обработки
                        imap_connection.store(email_id, '+FLAGS', '\\Deleted')
            imap_connection.expunge()  # Удаление писем из папки "Входящие"

        except Exception as e:
            print(f"Ошибка при обработке входящих писем: {e}")
            time.sleep(5)  # Задержка перед повторной попыткой

def send_metrics_loop():
    """Функция для отправки метрик каждые 10 секунд на главный сервер."""
    while True:
        check_smtp_connection()  # Проверяем соединение с SMTP перед отправкой
        metrics_list = collect_metrics()
        metrics_body = ""
        for metric in metrics_list:
            timestamp = metric['timestamp'][:19].replace("T", " ")
            metrics_body += "-------------------------------------\n"
            metrics_body += f"Время: {timestamp}\n"
            metrics_body += f"CPU Load: {metric['cpu_load']}%\n"
            metrics_body += f"RAM Usage: {metric['ram_usage']}%\n"
            metrics_body += f"Network Sent: {metric['network_sent']} bytes\n"
            metrics_body += f"Network Received: {metric['network_recv']} bytes\n"
            metrics_body += f"Temperature: {metric['temperatures']}\n"
            metrics_body += "-------------------------------------\n"

        send_email_response(
            to_email=main_server_email,
            subject=f"Metrics - {get_server_ip()}",
            body=metrics_body
        )
        time.sleep(10)

def await_commands_loop(server_ip):
    """Функция для постоянного ожидания команд от главного сервера."""
    while True:
        await_server_command(server_ip)


if __name__ == "__main__":
    config = initialize_config()
    if not check_flag_and_data(config):
        prompt_for_data(config)  # Запрашивает данные и устанавливает флаг
    # Инициализируем подключения
    connect_smtp()
    connect_imap()
    # Получаем IP адрес для использования в await_commands_loop
    server_ip = get_server_ip()

    main()

    # Создаем потоки для выполнения параллельных задач
    email_thread = threading.Thread(target=process_incoming_emails)
    metrics_thread = threading.Thread(target=send_metrics_loop)
    commands_thread = threading.Thread(target=await_commands_loop, args=(server_ip,))  # передаем аргумент server_ip

    # Запуск потоков
    email_thread.start()
    metrics_thread.start()
    commands_thread.start()

    # Ожидание завершения работы потоков
    email_thread.join()
    metrics_thread.join()
    commands_thread.join()
