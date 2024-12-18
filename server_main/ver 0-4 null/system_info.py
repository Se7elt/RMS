import smtplib
import platform
from distutils.command.config import config
import time
import psutil
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import subprocess
from config_utils import initialize_config, check_flag_and_data, prompt_for_data

config = initialize_config()

IMAP_USER = config["IMAP"]["IMAP_USER"]
IMAP_PASSWORD = config["IMAP"]["IMAP_PASSWORD"]
SMTP_SERVER = config["SMTP"]["SMTP_SERVER"]

# Получение IP-адреса сервера
def get_server_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        print(f"Ошибка при получении IP-адреса: {e}")
        return "Unable to get IP"

# Функция для сбора статических характеристик системы
# Сбор информации об устройстве
def get_system_info():
    cpu = platform.processor()
    ram = f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB"
    disk = f"{round(psutil.disk_usage('/').total / (1024 ** 3), 2)} GB"
    os_info = f"{platform.system()} {platform.release()}"
    gpu = get_gpu_info() # Функция для GPU
    ip = get_server_ip()

    device_info = f"""
    IP Address: {ip}
    CPU: {cpu}
    RAM: {ram}
    Disk: {disk}
    OS: {os_info}
    GPU: {gpu}
    """
    return device_info.strip()

# Функция для сбора динамических метрик системы
# Сбор системных метрик
def collect_metrics(duration=10):
    metrics = []
    start_time = time.time()

    while time.time() - start_time < duration:
        current_time = datetime.now().isoformat()
        cpu_load = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        network_load = psutil.net_io_counters()
        temperatures = get_temperatures()

        metrics.append({
            "timestamp": current_time,
            "cpu_load": cpu_load,
            "ram_usage": ram_usage,
            "network_sent": network_load.bytes_sent,
            "network_recv": network_load.bytes_recv,
            "temperatures": temperatures
        })

    return metrics
# Функция для отправки данных по email

def send_system_info_via_email(to_email, system_info):
    subject = f"Server Device Information - {get_server_ip()}"
    send_email_server_response(to_email, subject, system_info)

def send_metrics_via_email(to_email, metrics):
    subject = f"Metrics - {metrics['timestamp']}"
    body = "\n".join([f"{key}: {value}" for key, value in metrics.items()])
    send_email_server_response(to_email, subject, body)

def get_gpu_info():
    try:
        result = subprocess.run(['lspci'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            gpu_info = [line for line in result.stdout.splitlines() if 'VGA compatible controller' in line]
            return gpu_info[0] if gpu_info else "No GPU detected"
    except Exception as e:
        print(f"Ошибка при получении информации о GPU: {e}")
    return "No GPU detected"

# Получение температуры системы
def get_temperatures():
    try:
        result = subprocess.run(['sensors'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return result.stdout
    except Exception as e:
        print(f"Ошибка мониторинга температур: {e}")
    return "Temperatures unavailable"

# Функция для отправки server - email
def send_email_server_response(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = IMAP_USER
    msg['To'] = IMAP_USER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, 587)  # Замените на данные вашего SMTP
        server.starttls()
        server.login(IMAP_USER, IMAP_PASSWORD)
        server.sendmail(IMAP_USER, to_email, msg.as_string())
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")