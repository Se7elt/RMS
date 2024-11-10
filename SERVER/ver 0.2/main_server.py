import time
import logging
import threading
from email_utils import fetch_and_process_emails
from database_utils import connect_db, ensure_device_info_table, register_device_in_db, create_metrics_table
from system_info import get_system_info, collect_metrics, send_system_info_via_email, send_metrics_via_email, get_server_ip
import sys
from config_utils import initialize_config, check_flag_and_data, prompt_for_data, save_config
from utils import send_email_response

logging.basicConfig(level=logging.INFO)

def send_metrics_loop(config):
    """Функция для отправки метрик каждые 10 секунд."""
    email_to_send = config["SMTP"]["SMTP_USER"]

    while True:
        # Сбор метрик за 10 секунд
        metrics_list = collect_metrics()
        # Форматируем метрики в строку для отправки одним письмом
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

        # Отправляем собранные метрики на почту
        send_email_response(
            to_email=email_to_send,
            subject=f"Metrics - {get_server_ip()}",
            body=metrics_body
        )

        time.sleep(10)  # Пауза перед следующим сбором

def check_email_loop(db_connection):
    """Функция для регулярной проверки входящих писем."""
    fetch_and_process_emails(db_connection)

if __name__ == "__main__":
    # Инициализация и загрузка конфигурации
    config = initialize_config()

    # Проверка наличия данных и флага
    if not check_flag_and_data(config):
        prompt_for_data(config)

    # Подключение к базе данных
    db_connection = connect_db(
        db_name=config["DATABASE"]["DB_NAME"],
        user=config["DATABASE"]["DB_USER"],
        password=config["DATABASE"]["DB_PASSWORD"],
        host=config["DATABASE"]["DB_HOST"],
        port=config["DATABASE"]["DB_PORT"]
    )

    # Проверка подключения
    if not db_connection:
        logging.error("Не удалось подключиться к базе данных. Завершение работы сервера.")
        sys.exit(1)  # Завершаем выполнение скрипта

    # Убедимся, что таблица Device_info существует и корректна
    ensure_device_info_table(db_connection)

    # Проверка флага отправки системных характеристик
    if config["SYSTEM"].getboolean("SYSTEM_INFO_SENT") == False:
        email_to_send = config["SMTP"]["SMTP_USER"]
        system_info = get_system_info()
        send_system_info_via_email(email_to_send, system_info)

        # Устанавливаем флаг в True и сохраняем конфигурацию
        config["SYSTEM"]["SYSTEM_INFO_SENT"] = "True"
        save_config(config)

    # Ваш email
    email_to_send = config["SMTP"]["SMTP_USER"]

    # Получение и отправка информации о системе
    system_info = get_system_info()
    send_system_info_via_email(email_to_send, system_info)

    # Создание потоков для отправки метрик и проверки почты
    metrics_thread = threading.Thread(target=send_metrics_loop, args=(config,))
    email_thread = threading.Thread(target=check_email_loop, args=(db_connection,))

    # Запуск потоков
    metrics_thread.start()
    email_thread.start()

    # Ожидание завершения работы потоков
    metrics_thread.join()
    email_thread.join()
