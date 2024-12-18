import configparser
import os

CONFIG_FILE = "config.ini"

# Проверка существования и инициализация файла конфигурации
def initialize_config():
    config = configparser.ConfigParser()

    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as configfile:
            # Задаем базовую структуру
            config["DATABASE"] = {"DB_NAME": "", "DB_USER": "", "DB_PASSWORD": "", "DB_HOST": "", "DB_PORT": ""}
            config["SMTP"] = {"SMTP_SERVER": "", "SMTP_PORT": "", "SMTP_USER": "", "SMTP_PASSWORD": ""}
            config["IMAP"] = {"IMAP_SERVER": "", "IMAP_USER": "", "IMAP_PASSWORD": ""}
            config["FLAG"] = {"FLAG": "FALSE"}
            config["SYSTEM"] = {"SYSTEN_INFO_SENT": "False"}
            config.write(configfile)
    else:
        config.read(CONFIG_FILE)
    return config

# Проверка флага и доступности данных
def check_flag_and_data(config):
    if config["FLAG"].get("FLAG", "FALSE") == "TRUE":
        return True
    return False

# Запрос у пользователя данных для конфигурации
def prompt_for_data(config):
    print("Введите данные для подключения:")

    # Ввод данных для базы данных
    config["DATABASE"]["DB_NAME"] = input("Имя базы данных: ")
    config["DATABASE"]["DB_USER"] = input("Пользователь базы данных: ")
    config["DATABASE"]["DB_PASSWORD"] = input("Пароль базы данных: ")
    config["DATABASE"]["DB_HOST"] = input("Хост базы данных: ")
    config["DATABASE"]["DB_PORT"] = input("Порт базы данных: ")

    # Ввод данных для SMTP
    config["SMTP"]["SMTP_SERVER"] = input("SMTP сервер: ")
    config["SMTP"]["SMTP_PORT"] = input("SMTP порт: ")
    config["SMTP"]["SMTP_USER"] = input("SMTP пользователь: ")
    config["SMTP"]["SMTP_PASSWORD"] = input("SMTP пароль: ")

    # Ввод данных для IMAP
    config["IMAP"]["IMAP_SERVER"] = input("IMAP сервер: ")
    config["IMAP"]["IMAP_USER"] = input("IMAP пользователь: ")
    config["IMAP"]["IMAP_PASSWORD"] = input("IMAP пароль: ")

    # Установка флага
    config["FLAG"]["FLAG"] = "TRUE"

    # Сохранение данных
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
    print("Данные успешно сохранены в config.ini.")

def save_config(config):
    """Сохраняет изменения конфигурации в файл config.ini."""
    with open("config.ini", "w") as configfile:
        config.write(configfile)