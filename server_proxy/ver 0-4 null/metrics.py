import psutil
import platform
import socket
import subprocess
from datetime import datetime
import time

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

# Сбор информации об устройстве
def get_device_info():
    cpu = platform.processor()
    ram = f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB"
    disk = f"{round(psutil.disk_usage('/').total / (1024 ** 3), 2)} GB"
    os_info = f"{platform.system()} {platform.release()}"
    gpu = get_gpu_info()  # Функция для GPU
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

# Получение информации о видеокарте (GPU)
def get_gpu_info():
    try:
        result = subprocess.run(['lspci'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            gpu_info = [line for line in result.stdout.splitlines() if 'VGA compatible controller' in line]
            return gpu_info[0] if gpu_info else "No GPU detected"
    except Exception as e:
        print(f"Ошибка при получении информации о GPU: {e}")
    return "No GPU detected"

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

# Получение температуры системы
def get_temperatures():
    try:
        result = subprocess.run(['sensors'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return result.stdout
    except Exception as e:
        print(f"Ошибка мониторинга температур: {e}")
    return "Temperatures unavailable"