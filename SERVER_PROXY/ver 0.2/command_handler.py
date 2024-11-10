from email_utils import get_email_response, send_email_response
import time

def await_server_command(server_ip):
    print("Ожидание команды от главного сервера...")
    while True:
        command_email = get_email_response(f"Answer server - {server_ip}")
        if command_email:
            if "collect_metrics" in command_email.lower():
                print("Получена команда на сбор метрик.")
                # Здесь можно вызвать функцию сбора и отправки метрик
            elif "stop" in command_email.lower():
                print("Получена команда остановки.")
                break
            else:
                print("Неизвестная команда получена:", command_email)
        else:
            print("Команда не получена. Проверка через 5 секунд.")
        time.sleep(5)