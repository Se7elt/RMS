import time
from threading import Thread
from auth import send_key_to_server, load_key_status
from metrics import collect_metrics, get_device_info, get_server_ip
from email_utils import send_email_response
from config_loader import config  # Импортируем конфигурацию

# Настройки серверов из config.ini
proxy_server_email = config["Servers"]["proxy_server_email"]
main_server_email = config["Servers"]["main_server_email"]

def send_metrics_periodically():
    """Функция для сбора и отправки метрик каждые 10 секунд."""
    device_ip = get_server_ip()
    while True:
        metrics = collect_metrics(duration=10)

        # Формируем текст для отправки метрик
        metrics_text = ""
        for metric in metrics:
            timestamp = metric['timestamp'][:19].replace("T", " ")
            metrics_text += f"-------------------------------------\n"
            metrics_text += f"Время: {timestamp}\n"
            metrics_text += f"CPU Load: {metric['cpu_load']}%\n"
            metrics_text += f"RAM Usage: {metric['ram_usage']}%\n"
            metrics_text += f"Network Sent: {metric['network_sent']} bytes\n"
            metrics_text += f"Network Received: {metric['network_received']} bytes\n"
            metrics_text += f"Температуры:\n{metric['temperatures']}\n"
            metrics_text += "-------------------------------------\n\n"

        # Отправляем метрики на прокси-сервер
        send_email_response(proxy_server_email, f"Metrics - {device_ip}", metrics_text)
        time.sleep(10)

if __name__ == "__main__":
    # Проверка ключа на главном сервере, если он не был ранее подтвержден
    if not load_key_status():
        if not send_key_to_server(main_server_email):  # Отправка запроса на главный сервер
            print("Доступ к отправке метрик не получен. Завершение работы.")
            exit(1)

    # Отправка информации об устройстве после подтверждения ключа на прокси-сервер
    device_info = get_device_info()
    send_email_response(proxy_server_email, f"Client Device Information - {get_server_ip()}", device_info)
    print("Информация об устройстве отправлена.")

    # Запуск потока для отправки метрик
    metrics_thread = Thread(target=send_metrics_periodically)
    metrics_thread.start()
    metrics_thread.join()
