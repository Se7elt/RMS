from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from .models import DeviceInfo, SystemLog

# Пример функции представления
def logs_and_devices_view(request):
    logs = SystemLog.objects.order_by('-timestamp')[:3]
    devices = DeviceInfo.objects.all()
    context = {'logs': logs, 'devices': devices}
    return render(request, 'logs/base.html', context)

def device_details(request, device_id):
    try:
        device = DeviceInfo.objects.get(ip_address=device_id)  # Используем ip_address как ключ
        data = {
            "ip_address": device.ip_address,
            "cpu_info": device.cpu_info,
            "ram_info": device.ram_info,
            "disk_space": device.disk_space,
            "os_info": device.os_info,
            "gpu_info": device.gpu_info,
            "type": device.type,
        }
        return JsonResponse(data)
    except DeviceInfo.DoesNotExist:
        return JsonResponse({"error": "Device not found"}, status=404)


# Функция для получения метрик
def metrics_view(request, ip_address):
    # Формируем имя таблицы метрик
    table_name = f"metrics_{ip_address.replace('.', '_')}"

    # Проверяем, существует ли таблица
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, [table_name])
        exists = cursor.fetchone()[0]

    if not exists:
        return JsonResponse({"error": "Таблица метрик не найдена"}, status=404)

    # Извлекаем последние 10 записей из таблицы
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT * 
            FROM {table_name} 
            ORDER BY timestamp DESC 
            LIMIT 10;
        """)
        columns = [col[0] for col in cursor.description]  # Получаем названия колонок
        rows = cursor.fetchall()  # Получаем данные

    # Преобразуем время в нужный формат (YYYY-MM-DD HH:MM:SS)
    for row in rows:
        row = list(row)
        # Предположим, что timestamp находится в первом столбце, если он в другом столбце, измените индекс
        row[0] = row[0].strftime('%Y-%m-%d %H:%M:%S')  # Форматируем время в нужный формат

    # Формируем JSON-ответ
    data = {
        "columns": columns,
        "rows": rows,
    }
    return JsonResponse(data)


# Функция для получения логов в формате JSON
def get_logs(request):
    # Получаем последние 3 лога
    logs = SystemLog.objects.order_by('-timestamp')[:3]

    # Преобразуем их в список словарей
    logs_data = [{
        'ip_address': log.ip_address,
        'ram_usage': log.ram_usage,
        'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),  # Форматируем время
        'cpu_load': log.cpu_load,
        'log_message': log.log_message,
        'temperature': log.temperature,
    } for log in logs]

    # Возвращаем данные в формате JSON
    return JsonResponse({'logs': logs_data})